"""Reusable offline test harness for RAG / embedding features.

Import these helpers from any ``tests/test_*.py`` that exercises code touching
Azure AI Search or the (paid) embedding provider, so new features can be tested
with **zero cost and no credentials**. The real embedding call and the Azure
Search client are replaced with deterministic fakes.

Typical usage::

    from tests.rag_test_harness import FakeSearchClient, make_rag_service, seed_policies, patch_embeddings

    async def test_my_feature(tmp_path, monkeypatch):
        calls = patch_embeddings(monkeypatch)            # stub the paid call
        seed_policies(tmp_path)                           # fake policy tree
        svc = make_rag_service(FakeSearchClient())        # service w/ fake Search
        ...                                               # call the feature, assert
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.config import settings
from app.services.azure_support_rag import AzureSupportRAGService

# Fixed dimension for fake vectors. Small on purpose -- value/length are irrelevant
# to the logic under test (chunking, batching, purge guards, upload payloads).
FAKE_VECTOR = [0.1, 0.2, 0.3, 0.4]


class FakeSearchClient:
    """Drop-in async stand-in for Azure ``AsyncSearchClient``.

    Records uploads, deletes and purge calls so tests can assert on them without
    any network. ``existing_keys`` seeds what a purge would find/delete.
    """

    def __init__(self, existing_keys: list[str] | None = None) -> None:
        self._existing = existing_keys or []
        self.uploaded: list[dict] = []
        self.deleted: list[dict] = []
        self.purge_called = False
        self.searched = False

    async def search(self, *args, **kwargs):
        self.searched = True
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

    async def upload_documents(self, documents):
        return await self.merge_or_upload_documents(documents)


def make_rag_service(fake_client: FakeSearchClient) -> AzureSupportRAGService:
    """Build an ``AzureSupportRAGService`` forced-enabled but backed by a fake client.

    The real ``__init__`` no-ops without Azure config, so we flip ``_enabled`` and
    inject the fake search client directly.
    """
    service = AzureSupportRAGService(settings)
    service._enabled = True
    service._search_client = fake_client
    return service


def seed_policies(root: Path, audiences: tuple[str, ...] = ("customer", "vendor", "common")) -> None:
    """Create a small policy tree under ``root`` with enough text for several chunks."""
    para = ("This is a policy paragraph with enough words to matter. " * 12).strip()
    for audience in audiences:
        sub = root / audience
        sub.mkdir(parents=True, exist_ok=True)
        body = "\n\n".join(f"# {audience} policy\n\n{para}" for _ in range(4))
        (sub / f"{audience}_policy.md").write_text(body, encoding="utf-8")


def patch_embeddings(monkeypatch, module_path: str = "app.services.azure_support_rag") -> dict:
    """Replace the paid embedding calls in ``module_path`` with deterministic stubs.

    Patches whichever of ``aembed_texts`` / ``embed_texts`` the target module imported.
    Returns a dict that records every text passed in, so tests can assert call counts
    (e.g. a ``dry_run``/``limit`` path embeds only N items).
    """
    calls: dict[str, list[str]] = {"texts": []}

    async def _aembed(texts, kind="document"):
        calls["texts"].extend(texts)
        return [list(FAKE_VECTOR) for _ in texts]

    def _embed(texts, kind="document"):
        calls["texts"].extend(texts)
        return [list(FAKE_VECTOR) for _ in texts]

    import importlib

    module = importlib.import_module(module_path)
    if hasattr(module, "aembed_texts"):
        monkeypatch.setattr(f"{module_path}.aembed_texts", _aembed)
    if hasattr(module, "embed_texts"):
        monkeypatch.setattr(f"{module_path}.embed_texts", _embed)
    return calls
