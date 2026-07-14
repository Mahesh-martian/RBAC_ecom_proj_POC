"""Tests for the Azure usage-metrics aggregator and the /metrics/usage endpoint."""

from app.config import settings
from app.services.usage_metrics import UsageMetrics, usage_metrics


def test_aggregator_accumulates_calls_tokens_and_latency():
    m = UsageMetrics()
    m.record("azure_openai_chat", latency_ms=100, prompt_tokens=10, completion_tokens=5)
    m.record("azure_openai_chat", latency_ms=200, prompt_tokens=20, completion_tokens=5)
    m.record("azure_ai_search", latency_ms=50, result_count=3)

    snap = m.snapshot()
    chat = snap["services"]["azure_openai_chat"]
    assert chat["calls"] == 2
    assert chat["prompt_tokens"] == 30
    assert chat["completion_tokens"] == 10
    assert chat["total_tokens"] == 40
    assert chat["latency_ms_avg"] == 150.0
    assert snap["services"]["azure_ai_search"]["result_count"] == 3
    assert snap["totals"]["total_tokens"] == 40
    assert snap["totals"]["calls"] == 3


def test_aggregator_counts_errors():
    m = UsageMetrics()
    m.record("azure_openai_chat", latency_ms=10, error=True)
    snap = m.snapshot()
    assert snap["services"]["azure_openai_chat"]["errors"] == 1


def test_aggregator_reset_clears_state():
    m = UsageMetrics()
    m.record("azure_ai_search", latency_ms=10, result_count=1)
    m.reset()
    assert m.snapshot()["totals"]["calls"] == 0


def test_metrics_endpoint_requires_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "rag_admin_api_key", "secret-admin-key")
    resp = client.get("/metrics/usage")
    assert resp.status_code == 401


def test_metrics_endpoint_disabled_without_admin_key(client, monkeypatch):
    monkeypatch.setattr(settings, "rag_admin_api_key", None)
    resp = client.get("/metrics/usage", headers={"X-Admin-Key": "anything"})
    assert resp.status_code == 503


def test_metrics_endpoint_returns_snapshot_with_valid_key(client, monkeypatch):
    monkeypatch.setattr(settings, "rag_admin_api_key", "secret-admin-key")
    usage_metrics.reset()
    usage_metrics.record("azure_openai_chat", latency_ms=42, prompt_tokens=7, completion_tokens=3)

    resp = client.get("/metrics/usage", headers={"X-Admin-Key": "secret-admin-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["services"]["azure_openai_chat"]["total_tokens"] == 10
    assert body["totals"]["calls"] == 1
