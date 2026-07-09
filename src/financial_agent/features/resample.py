from __future__ import annotations

import pandas as pd


def resample_daily_to_weekly(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").set_index("date")
    weekly = data.resample("W-FRI").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "turnover": "sum",
        }
    )
    weekly = weekly.dropna(subset=["open", "high", "low", "close"]).reset_index()
    weekly["date"] = weekly["date"].dt.date
    return weekly
