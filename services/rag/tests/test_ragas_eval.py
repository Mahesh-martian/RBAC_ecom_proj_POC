"""Unit tests for the offline RAGAS evaluator.

These tests exercise the deterministic parts of the evaluator (dataset loading,
replay-driven verdict logic, threshold breaches, report shape) with a fake RAG
service. The actual RAGAS metric computation requires Azure OpenAI credentials
and is exercised separately by the offline CLI smoke tests.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.services.langchain_support_rag import LangChainSupportResult
from app.services.ragas_eval import (
    EvalCase,
    RagasEvaluator,
    RagasScores,
    ReplayResult,
    build_report,
    report_to_markdown,
    resolve_thresholds,
)


# ---------------------------------------------------------------- fake service


class _FakeRag:
    """Deterministic stand-in for LangChainSupportRAGService.answer()."""

    def __init__(self, scripted: dict[str, LangChainSupportResult]):
        self._scripted = scripted
        self.calls: list[dict] = []

    async def answer(
        self,
        query,
        top_k=3,
        user_name=None,
        history=None,
        audiences=None,
        persona=None,
    ):
        self.calls.append(
            {
                "query": query,
                "audiences": set(audiences or ()),
                "persona": persona,
            }
        )
        return self._scripted.get(query, _empty_result())


def _empty_result() -> LangChainSupportResult:
    return LangChainSupportResult(
        answer="I do not have enough information.",
        citations=[],
        confidence=0.0,
        latency_ms=1.0,
        contexts=[],
    )


def _grounded_result(answer: str, contexts_source: str) -> LangChainSupportResult:
    return LangChainSupportResult(
        answer=answer,
        citations=[f"Title ({contexts_source})"],
        confidence=0.9,
        latency_ms=5.0,
        retrieval_count=1,
        contexts=[{"title": "T", "source": contexts_source, "content": "Full policy text", "score": 0.9}],
        system_prompt_label="support_system@v1",
    )


# ---------------------------------------------------------------- tests


def test_load_dataset_reads_cases_and_skips_stretch(tmp_path):
    dataset = tmp_path / "rag.json"
    dataset.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "c1",
                        "audience": "customer",
                        "question": "Q1?",
                        "expect_keywords": ["k"],
                        "roles_allowed": ["customer"],
                        "roles_denied": [],
                    }
                ],
                "stretch_cases": [
                    {
                        "id": "s1",
                        "audience": "customer",
                        "question": "Q2?",
                        "roles_allowed": ["customer"],
                    }
                ],
            }
        )
    )

    cases = RagasEvaluator.load_dataset(dataset)
    assert [c.id for c in cases] == ["c1"]
    all_cases = RagasEvaluator.load_dataset(dataset, include_stretch=True)
    assert [c.id for c in all_cases] == ["c1", "s1"]


def test_build_ground_truth_precedence(tmp_path):
    policies = tmp_path / "policies"
    (policies / "customer").mkdir(parents=True)
    (policies / "customer" / "abc.md").write_text("policy body")

    explicit = EvalCase(id="x", question="Q", audience="customer", roles_allowed=["customer"], ground_truth="explicit")
    from_file = EvalCase(id="x", question="Q", audience="customer", roles_allowed=["customer"], expect_source="abc.md")
    from_keywords = EvalCase(
        id="x", question="Q", audience="customer", roles_allowed=["customer"], expect_keywords=["foo", "bar"]
    )
    fallback = EvalCase(id="x", question="Q", audience="customer", roles_allowed=["customer"])

    assert RagasEvaluator.build_ground_truth(explicit) == "explicit"
    assert "policy body" in RagasEvaluator.build_ground_truth(from_file, policies_root=policies)
    assert "foo" in RagasEvaluator.build_ground_truth(from_keywords)
    assert RagasEvaluator.build_ground_truth(fallback) == "Q"


def test_replay_one_records_keyword_and_rbac_signals():
    case = EvalCase(
        id="c1",
        question="Which payment method is a refund issued to?",
        audience="customer",
        roles_allowed=["customer", "admin"],
        roles_denied=[],
        expect_keywords=["original payment method"],
        expect_source="202111770.md",
    )
    scripted = {
        case.question: _grounded_result(
            "The refund is issued to the original payment method.",
            "customer/202111770.md",
        )
    }
    evaluator = RagasEvaluator(rag_service=_FakeRag(scripted))

    replay = asyncio.run(evaluator.replay_one(case, role="customer"))

    assert replay.keyword_hit is True
    assert replay.keyword_missing == []
    assert replay.retrieved_own_audience is True
    assert replay.is_refusal is False
    assert replay.contexts == ["Full policy text"]
    assert replay.system_prompt_label == "support_system@v1"


def test_replay_one_flags_missing_keywords_and_refusal():
    case = EvalCase(
        id="c1",
        question="Where is my shipment?",
        audience="customer",
        roles_allowed=["customer"],
        expect_keywords=["tracking number"],
    )
    scripted = {case.question: _empty_result()}
    evaluator = RagasEvaluator(rag_service=_FakeRag(scripted))

    replay = asyncio.run(evaluator.replay_one(case, role="customer"))
    assert replay.is_refusal is True
    assert replay.keyword_missing == ["tracking number"]
    assert replay.retrieved_own_audience is False


def test_evaluate_replays_flags_rbac_leak():
    case = EvalCase(
        id="c1",
        question="Vendor secret?",
        audience="vendor",
        roles_allowed=["vendor", "admin"],
        roles_denied=["customer"],
        expect_keywords=["fee"],
    )
    evaluator = RagasEvaluator(rag_service=_FakeRag({}))

    # A customer somehow got a vendor doc back: RBAC leak.
    leaked = ReplayResult(
        case_id="c1",
        role="customer",
        question=case.question,
        answer="The fee is 15%.",
        citations=["Vendor doc (vendor/g200336920.md)"],
        contexts=["Full text"],
        context_sources=["vendor/g200336920.md"],
        retrieval_count=1,
        latency_ms=1.0,
        search_latency_ms=0.5,
        llm_latency_ms=0.5,
        prompt_versions={},
        system_prompt_label="support_system@v1",
        confidence=0.9,
        ground_truth="",
        keyword_hit=True,
        keyword_missing=[],
        retrieved_own_audience=False,
        is_refusal=False,
    )
    rows = evaluator.evaluate_replays(
        replays=[leaked],
        cases_by_id={case.id: case},
        scores_by_key={},
        thresholds={},
    )
    assert rows[0].passed is False
    joined = " ".join(rows[0].failure_reasons)
    assert "rbac_leak" in joined
    assert "denied_role_received_grounded_answer" in joined


def test_evaluate_replays_threshold_gate_only_for_allowed_role():
    case = EvalCase(
        id="c1",
        question="Q",
        audience="customer",
        roles_allowed=["customer"],
        expect_keywords=["k"],
    )
    ok_replay = ReplayResult(
        case_id="c1",
        role="customer",
        question="Q",
        answer="A with k",
        citations=[],
        contexts=["ctx"],
        context_sources=["customer/foo.md"],
        retrieval_count=1,
        latency_ms=1.0,
        search_latency_ms=1.0,
        llm_latency_ms=1.0,
        prompt_versions={},
        system_prompt_label="support_system@v1",
        confidence=0.5,
        ground_truth="",
        keyword_hit=True,
        keyword_missing=[],
        retrieved_own_audience=True,
        is_refusal=False,
    )
    evaluator = RagasEvaluator(rag_service=_FakeRag({}))
    rows = evaluator.evaluate_replays(
        replays=[ok_replay],
        cases_by_id={case.id: case},
        scores_by_key={("c1", "customer"): RagasScores(faithfulness=0.3)},
        thresholds={"faithfulness": 0.7},
    )
    assert rows[0].passed is False
    assert any("faithfulness" in r for r in rows[0].failure_reasons)


def test_build_report_shape_and_markdown(tmp_path):
    case = EvalCase(
        id="c1",
        question="Q",
        audience="customer",
        roles_allowed=["customer"],
        expect_keywords=[],
    )
    replay = ReplayResult(
        case_id="c1",
        role="customer",
        question="Q",
        answer="A",
        citations=[],
        contexts=["ctx"],
        context_sources=["customer/foo.md"],
        retrieval_count=1,
        latency_ms=1.0,
        search_latency_ms=1.0,
        llm_latency_ms=1.0,
        prompt_versions={"support_system": "support_system@v1"},
        system_prompt_label="support_system@v1",
        confidence=0.7,
        ground_truth="",
        keyword_hit=True,
        keyword_missing=[],
        retrieved_own_audience=True,
        is_refusal=False,
    )
    evaluator = RagasEvaluator(rag_service=_FakeRag({}))
    rows = evaluator.evaluate_replays(
        replays=[replay],
        cases_by_id={case.id: case},
        scores_by_key={("c1", "customer"): RagasScores(faithfulness=0.8)},
        thresholds={"faithfulness": 0.7},
    )
    report = build_report(
        rows=rows,
        metrics_used=["faithfulness"],
        ragas_skipped_reason=None,
        thresholds={"faithfulness": 0.7},
        duration_seconds=0.5,
        dataset_path="unit-test",
        dataset_size=1,
    )
    assert report["summary"]["passed"] == 1
    assert report["aggregate_scores"]["faithfulness"] == 0.8
    md = report_to_markdown(report)
    assert "faithfulness" in md
    assert "support_system" in md


def test_resolve_thresholds_pulls_from_settings():
    thresholds = resolve_thresholds()
    for key in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        assert key in thresholds
        assert 0.0 <= thresholds[key] <= 1.0
