"""External RAG API client with timeout and basic circuit breaker."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class ExternalRAGClient:
    """Call an external RAG service with guarded failure behavior."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._failure_count = 0
        self._opened_until = 0.0
        self._failure_threshold = 3
        self._open_seconds = 30
        self._timeout_seconds = max(1.0, float(settings.rag_chat_timeout_seconds))

    @property
    def enabled(self) -> bool:
        return bool(self._settings.rag_chat_api_url)

    def _circuit_open(self) -> bool:
        return time.monotonic() < self._opened_until

    def _record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._opened_until = time.monotonic() + self._open_seconds

    def _record_success(self) -> None:
        self._failure_count = 0
        self._opened_until = 0.0

    @staticmethod
    def _extract_response(data: dict[str, Any]) -> tuple[str, list[str], float, list[dict[str, Any]]]:
        """Normalize answer payload into app-level answer/citations/confidence fields."""
        answer = str(data.get("answer") or "").strip()
        raw_sources = data.get("sources") or []

        citations: list[str] = []
        seen: set[str] = set()
        confidence = 0.0
        for source in raw_sources:
            if not isinstance(source, dict):
                continue
            title = str(source.get("title") or "Untitled")
            src = str(source.get("source") or "unknown")
            citation = f"{title} ({src})"
            if citation not in seen:
                seen.add(citation)
                citations.append(citation)
            try:
                score = float(source.get("score") or 0.0)
                confidence = max(confidence, score)
            except (TypeError, ValueError):
                pass

        return answer, citations, confidence, raw_sources

    async def answer(self, query: str, request_id: str | None = None) -> tuple[str, list[str], float]:
        """Return answer, citations, and confidence from external RAG endpoint."""
        if not self.enabled:
            return "", [], 0.0

        if self._circuit_open():
            logger.warning("external_rag circuit open, skipping outbound call")
            return "", [], 0.0

        base_url = (self._settings.rag_chat_api_url or "").rstrip("/")
        headers = {"Content-Type": "application/json"}
        if self._settings.rag_chat_api_key:
            headers["X-API-Key"] = self._settings.rag_chat_api_key
        if request_id:
            headers["X-Request-Id"] = request_id

        payload: dict[str, Any] = {
            "query": query,
            "top_k": self._settings.rag_top_k,
            "return_sources": True,
            "search_mode": (
                self._settings.rag_chat_search_mode.strip().lower()
                if self._settings.rag_chat_search_mode
                else "keyword"
            ),
        }

        if payload["search_mode"] not in {"hybrid", "keyword", "vector"}:
            payload["search_mode"] = "keyword"

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                    response = await client.post(f"{base_url}/query", json=payload, headers=headers)

                if response.status_code >= 500:
                    logger.warning(
                        "external_rag upstream error status=%s attempt=%s request_id=%s",
                        response.status_code,
                        attempt,
                        request_id,
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep((0.2 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.15))
                        continue
                    self._record_failure()
                    return "", [], 0.0

                if response.status_code >= 400:
                    # Treat 4xx as non-retryable for now and avoid tripping the breaker.
                    logger.info(
                        "external_rag client-side reject status=%s request_id=%s",
                        response.status_code,
                        request_id,
                    )
                    return "", [], 0.0

                data = response.json()
                answer, citations, confidence, raw_sources = self._extract_response(data)

                # Some indexes rank better in keyword mode than hybrid/semantic.
                # Retry once with keyword when initial retrieval has no sources.
                if not raw_sources and payload["search_mode"] != "keyword":
                    retry_payload = dict(payload)
                    retry_payload["search_mode"] = "keyword"
                    async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                        retry_response = await client.post(f"{base_url}/query", json=retry_payload, headers=headers)
                    if retry_response.status_code < 400:
                        retry_data = retry_response.json()
                        retry_answer, retry_citations, retry_confidence, retry_sources = self._extract_response(retry_data)
                        if retry_sources:
                            answer = retry_answer
                            citations = retry_citations
                            confidence = retry_confidence

                if answer:
                    self._record_success()
                else:
                    self._record_failure()

                return answer, citations, confidence

            except Exception as exc:
                logger.warning(
                    "external_rag call failed attempt=%s request_id=%s error=%s",
                    attempt,
                    request_id,
                    repr(exc),
                )
                if attempt < max_attempts:
                    await asyncio.sleep((0.2 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.15))
                    continue
                self._record_failure()
                return "", [], 0.0

        return "", [], 0.0

    async def index_policy_documents(self, policies_dir: Path, request_id: str | None = None) -> int:
        """Upload local policy markdown files into the external RAG service."""
        if not self.enabled:
            return 0

        files = sorted(policies_dir.glob("*.md"))
        if not files:
            return 0

        base_url = (self._settings.rag_chat_api_url or "").rstrip("/")
        headers = {"Content-Type": "application/json"}
        if self._settings.rag_chat_api_key:
            headers["X-API-Key"] = self._settings.rag_chat_api_key
        if request_id:
            headers["X-Request-Id"] = request_id

        total_chunks = 0
        async with httpx.AsyncClient(timeout=max(self._timeout_seconds, 15.0)) as client:
            for file_path in files:
                raw = file_path.read_text(encoding="utf-8").strip()
                if not raw:
                    continue

                first_line = raw.splitlines()[0].strip() if raw.splitlines() else file_path.stem
                title = first_line.lstrip("# ").strip() or file_path.stem
                payload: dict[str, Any] = {
                    "content": raw,
                    "document_id": f"policy-{file_path.stem}",
                    "title": title,
                    "source": file_path.name,
                    "category": "policy",
                    "metadata": {
                        "ingest_source": "ecom-admin",
                        "policy_file": file_path.name,
                    },
                }

                try:
                    response = await client.post(f"{base_url}/ingest/text", json=payload, headers=headers)
                except httpx.HTTPError as exc:
                    raise RuntimeError(f"{file_path.name} upload failed: service unreachable") from exc
                if response.status_code >= 400:
                    detail = response.text.strip() or f"HTTP {response.status_code}"
                    raise RuntimeError(
                        f"{file_path.name} upload failed with status {response.status_code}: {detail}"
                    )

                data = response.json()
                try:
                    total_chunks += int(data.get("chunks_indexed") or 0)
                except (TypeError, ValueError):
                    continue

        return total_chunks
