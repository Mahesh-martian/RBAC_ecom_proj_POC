#!/usr/bin/env python3
"""RAGAS offline evaluation CLI for the policy RAG pipeline.

Runs every case in ``tests/rag_qa_validation.json`` (or a caller-supplied
dataset) through the live :class:`LangChainSupportRAGService` **in-process**
so raw retrieved contexts are available for RAGAS metrics. Writes a JSON +
Markdown report to ``reports/ragas/<timestamp>/``.

Typical usage
-------------
Smoke run (no RAGAS scoring, just replay to catch retrieval/RBAC regressions)::

    python scripts/ragas_eval.py --dry-run --limit 3

Full scored run against the golden set::

    python scripts/ragas_eval.py

CI gate (exit 1 if any metric drops below the settings thresholds)::

    python scripts/ragas_eval.py --fail-on-threshold

The script is intentionally in-process so it never needs a running FastAPI
server \u2014 point it at a working ``.env`` (Azure OpenAI + Azure AI Search) and
run. When those are absent it still produces a grounding report (keyword
coverage + RBAC leakage), with the RAGAS section flagged ``skipped``.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make the rag service package importable when running the script from the
# ``services/rag`` directory (which is where the Dockerfile / CI would).
_HERE = Path(__file__).resolve()
_RAG_ROOT = _HERE.parents[1]
sys.path.insert(0, str(_RAG_ROOT))

from app.config import settings  # noqa: E402  (path munging happens above)
from app.services.langchain_support_rag import LangChainSupportRAGService  # noqa: E402
from app.services.ragas_eval import (  # noqa: E402
    RagasEvaluator,
    build_report,
    resolve_thresholds,
    write_report,
)

logger = logging.getLogger("ragas_eval")


DEFAULT_DATASET = _RAG_ROOT / "tests" / "rag_qa_validation.json"
DEFAULT_POLICIES = _RAG_ROOT / "policies"
DEFAULT_OUTPUT_BASE = _RAG_ROOT / "reports" / "ragas"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RAGAS evaluation against the policy RAG pipeline.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=f"Path to the golden dataset JSON (default: {DEFAULT_DATASET}).",
    )
    parser.add_argument(
        "--policies",
        type=Path,
        default=DEFAULT_POLICIES,
        help=(
            "Root of the policy markdown tree, used to synthesise ground-truth "
            "answers when a case supplies `expect_source`."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory to write report files to (default: reports/ragas/<timestamp>).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only evaluate the first N cases (useful for smoke tests).",
    )
    parser.add_argument(
        "--role",
        choices=["customer", "vendor", "admin"],
        default=None,
        help="Only evaluate cases whose `roles_allowed` includes this role.",
    )
    parser.add_argument(
        "--include-stretch",
        action="store_true",
        help="Also run the `stretch_cases` set (documented retrieval gaps).",
    )
    parser.add_argument(
        "--skip-denied",
        action="store_true",
        help="Skip `roles_denied` (negative RBAC) replays.",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default=None,
        help=(
            "Comma-separated subset of "
            "faithfulness,answer_relevancy,context_precision,context_recall,answer_similarity. "
            "Default uses settings.ragas_metrics."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of parallel replays (default 2 to respect Azure rate limits).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Replay and produce grounding report, but skip RAGAS metric scoring.",
    )
    parser.add_argument(
        "--fail-on-threshold",
        action="store_true",
        help="Exit with code 1 if any per-row metric is below the configured thresholds.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable INFO-level logging."
    )
    return parser.parse_args(argv)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO if verbose else logging.WARNING,
        stream=sys.stderr,
    )


def _resolve_output_dir(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_OUTPUT_BASE / stamp


async def _run(args: argparse.Namespace) -> int:
    if not args.dataset.exists():
        logger.error("dataset not found: %s", args.dataset)
        return 2

    output_dir = _resolve_output_dir(args.output)
    logger.info("output dir: %s", output_dir)

    metrics_requested = [
        m.strip()
        for m in (args.metrics or settings.ragas_metrics).split(",")
        if m.strip()
    ]

    evaluator = RagasEvaluator(rag_service=LangChainSupportRAGService())

    all_cases = RagasEvaluator.load_dataset(
        args.dataset, include_stretch=args.include_stretch
    )
    if args.role:
        all_cases = [c for c in all_cases if args.role in c.roles_allowed]
    if args.limit is not None:
        all_cases = all_cases[: max(0, args.limit)]

    if not all_cases:
        logger.error("no cases to evaluate after filters")
        return 2

    logger.info("running %d cases (concurrency=%d)", len(all_cases), args.concurrency)

    started = time.perf_counter()
    replays = await evaluator.replay_all(
        all_cases,
        policies_root=args.policies if args.policies.exists() else None,
        concurrency=args.concurrency,
        skip_denied=args.skip_denied,
    )

    if args.dry_run:
        scores_by_key: dict = {}
        skip_reason = "dry-run"
    else:
        logger.info("scoring %d replays with RAGAS (%s)", len(replays), ", ".join(metrics_requested))
        scores_by_key, skip_reason = evaluator.score_with_ragas(
            replays=replays,
            metrics=metrics_requested,
            judge_deployment=settings.ragas_judge_deployment,
            embedding_deployment=settings.azure_openai_embedding_deployment,
        )
        if skip_reason:
            logger.warning("RAGAS scoring skipped: %s", skip_reason)

    thresholds = resolve_thresholds()
    cases_by_id = {c.id: c for c in all_cases}
    rows = evaluator.evaluate_replays(
        replays=replays,
        cases_by_id=cases_by_id,
        scores_by_key=scores_by_key,
        thresholds=thresholds,
    )

    duration = time.perf_counter() - started
    report = build_report(
        rows=rows,
        metrics_used=metrics_requested,
        ragas_skipped_reason=skip_reason,
        thresholds=thresholds,
        duration_seconds=duration,
        dataset_path=str(args.dataset),
        dataset_size=len(all_cases),
    )
    json_path, md_path = write_report(report, output_dir)

    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}\n")
    print(
        f"Summary: replays={report['summary']['replays']} "
        f"passed={report['summary']['passed']} "
        f"failed={report['summary']['failed']} "
        f"duration={report['summary']['duration_seconds']}s"
    )
    if report["aggregate_scores"]:
        print("Aggregate scores:")
        for name, value in report["aggregate_scores"].items():
            print(f"  {name}: {value:.4f}")

    if args.fail_on_threshold and report["summary"]["failed"] > 0:
        logger.error("threshold gate: %d row(s) failed", report["summary"]["failed"])
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.verbose)
    # Disable Azure Monitor auto-configure noise during CLI runs.
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
