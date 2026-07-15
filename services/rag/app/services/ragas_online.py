"""Online RAGAS sampling for production /chat/query calls.

Samples a configurable fraction of successful policy-support RAG responses and
scores them asynchronously with ground-truth-free RAGAS metrics (``faithfulness``
and ``answer_relevancy``). Every scored request produces one structured log
line \u2014 shipped to Azure Application Insights by the existing OpenTelemetry
wiring \u2014 so quality regressions can be watched in real time without a nightly
eval cycle.

Design guarantees
-----------------
* **Never blocks the request.** Scoring runs on a fire-and-forget
  :func:`asyncio.create_task` scheduled by the router; the client response has
  already been flushed by the time RAGAS talks to Azure.
* **Deterministic sampling.** Selection is based on
  ``hash(request_id) % 10_000 < rate * 10_000`` so the same request either
  always samples or never samples, and rates such as ``0.001`` still hit small
  discrete buckets rather than drifting with ``random.random()``.
* **Concurrency capped.** A module-level :class:`asyncio.Semaphore` bounds how
  many scoring calls are in flight at once, so a burst of sampled requests can
  never queue up unbounded Azure calls.
* **Circuit breaker.** After ``_FAILURE_WINDOW`` consecutive scoring failures
  we skip sampling for ``_COOLDOWN_SECONDS`` seconds so an Azure outage cannot
  silently rack up 429s or add hidden latency to worker pools.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any, Iterable, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# --- Only metrics that don't require ground_truth are safe for online use.
_ONLINE_ELIGIBLE_METRICS: frozenset[str] = frozenset(
    {"faithfulness", "answer_relevancy"}
)

# --- Circuit-breaker knobs (module-level rather than settings so an operator
#     can tune them without a redeploy via env vars; kept private since they
#     rarely need tuning).
_FAILURE_WINDOW = 5
_COOLDOWN_SECONDS = 300

_semaphore: Optional[asyncio.Semaphore] = None
_recent_failures: int = 0
_cooldown_until: float = 0.0


def _semaphore_for_loop() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max(1, settings.ragas_online_max_concurrent))
    return _semaphore


def _resolve_metrics() -> list[str]:
    """Parse ``settings.ragas_online_metrics`` and filter to safe metrics."""
    raw = settings.ragas_online_metrics or "faithfulness"
    requested = {m.strip().lower() for m in raw.split(",") if m.strip()}
    return sorted(requested & _ONLINE_ELIGIBLE_METRICS)


def should_sample(request_id: str) -> bool:
    """Return True when this request should be scored online.

    Rate 0 disables sampling. Rate >=1 samples everything. The decision is
    deterministic in ``request_id`` so retrying a request or investigating a
    log line yields the same verdict every time.
    """
    rate = settings.ragas_online_sample_rate or 0.0
    if rate <= 0:
        return False
    if rate >= 1.0:
        return True
    if not request_id:
        return False

    # Cheap, deterministic 4-hex-nibble hash \u2192 [0, 65536).
    digest = hashlib.blake2b(request_id.encode("utf-8"), digest_size=2).digest()
    bucket = int.from_bytes(digest, "big")  # 0..65535
    threshold = int(rate * 65536)
    return bucket < threshold


def _breaker_open() -> bool:
    """True while the breaker is cooling down."""
    return time.time() < _cooldown_until


def _record_failure() -> None:
    global _recent_failures, _cooldown_until
    _recent_failures += 1
    if _recent_failures >= _FAILURE_WINDOW:
        _cooldown_until = time.time() + _COOLDOWN_SECONDS
        _recent_failures = 0
        logger.warning(
            "ragas_online breaker opened for %ds after %d consecutive failures",
            _COOLDOWN_SECONDS,
            _FAILURE_WINDOW,
        )


def _record_success() -> None:
    global _recent_failures
    _recent_failures = 0


async def _score_faithfulness_and_relevancy(
    metrics: list[str],
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, Optional[float]]:
    """Invoke RAGAS on a single sample. Returns ``{metric_name: score|None}``.

    Isolated in its own function so callers can wrap it in a semaphore and
    exception handler; imports are lazy so the online path pays no cost when
    sampling is disabled.
    """
    try:
        from datasets import Dataset  # type: ignore
        from ragas import evaluate as ragas_evaluate  # type: ignore
        from ragas import metrics as ragas_metrics_mod  # type: ignore
        from langchain_openai import AzureChatOpenAI  # type: ignore
    except ImportError as exc:
        raise RuntimeError(f"ragas dependencies missing: {exc}") from exc

    judge_dep = (
        settings.ragas_judge_deployment
        or settings.azure_openai_chat_deployment
    )
    if not (settings.azure_openai_endpoint and settings.azure_openai_api_key and judge_dep):
        raise RuntimeError("azure_openai judge not configured")

    judge_llm = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=judge_dep,
        temperature=0,
    )

    metric_objs = []
    for name in metrics:
        attr = getattr(ragas_metrics_mod, name, None)
        if attr is not None:
            metric_objs.append(attr)
    if not metric_objs:
        raise RuntimeError("no supported online RAGAS metrics loaded")

    ds = Dataset.from_dict(
        {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
    )
    # ragas.evaluate is sync/CPU-bound with network I/O to the judge.
    # Off-thread it so we don't stall the event loop.
    result = await asyncio.to_thread(
        ragas_evaluate,
        ds,
        metrics=metric_objs,
        llm=judge_llm,
        raise_exceptions=False,
    )
    try:
        df = result.to_pandas()  # type: ignore[attr-defined]
    except AttributeError:
        df = result

    scores: dict[str, Optional[float]] = {}
    row = df.iloc[0]
    for name in metrics:
        value = row.get(name)
        try:
            f = float(value)
            if f != f:  # NaN
                f = None
        except (TypeError, ValueError):
            f = None
        scores[name] = f
    return scores


def schedule_online_score(
    *,
    request_id: str,
    query: str,
    answer: str,
    contexts: list[str],
    role: str,
    audience: Optional[str] = None,
    system_prompt_label: Optional[str] = None,
    prompt_versions: Optional[dict[str, str]] = None,
) -> None:
    """Fire-and-forget: schedule a background scoring task for ``request_id``.

    No-op when sampling is disabled, the breaker is open, contexts are empty,
    or the current process is not running inside an asyncio loop. Every call
    is safe to invoke from a request handler.
    """
    if not settings.ragas_enabled:
        return
    if not should_sample(request_id):
        return
    if _breaker_open():
        return
    if not contexts or not answer or not query:
        return

    metrics = _resolve_metrics()
    if not metrics:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Called outside an event loop (unit test) \u2014 skip silently.
        return

    async def _worker() -> None:
        started = time.perf_counter()
        semaphore = _semaphore_for_loop()
        try:
            async with semaphore:
                scores = await _score_faithfulness_and_relevancy(
                    metrics=metrics,
                    question=query,
                    answer=answer,
                    contexts=contexts,
                )
        except Exception as exc:  # noqa: BLE001 - never let sampling raise
            _record_failure()
            logger.warning(
                "ragas_online_failure request_id=%s error=%r elapsed_ms=%s",
                request_id,
                exc,
                round((time.perf_counter() - started) * 1000, 1),
            )
            return

        _record_success()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        # Structured single-line log. The JsonLogFormatter (see logging_utils)
        # folds the ``extra`` fields into the top-level payload, so App Insights
        # receives them as first-class custom dimensions.
        logger.info(
            "ragas_online",
            extra={
                "event": "ragas_online",
                "request_id": request_id,
                "role": role,
                "audience": audience,
                "system_prompt_label": system_prompt_label,
                "prompt_versions": prompt_versions or {},
                "scores": scores,
                "scoring_latency_ms": latency_ms,
                "answer_chars": len(answer),
                "context_count": len(contexts),
            },
        )

    loop.create_task(_worker())


def reset_online_state() -> None:
    """Test helper: clear the breaker + semaphore singleton."""
    global _semaphore, _recent_failures, _cooldown_until
    _semaphore = None
    _recent_failures = 0
    _cooldown_until = 0.0
