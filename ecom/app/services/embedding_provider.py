"""Unified text-embedding provider.

Embeddings may be served by either:

* **Azure AI Foundry / Azure AI Inference** -- e.g. Cohere ``embed-v-4-0`` -- when
  ``AZURE_EMBEDDING_ENDPOINT`` + ``AZURE_EMBEDDING_API_KEY`` are configured, or
* **Azure OpenAI** (``text-embedding-*``) as the fallback.

Every embedding call site (document indexing, policy retrieval, and the semantic
intent router) goes through this module so that query and document vectors always
come from the *same* model -- mixing models would make cosine similarity meaningless.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Optional

from app.config import settings
from app.logging_utils import log_step
from app.services.usage_metrics import usage_metrics

logger = logging.getLogger(__name__)

# Azure AI Inference (Foundry) SDK -- used for Cohere/partner embedding models.
try:
    from azure.ai.inference import EmbeddingsClient
    from azure.ai.inference.aio import EmbeddingsClient as AsyncEmbeddingsClient
    from azure.ai.inference.models import EmbeddingInputType
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import HttpResponseError

    _INFERENCE_AVAILABLE = True
except ModuleNotFoundError:
    _INFERENCE_AVAILABLE = False

# Azure OpenAI SDK -- fallback when no dedicated inference endpoint is configured.
try:
    from openai import AsyncAzureOpenAI, AzureOpenAI

    _OPENAI_AVAILABLE = True
except ModuleNotFoundError:
    _OPENAI_AVAILABLE = False


def use_inference() -> bool:
    """True when a dedicated Azure AI Inference embedding endpoint is configured."""
    return _INFERENCE_AVAILABLE and bool(
        settings.azure_embedding_endpoint and settings.azure_embedding_api_key
    )


def _dimensions() -> Optional[int]:
    return settings.azure_search_vector_dimensions or None


def _input_type(kind: str):
    """Map our string kind to the SDK's EmbeddingInputType.

    Cohere distinguishes query vs document embeddings; ``text`` is the neutral type
    used for symmetric similarity (e.g. the intent router).
    """
    return {
        "query": EmbeddingInputType.QUERY,
        "document": EmbeddingInputType.DOCUMENT,
        "text": EmbeddingInputType.TEXT,
    }.get(kind, EmbeddingInputType.TEXT)


# --- Lazily-cached clients (reused across calls within the app's single loop). ---
_sync_inference_client: "EmbeddingsClient | None" = None
_async_inference_client: "AsyncEmbeddingsClient | None" = None
_sync_openai_client: "AzureOpenAI | None" = None
_async_openai_client: "AsyncAzureOpenAI | None" = None


def _get_sync_inference() -> "EmbeddingsClient":
    global _sync_inference_client
    if _sync_inference_client is None:
        _sync_inference_client = EmbeddingsClient(
            endpoint=settings.azure_embedding_endpoint,
            credential=AzureKeyCredential(settings.azure_embedding_api_key),
            model=settings.azure_openai_embedding_deployment,
        )
    return _sync_inference_client


def _get_async_inference() -> "AsyncEmbeddingsClient":
    global _async_inference_client
    if _async_inference_client is None:
        _async_inference_client = AsyncEmbeddingsClient(
            endpoint=settings.azure_embedding_endpoint,
            credential=AzureKeyCredential(settings.azure_embedding_api_key),
            model=settings.azure_openai_embedding_deployment,
        )
    return _async_inference_client


def _get_sync_openai() -> "AzureOpenAI":
    global _sync_openai_client
    if _sync_openai_client is None:
        _sync_openai_client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    return _sync_openai_client


def _get_async_openai() -> "AsyncAzureOpenAI":
    global _async_openai_client
    if _async_openai_client is None:
        _async_openai_client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    return _async_openai_client


def _openai_supports_dimensions() -> bool:
    dep = settings.azure_openai_embedding_deployment or ""
    return dep.startswith("text-embedding-3")


# Retry policy for transient embedding failures (notably 429 rate limits on the
# AIServices S0 tier). Exponential backoff with jitter, honoring Retry-After.
_MAX_RETRIES = 6
_BASE_DELAY = 2.0


def _retry_delay(exc: "HttpResponseError", attempt: int) -> Optional[float]:
    """Seconds to wait before retrying, or None if the error is not retryable / exhausted."""
    status = getattr(exc, "status_code", None)
    if status not in (429, 500, 502, 503, 504):
        return None
    if attempt >= _MAX_RETRIES:
        return None
    # Prefer the server-provided Retry-After header when present.
    try:
        retry_after = exc.response.headers.get("Retry-After")  # type: ignore[union-attr]
        if retry_after:
            return float(retry_after) + random.uniform(0, 1)
    except Exception:
        pass
    return _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)


def _record_embedding(service: str, resp, count: int, kind: str, started: float) -> None:
    """Record usage metrics + emit a per-step log for one successful embedding call."""
    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    usage = getattr(resp, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or prompt_tokens)
    usage_metrics.record(
        service,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
    )
    log_step(
        logger,
        "embed",
        enabled=settings.rag_step_logging,
        service=service,
        kind=kind,
        text_count=count,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    )


def embed_texts(texts: list[str], kind: str = "document") -> list[list[float]]:
    """Embed a batch of texts synchronously, preserving input order."""
    if not texts:
        return []
    started = time.perf_counter()
    if use_inference():
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = _get_sync_inference().embed(
                    input=texts, dimensions=_dimensions(), input_type=_input_type(kind)
                )
                _record_embedding("azure_cohere_embeddings", resp, len(texts), kind, started)
                return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
            except HttpResponseError as exc:
                delay = _retry_delay(exc, attempt)
                if delay is None:
                    raise
                logger.warning("embedding retry in %.1fs after %s (attempt %d)", delay, getattr(exc, "status_code", "?"), attempt + 1)
                time.sleep(delay)

    payload: dict[str, object] = {
        "model": settings.azure_openai_embedding_deployment,
        "input": texts,
    }
    if _openai_supports_dimensions() and _dimensions():
        payload["dimensions"] = _dimensions()
    resp = _get_sync_openai().embeddings.create(**payload)
    _record_embedding("azure_openai_embeddings", resp, len(texts), kind, started)
    return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]


async def aembed_texts(texts: list[str], kind: str = "document") -> list[list[float]]:
    """Embed a batch of texts asynchronously, preserving input order."""
    if not texts:
        return []
    started = time.perf_counter()
    if use_inference():
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await _get_async_inference().embed(
                    input=texts, dimensions=_dimensions(), input_type=_input_type(kind)
                )
                _record_embedding("azure_cohere_embeddings", resp, len(texts), kind, started)
                return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
            except HttpResponseError as exc:
                delay = _retry_delay(exc, attempt)
                if delay is None:
                    raise
                logger.warning("embedding retry in %.1fs after %s (attempt %d)", delay, getattr(exc, "status_code", "?"), attempt + 1)
                await asyncio.sleep(delay)

    payload: dict[str, object] = {
        "model": settings.azure_openai_embedding_deployment,
        "input": texts,
    }
    if _openai_supports_dimensions() and _dimensions():
        payload["dimensions"] = _dimensions()
    resp = await _get_async_openai().embeddings.create(**payload)
    _record_embedding("azure_openai_embeddings", resp, len(texts), kind, started)
    return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
