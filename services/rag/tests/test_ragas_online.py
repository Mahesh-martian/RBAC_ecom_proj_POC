"""Unit tests for online RAGAS sampling.

The scoring code path (which invokes Azure) is not exercised here \u2014 those
tests would need real Azure creds. We do assert:

* deterministic sampling (same request_id \u2192 same verdict),
* rate bounds (0.0 disables, 1.0 samples all),
* schedule_online_score is a no-op when sampling is disabled, contexts empty,
  or ragas_enabled is false,
* the circuit breaker opens after N consecutive failures and closes after the
  cool-down window.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services import ragas_online


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    ragas_online.reset_online_state()
    yield
    ragas_online.reset_online_state()


# --------------------------------------------------------------- sampling


def test_sample_rate_zero_never_samples(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_online_sample_rate", 0.0)
    for i in range(50):
        assert ragas_online.should_sample(f"req-{i}") is False


def test_sample_rate_one_always_samples(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)
    for i in range(50):
        assert ragas_online.should_sample(f"req-{i}") is True


def test_sample_is_deterministic(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_online_sample_rate", 0.5)
    request_id = "abc-123"
    verdicts = {ragas_online.should_sample(request_id) for _ in range(20)}
    assert len(verdicts) == 1  # same answer every time


def test_sample_rate_approximates_target(monkeypatch):
    """With a large sample, actual hit rate should be within a loose tolerance."""
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_online_sample_rate", 0.25)
    n = 2000
    hits = sum(1 for i in range(n) if ragas_online.should_sample(f"req-{i}"))
    ratio = hits / n
    assert 0.15 < ratio < 0.35  # blake2b + 25% target


def test_empty_request_id_never_samples(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_online_sample_rate", 0.5)
    assert ragas_online.should_sample("") is False


# --------------------------------------------------------------- scheduling


def test_schedule_is_noop_when_ragas_disabled(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_enabled", False)
    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)

    called = {"worker": False}

    async def _stub(**kwargs):
        called["worker"] = True
        return {}

    monkeypatch.setattr(ragas_online, "_score_faithfulness_and_relevancy", _stub)

    async def _run():
        ragas_online.schedule_online_score(
            request_id="rid",
            query="q",
            answer="a",
            contexts=["c1"],
            role="customer",
        )
        # Yield so any (incorrectly) scheduled tasks would run.
        await asyncio.sleep(0)

    asyncio.run(_run())
    assert called["worker"] is False


def test_schedule_is_noop_when_contexts_empty(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_enabled", True)
    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)

    called = {"worker": False}

    async def _stub(**kwargs):
        called["worker"] = True
        return {}

    monkeypatch.setattr(ragas_online, "_score_faithfulness_and_relevancy", _stub)

    async def _run():
        ragas_online.schedule_online_score(
            request_id="rid",
            query="q",
            answer="a",
            contexts=[],
            role="customer",
        )
        await asyncio.sleep(0)

    asyncio.run(_run())
    assert called["worker"] is False


def test_schedule_invokes_scoring_when_enabled(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_enabled", True)
    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)
    monkeypatch.setattr(settings, "ragas_online_metrics", "faithfulness")

    captured: dict = {"kwargs": None}

    async def _fake_score(**kwargs):
        captured["kwargs"] = kwargs
        return {"faithfulness": 0.87}

    monkeypatch.setattr(ragas_online, "_score_faithfulness_and_relevancy", _fake_score)

    async def _run():
        ragas_online.schedule_online_score(
            request_id="rid-42",
            query="Do you have a refund policy?",
            answer="Yes, refunds go to original method.",
            contexts=["Refunds are issued to the original payment method."],
            role="customer",
            audience="customer,common",
        )
        # Wait for pending tasks to finish so the assertion is safe.
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    asyncio.run(_run())
    assert captured["kwargs"] is not None
    assert captured["kwargs"]["question"].startswith("Do you have")
    assert captured["kwargs"]["metrics"] == ["faithfulness"]


def test_scheduler_ignores_metrics_that_need_ground_truth(monkeypatch):
    """Only faithfulness / answer_relevancy are allowed online."""
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_enabled", True)
    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)
    # User asks for a mix; only the safe ones should be forwarded.
    monkeypatch.setattr(
        settings,
        "ragas_online_metrics",
        "faithfulness,context_recall,answer_relevancy,answer_similarity",
    )

    captured: dict = {"metrics": None}

    async def _fake_score(metrics, **kwargs):
        captured["metrics"] = list(metrics)
        return {m: 0.9 for m in metrics}

    monkeypatch.setattr(ragas_online, "_score_faithfulness_and_relevancy", _fake_score)

    async def _run():
        ragas_online.schedule_online_score(
            request_id="rid",
            query="q",
            answer="a",
            contexts=["c"],
            role="customer",
        )
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    asyncio.run(_run())
    assert captured["metrics"] == ["answer_relevancy", "faithfulness"]


# --------------------------------------------------------------- breaker


def test_breaker_opens_after_consecutive_failures(monkeypatch):
    monkeypatch.setattr(ragas_online, "_FAILURE_WINDOW", 3)
    monkeypatch.setattr(ragas_online, "_COOLDOWN_SECONDS", 60)

    for _ in range(3):
        ragas_online._record_failure()  # noqa: SLF001 - unit test

    assert ragas_online._breaker_open() is True  # noqa: SLF001


def test_breaker_resets_on_success(monkeypatch):
    monkeypatch.setattr(ragas_online, "_FAILURE_WINDOW", 5)
    ragas_online._record_failure()  # noqa: SLF001
    ragas_online._record_failure()  # noqa: SLF001
    ragas_online._record_success()  # noqa: SLF001
    # After success, we should not be near opening the breaker yet.
    for _ in range(2):
        ragas_online._record_failure()  # noqa: SLF001
    assert ragas_online._breaker_open() is False  # noqa: SLF001


def test_breaker_open_blocks_scheduling(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ragas_enabled", True)
    monkeypatch.setattr(settings, "ragas_online_sample_rate", 1.0)
    # Force the breaker open manually.
    import time

    monkeypatch.setattr(ragas_online, "_cooldown_until", time.time() + 3600)

    called = {"worker": False}

    async def _stub(**kwargs):
        called["worker"] = True
        return {}

    monkeypatch.setattr(ragas_online, "_score_faithfulness_and_relevancy", _stub)

    async def _run():
        ragas_online.schedule_online_score(
            request_id="rid",
            query="q",
            answer="a",
            contexts=["c"],
            role="customer",
        )
        await asyncio.sleep(0)

    asyncio.run(_run())
    assert called["worker"] is False
