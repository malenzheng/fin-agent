from __future__ import annotations

from typing import Literal

from financial_agent.sources.market import (
    EvidenceKind, MarketEvidence, MarketSource, NonEmptyText, ResearchModel, ResearchTask,
)


class Finding(ResearchModel):
    kind: EvidenceKind
    text: NonEmptyText
    evidence_id: NonEmptyText


class TraceStep(ResearchModel):
    tool: NonEmptyText
    input: dict
    evidence_ids: list[str]


class ResearchBrief(ResearchModel):
    task: ResearchTask
    mode: Literal["deterministic-fixture"] = "deterministic-fixture"
    provider: NonEmptyText
    status: Literal["ok", "insufficient_evidence"]
    findings: list[Finding]
    evidence: list[MarketEvidence]
    trace: list[TraceStep]
    limitations: list[str]


def build_research_brief(task: ResearchTask, source: MarketSource) -> ResearchBrief:
    evidence = source.search(task)
    ids = [item.id for item in evidence]
    limitations = ["合成资料与人工分类，仅用于离线工程演示；当前为原文摘录基线，未调用 LLM。"]
    if not evidence:
        limitations.insert(0, "信息不足：指定标的与时间窗口内没有可获得的资料。")
    elif not any(item.kind == "risk" for item in evidence):
        limitations.append("未检索到风险类资料，不代表不存在风险。")
    return ResearchBrief(
        task=task, provider=source.name, status="ok" if evidence else "insufficient_evidence",
        findings=[Finding(kind=item.kind, text=item.text, evidence_id=item.id) for item in evidence],
        evidence=evidence,
        trace=[
            TraceStep(tool="market.search", input=task.model_dump(mode="json"), evidence_ids=ids),
            TraceStep(tool="research.extract", input={"strategy": "verbatim-v1"}, evidence_ids=ids),
        ],
        limitations=limitations,
    )
