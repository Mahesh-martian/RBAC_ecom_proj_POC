"""Unit tests for the admin RAGAS endpoints and the underlying job store.

The full evaluator + RAGAS metrics are exercised by tests/test_ragas_eval.py.
Here we only assert:
  * auth is enforced (503 without RAG_ADMIN_API_KEY, 401 for wrong key),
  * a valid POST returns 202 with a queued job,
  * single-flight semantics (409 while another job is running),
  * GET endpoints for list/detail/latest return the expected shapes.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services.ragas_jobs import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_QUEUED,
    RagasJob,
    RagasJobParams,
    RagasJobStore,
)


@pytest.fixture(autouse=True)
def _reset_store():
    RagasJobStore.reset_instance()
    yield
    RagasJobStore.reset_instance()


# --------------------------------------------------------------------- store


def test_store_submit_without_event_loop_returns_queued(tmp_path):
    store = RagasJobStore(base_dir=tmp_path)
    job = store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))
    assert job.status == JOB_STATUS_QUEUED
    assert store.is_busy() is True
    assert store.get(job.id) is job


def test_store_rejects_concurrent_submit(tmp_path):
    store = RagasJobStore(base_dir=tmp_path)
    store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))
    with pytest.raises(RuntimeError, match="already"):
        store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))


def test_store_lists_jobs_newest_first(tmp_path):
    store = RagasJobStore(base_dir=tmp_path)
    a = store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))
    # Force-complete the first job so the second one can be submitted.
    a.status = JOB_STATUS_COMPLETED
    store._active_id = None  # noqa: SLF001 - test white-box access
    b = store.submit(RagasJobParams(dry_run=True, limit=2, skip_denied=True))
    listed = store.list(limit=10)
    assert [j.id for j in listed] == [b.id, a.id]


def test_latest_completed_returns_most_recent(tmp_path):
    store = RagasJobStore(base_dir=tmp_path)
    j1 = store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))
    j1.status = JOB_STATUS_COMPLETED
    store._active_id = None  # noqa: SLF001
    j2 = store.submit(RagasJobParams(dry_run=True, limit=1, skip_denied=True))
    j2.status = JOB_STATUS_COMPLETED
    store._active_id = None  # noqa: SLF001

    latest = store.latest_completed()
    assert latest is not None and latest.id == j2.id


def test_job_summary_hides_full_report_body():
    job = RagasJob(
        id="abc",
        status=JOB_STATUS_COMPLETED,
        submitted_at="2026-07-15T00:00:00Z",
        report={"summary": {"replays": 3, "passed": 2}, "rows": [{"answer": "x" * 1000}]},
    )
    summary = job.to_summary()
    assert "report_summary" in summary
    assert summary["report_summary"] == {"replays": 3, "passed": 2}
    # Full row bodies should NOT be inlined into the summary payload.
    assert "rows" not in summary


# --------------------------------------------------------------------- HTTP


def _client_with_admin_key(monkeypatch, key: str | None):
    from app.config import settings

    monkeypatch.setattr(settings, "rag_admin_api_key", key)
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def test_ragas_run_requires_admin_key_configured(monkeypatch):
    client = _client_with_admin_key(monkeypatch, None)
    resp = client.post("/admin/rag/ragas/run", json={"dry_run": True, "limit": 1})
    assert resp.status_code == 503
    assert "RAG_ADMIN_API_KEY" in resp.json()["detail"]


def test_ragas_run_rejects_bad_key(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "correct-key")
    resp = client.post(
        "/admin/rag/ragas/run",
        json={"dry_run": True, "limit": 1},
        headers={"X-Admin-Key": "wrong"},
    )
    assert resp.status_code == 401


def test_ragas_run_returns_202_with_queued_job(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")

    # Stop the background execution from actually running so the test stays
    # deterministic; the store still marks the job queued+active.
    async def _noop_execute(self, job, params):
        return {"summary": {"replays": 0, "passed": 0, "failed": 0}}

    monkeypatch.setattr(RagasJobStore, "_execute", _noop_execute)

    resp = client.post(
        "/admin/rag/ragas/run",
        json={"dry_run": True, "limit": 1, "skip_denied": True},
        headers={"X-Admin-Key": "k"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] in {"queued", "running", "completed"}
    assert body["params"]["dry_run"] is True
    assert body["id"]


def test_ragas_run_returns_409_when_another_active(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")

    async def _slow_execute(self, job, params):
        # Never resolve during the test: keeps the job "active".
        await asyncio.sleep(3600)
        return {}

    monkeypatch.setattr(RagasJobStore, "_execute", _slow_execute)

    first = client.post(
        "/admin/rag/ragas/run",
        json={"dry_run": True, "limit": 1, "skip_denied": True},
        headers={"X-Admin-Key": "k"},
    )
    assert first.status_code == 202

    second = client.post(
        "/admin/rag/ragas/run",
        json={"dry_run": True, "limit": 1, "skip_denied": True},
        headers={"X-Admin-Key": "k"},
    )
    assert second.status_code == 409


def test_ragas_get_run_404_when_missing(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")
    resp = client.get("/admin/rag/ragas/runs/does-not-exist", headers={"X-Admin-Key": "k"})
    assert resp.status_code == 404


def test_ragas_latest_404_when_none(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")
    resp = client.get("/admin/rag/ragas/latest", headers={"X-Admin-Key": "k"})
    assert resp.status_code == 404


def test_ragas_list_returns_empty_when_no_runs(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")
    resp = client.get("/admin/rag/ragas/runs", headers={"X-Admin-Key": "k"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["jobs"] == []


def test_ragas_bad_role_returns_422(monkeypatch):
    client = _client_with_admin_key(monkeypatch, "k")
    resp = client.post(
        "/admin/rag/ragas/run",
        json={"role": "hacker"},
        headers={"X-Admin-Key": "k"},
    )
    assert resp.status_code == 422
