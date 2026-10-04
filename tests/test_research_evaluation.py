from pathlib import Path

import pytest

from financial_agent.agent.research import Finding, build_research_brief
from financial_agent.evaluation.research import BenchmarkCase, evaluate_brief, load_cases, run_benchmark
from financial_agent.sources.market import FixtureMarketSource
from tests.test_market_research import evidence, task


def setup_case():
    risk = evidence(id="chip-risk", kind="risk", text="客户集中风险。")
    source = FixtureMarketSource([evidence(), risk])
    case = BenchmarkCase(id="case-chip", task=task(), expected_evidence_ids=["chip-order", "chip-risk"])
    return case, source, build_research_brief(case.task, source)


def test_correct_brief_passes_independent_evaluation():
    case, source, brief = setup_case()
    result = evaluate_brief(brief, case, source)
    assert result.passed
    assert result.score == 100
    assert not result.failures


@pytest.mark.parametrize("update,metric", [
    ({"text": "没有依据的利润翻倍预测。"}, "quote_support"),
    ({"kind": "risk"}, "quote_support"),
    ({"evidence_id": "invented"}, "citation_validity"),
])
def test_existing_or_fake_citation_cannot_launder_unsupported_claims(update, metric):
    case, source, brief = setup_case()
    findings = [brief.findings[0].model_copy(update=update), brief.findings[1]]
    result = evaluate_brief(brief.model_copy(update={"findings": findings}), case, source)
    assert not result.passed
    assert result.metrics[metric] < 1
    assert result.failures


def test_forged_attached_evidence_is_checked_against_trusted_source():
    case, source, brief = setup_case()
    forged = "伪造资料。"
    altered = brief.model_copy(update={
        "findings": [brief.findings[0].model_copy(update={"text": forged}), brief.findings[1]],
        "evidence": [brief.evidence[0].model_copy(update={"text": forged}), brief.evidence[1]],
    })
    result = evaluate_brief(altered, case, source)
    assert not result.passed
    assert result.metrics["evidence_integrity"] == 0
    assert result.metrics["quote_support"] == 0.5


def test_omitted_risk_and_duplicate_findings_are_detected():
    case, source, brief = setup_case()
    missing = brief.model_copy(update={"findings": [brief.findings[0]], "evidence": [brief.evidence[0]]})
    result = evaluate_brief(missing, case, source)
    assert result.metrics["risk_coverage"] == 0
    assert result.metrics["evidence_coverage"] == 0.5
    repeated = brief.model_copy(update={"findings": brief.findings + [brief.findings[0]]})
    assert not evaluate_brief(repeated, case, source).passed


def test_evaluation_uses_case_time_even_if_agent_changes_its_task():
    future = evidence(id="future", published_at="2026-10-03T09:00:00+08:00", available_at="2026-10-03T10:00:00+08:00")
    source = FixtureMarketSource([evidence(), future])
    case = BenchmarkCase(id="historical", task=task(), expected_evidence_ids=["chip-order"])
    brief = build_research_brief(task(as_of="2026-10-04T12:00:00+08:00"), source)
    result = evaluate_brief(brief, case, source)
    assert result.metrics["task_alignment"] == 0
    assert result.metrics["citation_validity"] == 0.5
    assert not result.passed


def test_abstention_is_valid_only_for_empty_expected_evidence():
    source = FixtureMarketSource([])
    case = BenchmarkCase(id="empty", task=task(), expected_evidence_ids=[])
    brief = build_research_brief(case.task, source)
    assert evaluate_brief(brief, case, source).passed
    invented = brief.model_copy(update={"findings": [Finding(kind="catalyst", text="无证据预测", evidence_id="fake")]})
    assert not evaluate_brief(invented, case, source).passed


def test_benchmark_rejects_empty_duplicate_and_impossible_gold_cases():
    case, source, _ = setup_case()
    with pytest.raises(ValueError, match="empty"):
        run_benchmark([], source)
    with pytest.raises(ValueError, match="duplicate"):
        run_benchmark([case, case], source)
    with pytest.raises(ValueError, match="expected evidence"):
        run_benchmark([case.model_copy(update={"expected_evidence_ids": ["missing"]})], source)


def test_bundled_benchmark_exercises_distinct_time_and_symbol_cases():
    path = Path(__file__).resolve().parents[1] / "benchmarks" / "research_cases.json"
    cases = load_cases(path)
    assert len(cases) == 6
    result = run_benchmark(cases, FixtureMarketSource.from_fixture())
    assert result.total == 6
    assert result.passed == 6
    assert result.pass_rate == 1
