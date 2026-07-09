from __future__ import annotations

import pandas as pd


def make_sample_ohlcv(symbol: str, days: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=days)
    base = 50 + (abs(hash(symbol)) % 30)
    rows = []
    for idx, date in enumerate(dates):
        close = base + idx * 0.25
        open_price = close - 0.2
        high = close + 0.8
        low = close - 1.0
        volume = 1_000_000 + idx * 5_000
        rows.append(
            {
                "date": date.date(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "turnover": close * volume,
            }
        )
    return pd.DataFrame(rows)
