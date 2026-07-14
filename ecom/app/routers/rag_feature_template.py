"""TEMPLATE (inert): a new admin RAG/embedding endpoint with a guarded dry-run.

This file is NOT imported anywhere, so it has no effect until you wire it up.
To turn it into a real feature:

  1. Copy/rename to ``app/routers/<your_feature>.py`` and rename the router/prefix.
  2. Replace the body of ``_run_feature`` with your real logic.
  3. Register it in ``app/main.py``:  ``app.include_router(<module>.router)``
  4. Add tests by copying ``tests/test_rag_feature_template.py``.

Why the guards matter here:
  * Admin auth (X-Admin-Key) -- same pattern as app/routers/rag_admin.py.
  * ``dry_run`` / ``limit`` -- lets you validate the PAID embedding path on a tiny
    sample and SKIP any destructive purge before committing to a full run.
"""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Header, HTTPException

from app.config import settings

# NOTE: choose a unique prefix so it doesn't collide with app/routers/rag_admin.py.
router = APIRouter(prefix="/admin/rag", tags=["admin-rag"])


async def _run_feature(*, dry_run: bool, limit: int | None) -> dict:
    """TODO: implement the real feature.

    Guard contract:
      * When ``dry_run`` is True: process at most ``limit`` items, perform NO
        destructive writes (no purge/delete), and return what *would* happen.
      * When ``dry_run`` is False: run for real.

    Example skeleton using the shared services::

        from pathlib import Path
        from app.services.azure_support_rag import AzureSupportRAGService

        svc = AzureSupportRAGService(settings)
        if not svc.enabled:
            raise HTTPException(503, "Azure RAG not configured")
        svc.ensure_index()
        policies_dir = Path(__file__).resolve().parents[2] / "policies"
        processed = await svc.index_policy_documents(policies_dir, limit=limit if dry_run else None)
        return {"processed": processed, "dry_run": dry_run}
    """
    raise NotImplementedError("Fill in _run_feature with your logic.")


@router.post("/feature-template")
async def feature_template(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """Admin-only feature endpoint.

    Pass ``?dry_run=true&limit=3`` for a cheap, non-destructive pre-flight before
    running the full (paid) operation.
    """
    # 1. Disabled unless an admin key is configured.
    if not settings.rag_admin_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAG admin endpoint is disabled. Set RAG_ADMIN_API_KEY to enable it.",
        )
    # 2. Constant-time key comparison (avoids timing leaks).
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.rag_admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")

    # 3. A dry-run must be cheap and bounded.
    if dry_run and (limit is None or limit < 1):
        limit = 3

    result = await _run_feature(dry_run=dry_run, limit=limit)
    return {"status": "success", **result}
