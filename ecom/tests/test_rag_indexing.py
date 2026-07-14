"""Unit tests for the policy indexing pipeline and embedding retry logic.

These run fully offline: the Azure Search client and the (paid) embedding call are
replaced with fakes, so no network/credentials/cost are involved. They lock in the
behaviour we rely on in production:

* ``limit=N`` embeds only the first N chunks and never purges existing data
  (the cheap pre-flight test path).
* A full run (``limit=None``) purges stale chunks before re-uploading.
* Chunk IDs are deterministic so re-runs overwrite rather than duplicate.
* The embedding provider retries transient 429s with backoff and honours
  ``Retry-After``, but does not retry non-retryable errors.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import settings
from app.services.azure_support_rag import AzureSupportRAGService


class FakeSearchClient:
    """Records uploads/purges so tests can assert on them without Azure."""

    def __init__(self, existing_keys: list[str] | None = None) -> None:
        self._existing = existing_keys or []
        self.uploaded: list[dict] = []
        self.deleted: list[dict] = []
        self.purge_called = False

    async def search(self, *args, **kwargs):
        keys = self._existing

        async def _gen():
            for key in keys:
                yield {"chunk_id": key}

        return _gen()

    async def delete_documents(self, documents):
        self.purge_called = True
        self.deleted.extend(documents)
        return [SimpleNamespace(succeeded=True) for _ in documents]

    async def merge_or_upload_documents(self, documents):
        self.uploaded.extend(documents)
        return [SimpleNamespace(succeeded=True) for _ in documents]


def _make_service(fake_client: FakeSearchClient) -> AzureSupportRAGService:
    """Build a service with Azure forcibly enabled but backed by a fake client."""
    service = AzureSupportRAGService(settings)
    service._enabled = True
    service._search_client = fake_client
    return service


def _seed_policies(root: Path) -> None:
    """Create a small policy tree with enough text to yield several chunks."""
    para = ("This is a policy paragraph with enough words to matter. " * 12).strip()
    for audience in ("customer", "vendor", "common"):
        sub = root / audience
        sub.mkdir(parents=True, exist_ok=True)
        body = "\n\n".join(f"# {audience} policy\n\n{para}" for _ in range(4))
        (sub / f"{audience}_policy.md").write_text(body, encoding="utf-8")


@pytest.fixture
def fake_embed(monkeypatch):
    """Replace the paid embedding call with a deterministic stub."""
    calls = {"texts": []}

    async def _aembed(texts, kind="document"):
        calls["texts"].extend(texts)
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    monkeypatch.setattr("app.services.azure_support_rag.aembed_texts", _aembed)
    return calls


@pytest.mark.asyncio
async def test_limit_embeds_only_n_and_skips_purge(tmp_path, fake_embed):
    _seed_policies(tmp_path)
    fake_client = FakeSearchClient(existing_keys=["old-1", "old-2"])
    service = _make_service(fake_client)

    indexed = await service.index_policy_documents(tmp_path, limit=3)

    assert indexed == 3
    assert len(fake_embed["texts"]) == 3
    assert len(fake_client.uploaded) == 3
    # The cheap test path must never destroy existing data.
    assert fake_client.purge_called is False


@pytest.mark.asyncio
async def test_full_run_purges_before_upload(tmp_path, fake_embed):
    _seed_policies(tmp_path)
    fake_client = FakeSearchClient(existing_keys=["old-1", "old-2", "old-3"])
    service = _make_service(fake_client)

    indexed = await service.index_policy_documents(tmp_path, limit=None)

    assert indexed > 3
    assert indexed == len(fake_client.uploaded)
    # Stale chunks from previous runs must be cleared first.
    assert fake_client.purge_called is True
    assert len(fake_client.deleted) == 3


@pytest.mark.asyncio
async def test_chunk_ids_are_deterministic(tmp_path, fake_embed):
    _seed_policies(tmp_path)

    first = _make_service(FakeSearchClient())
    await first.index_policy_documents(tmp_path, limit=5)
    ids_first = [d["chunk_id"] for d in first._search_client.uploaded]

    second = _make_service(FakeSearchClient())
    await second.index_policy_documents(tmp_path, limit=5)
    ids_second = [d["chunk_id"] for d in second._search_client.uploaded]

    assert ids_first == ids_second
    assert len(set(ids_first)) == len(ids_first)  # no collisions


@pytest.mark.asyncio
async def test_uploaded_docs_carry_audience_and_vector(tmp_path, fake_embed):
    _seed_policies(tmp_path)
    service = _make_service(FakeSearchClient())

    await service.index_policy_documents(tmp_path, limit=3)

    for doc in service._search_client.uploaded:
        assert doc["audience"] in {"customer", "vendor", "common"}
        assert doc["content_vector"] == [0.1, 0.2, 0.3, 0.4]
        assert doc["category"] == "policy"


@pytest.mark.asyncio
async def test_disabled_service_indexes_nothing(tmp_path, fake_embed):
    _seed_policies(tmp_path)
    service = AzureSupportRAGService(settings)
    service._enabled = False

    assert await service.index_policy_documents(tmp_path, limit=3) == 0


# --- Embedding retry/backoff -------------------------------------------------


def _http_error(status: int, retry_after: str | None = None):
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    return SimpleNamespace(
        status_code=status,
        response=SimpleNamespace(headers=headers),
    )


def test_retry_delay_retries_on_429():
    from app.services.embedding_provider import _retry_delay

    delay = _retry_delay(_http_error(429), attempt=0)
    assert delay is not None and delay > 0


def test_retry_delay_honours_retry_after_header():
    from app.services.embedding_provider import _retry_delay

    delay = _retry_delay(_http_error(429, retry_after="5"), attempt=0)
    assert 5.0 <= delay < 6.0  # base 5s + <1s jitter


def test_retry_delay_skips_non_retryable_status():
    from app.services.embedding_provider import _retry_delay

    assert _retry_delay(_http_error(400), attempt=0) is None
    assert _retry_delay(_http_error(401), attempt=0) is None


def test_retry_delay_stops_after_max_retries():
    from app.services.embedding_provider import _MAX_RETRIES, _retry_delay

    assert _retry_delay(_http_error(429), attempt=_MAX_RETRIES) is None


def test_retry_delay_backoff_grows():
    from app.services.embedding_provider import _retry_delay

    early = _retry_delay(_http_error(503), attempt=1)
    later = _retry_delay(_http_error(503), attempt=3)
    assert later > early
