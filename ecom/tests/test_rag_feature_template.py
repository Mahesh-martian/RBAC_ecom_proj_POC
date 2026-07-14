"""TEMPLATE: offline tests for a new RAG / embedding feature.

Copy this file to ``tests/test_<your_feature>.py`` and adapt it. It is **self-contained
and green as-is** so you can see the pattern run, then swap the demo logic for your
real feature. It shows the four checks every paid/destructive RAG feature should have
BEFORE production:

  1. Admin auth is enforced (401 without a valid key, 503 when disabled).
  2. The dry-run / ``limit`` guard embeds only N items and never purges real data.
  3. The real logic runs with the paid embedding call MOCKED (zero cost).
  4. Re-runs are idempotent (deterministic IDs -> overwrite, not duplicate).

Run inside the container (the host .venv has broken dep versions):
    docker cp tests shopease-rag-api:/app/tests
    docker exec shopease-rag-api sh -c "cd /app && python -m pytest tests/test_rag_feature_template.py -v"
"""

from __future__ import annotations

import hashlib

import pytest

from app.services import azure_support_rag
from tests.rag_test_harness import FakeSearchClient, patch_embeddings

# ---------------------------------------------------------------------------
# DEMO feature under test. Replace this with a call into YOUR real service.
# It models the guard contract: dry_run -> bounded by `limit` AND no purge.
# ---------------------------------------------------------------------------


async def demo_index(search_client, items: list[str], *, dry_run: bool, limit: int | None) -> int:
    """Embed `items` and upload them; honor the dry-run/limit guard.

    Mirrors the shape of AzureSupportRAGService.index_policy_documents so the test
    structure transfers directly to the real thing.
    """
    if not dry_run:
        # Real run: clear stale docs first. A dry-run must NEVER reach this.
        results = await search_client.search(search_text="*", select=["chunk_id"])
        keys = [doc["chunk_id"] async for doc in results]
        if keys:
            await search_client.delete_documents(documents=[{"chunk_id": k} for k in keys])

    if dry_run and limit is not None:
        items = items[:limit]

    # Paid call -- patched to a stub in tests via the module's imported name.
    vectors = await azure_support_rag.aembed_texts(items, kind="document")
    docs = [
        {"chunk_id": hashlib.sha256(t.encode()).hexdigest()[:40], "content": t, "content_vector": v}
        for t, v in zip(items, vectors)
    ]
    result = await search_client.merge_or_upload_documents(documents=docs)
    return sum(1 for r in result if r.succeeded)


# --- 1. Admin auth -----------------------------------------------------------
# These use the `client` fixture from conftest.py and need no Azure backend.
# In the default test env RAG_ADMIN_API_KEY is unset -> the endpoint is disabled.


def test_admin_endpoint_disabled_without_key(client, monkeypatch):
    from app.config import settings

    # Force the key off so the test is deterministic regardless of the host env
    # (in a deployed/container env RAG_ADMIN_API_KEY is usually set).
    monkeypatch.setattr(settings, "rag_admin_api_key", "")
    # The existing admin endpoint stands in for "your new admin endpoint".
    resp = client.post("/admin/rag/index-policies")
    assert resp.status_code == 503  # disabled when RAG_ADMIN_API_KEY is unset


def test_admin_endpoint_rejects_bad_key(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "rag_admin_api_key", "the-real-key")
    resp = client.post("/admin/rag/index-policies", headers={"X-Admin-Key": "wrong"})
    assert resp.status_code == 401


# --- 2. Dry-run / limit guard ------------------------------------------------


@pytest.mark.asyncio
async def test_dry_run_embeds_only_n_and_skips_purge(monkeypatch):
    calls = patch_embeddings(monkeypatch)
    fake_client = FakeSearchClient(existing_keys=["old-1", "old-2"])
    items = [f"chunk {i}" for i in range(20)]

    uploaded = await demo_index(fake_client, items, dry_run=True, limit=3)

    assert uploaded == 3
    assert len(calls["texts"]) == 3            # only N paid calls' worth of input
    assert fake_client.purge_called is False   # MUST NOT destroy real data


# --- 3. Real logic with paid call mocked -------------------------------------


@pytest.mark.asyncio
async def test_feature_happy_path(monkeypatch):
    patch_embeddings(monkeypatch)
    fake_client = FakeSearchClient(existing_keys=["stale-1"])
    items = [f"chunk {i}" for i in range(10)]

    uploaded = await demo_index(fake_client, items, dry_run=False, limit=None)

    assert uploaded == 10
    assert uploaded == len(fake_client.uploaded)
    assert fake_client.purge_called is True    # full run clears stale docs first
    for doc in fake_client.uploaded:
        assert doc["content_vector"]           # every doc carries an embedding


# --- 4. Idempotency ----------------------------------------------------------


@pytest.mark.asyncio
async def test_reruns_are_idempotent(monkeypatch):
    patch_embeddings(monkeypatch)
    items = [f"chunk {i}" for i in range(5)]

    first = FakeSearchClient()
    await demo_index(first, items, dry_run=False, limit=None)
    ids_first = [d["chunk_id"] for d in first.uploaded]

    second = FakeSearchClient()
    await demo_index(second, items, dry_run=False, limit=None)
    ids_second = [d["chunk_id"] for d in second.uploaded]

    assert ids_first == ids_second                 # stable IDs across runs
    assert len(set(ids_first)) == len(ids_first)    # no collisions/duplicates
