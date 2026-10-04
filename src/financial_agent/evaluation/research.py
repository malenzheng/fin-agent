from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import TypeAdapter, model_validator

from financial_agent.agent.research import ResearchBrief, build_research_brief
from financial_agent.sources.market import MarketSource, NonEmptyText, ResearchModel, ResearchTask


class BenchmarkCase(ResearchModel):
    id: NonEmptyText
    task: ResearchTask
    expected_evidence_ids: list[NonEmptyText]

    @model_validator(mode="after")
    def check_unique_ids(self) -> Self:
        if len(self.expected_evidence_ids) != len(set(self.expected_evidence_ids)):
            raise ValueError("duplicate expected evidence ids")
        return self


class EvaluationResult(ResearchModel):
    case_id: str
    metrics: dict[str, float]
    score: float
    passed: bool
    failures: list[str]


class BenchmarkResult(ResearchModel):
    workflow: str = "deterministic-fixture"
    total: int
    passed: int
    pass_rate: float
    results: list[EvaluationResult]
    limitations: str = "合成资料上的规则基线回归评测，不代表真实金融研究能力或 LLM 能力。"


def load_cases(path: Path) -> list[BenchmarkCase]:
    return TypeAdapter(list[BenchmarkCase]).validate_json(path.read_text(encoding="utf-8"))


def evaluate_brief(brief: ResearchBrief, case: BenchmarkCase, source: MarketSource) -> EvaluationResult:
    # Resolve against the evaluator's task and source, never the agent's attached evidence.
    trusted = {item.id: item for item in source.search(case.task)}
    expected = set(case.expected_evidence_ids)
    if not expected <= trusted.keys():
        raise ValueError(f"{case.id}: expected evidence is unavailable for the benchmark task")

    findings = brief.findings
    citation_matches = [item.evidence_id in trusted for item in findings]
    quote_matches = [
        item.evidence_id in trusted
        and item.text == trusted[item.evidence_id].text
        and item.kind == trusted[item.evidence_id].kind
        for item in findings
    ]
    supported_ids = {item.evidence_id for item, valid in zip(findings, quote_matches) if valid}
    cited_ids = [item.evidence_id for item in findings]
    attached_ids = [item.id for item in brief.evidence]
    integrity = (
        len(attached_ids) == len(set(attached_ids))
        and len(cited_ids) == len(set(cited_ids))
        and set(attached_ids) == set(cited_ids)
        and all(item.id in trusted and item == trusted[item.id] for item in brief.evidence)
    )
    expected_risks = {item_id for item_id in expected if trusted[item_id].kind == "risk"}
    empty_score = 1.0 if not expected else 0.0
    status_matches = (
        brief.status == ("ok" if expected else "insufficient_evidence")
        and bool(findings) == bool(expected)
    )
    metrics = {
        "task_alignment": float(brief.task == case.task),
        "citation_validity": sum(citation_matches) / len(findings) if findings else empty_score,
        "quote_support": sum(quote_matches) / len(findings) if findings else empty_score,
        "evidence_integrity": float(integrity),
        "evidence_coverage": len(supported_ids & expected) / len(expected) if expected else float(not findings),
        "risk_coverage": len(supported_ids & expected_risks) / len(expected_risks) if expected_risks else 1.0,
        "status_correctness": float(status_matches),
    }
    explanations = {
        "task_alignment": "标的、查询时点或时间窗口与评测任务不符",
        "citation_validity": "引用不存在、标的不符、超出窗口或在查询时点尚不可获得",
        "quote_support": "摘录文本或分类与可信原文不符，或缺少有效摘录",
        "evidence_integrity": "随附证据被改写、缺失、重复或与引用列表不一致",
        "evidence_coverage": "未覆盖预期证据，或应信息不足时仍输出摘录",
        "risk_coverage": "遗漏预期风险证据",
        "status_correctness": "信息充分性状态与预期不符",
    }
    failures = [f"{key}: {explanations[key]}" for key, value in metrics.items() if value < 1]
    return EvaluationResult(
        case_id=case.id, metrics=metrics, score=round(sum(metrics.values()) / len(metrics) * 100, 2),
        passed=not failures, failures=failures,
    )


def run_benchmark(cases: list[BenchmarkCase], source: MarketSource) -> BenchmarkResult:
    if not cases:
        raise ValueError("benchmark cases must not be empty")
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("duplicate benchmark case ids")
    results = [evaluate_brief(build_research_brief(case.task, source), case, source) for case in cases]
    passed = sum(result.passed for result in results)
    return BenchmarkResult(total=len(results), passed=passed, pass_rate=passed / len(results), results=results)
