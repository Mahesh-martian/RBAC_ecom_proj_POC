"""In-process Azure service usage metrics aggregator.

Collects per-service usage counters (call count, errors, token usage, latency) for
the Azure services the RAG pipeline calls:

* ``azure_openai_chat`` -- chat completions (prompt/completion/total tokens, latency)
* ``azure_openai_embeddings`` / ``azure_cohere_embeddings`` -- embedding calls
* ``azure_ai_search`` -- retrieval queries (result count, latency)

The aggregator is a lightweight, thread-safe, in-memory singleton. Counters reset on
process restart and are per-process (not shared across Container Apps replicas), so
they are intended for quick local/dev visibility via ``GET /metrics/usage``. Use
Application Insights (when wired) for durable, cross-instance aggregation.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class _ServiceStats:
    """Accumulated stats for a single service."""

    calls: int = 0
    errors: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    result_count: int = 0
    latency_ms_sum: float = 0.0
    latency_samples: list[float] = field(default_factory=list)

    # Cap retained latency samples to bound memory; percentiles use this window.
    _MAX_SAMPLES: int = 1000

    def record(
        self,
        *,
        latency_ms: Optional[float],
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        result_count: int,
        error: bool,
    ) -> None:
        self.calls += 1
        if error:
            self.errors += 1
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += total_tokens
        self.result_count += result_count
        if latency_ms is not None:
            self.latency_ms_sum += latency_ms
            self.latency_samples.append(latency_ms)
            if len(self.latency_samples) > self._MAX_SAMPLES:
                # Drop the oldest sample to keep a rolling window.
                self.latency_samples.pop(0)

    def snapshot(self) -> dict:
        samples = sorted(self.latency_samples)
        avg = round(self.latency_ms_sum / self.calls, 2) if self.calls else 0.0
        return {
            "calls": self.calls,
            "errors": self.errors,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "result_count": self.result_count,
            "latency_ms_avg": avg,
            "latency_ms_p95": _percentile(samples, 0.95),
            "latency_ms_max": round(samples[-1], 2) if samples else 0.0,
        }


def _percentile(sorted_samples: list[float], pct: float) -> float:
    """Nearest-rank percentile of an already-sorted list; 0.0 when empty."""
    if not sorted_samples:
        return 0.0
    rank = max(0, min(len(sorted_samples) - 1, int(round(pct * len(sorted_samples))) - 1))
    return round(sorted_samples[rank], 2)


class UsageMetrics:
    """Thread-safe registry of per-service usage stats."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._services: dict[str, _ServiceStats] = {}

    def record(
        self,
        service: str,
        *,
        latency_ms: Optional[float] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        result_count: int = 0,
        error: bool = False,
    ) -> None:
        """Record a single call to ``service``.

        ``total_tokens`` defaults to ``prompt_tokens + completion_tokens`` when not
        supplied explicitly.
        """
        if total_tokens == 0 and (prompt_tokens or completion_tokens):
            total_tokens = prompt_tokens + completion_tokens
        with self._lock:
            stats = self._services.get(service)
            if stats is None:
                stats = _ServiceStats()
                self._services[service] = stats
            stats.record(
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                result_count=result_count,
                error=error,
            )

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot of all service stats plus totals."""
        with self._lock:
            services = {name: stats.snapshot() for name, stats in self._services.items()}
        totals = {
            "calls": sum(s["calls"] for s in services.values()),
            "errors": sum(s["errors"] for s in services.values()),
            "prompt_tokens": sum(s["prompt_tokens"] for s in services.values()),
            "completion_tokens": sum(s["completion_tokens"] for s in services.values()),
            "total_tokens": sum(s["total_tokens"] for s in services.values()),
        }
        return {"services": services, "totals": totals}

    def reset(self) -> None:
        """Clear all recorded stats (primarily for tests)."""
        with self._lock:
            self._services.clear()


# Module-level singleton shared across the app.
usage_metrics = UsageMetrics()
