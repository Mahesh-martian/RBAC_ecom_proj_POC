"""RAGAS-based offline evaluation for the policy RAG pipeline.

This module drives the RAG service against a golden dataset (typically
``tests/rag_qa_validation.json``), collects the full ``(question, answer,
contexts, ground_truth)`` tuple per case, and computes RAGAS metrics.

Design decisions
----------------
* **In-process, no HTTP hop.** The evaluator calls
  :class:`~app.services.langchain_support_rag.LangChainSupportRAGService`
  directly. That gives us access to raw retrieved passages (needed by
  ``context_precision`` / ``context_recall``) without exposing a debug field on
  the public API. Access control is enforced by passing the case's
  ``roles_allowed[0]`` mapped to the same ``audiences`` set the router uses at
  runtime \u2014 so RBAC-scoped retrieval is exercised end to end.
* **Graceful degradation.** If the ``ragas`` package or its Azure dependencies
  are missing/unconfigured, we still produce a *grounding report* with the
  replay data + deterministic sanity checks (keyword coverage, RBAC leakage).
  The RAGAS section of the report is then flagged as ``skipped`` with a reason.
* **Reproducibility.** Every result records the prompt versions actually used
  (``support_system@vN`` etc.) so a regression can be traced to the specific
  prompt bump that caused it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.services.langchain_support_rag import (
    LangChainSupportRAGService,
    LangChainSupportResult,
)
from app.services.prompt_registry import (
    PromptNotFoundError,
    collect_prompt_labels,
    get_prompt_registry,
)

logger = logging.getLogger(__name__)

# --- Shared with app.routers.chat so both code paths use the same RBAC map.
ROLE_AUDIENCES: dict[str, set[str]] = {
    "customer": {"customer", "common"},
    "vendor": {"vendor", "common"},
    "admin": {"customer", "vendor", "common"},
}

# Metric names accepted from settings / CLI, mapped to RAGAS metric objects.
# Import is lazy so callers can produce a plain grounding report even when the
# ``ragas`` package is not installed.
_METRIC_LOADERS: dict[str, str] = {
    "faithfulness": "faithfulness",
    "answer_relevancy": "answer_relevancy",
    "context_precision": "context_precision",
    "context_recall": "context_recall",
    "answer_similarity": "answer_similarity",
}


# ---------------------------------------------------------------- data classes


@dataclass
class EvalCase:
    """One question from the golden dataset."""

    id: str
    question: str
    audience: str
    roles_allowed: list[str]
    roles_denied: list[str] = field(default_factory=list)
    expect_keywords: list[str] = field(default_factory=list)
    expect_source: Optional[str] = None
    source_hint: Optional[str] = None
    note: Optional[str] = None
    ground_truth: Optional[str] = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "EvalCase":
        return cls(
            id=str(data["id"]),
            question=str(data["question"]),
            audience=str(data.get("audience", "common")),
            roles_allowed=list(data.get("roles_allowed") or []),
            roles_denied=list(data.get("roles_denied") or []),
            expect_keywords=list(data.get("expect_keywords") or []),
            expect_source=data.get("expect_source"),
            source_hint=data.get("source_hint"),
            note=data.get("note"),
            ground_truth=data.get("ground_truth"),
        )


@dataclass
class ReplayResult:
    """Raw output of running one case through the RAG service for one role."""

    case_id: str
    role: str
    question: str
    answer: str
    citations: list[str]
    contexts: list[str]
    context_sources: list[str]
    retrieval_count: int
    latency_ms: float
    search_latency_ms: float
    llm_latency_ms: float
    prompt_versions: dict[str, str]
    system_prompt_label: str
    confidence: float
    ground_truth: str
    # Deterministic sanity checks computed inline so the report is useful even
    # when RAGAS scoring is skipped.
    keyword_hit: bool
    keyword_missing: list[str]
    retrieved_own_audience: bool
    is_refusal: bool
    error: Optional[str] = None


@dataclass
class RagasScores:
    """RAGAS metric scores for a single (case, role) replay.

    Fields are ``Optional[float]`` so the report can distinguish "not evaluated"
    from ``0.0`` (a real failing score).
    """

    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    answer_similarity: Optional[float] = None


@dataclass
class EvalRow:
    """One row in the final report: replay + optional RAGAS scores + verdict."""

    replay: ReplayResult
    scores: RagasScores
    passed: bool
    failure_reasons: list[str]


# ---------------------------------------------------------------- deny detection


_DEFAULT_DENY_PHRASES = (
    "do not have enough information",
    "don't have enough information",
    "not enough information",
    "contact support",
    "i do not have",
)


def _is_refusal(answer: str, deny_phrases: tuple[str, ...] = _DEFAULT_DENY_PHRASES) -> bool:
    a = answer.lower()
    return any(p in a for p in deny_phrases)


# ---------------------------------------------------------------- evaluator


class RagasEvaluator:
    """Replay a golden dataset against the RAG service and score with RAGAS."""

    def __init__(
        self,
        rag_service: Optional[LangChainSupportRAGService] = None,
        deny_phrases: tuple[str, ...] = _DEFAULT_DENY_PHRASES,
    ) -> None:
        self._rag = rag_service or LangChainSupportRAGService()
        self._deny_phrases = deny_phrases

    # -- Dataset loading ------------------------------------------------

    @staticmethod
    def load_dataset(
        path: Path,
        *,
        include_stretch: bool = False,
    ) -> list[EvalCase]:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        cases_raw = list(raw.get("cases") or [])
        if include_stretch:
            cases_raw.extend(raw.get("stretch_cases") or [])
        deny_phrases = tuple(raw.get("deny_phrases") or ())
        # Store deny phrases as instance state via a side channel if the caller
        # constructed via a helper; here we just return the parsed cases.
        del deny_phrases  # kept for future extension
        return [EvalCase.from_json(c) for c in cases_raw]

    # -- Ground truth ---------------------------------------------------

    @staticmethod
    def build_ground_truth(case: EvalCase, policies_root: Optional[Path] = None) -> str:
        """Return a ground-truth string for RAGAS metrics.

        Precedence:
          1. Explicit ``ground_truth`` field on the case.
          2. Content of the ``expect_source`` file under ``policies_root``.
          3. Comma-joined ``expect_keywords`` framed as an expected answer.
        """
        if case.ground_truth:
            return case.ground_truth

        if case.expect_source and policies_root:
            candidates = list(policies_root.rglob(case.expect_source))
            if candidates:
                try:
                    text = candidates[0].read_text(encoding="utf-8")
                    # Keep it bounded so RAGAS token cost stays sane.
                    return text.strip()[:2000]
                except OSError:
                    pass

        if case.expect_keywords:
            joined = ", ".join(case.expect_keywords)
            return f"The correct answer should reference: {joined}."

        return case.question  # last resort

    # -- Replay ---------------------------------------------------------

    async def replay_one(
        self,
        case: EvalCase,
        role: str,
        policies_root: Optional[Path] = None,
    ) -> ReplayResult:
        audiences = ROLE_AUDIENCES.get(role, {"customer", "common"})
        persona = self._load_persona(role)
        ground_truth = self.build_ground_truth(case, policies_root=policies_root)

        error: Optional[str] = None
        result: Optional[LangChainSupportResult] = None
        try:
            result = await self._rag.answer(
                query=case.question,
                top_k=settings.rag_top_k,
                user_name=None,
                history=None,
                audiences=audiences,
                persona=persona,
            )
        except Exception as exc:  # noqa: BLE001 - surface every failure in the report
            error = f"{type(exc).__name__}: {exc}"
            logger.error("ragas_eval replay failed for %s/%s: %s", case.id, role, error)

        answer = result.answer if result else ""
        citations = list(result.citations) if result else []
        contexts_payload = list(result.contexts) if result else []
        context_texts = [str(c.get("content") or "") for c in contexts_payload]
        context_sources = [str(c.get("source") or "") for c in contexts_payload]

        prompt_versions = self._collect_prompt_versions(role, result)

        # Deterministic sanity checks (RAGAS-independent).
        answer_lower = answer.lower()
        missing = [k for k in case.expect_keywords if k.lower() not in answer_lower]
        prefix = f"{case.audience}/"
        retrieved_own = any(prefix in src for src in context_sources)
        refusal = _is_refusal(answer, self._deny_phrases)

        return ReplayResult(
            case_id=case.id,
            role=role,
            question=case.question,
            answer=answer,
            citations=citations,
            contexts=context_texts,
            context_sources=context_sources,
            retrieval_count=result.retrieval_count if result else 0,
            latency_ms=result.latency_ms if result else 0.0,
            search_latency_ms=result.search_latency_ms if result else 0.0,
            llm_latency_ms=result.llm_latency_ms if result else 0.0,
            prompt_versions=prompt_versions,
            system_prompt_label=result.system_prompt_label if result else "",
            confidence=result.confidence if result else 0.0,
            ground_truth=ground_truth,
            keyword_hit=(not missing and not refusal and bool(answer)),
            keyword_missing=missing,
            retrieved_own_audience=retrieved_own,
            is_refusal=refusal,
            error=error,
        )

    async def replay_all(
        self,
        cases: list[EvalCase],
        *,
        policies_root: Optional[Path] = None,
        concurrency: int = 2,
        skip_denied: bool = False,
    ) -> list[ReplayResult]:
        """Replay every ``(case, role)`` pair in ``cases`` under a concurrency cap.

        Both ``roles_allowed`` (positive validation) and ``roles_denied``
        (RBAC leakage negative test) are replayed unless ``skip_denied=True``.
        """
        semaphore = asyncio.Semaphore(max(1, concurrency))
        tasks: list[asyncio.Task[ReplayResult]] = []

        async def _run(case: EvalCase, role: str) -> ReplayResult:
            async with semaphore:
                return await self.replay_one(case, role, policies_root=policies_root)

        for case in cases:
            for role in case.roles_allowed:
                tasks.append(asyncio.create_task(_run(case, role)))
            if not skip_denied:
                for role in case.roles_denied:
                    tasks.append(asyncio.create_task(_run(case, role)))

        return list(await asyncio.gather(*tasks))

    # -- Prompt-version bookkeeping ------------------------------------

    def _load_persona(self, role: str) -> Optional[str]:
        try:
            tpl = get_prompt_registry().get("role_persona", variant=role)
            return tpl.template.strip() or None
        except PromptNotFoundError:
            return None

    def _collect_prompt_versions(
        self, role: str, result: Optional[LangChainSupportResult]
    ) -> dict[str, str]:
        registry = get_prompt_registry()
        templates: list[Any] = []
        try:
            templates.append(registry.get("role_persona", variant=role))
        except PromptNotFoundError:
            pass
        try:
            templates.append(registry.get("role_help_text", variant=role))
        except PromptNotFoundError:
            pass
        out = collect_prompt_labels(templates)
        if result and getattr(result, "system_prompt_label", ""):
            out["support_system"] = result.system_prompt_label
        return out

    # -- Verdict --------------------------------------------------------

    def evaluate_replays(
        self,
        replays: list[ReplayResult],
        cases_by_id: dict[str, EvalCase],
        scores_by_key: dict[tuple[str, str], RagasScores],
        thresholds: dict[str, float],
    ) -> list[EvalRow]:
        rows: list[EvalRow] = []
        for replay in replays:
            case = cases_by_id.get(replay.case_id)
            reasons: list[str] = []

            if replay.error:
                reasons.append(f"replay_error: {replay.error}")

            is_allowed_role = bool(case and replay.role in case.roles_allowed)
            is_denied_role = bool(case and replay.role in case.roles_denied)

            # Positive path: allowed roles must produce a grounded, on-keyword,
            # non-refusal answer using at least one document from their own
            # audience (or a common doc \u2014 which retrieved_own_audience allows).
            if is_allowed_role:
                if replay.is_refusal:
                    reasons.append("refused_for_allowed_role")
                if replay.keyword_missing:
                    reasons.append(f"missing_keywords: {replay.keyword_missing}")
                if not replay.retrieved_own_audience:
                    reasons.append(
                        f"no_own_audience_doc_retrieved (audience={case.audience if case else '?'})"
                    )

            # Negative path: denied roles must NOT see the audience's docs.
            if is_denied_role and case:
                own_prefix = f"{case.audience}/"
                leak = [s for s in replay.context_sources if own_prefix in s]
                if leak:
                    reasons.append(f"rbac_leak: {leak}")
                if not replay.is_refusal and case.audience != "common":
                    reasons.append("denied_role_received_grounded_answer")

            # RAGAS thresholds \u2014 only applied on the allowed path where a real
            # grounded answer is expected. Missing scores (RAGAS skipped) are
            # neutral.
            scores = scores_by_key.get((replay.case_id, replay.role), RagasScores())
            if is_allowed_role:
                for metric_name, threshold in thresholds.items():
                    value = getattr(scores, metric_name, None)
                    if value is not None and value < threshold:
                        reasons.append(
                            f"{metric_name}={value:.3f} < threshold {threshold:.2f}"
                        )

            rows.append(EvalRow(replay=replay, scores=scores, passed=not reasons, failure_reasons=reasons))
        return rows

    # -- RAGAS scoring --------------------------------------------------

    def score_with_ragas(
        self,
        replays: list[ReplayResult],
        metrics: list[str],
        judge_deployment: Optional[str] = None,
        embedding_deployment: Optional[str] = None,
    ) -> tuple[dict[tuple[str, str], RagasScores], Optional[str]]:
        """Compute RAGAS metrics for every replay with retrieved contexts.

        Returns ``(scores_by_key, skip_reason)``: when RAGAS or its Azure judge
        cannot be loaded, ``skip_reason`` is a human-readable string and every
        entry in ``scores_by_key`` is an empty :class:`RagasScores`.
        """
        empty: dict[tuple[str, str], RagasScores] = {
            (r.case_id, r.role): RagasScores() for r in replays
        }

        try:
            from datasets import Dataset  # type: ignore
            from ragas import evaluate as ragas_evaluate  # type: ignore
            from ragas import metrics as ragas_metrics_mod  # type: ignore
        except ImportError as exc:
            return empty, f"ragas package not installed ({exc})"

        # Resolve judge/embedding via Azure OpenAI (LangChain wrappers RAGAS accepts).
        try:
            from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings  # type: ignore
        except ImportError as exc:
            return empty, f"langchain-openai not installed ({exc})"

        judge_dep = (
            judge_deployment
            or settings.ragas_judge_deployment
            or settings.azure_openai_chat_deployment
        )
        embed_dep = embedding_deployment or settings.azure_openai_embedding_deployment
        if not (settings.azure_openai_endpoint and settings.azure_openai_api_key and judge_dep):
            return empty, "azure_openai judge not configured"

        try:
            judge_llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_deployment=judge_dep,
                temperature=0,
            )
            judge_embeddings = None
            if embed_dep:
                judge_embeddings = AzureOpenAIEmbeddings(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                    azure_deployment=embed_dep,
                )
        except Exception as exc:  # noqa: BLE001
            return empty, f"judge init failed: {exc}"

        # Build the RAGAS dataset. Skip replays with no contexts (nothing to score).
        rows_ordered: list[tuple[str, str]] = []
        payload: dict[str, list[Any]] = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": [],
            "reference": [],
        }
        for r in replays:
            if r.error or not r.contexts or not r.answer:
                continue
            rows_ordered.append((r.case_id, r.role))
            payload["question"].append(r.question)
            payload["answer"].append(r.answer)
            payload["contexts"].append(r.contexts)
            payload["ground_truth"].append(r.ground_truth)
            payload["reference"].append(r.ground_truth)

        if not rows_ordered:
            return empty, "no replays with retrievable contexts to score"

        metric_objs = []
        wanted = {m.strip().lower() for m in metrics if m and m.strip()}
        for name in wanted:
            attr = _METRIC_LOADERS.get(name)
            if attr is None:
                logger.warning("ragas_eval unknown metric %r ignored", name)
                continue
            metric = getattr(ragas_metrics_mod, attr, None)
            if metric is None:
                logger.warning("ragas_eval metric %r not present in installed ragas", name)
                continue
            metric_objs.append(metric)

        if not metric_objs:
            return empty, "no supported RAGAS metrics could be loaded"

        try:
            ds = Dataset.from_dict(payload)
            result = ragas_evaluate(
                ds,
                metrics=metric_objs,
                llm=judge_llm,
                embeddings=judge_embeddings,
                raise_exceptions=False,
            )
        except Exception as exc:  # noqa: BLE001 - never let scoring failure kill the report
            return empty, f"ragas evaluate() failed: {exc}"

        # Extract per-row metric values.
        # ``result`` is a ragas.dataset_schema.EvaluationResult in recent versions;
        # older releases returned a pandas.DataFrame directly. Handle both.
        try:
            df = result.to_pandas()  # type: ignore[attr-defined]
        except AttributeError:
            df = result  # already a DataFrame

        scores: dict[tuple[str, str], RagasScores] = {
            (r.case_id, r.role): RagasScores() for r in replays
        }
        for (case_id, role), (_, row) in zip(rows_ordered, df.iterrows()):
            scores[(case_id, role)] = RagasScores(
                faithfulness=_maybe_float(row.get("faithfulness")),
                answer_relevancy=_maybe_float(row.get("answer_relevancy")),
                context_precision=_maybe_float(row.get("context_precision")),
                context_recall=_maybe_float(row.get("context_recall")),
                answer_similarity=_maybe_float(row.get("answer_similarity")),
            )
        return scores, None


# ---------------------------------------------------------------- helpers


def _maybe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    # RAGAS emits NaN for cases it couldn't score (e.g. LLM refusal).
    if f != f:  # NaN check
        return None
    return f


# ---------------------------------------------------------------- report writer


def _mean(values: list[float]) -> Optional[float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def build_report(
    rows: list[EvalRow],
    *,
    metrics_used: list[str],
    ragas_skipped_reason: Optional[str],
    thresholds: dict[str, float],
    duration_seconds: float,
    dataset_path: str,
    dataset_size: int,
) -> dict[str, Any]:
    """Aggregate per-row results into a JSON-serialisable report."""
    total = len(rows)
    passed = sum(1 for r in rows if r.passed)
    by_metric: dict[str, list[float]] = {name: [] for name in _METRIC_LOADERS}
    for row in rows:
        for name in _METRIC_LOADERS:
            value = getattr(row.scores, name, None)
            if value is not None:
                by_metric[name].append(value)

    aggregate = {
        name: _mean(values)
        for name, values in by_metric.items()
        if values
    }

    per_role: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = per_role.setdefault(row.replay.role, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if row.passed:
            bucket["passed"] += 1

    prompt_versions_seen: dict[str, set[str]] = {}
    for row in rows:
        for pid, label in row.replay.prompt_versions.items():
            prompt_versions_seen.setdefault(pid, set()).add(label)

    threshold_breaches = [
        {"case_id": row.replay.case_id, "role": row.replay.role, "reasons": row.failure_reasons}
        for row in rows
        if not row.passed
    ]

    return {
        "summary": {
            "dataset": dataset_path,
            "dataset_size": dataset_size,
            "replays": total,
            "passed": passed,
            "failed": total - passed,
            "duration_seconds": round(duration_seconds, 2),
            "metrics_requested": metrics_used,
            "ragas_skipped_reason": ragas_skipped_reason,
        },
        "aggregate_scores": {k: round(v, 4) for k, v in aggregate.items()},
        "thresholds": thresholds,
        "per_role": per_role,
        "prompt_versions": {k: sorted(v) for k, v in prompt_versions_seen.items()},
        "failures": threshold_breaches,
        "rows": [
            {
                "case_id": row.replay.case_id,
                "role": row.replay.role,
                "passed": row.passed,
                "question": row.replay.question,
                "answer": row.replay.answer,
                "confidence": row.replay.confidence,
                "retrieval_count": row.replay.retrieval_count,
                "citations": row.replay.citations,
                "context_sources": row.replay.context_sources,
                "keyword_missing": row.replay.keyword_missing,
                "is_refusal": row.replay.is_refusal,
                "retrieved_own_audience": row.replay.retrieved_own_audience,
                "prompt_versions": row.replay.prompt_versions,
                "scores": {
                    name: getattr(row.scores, name)
                    for name in _METRIC_LOADERS
                    if getattr(row.scores, name) is not None
                },
                "failure_reasons": row.failure_reasons,
                "latency_ms": row.replay.latency_ms,
                "search_latency_ms": row.replay.search_latency_ms,
                "llm_latency_ms": row.replay.llm_latency_ms,
                "error": row.replay.error,
            }
            for row in rows
        ],
    }


def report_to_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    summary = report["summary"]
    lines.append(f"# RAGAS Evaluation Report")
    lines.append("")
    lines.append(f"- Dataset: `{summary['dataset']}` ({summary['dataset_size']} cases)")
    lines.append(f"- Replays: **{summary['replays']}** (passed **{summary['passed']}**, failed **{summary['failed']}**)")
    lines.append(f"- Duration: {summary['duration_seconds']}s")
    lines.append(f"- Metrics: {', '.join(summary['metrics_requested']) or 'none'}")
    if summary.get("ragas_skipped_reason"):
        lines.append(f"- RAGAS scoring skipped: `{summary['ragas_skipped_reason']}`")
    lines.append("")
    lines.append("## Aggregate scores")
    lines.append("")
    if not report["aggregate_scores"]:
        lines.append("_No RAGAS scores available._")
    else:
        lines.append("| Metric | Mean | Threshold |")
        lines.append("|---|---|---|")
        for name, mean in report["aggregate_scores"].items():
            threshold = report["thresholds"].get(name)
            threshold_txt = f"{threshold:.2f}" if threshold is not None else "\u2013"
            lines.append(f"| {name} | {mean:.4f} | {threshold_txt} |")
    lines.append("")
    lines.append("## By role")
    lines.append("")
    lines.append("| Role | Total | Passed |")
    lines.append("|---|---|---|")
    for role, bucket in sorted(report["per_role"].items()):
        lines.append(f"| {role} | {bucket['total']} | {bucket['passed']} |")
    lines.append("")
    if report["failures"]:
        lines.append("## Failures")
        lines.append("")
        for f in report["failures"]:
            reasons = "; ".join(f["reasons"])
            lines.append(f"- **{f['case_id']}** / {f['role']}: {reasons}")
        lines.append("")
    lines.append("## Prompt versions in use")
    lines.append("")
    for pid, labels in sorted(report["prompt_versions"].items()):
        lines.append(f"- `{pid}`: {', '.join(labels)}")
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path.write_text(report_to_markdown(report), encoding="utf-8")
    return json_path, md_path


# ---------------------------------------------------------------- convenience


def resolve_thresholds() -> dict[str, float]:
    """Read per-metric thresholds from settings."""
    return {
        "faithfulness": settings.ragas_min_faithfulness,
        "answer_relevancy": settings.ragas_min_answer_relevancy,
        "context_precision": settings.ragas_min_context_precision,
        "context_recall": settings.ragas_min_context_recall,
    }
