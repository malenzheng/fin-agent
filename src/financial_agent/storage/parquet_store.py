from __future__ import annotations

from pathlib import Path

import pandas as pd


class OhlcvStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _daily_path(self, symbol: str) -> Path:
        safe_symbol = symbol.replace("/", "_")
        return self.root / "daily" / f"{safe_symbol}.parquet"

    def write_daily(self, symbol: str, frame: pd.DataFrame) -> Path:
        path = self._daily_path(symbol)
        path.parent.mkdir(parents=True, exist_ok=True)
        clean = frame.copy()
        clean["date"] = pd.to_datetime(clean["date"]).dt.date
        clean = clean.sort_values("date").drop_duplicates("date", keep="last")
        clean.to_parquet(path, index=False)
        return path

    def read_daily(self, symbol: str) -> pd.DataFrame:
        path = self._daily_path(symbol)
        frame = pd.read_parquet(path)
        frame["date"] = pd.to_datetime(frame["date"]).dt.date
        return frame.sort_values("date").reset_index(drop=True)
