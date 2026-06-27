"""LangChain-backed policy RAG service using Azure OpenAI for embeddings and generation."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter
from openai import AzureOpenAI, BadRequestError

from app.config import settings


@dataclass
class LangChainSupportResult:
    answer: str
    citations: list[str]
    confidence: float
    latency_ms: float


class _AzureOpenAIEmbeddingsAdapter(Embeddings):
    """LangChain embedding adapter backed by Azure OpenAI SDK v1.x."""

    def __init__(self) -> None:
        self._client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_embedding_deployment
        self._dimensions = settings.azure_search_vector_dimensions
        self._supports_dimensions = self._deployment.startswith("text-embedding-3")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload: dict[str, object] = {
            "model": self._deployment,
            "input": texts,
        }
        if self._supports_dimensions:
            payload["dimensions"] = self._dimensions
        response = self._client.embeddings.create(**payload)
        return [d.embedding for d in sorted(response.data, key=lambda d: d.index)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class LangChainSupportRAGService:
    """In-memory LangChain retriever over local policy markdown docs backed by Azure OpenAI."""

    def __init__(self, policies_dir: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self._policies_dir = policies_dir or (base_dir / "policies")
        self._azure_ready = bool(
            settings.azure_openai_endpoint
            and settings.azure_openai_api_key
            and settings.azure_openai_embedding_deployment
            and settings.azure_openai_chat_deployment
        )
        self._embeddings = _AzureOpenAIEmbeddingsAdapter() if self._azure_ready else None
        self._llm_client = (
            AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            if self._azure_ready
            else None
        )
        self._chat_deployment = settings.azure_openai_chat_deployment
        # Prefer newer token parameter by default; downgrade once if deployment rejects it.
        self._prefer_max_completion_tokens = True
        self._store = InMemoryVectorStore(self._embeddings) if self._azure_ready and self._embeddings else None
        self._loaded = False

    @property
    def is_configured(self) -> bool:
        """True when Azure OpenAI settings are present and the backend can answer."""
        return self._azure_ready

    def _load(self) -> None:
        if self._loaded:
            return
        if not self._azure_ready or not self._store:
            self._loaded = True
            return

        documents: list[Document] = []
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "title"), ("##", "section")],
            strip_headers=False,
        )

        if self._policies_dir.exists():
            for file_path in sorted(self._policies_dir.rglob("*.md")):
                parent_name = file_path.parent.name.lower()
                audience = parent_name if file_path.parent != self._policies_dir else "common"
                text = file_path.read_text(encoding="utf-8")
                title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else file_path.stem
                split_docs = splitter.split_text(text)
                if not split_docs:
                    split_docs = [Document(page_content=text, metadata={})]

                for index, doc in enumerate(split_docs):
                    metadata = dict(doc.metadata)
                    metadata.update(
                        {
                            "chunk_id": f"{file_path.stem}-{index}",
                            "title": metadata.get("title") or title,
                            "source": file_path.name,
                            "audience": audience,
                        }
                    )
                    documents.append(Document(page_content=doc.page_content, metadata=metadata))

        if documents:
            self._store.add_documents(documents)
        self._loaded = True

    async def answer(
        self,
        query: str,
        top_k: int = 3,
        user_name: Optional[str] = None,
        history: Optional[list[tuple[str, str]]] = None,
        audiences: Optional[set[str]] = None,
        persona: Optional[str] = None,
    ) -> LangChainSupportResult:
        return await asyncio.to_thread(
            self._answer_sync, query, top_k, user_name, history, audiences, persona
        )

    def _answer_sync(
        self,
        query: str,
        top_k: int,
        user_name: Optional[str] = None,
        history: Optional[list[tuple[str, str]]] = None,
        audiences: Optional[set[str]] = None,
        persona: Optional[str] = None,
    ) -> LangChainSupportResult:
        if not self._azure_ready or not self._llm_client or not self._store:
            return LangChainSupportResult(
                answer="LangChain Azure backend is not configured yet. Set AZURE_OPENAI_* settings for the API service.",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
            )

        self._load()
        started = time.perf_counter()

        if not query.strip():
            return LangChainSupportResult(
                answer="I do not have enough policy context to answer that yet. Please contact support with your order number.",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
            )

        allowed = {a.lower() for a in audiences} if audiences else None
        doc_filter = None
        if allowed is not None:
            def doc_filter(doc: Document) -> bool:
                return str(doc.metadata.get("audience", "common")).lower() in allowed

        docs_with_scores = self._store.similarity_search_with_score(
            query, k=top_k, filter=doc_filter
        )
        if not docs_with_scores:
            return LangChainSupportResult(
                answer="I do not have enough policy context to answer that yet. Please contact support with your order number.",
                citations=[],
                confidence=0.0,
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
            )

        citations: list[str] = []
        seen: set[str] = set()
        context_blocks: list[str] = []
        top_score = 0.0

        for idx, (doc, score) in enumerate(docs_with_scores, start=1):
            title = str(doc.metadata.get("title") or "Untitled")
            source = str(doc.metadata.get("source") or "unknown")
            citation = f"{title} ({source})"
            if citation not in seen:
                seen.add(citation)
                citations.append(citation)
            snippet = doc.page_content.replace("\n", " ").strip()
            if len(snippet) > 220:
                snippet = snippet[:217] + "..."
            context_blocks.append(f"[{idx}] {title} ({source}): {snippet}")
            top_score = max(top_score, float(score))

        system_prompt = (
            "You are a customer support assistant. Answer only from provided policy context. "
            "If insufficient context exists, say you do not have enough information. "
            "Keep answers concise and actionable."
        )
        if persona:
            system_prompt = persona + " " + system_prompt
        if user_name:
            system_prompt += (
                f" Address the customer by their first name, {user_name}, when it feels natural."
            )

        history_block = ""
        if history:
            recent = history[-6:]
            history_block = (
                "Recent conversation:\n"
                + "\n".join(f"{role}: {text}" for role, text in recent)
                + "\n\n"
            )
        user_prompt = (
            history_block
            + "Policy context:\n"
            + "\n\n".join(context_blocks)
            + f"\n\nQuestion: {query}"
        )

        completion_kwargs: dict[str, object] = {
            "model": self._chat_deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self._prefer_max_completion_tokens:
            completion_kwargs["max_completion_tokens"] = 320
        else:
            completion_kwargs["max_tokens"] = 320

        for _ in range(3):
            try:
                completion = self._llm_client.chat.completions.create(**completion_kwargs)
                break
            except BadRequestError as exc:
                message = str(exc)
                adjusted = False
                if "max_completion_tokens" in message and "max_completion_tokens" in completion_kwargs:
                    completion_kwargs.pop("max_completion_tokens", None)
                    completion_kwargs["max_tokens"] = 320
                    self._prefer_max_completion_tokens = False
                    adjusted = True
                if "max_tokens" in message and "max_tokens" in completion_kwargs:
                    completion_kwargs.pop("max_tokens", None)
                    completion_kwargs["max_completion_tokens"] = 320
                    self._prefer_max_completion_tokens = True
                    adjusted = True
                if not adjusted:
                    raise
        else:
            completion = self._llm_client.chat.completions.create(**completion_kwargs)

        content = completion.choices[0].message.content or ""
        answer = content.strip() or "I do not have enough policy context to answer that yet."

        return LangChainSupportResult(
            answer=answer,
            citations=citations,
            confidence=round(top_score, 4),
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )
