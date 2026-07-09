from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from financial_agent.config.settings import Settings


@dataclass(frozen=True)
class ProjectPaths:
    data_dir: Path
    report_dir: Path
    ohlcv_dir: Path
    universe_dir: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProjectPaths":
        data_dir = Path(settings.data_dir)
        report_dir = Path(settings.report_dir)
        return cls(
            data_dir=data_dir,
            report_dir=report_dir,
            ohlcv_dir=data_dir / "ohlcv",
            universe_dir=data_dir / "universe",
        )

    def ensure(self) -> None:
        for path in [self.data_dir, self.report_dir, self.ohlcv_dir, self.universe_dir]:
            path.mkdir(parents=True, exist_ok=True)
