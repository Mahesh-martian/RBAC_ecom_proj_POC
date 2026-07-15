"""LangChain-style policy RAG service: retrieves from Azure AI Search, generates with Azure OpenAI."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from openai import AzureOpenAI, BadRequestError

from app.config import settings
from app.logging_utils import log_step
from app.services.prompt_registry import PromptNotFoundError, get_prompt_registry
from app.services.usage_metrics import usage_metrics

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import HttpResponseError
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
    _AZURE_SEARCH_AVAILABLE = True
except ModuleNotFoundError:
    _AZURE_SEARCH_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class LangChainSupportResult:
    answer: str
    citations: list[str]
    confidence: float
    latency_ms: float
    # Azure usage metrics captured during the request (0 when not applicable).
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retrieval_count: int = 0
    search_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    # Version of the system prompt used to build this answer, e.g.
    # ``support_system@v2``. Empty string when the registry lookup fell back to
    # the hard-coded default.
    system_prompt_label: str = ""


def _is_semantic_unsupported(exc: "HttpResponseError") -> bool:
    """True when the search service tier rejects semantic ranking."""
    message = str(getattr(exc, "message", "") or exc).lower()
    return "semantic" in message and (
        "not enabled" in message or "not available" in message or "notsupported" in message
    )


class LangChainSupportRAGService:
    """Policy RAG that retrieves from the Azure AI Search index and answers with Azure OpenAI.

    RBAC is enforced at retrieval time via an OData filter on the ``audience`` field
    (populated from the policy subfolder during indexing), so a caller only ever sees
    chunks for their allowed audiences.
    """

    def __init__(self) -> None:
        self._azure_ready = settings.azure_rag_configured and _AZURE_SEARCH_AVAILABLE
        self._chat_deployment = settings.azure_openai_chat_deployment
        self._embedding_deployment = settings.azure_openai_embedding_deployment
        self._semantic_config = settings.azure_search_semantic_config
        self._dimensions = settings.azure_search_vector_dimensions
        self._supports_dimensions = bool(
            self._embedding_deployment and self._embedding_deployment.startswith("text-embedding-3")
        )
        # Prefer newer token parameter by default; downgrade once if deployment rejects it.
        self._prefer_max_completion_tokens = True
        # Some Azure AI Search tiers (Free/Basic) do not support semantic ranking;
        # fall back to plain hybrid search and remember so we skip the failing call.
        self._semantic_unavailable = False

        if self._azure_ready:
            self._llm_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            self._search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index_name,
                credential=AzureKeyCredential(settings.azure_search_admin_key),
            )
        else:
            self._llm_client = None
            self._search_client = None

    @property
    def is_configured(self) -> bool:
        """True when Azure OpenAI + Azure AI Search settings are present."""
        return self._azure_ready

    def _embed_query(self, text: str) -> list[float]:
        from app.services.embedding_provider import embed_texts

        started = time.perf_counter()
        vector = embed_texts([text], kind="query")[0]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        log_step(
            logger,
            "embed_query",
            enabled=settings.rag_step_logging,
            latency_ms=elapsed_ms,
            dimensions=len(vector),
        )
        return vector

    @staticmethod
    def _audience_filter(audiences: Optional[set[str]]) -> Optional[str]:
        """Build an OData filter scoping results to the caller's allowed audiences."""
        if not audiences:
            return None
        return " or ".join(f"audience eq '{a.lower()}'" for a in sorted(audiences))

    def _search(
        self,
        query: str,
        vector: list[float],
        top_k: int,
        audiences: Optional[set[str]],
    ):
        """Retrieve from Azure AI Search, preferring semantic ranking with a hybrid fallback.

        RBAC is enforced here via the ``audience`` OData filter regardless of the
        ranking mode, so falling back to plain hybrid search never widens access.
        """
        common_kwargs = dict(
            search_text=query,
            vector_queries=[
                VectorizedQuery(vector=vector, k_nearest_neighbors=top_k, fields="content_vector")
            ],
            filter=self._audience_filter(audiences),
            top=top_k,
            select=["title", "source", "content", "audience"],
        )
        started = time.perf_counter()
        mode = "hybrid"
        error = False
        results: list = []
        try:
            if not self._semantic_unavailable:
                try:
                    results = list(
                        self._search_client.search(
                            query_type="semantic",
                            semantic_configuration_name=self._semantic_config,
                            **common_kwargs,
                        )
                    )
                    mode = "semantic"
                    return results
                except HttpResponseError as exc:
                    if not _is_semantic_unsupported(exc):
                        error = True
                        raise
                    # Remember so we don't pay the failed round-trip on every request.
                    self._semantic_unavailable = True
                    log_step(
                        logger,
                        "retrieve_semantic_fallback",
                        enabled=settings.rag_step_logging,
                        reason="semantic_ranking_unavailable",
                    )
            results = list(self._search_client.search(**common_kwargs))
            return results
        except Exception:
            error = True
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            usage_metrics.record(
                "azure_ai_search",
                latency_ms=elapsed_ms,
                result_count=len(results),
                error=error,
            )
            log_step(
                logger,
                "retrieve",
                enabled=settings.rag_step_logging,
                mode=mode,
                top_k=top_k,
                audience_filter=bool(audiences),
                audiences=sorted(audiences) if audiences else [],
                result_count=len(results),
                latency_ms=elapsed_ms,
                error=error,
            )

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
        if not self._azure_ready or not self._llm_client or not self._search_client:
            return LangChainSupportResult(
                answer="LangChain Azure backend is not configured yet. Set AZURE_OPENAI_* and AZURE_SEARCH_* settings for the API service.",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
            )

        if not query.strip():
            return LangChainSupportResult(
                answer="I do not have enough policy context to answer that yet. Please contact support with your order number.",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
            )

        started = time.perf_counter()
        vector = self._embed_query(query)
        search_started = time.perf_counter()
        results = self._search(
            query=query,
            vector=vector,
            top_k=top_k,
            audiences=audiences,
        )
        search_latency_ms = round((time.perf_counter() - search_started) * 1000, 1)
        rows = [
            (
                str(r.get("title") or "Untitled"),
                str(r.get("source") or "unknown"),
                str(r.get("content") or ""),
                float(r.get("@search.reranker_score") or r.get("@search.score") or 0.0),
            )
            for r in results
        ]
        if not rows:
            log_step(
                logger,
                "no_context",
                enabled=settings.rag_step_logging,
                search_latency_ms=search_latency_ms,
            )
            return LangChainSupportResult(
                answer="I do not have enough policy context to answer that yet. Please contact support with your order number.",
                citations=[],
                confidence=0.0,
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                retrieval_count=0,
                search_latency_ms=search_latency_ms,
            )

        citations: list[str] = []
        seen: set[str] = set()
        context_blocks: list[str] = []
        top_score = 0.0

        for idx, (title, source, content, score) in enumerate(rows, start=1):
            citation = f"{title} ({source})"
            if citation not in seen:
                seen.add(citation)
                citations.append(citation)
            snippet = content.replace("\n", " ").strip()
            if len(snippet) > 220:
                snippet = snippet[:217] + "..."
            context_blocks.append(f"[{idx}] {title} ({source}): {snippet}")
            top_score = max(top_score, score)

        # Log retrieved sources + scores only (never document content) so logs do
        # not leak policy text.
        log_step(
            logger,
            "retrieve_docs",
            enabled=settings.rag_step_logging,
            retrieval_count=len(rows),
            documents=[
                {"title": t, "source": s, "score": round(sc, 4)}
                for (t, s, _content, sc) in rows
            ],
            top_score=round(top_score, 4),
        )

        system_prompt_label = ""
        try:
            support_prompt = get_prompt_registry().get("support_system")
            system_prompt = support_prompt.template.strip() or (
                "You are a customer support assistant. Answer only from provided policy context. "
                "If insufficient context exists, say you do not have enough information. "
                "Keep answers concise and actionable."
            )
            system_prompt_label = support_prompt.label
        except PromptNotFoundError as exc:
            logger.warning(
                "prompt_registry support_system miss: %s; using hard-coded fallback", exc
            )
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

        log_step(
            logger,
            "prompt",
            enabled=settings.rag_step_logging,
            context_blocks=len(context_blocks),
            system_prompt_chars=len(system_prompt),
            user_prompt_chars=len(user_prompt),
            history_turns=len(history[-6:]) if history else 0,
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

        llm_started = time.perf_counter()
        token_param_downgraded = False
        llm_error = False
        completion = None
        try:
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
                        token_param_downgraded = True
                    if "max_tokens" in message and "max_tokens" in completion_kwargs:
                        completion_kwargs.pop("max_tokens", None)
                        completion_kwargs["max_completion_tokens"] = 320
                        self._prefer_max_completion_tokens = True
                        adjusted = True
                        token_param_downgraded = True
                    if not adjusted:
                        raise
            else:
                completion = self._llm_client.chat.completions.create(**completion_kwargs)
        except Exception:
            llm_error = True
            raise
        finally:
            llm_latency_ms = round((time.perf_counter() - llm_started) * 1000, 1)
            _usage = getattr(completion, "usage", None) if completion is not None else None
            _prompt_tokens = int(getattr(_usage, "prompt_tokens", 0) or 0)
            _completion_tokens = int(getattr(_usage, "completion_tokens", 0) or 0)
            _total_tokens = int(getattr(_usage, "total_tokens", 0) or 0)
            usage_metrics.record(
                "azure_openai_chat",
                latency_ms=llm_latency_ms,
                prompt_tokens=_prompt_tokens,
                completion_tokens=_completion_tokens,
                total_tokens=_total_tokens,
                error=llm_error,
            )
            log_step(
                logger,
                "llm",
                enabled=settings.rag_step_logging,
                deployment=self._chat_deployment,
                latency_ms=llm_latency_ms,
                prompt_tokens=_prompt_tokens,
                completion_tokens=_completion_tokens,
                total_tokens=_total_tokens,
                finish_reason=(
                    completion.choices[0].finish_reason
                    if completion is not None and completion.choices
                    else None
                ),
                token_param_downgraded=token_param_downgraded,
                error=llm_error,
            )

        content = completion.choices[0].message.content or ""
        answer = content.strip() or "I do not have enough policy context to answer that yet."

        return LangChainSupportResult(
            answer=answer,
            citations=citations,
            confidence=round(top_score, 4),
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            prompt_tokens=_prompt_tokens,
            completion_tokens=_completion_tokens,
            total_tokens=_total_tokens,
            retrieval_count=len(rows),
            search_latency_ms=search_latency_ms,
            llm_latency_ms=llm_latency_ms,
            system_prompt_label=system_prompt_label,
        )
