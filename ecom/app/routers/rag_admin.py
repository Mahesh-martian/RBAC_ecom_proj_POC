"""Admin helpers for Azure RAG indexing operations."""

import hmac
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.services.azure_support_rag import AzureSupportRAGService
from app.services.external_rag_client import ExternalRAGClient

router = APIRouter(prefix="/admin/rag", tags=["admin-rag"])

azure_rag = AzureSupportRAGService(settings)
external_rag = ExternalRAGClient(settings)


@router.post("/index-policies")
async def index_policies(
    request: Request,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    limit: int | None = None,
) -> dict:
    """Create/ensure Azure Search index and upload local policy docs.

    Pass ``?limit=N`` to embed only the first N chunks (skips the destructive
    purge) as a cheap end-to-end test before running the full paid indexing.
    """
    if not settings.rag_admin_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAG admin endpoint is disabled. Set RAG_ADMIN_API_KEY to enable it.",
        )

    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.rag_admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")

    policies_dir = Path(__file__).resolve().parents[2] / "policies"
    request_id = request.headers.get("X-Request-Id")

    if settings.azure_rag_configured and azure_rag.enabled:
        azure_rag.ensure_index()
        indexed = await azure_rag.index_policy_documents(policies_dir, limit=limit)
        backend = "azure"
        message = "Policies indexed into Azure Search"
    elif external_rag.enabled:
        try:
            indexed = await external_rag.index_policy_documents(policies_dir, request_id=request_id)
        except RuntimeError as exc:
            if settings.is_development:
                return {
                    "status": "skipped",
                    "backend": "external",
                    "indexed_chunks": 0,
                    "policies_dir": str(policies_dir),
                    "index_name": settings.azure_search_index_name,
                    "message": "External RAG service unavailable in development; indexing skipped",
                }
            raise HTTPException(status_code=502, detail="External RAG policy indexing failed") from exc
        backend = "external"
        message = "Policies indexed through external RAG service"
    else:
        if settings.is_development:
            return {
                "status": "skipped",
                "backend": "none",
                "indexed_chunks": 0,
                "policies_dir": str(policies_dir),
                "index_name": settings.azure_search_index_name,
                "message": (
                    "No policy indexing backend configured in development; "
                    "set AZURE_OPENAI_*/AZURE_SEARCH_* or RAG_CHAT_API_URL to enable indexing"
                ),
            }
        raise HTTPException(
            status_code=400,
            detail=(
                "No policy indexing backend configured. Configure AZURE_OPENAI_* and AZURE_SEARCH_* "
                "or set RAG_CHAT_API_URL for external indexing."
            ),
        )

    return {
        "status": "success",
        "backend": backend,
        "indexed_chunks": indexed,
        "policies_dir": str(policies_dir),
        "index_name": settings.azure_search_index_name,
        "message": message,
    }
