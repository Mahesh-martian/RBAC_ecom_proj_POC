"""Admin helpers for Azure RAG indexing operations."""

import hmac
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.config import settings
from app.schemas import (
    RagasJobDetailResponse,
    RagasJobListResponse,
    RagasJobSummaryResponse,
    RagasRunRequest,
)
from app.services.azure_support_rag import AzureSupportRAGService
from app.services.external_rag_client import ExternalRAGClient
from app.services.ragas_jobs import RagasJobParams, get_job_store

router = APIRouter(prefix="/admin/rag", tags=["admin-rag"])

azure_rag = AzureSupportRAGService(settings)
external_rag = ExternalRAGClient(settings)


def _require_admin_key(x_admin_key: str | None) -> None:
    """Constant-time check for the ``X-Admin-Key`` header.

    Raises 503 when the server is missing ``RAG_ADMIN_API_KEY`` (so admin ops
    are disabled by default) and 401 for a mismatched key.
    """
    if not settings.rag_admin_api_key:
        raise HTTPException(
            status_code=503,
            detail="RAG admin endpoint is disabled. Set RAG_ADMIN_API_KEY to enable it.",
        )
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.rag_admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")


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
    _require_admin_key(x_admin_key)

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


# --------------------------------------------------------------------- RAGAS


def _job_to_summary(job) -> RagasJobSummaryResponse:
    return RagasJobSummaryResponse(**job.to_summary())


def _job_to_detail(job) -> RagasJobDetailResponse:
    payload = job.to_summary()
    payload["report_dir"] = job.report_dir
    payload["report"] = job.report
    return RagasJobDetailResponse(**payload)


@router.post(
    "/ragas/run",
    response_model=RagasJobDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Kick off an on-demand RAGAS evaluation",
)
async def ragas_run(
    body: RagasRunRequest,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> RagasJobDetailResponse:
    """Submit a RAGAS evaluation job.

    Returns HTTP 202 with the queued job. Poll ``GET /admin/rag/ragas/runs/{id}``
    for progress and (once complete) the full report body. Only one job may be
    in flight at a time \u2014 concurrent submissions receive HTTP 409.
    """
    _require_admin_key(x_admin_key)

    params = RagasJobParams(
        limit=body.limit,
        role=body.role,
        include_stretch=body.include_stretch,
        skip_denied=body.skip_denied,
        dry_run=body.dry_run,
        metrics=body.metrics,
        concurrency=body.concurrency,
        fail_on_threshold=body.fail_on_threshold,
    )

    try:
        job = get_job_store().submit(params)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _job_to_detail(job)


@router.get(
    "/ragas/runs",
    response_model=RagasJobListResponse,
    summary="List recent RAGAS evaluation runs",
)
async def ragas_list_runs(
    limit: int = 20,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> RagasJobListResponse:
    """Return the last ``limit`` (default 20) evaluation runs, newest first."""
    _require_admin_key(x_admin_key)
    jobs = get_job_store().list(limit=limit)
    return RagasJobListResponse(
        jobs=[_job_to_summary(job) for job in jobs],
        total=len(jobs),
    )


@router.get(
    "/ragas/runs/{job_id}",
    response_model=RagasJobDetailResponse,
    summary="Fetch a single RAGAS evaluation run",
)
async def ragas_get_run(
    job_id: str,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> RagasJobDetailResponse:
    _require_admin_key(x_admin_key)
    job = get_job_store().get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return _job_to_detail(job)


@router.get(
    "/ragas/latest",
    response_model=RagasJobDetailResponse,
    summary="Fetch the most recent completed RAGAS run",
)
async def ragas_latest(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> RagasJobDetailResponse:
    _require_admin_key(x_admin_key)
    job = get_job_store().latest_completed()
    if job is None:
        raise HTTPException(status_code=404, detail="no completed RAGAS runs yet")
    return _job_to_detail(job)
