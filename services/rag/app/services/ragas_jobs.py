"""In-process job store for admin-triggered RAGAS evaluations.

The scheduled workflow in ``.github/workflows/rag-eval.yml`` covers regular
regression detection. This module powers the on-demand admin endpoint so an
operator can kick off an evaluation from a running service \u2014 useful for
validating a prompt change against a live index without waiting for the
nightly cron.

Design
------
* **Singleton in-memory index + on-disk reports.** Each run writes its JSON +
  Markdown report into ``services/rag/reports/ragas/<job_id>/`` (same layout
  as the CLI), and the store keeps the last N :class:`RagasJob` entries in
  memory for fast listing. Reports survive restarts because they live on disk;
  in-flight jobs do not (they are marked failed at the next process start).
* **Single-flight**. Only one evaluation can run at a time. Concurrent
  submissions receive HTTP 409 from the router. RAGAS + Azure calls are
  quota-hungry, so serialising is a safety feature, not a limitation.
* **Fire-and-forget with asyncio.create_task.** FastAPI's own BackgroundTasks
  runs *after* the response is sent, which delays the ``queued`` \u2192 ``running``
  transition. Using ``asyncio.create_task`` inside the running event loop lets
  us flip status synchronously before returning.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.services.ragas_eval import (
    RagasEvaluator,
    build_report,
    resolve_thresholds,
    write_report,
)

logger = logging.getLogger(__name__)


JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_ABORTED = "aborted"


@dataclass
class RagasJobParams:
    """User-supplied parameters that shape a single evaluation run."""

    limit: Optional[int] = None
    role: Optional[str] = None
    include_stretch: bool = False
    skip_denied: bool = False
    dry_run: bool = False
    metrics: Optional[list[str]] = None
    concurrency: int = 2
    fail_on_threshold: bool = False


@dataclass
class RagasJob:
    """A single evaluation run tracked in memory + on disk."""

    id: str
    status: str
    submitted_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)
    report_dir: Optional[str] = None
    report: Optional[dict[str, Any]] = None
    # Progress tracking so slow runs show "12/45 cases replayed" in the API.
    total_cases: Optional[int] = None
    replays_expected: Optional[int] = None
    replays_completed: int = 0

    def to_summary(self) -> dict[str, Any]:
        """Compact representation for list endpoints (no full report body)."""
        return {
            "id": self.id,
            "status": self.status,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "params": self.params,
            "total_cases": self.total_cases,
            "replays_expected": self.replays_expected,
            "replays_completed": self.replays_completed,
            "report_summary": (self.report or {}).get("summary"),
        }


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RagasJobStore:
    """Singleton, thread-safe job registry with single-flight semantics."""

    _instance: Optional["RagasJobStore"] = None
    _class_lock = threading.Lock()

    def __init__(self, base_dir: Path | None = None, max_in_memory: int = 20) -> None:
        self._base_dir = base_dir or (
            Path(__file__).resolve().parents[2] / "reports" / "ragas"
        )
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: OrderedDict[str, RagasJob] = OrderedDict()
        self._max_in_memory = max_in_memory
        self._lock = threading.Lock()
        self._active_id: Optional[str] = None
        self._task: Optional[asyncio.Task[None]] = None

    # ------------------------------------------------------------- singleton
    @classmethod
    def get_instance(cls) -> "RagasJobStore":
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Test helper: drop the singleton."""
        with cls._class_lock:
            cls._instance = None

    # ---------------------------------------------------------------- state
    def is_busy(self) -> bool:
        with self._lock:
            if self._active_id is None:
                return False
            job = self._jobs.get(self._active_id)
            return bool(job and job.status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING})

    def active_job(self) -> Optional[RagasJob]:
        with self._lock:
            if not self._active_id:
                return None
            return self._jobs.get(self._active_id)

    def get(self, job_id: str) -> Optional[RagasJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, limit: int = 20) -> list[RagasJob]:
        with self._lock:
            return list(self._jobs.values())[-max(1, limit) :][::-1]

    def latest_completed(self) -> Optional[RagasJob]:
        with self._lock:
            for job in reversed(self._jobs.values()):
                if job.status == JOB_STATUS_COMPLETED:
                    return job
            return None

    # ---------------------------------------------------------- job control
    def submit(self, params: RagasJobParams) -> RagasJob:
        """Create a new job and start the async runner, or raise if busy."""
        if self.is_busy():
            active = self.active_job()
            raise RuntimeError(
                f"another RAGAS evaluation is already {active.status if active else 'in flight'}"
            )

        job_id = uuid.uuid4().hex
        job = RagasJob(
            id=job_id,
            status=JOB_STATUS_QUEUED,
            submitted_at=_utcnow_iso(),
            params=asdict(params),
        )
        with self._lock:
            self._jobs[job_id] = job
            self._active_id = job_id
            self._evict_locked()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None:
            # No event loop \u2014 caller must run the job synchronously (tests).
            return job

        self._task = loop.create_task(self._run(job, params))
        return job

    async def _run(self, job: RagasJob, params: RagasJobParams) -> None:
        started = time.perf_counter()
        with self._lock:
            job.status = JOB_STATUS_RUNNING
            job.started_at = _utcnow_iso()

        try:
            report = await self._execute(job, params)
        except Exception as exc:  # noqa: BLE001 - surface every error
            logger.exception("ragas_jobs run %s failed", job.id)
            with self._lock:
                job.status = JOB_STATUS_FAILED
                job.error = f"{type(exc).__name__}: {exc}"
                job.completed_at = _utcnow_iso()
                job.duration_seconds = round(time.perf_counter() - started, 2)
                self._active_id = None
            return

        with self._lock:
            job.report = report
            job.status = JOB_STATUS_COMPLETED
            job.completed_at = _utcnow_iso()
            job.duration_seconds = round(time.perf_counter() - started, 2)
            self._active_id = None

    async def _execute(self, job: RagasJob, params: RagasJobParams) -> dict[str, Any]:
        # Late imports so the FastAPI process doesn't pay ragas import cost at
        # startup when the admin endpoint is never used.
        from app.services.langchain_support_rag import LangChainSupportRAGService

        dataset_path = (
            Path(__file__).resolve().parents[2] / "tests" / "rag_qa_validation.json"
        )
        policies_root = Path(__file__).resolve().parents[2] / "policies"

        evaluator = RagasEvaluator(rag_service=LangChainSupportRAGService())
        cases = RagasEvaluator.load_dataset(
            dataset_path, include_stretch=params.include_stretch
        )
        if params.role:
            cases = [c for c in cases if params.role in c.roles_allowed]
        if params.limit is not None:
            cases = cases[: max(0, params.limit)]

        expected_replays = sum(
            len(c.roles_allowed) + (0 if params.skip_denied else len(c.roles_denied))
            for c in cases
        )
        with self._lock:
            job.total_cases = len(cases)
            job.replays_expected = expected_replays

        if not cases:
            raise RuntimeError("no cases matched the supplied filters")

        replays = await evaluator.replay_all(
            cases,
            policies_root=policies_root if policies_root.exists() else None,
            concurrency=max(1, params.concurrency),
            skip_denied=params.skip_denied,
        )
        with self._lock:
            job.replays_completed = len(replays)

        metrics = params.metrics or [
            m.strip() for m in settings.ragas_metrics.split(",") if m.strip()
        ]

        if params.dry_run:
            scores_by_key: dict = {}
            skip_reason: Optional[str] = "dry-run"
        else:
            scores_by_key, skip_reason = evaluator.score_with_ragas(
                replays=replays,
                metrics=metrics,
                judge_deployment=settings.ragas_judge_deployment,
                embedding_deployment=settings.azure_openai_embedding_deployment,
            )

        thresholds = resolve_thresholds()
        cases_by_id = {c.id: c for c in cases}
        rows = evaluator.evaluate_replays(
            replays=replays,
            cases_by_id=cases_by_id,
            scores_by_key=scores_by_key,
            thresholds=thresholds,
        )
        report = build_report(
            rows=rows,
            metrics_used=metrics,
            ragas_skipped_reason=skip_reason,
            thresholds=thresholds,
            duration_seconds=job.duration_seconds or 0.0,
            dataset_path=str(dataset_path),
            dataset_size=len(cases),
        )

        # Persist to disk so the report survives a process restart and can be
        # downloaded/inspected out-of-band by ops (same layout as the CLI).
        out_dir = self._base_dir / job.id
        write_report(report, out_dir)
        with self._lock:
            job.report_dir = str(out_dir)

        if params.fail_on_threshold and report["summary"]["failed"] > 0:
            raise RuntimeError(
                f"threshold gate: {report['summary']['failed']} replay(s) below threshold"
            )

        return report

    # ---------------------------------------------------------------- utils
    def _evict_locked(self) -> None:
        """Drop the oldest entries so we bound memory usage."""
        while len(self._jobs) > self._max_in_memory:
            self._jobs.popitem(last=False)


def get_job_store() -> RagasJobStore:
    """FastAPI dependency-injection friendly accessor."""
    return RagasJobStore.get_instance()
