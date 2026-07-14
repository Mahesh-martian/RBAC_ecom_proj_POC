"""Operational endpoint exposing in-process Azure service usage metrics.

``GET /metrics/usage`` returns a snapshot of per-service counters (calls, errors,
token usage, latency) collected by :mod:`app.services.usage_metrics`. It is gated
behind the same ``X-Admin-Key`` shared secret used by the RAG admin endpoints.

Counters are in-memory and per-process (reset on restart, not aggregated across
Container Apps replicas). For durable, cross-instance metrics use Application
Insights when it is wired in.
"""

import hmac

from fastapi import APIRouter, Header, HTTPException

from app.config import settings
from app.services.usage_metrics import usage_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _require_admin(x_admin_key: str | None) -> None:
    """Reject the request unless a valid admin key is presented."""
    if not settings.rag_admin_api_key:
        raise HTTPException(
            status_code=503,
            detail="Metrics endpoint is disabled. Set RAG_ADMIN_API_KEY to enable it.",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.rag_admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.get("/usage", summary="Azure service usage metrics snapshot")
async def usage_snapshot(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    """Return aggregated Azure usage metrics (tokens, calls, latency) per service."""
    _require_admin(x_admin_key)
    return usage_metrics.snapshot()
