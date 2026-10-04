from __future__ import annotations

from datetime import timedelta
from importlib.resources import files
from typing import Annotated, Literal, Protocol, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, TypeAdapter, model_validator

NonEmptyText = Annotated[str, Field(min_length=1)]
EvidenceKind = Literal["catalyst", "risk", "context"]


class ResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ResearchTask(ResearchModel):
    symbol: NonEmptyText
    as_of: AwareDatetime
    max_age_days: int = Field(default=7, ge=1, le=3650, strict=True)


class MarketEvidence(ResearchModel):
    id: NonEmptyText
    symbol: NonEmptyText
    kind: EvidenceKind
    source_type: Literal["news", "announcement", "filing"]
    title: NonEmptyText
    text: NonEmptyText
    publisher: NonEmptyText
    uri: NonEmptyText
    published_at: AwareDatetime
    available_at: AwareDatetime

    @model_validator(mode="after")
    def check_times(self) -> Self:
        if self.available_at < self.published_at:
            raise ValueError("available_at must not precede published_at")
        return self


class MarketSource(Protocol):
    name: str

    def search(self, task: ResearchTask) -> list[MarketEvidence]: ...


def is_eligible(item: MarketEvidence, task: ResearchTask) -> bool:
    return (
        item.symbol == task.symbol
        and task.as_of - timedelta(days=task.max_age_days) <= item.published_at <= task.as_of
        and item.available_at <= task.as_of
    )


class FixtureMarketSource:
    name = "synthetic-fixtures-v1"

    def __init__(self, evidence: list[MarketEvidence]) -> None:
        self._items: dict[str, MarketEvidence] = {}
        for item in evidence:
            if item.id in self._items and self._items[item.id] != item:
                raise ValueError(f"conflicting duplicate evidence id: {item.id}")
            self._items[item.id] = item

    @classmethod
    def from_fixture(cls) -> FixtureMarketSource:
        raw = files("financial_agent.sources").joinpath("fixtures/market.json").read_text(encoding="utf-8")
        return cls(TypeAdapter(list[MarketEvidence]).validate_json(raw))

    def search(self, task: ResearchTask) -> list[MarketEvidence]:
        return sorted(
            (item for item in self._items.values() if is_eligible(item, task)),
            key=lambda item: (item.published_at, item.id),
        )
