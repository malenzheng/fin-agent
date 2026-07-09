from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseMember:
    symbol: str
    name: str
    source: str
