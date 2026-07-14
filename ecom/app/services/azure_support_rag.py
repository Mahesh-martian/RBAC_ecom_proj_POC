"""Azure OpenAI + Azure AI Search RAG service for support/policy queries."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
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
from app.services.embedding_provider import aembed_texts
from app.services.usage_metrics import usage_metrics

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
        """Create the index if missing, or non-destructively add the ``audience`` field.

        Adding a field is a backward-compatible schema change. To avoid the "cannot
        modify vector-search algorithm" error, we never re-send the vector config on an
        existing index: we fetch it, append ``audience`` if absent, and update in place.
        Only when the index does not exist do we build the full definition from scratch.
        No documents are deleted.
        """
        if not self._enabled:
            return

        index_name = self._settings.azure_search_index_name

        # Fast path: index already exists -> only ensure the audience field is present,
        # preserving Azure's stored vector-search algorithm/profile exactly.
        try:
            existing = self._index_client.get_index(index_name)
        except Exception:
            existing = None

        if existing is not None:
            has_audience = any(f.name == "audience" for f in existing.fields)
            if not has_audience:
                existing.fields.append(
                    SimpleField(
                        name="audience",
                        type=SearchFieldDataType.String,
                        filterable=True,
                        facetable=True,
                    )
                )
                self._index_client.create_or_update_index(existing)
            return

        # No existing index: build the full definition fresh.
        fields = [
            SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="source", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            # RBAC tag (customer/vendor/common) derived from the policy subfolder;
            # filterable so retrieval can scope results to the caller's role.
            SimpleField(name="audience", type=SearchFieldDataType.String, filterable=True, facetable=True),
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

    async def _purge_all_documents(self) -> int:
        """Delete every document from the index while keeping its schema intact.

        Chunk IDs are derived from ``{file}:{chunk_index}``, so a re-run with a
        different chunking strategy leaves orphaned high-index chunks behind. Clearing
        first guarantees the index reflects only the current policy content.
        """
        results = await self._search_client.search(search_text="*", select=["chunk_id"])
        keys = [doc["chunk_id"] async for doc in results]
        deleted = 0
        for i in range(0, len(keys), 1000):
            batch = [{"chunk_id": k} for k in keys[i : i + 1000]]
            await self._search_client.delete_documents(documents=batch)
            deleted += len(batch)
        return deleted

    async def index_policy_documents(self, policies_dir: Path, limit: int | None = None) -> int:
        """Chunk and upload local policy markdown files into Azure AI Search.

        When ``limit`` is set, only the first ``limit`` chunks are embedded/uploaded
        and the destructive purge is skipped. This enables a cheap end-to-end test
        (embed -> upload -> retrieve) before committing to the full paid run.
        """
        if not self._enabled:
            return 0

        files = sorted(policies_dir.rglob("*.md"))
        if not files:
            return 0

        # Remove stale chunks from previous runs before re-indexing (keeps schema).
        # Skipped for limited test runs so existing data is never destroyed.
        if limit is None:
            await self._purge_all_documents()

        docs: list[dict[str, Any]] = []
        # Imported lazily: ``langchain_text_splitters`` eagerly pulls in optional
        # heavy deps (e.g. spacy) at package import, so we defer it to the one
        # method that needs it to keep module import light and resilient.
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # Pack content into ~1000-char chunks instead of splitting on every blank
        # line. The scraped vendor pages contain thousands of tiny sections; naive
        # blank-line splitting produced ~9.5k noisy chunks. Recursive splitting keeps
        # related text together and collapses the count to a few hundred clean chunks.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n| ", "\n", ". ", " ", ""],
        )
        for file_path in files:
            rel = file_path.relative_to(policies_dir).as_posix()
            # Audience is the immediate subfolder (customer/vendor/common); files at
            # the policies root default to "common" so everyone can see them.
            parent = file_path.parent.name.lower()
            audience = parent if file_path.parent != policies_dir else "common"
            raw = file_path.read_text(encoding="utf-8")
            title = raw.splitlines()[0].lstrip("# ").strip() if raw.splitlines() else file_path.stem
            sections = [s.strip() for s in splitter.split_text(raw) if s.strip()]
            for idx, section in enumerate(sections):
                chunk_id = hashlib.sha256(f"{rel}:{idx}".encode()).hexdigest()[:40]
                docs.append(
                    {
                        "chunk_id": chunk_id,
                        "title": title,
                        "source": rel,
                        "content": section,
                        "category": "policy",
                        "audience": audience,
                    }
                )

        # Embed in batches. A smaller batch plus a short inter-batch pause keeps the
        # request rate under the AIServices S0 tier limit (retries in the embedding
        # provider cover any remaining transient 429s).
        if limit is not None:
            docs = docs[:limit]
        batch_size = 32
        batch_delay = 0.5
        with_vectors: list[dict[str, Any]] = []
        for i in range(0, len(docs), batch_size):
            batch = docs[i : i + batch_size]
            vectors = await aembed_texts([d["content"] for d in batch], kind="document")
            for d, vec in zip(batch, vectors):
                d["content_vector"] = vec
                with_vectors.append(d)
            if i + batch_size < len(docs):
                await asyncio.sleep(batch_delay)

        # Upload in small batches so a single request never exceeds the Azure Search
        # request-size limit. Uploading everything at once triggers a 413 and the
        # SDK's buggy auto-split recovery path (KeyError: 'error_map' in 11.6.0b9).
        upload_batch_size = 50
        succeeded = 0
        for i in range(0, len(with_vectors), upload_batch_size):
            batch = with_vectors[i : i + upload_batch_size]
            result = await self._search_client.merge_or_upload_documents(documents=batch)
            succeeded += sum(1 for r in result if r.succeeded)
        return succeeded

    async def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Retrieve top policy chunks via hybrid+vector search."""
        if not self._enabled:
            return []

        vector = (await aembed_texts([query], kind="query"))[0]

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

        llm_started = time.perf_counter()
        llm_error = False
        completion = None
        try:
            completion = await self._client.chat.completions.create(
                model=self._settings.azure_openai_chat_deployment,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=280,
            )
        except Exception:
            llm_error = True
            raise
        finally:
            usage = getattr(completion, "usage", None) if completion is not None else None
            usage_metrics.record(
                "azure_openai_chat",
                latency_ms=round((time.perf_counter() - llm_started) * 1000, 1),
                prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
                error=llm_error,
            )
        answer = completion.choices[0].message.content or "I do not have enough policy context to answer that question."
        return answer, citations, top_score

    async def close(self) -> None:
        if self._search_client:
            await self._search_client.close()
        if self._client:
            await self._client.close()
