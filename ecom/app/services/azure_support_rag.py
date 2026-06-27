"""Azure OpenAI + Azure AI Search RAG service for support/policy queries."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.aio import SearchClient as AsyncSearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SearchableField,
        SemanticConfiguration,
        SemanticField,
        SemanticPrioritizedFields,
        SemanticSearch,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )
    from azure.search.documents.models import VectorizedQuery
    from openai import AsyncAzureOpenAI
    _AZURE_SDK_AVAILABLE = True
except ModuleNotFoundError:
    _AZURE_SDK_AVAILABLE = False

from app.config import Settings

logger = logging.getLogger(__name__)


class AzureSupportRAGService:
    """RAG over policy docs using Azure OpenAI and Azure AI Search."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._enabled = settings.azure_rag_configured and _AZURE_SDK_AVAILABLE
        if not self._enabled:
            self._client = None
            self._index_client = None
            self._search_client = None
            if settings.azure_rag_configured and not _AZURE_SDK_AVAILABLE:
                logger.warning("Azure RAG disabled because Azure SDK dependencies are not installed")
            return

        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        credential = AzureKeyCredential(settings.azure_search_admin_key)
        self._index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=credential,
        )
        try:
            self._search_client = AsyncSearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=credential,
            )
        except ModuleNotFoundError as exc:
            self._enabled = False
            self._client = None
            self._index_client = None
            self._search_client = None
            logger.warning(
                "Azure RAG disabled because async transport dependency is missing: %s",
                exc,
            )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def ensure_index(self) -> None:
        """Create index if missing."""
        if not self._enabled:
            return

        index_name = self._settings.azure_search_index_name
        existing = [idx.name for idx in self._index_client.list_indexes()]
        if index_name in existing:
            return

        fields = [
            SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="source", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self._settings.azure_search_vector_dimensions,
                vector_search_profile_name="support-hnsw-profile",
            ),
        ]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="support-hnsw")],
                profiles=[
                    VectorSearchProfile(
                        name="support-hnsw-profile",
                        algorithm_configuration_name="support-hnsw",
                    )
                ],
            ),
            semantic_search=SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name=self._settings.azure_search_semantic_config,
                        prioritized_fields=SemanticPrioritizedFields(
                            content_fields=[SemanticField(field_name="content")],
                            keywords_fields=[SemanticField(field_name="title")],
                        ),
                    )
                ]
            ),
        )
        self._index_client.create_index(index)

    async def index_policy_documents(self, policies_dir: Path) -> int:
        """Chunk and upload local policy markdown files into Azure AI Search."""
        if not self._enabled:
            return 0

        files = sorted(policies_dir.glob("*.md"))
        if not files:
            return 0

        docs: list[dict[str, Any]] = []
        for file_path in files:
            raw = file_path.read_text(encoding="utf-8")
            title = raw.splitlines()[0].lstrip("# ").strip() if raw.splitlines() else file_path.stem
            sections = [s.strip() for s in raw.split("\n\n") if s.strip()]
            for idx, section in enumerate(sections):
                chunk_id = hashlib.sha256(f"{file_path.name}:{idx}".encode()).hexdigest()[:40]
                docs.append(
                    {
                        "chunk_id": chunk_id,
                        "title": title,
                        "source": file_path.name,
                        "content": section,
                        "category": "policy",
                    }
                )

        # Embed in small batches
        batch_size = 16
        with_vectors: list[dict[str, Any]] = []
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            emb = await self._client.embeddings.create(
                model=self._settings.azure_openai_embedding_deployment,
                input=[d["content"] for d in batch],
            )
            for d, e in zip(batch, emb.data):
                d["content_vector"] = e.embedding
                with_vectors.append(d)

        result = await self._search_client.merge_or_upload_documents(documents=with_vectors)
        return sum(1 for r in result if r.succeeded)

    async def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Retrieve top policy chunks via hybrid+vector search."""
        if not self._enabled:
            return []

        query_embedding = await self._client.embeddings.create(
            model=self._settings.azure_openai_embedding_deployment,
            input=query,
        )
        vector = query_embedding.data[0].embedding

        k = top_k or self._settings.rag_top_k
        results = await self._search_client.search(
            search_text=query,
            vector_queries=[
                VectorizedQuery(
                    vector=vector,
                    k_nearest_neighbors=k,
                    fields="content_vector",
                )
            ],
            query_type="semantic",
            semantic_configuration_name=self._settings.azure_search_semantic_config,
            top=k,
            select=["title", "source", "content", "category"],
        )

        chunks: list[dict[str, Any]] = []
        async for row in results:
            chunks.append(
                {
                    "title": row.get("title", "Untitled"),
                    "source": row.get("source", "unknown"),
                    "content": row.get("content", ""),
                    "score": row.get("@search.reranker_score") or row.get("@search.score") or 0,
                }
            )

        return chunks

    async def answer(self, query: str, top_k: int | None = None) -> tuple[str, list[str], float]:
        """Generate grounded answer with citations from retrieved policy chunks."""
        if not self._enabled:
            return "", [], 0.0

        chunks = await self.retrieve(query, top_k=top_k)
        if not chunks:
            return "I do not have enough policy context to answer that question.", [], 0.0

        top_score = float(chunks[0].get("score", 0.0))
        if top_score < self._settings.rag_min_azure_score:
            return "I do not have enough policy context to answer that question.", [], top_score

        context_parts = []
        citations: list[str] = []
        seen_citations: set[str] = set()
        for idx, ch in enumerate(chunks, start=1):
            context_parts.append(f"[{idx}] {ch['title']} ({ch['source']}): {ch['content']}")
            citation = f"{ch['title']} ({ch['source']})"
            if citation not in seen_citations:
                seen_citations.add(citation)
                citations.append(citation)

        system = (
            "You are a customer support assistant. Use only the provided policy context. "
            "If context is insufficient, say you do not have enough information. "
            "Keep answers concise and actionable."
        )
        user = f"Policy context:\n" + "\n\n".join(context_parts) + f"\n\nQuestion: {query}"

        completion = await self._client.chat.completions.create(
            model=self._settings.azure_openai_chat_deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=280,
        )
        answer = completion.choices[0].message.content or "I do not have enough policy context to answer that question."
        return answer, citations, top_score

    async def close(self) -> None:
        if self._search_client:
            await self._search_client.close()
        if self._client:
            await self._client.close()
