from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from financial_agent.agent.research import build_research_brief
from financial_agent.sources.market import FixtureMarketSource, MarketEvidence, ResearchTask


def evidence(**updates):
    values = {
        "id": "chip-order", "symbol": "DEMO.CHIP", "kind": "catalyst",
        "source_type": "announcement", "title": "合成订单公告",
        "text": "示例芯片公司新增订单 120 万元。", "publisher": "合成数据集",
        "uri": "fixture://market/chip-order", "published_at": "2026-10-01T09:00:00+08:00",
        "available_at": "2026-10-01T10:00:00+08:00",
    }
    return MarketEvidence.model_validate({**values, **updates})


def task(**updates):
    return ResearchTask.model_validate({
        "symbol": "DEMO.CHIP", "as_of": "2026-10-02T12:00:00+08:00",
        "max_age_days": 7, **updates,
    })


def test_source_filters_symbol_publication_availability_and_age():
    source = FixtureMarketSource([
        evidence(), evidence(),
        evidence(id="other", symbol="DEMO.AUTO"),
        evidence(id="future", published_at="2026-10-03T09:00:00+08:00", available_at="2026-10-03T10:00:00+08:00"),
        evidence(id="late", available_at="2026-10-02T13:00:00+08:00"),
        evidence(id="old", published_at="2026-09-01T09:00:00+08:00", available_at="2026-09-01T10:00:00+08:00"),
    ])
    assert [item.id for item in source.search(task())] == ["chip-order"]


def test_source_includes_time_boundaries_and_accepts_equivalent_timezone():
    source = FixtureMarketSource([evidence()])
    assert len(source.search(task(as_of="2026-10-01T02:00:00Z"))) == 1
    assert len(source.search(task(as_of="2026-10-08T09:00:00+08:00"))) == 1
    assert not source.search(task(as_of="2026-10-08T09:00:01+08:00"))


def test_conflicting_duplicate_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        FixtureMarketSource([evidence(), evidence(text="不同内容")])


@pytest.mark.parametrize("changes", [
    {"as_of": "2026-10-02T12:00:00"}, {"symbol": " "},
    {"max_age_days": 0}, {"max_age_days": -1},
])
def test_invalid_task_is_rejected(changes):
    with pytest.raises(ValidationError):
        task(**changes)


def test_evidence_rejects_invalid_time_order_and_naive_time():
    with pytest.raises(ValidationError):
        evidence(available_at="2026-10-01T08:00:00+08:00")
    with pytest.raises(ValidationError):
        evidence(published_at="2026-10-01T09:00:00")


def test_workflow_preserves_quotes_risks_and_trace():
    risk = evidence(id="chip-risk", kind="risk", text="示例芯片公司的客户集中度较高。")
    brief = build_research_brief(task(), FixtureMarketSource([evidence(), risk]))
    assert brief.status == "ok"
    assert {(item.evidence_id, item.text) for item in brief.findings} == {
        ("chip-order", evidence().text), ("chip-risk", risk.text),
    }
    assert [step.tool for step in brief.trace] == ["market.search", "research.extract"]
    assert brief.trace[0].evidence_ids == ["chip-order", "chip-risk"]
    assert brief.mode == "deterministic-fixture"


def test_workflow_abstains_without_evidence():
    brief = build_research_brief(task(), FixtureMarketSource([]))
    assert brief.status == "insufficient_evidence"
    assert not brief.findings
    assert "信息不足" in brief.limitations[0]


def test_packaged_fixture_can_be_loaded():
    source = FixtureMarketSource.from_fixture()
    brief = build_research_brief(task(), source)
    assert {item.evidence_id for item in brief.findings} == {"chip-order", "chip-risk", "chip-context"}
    assert all(item.available_at <= datetime(2026, 10, 2, 4, tzinfo=timezone.utc) for item in brief.evidence)
