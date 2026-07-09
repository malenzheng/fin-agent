from __future__ import annotations

import pandas as pd


def add_indicator_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy().sort_values("date").reset_index(drop=True)
    close = data["close"]
    high = data["high"]
    low = data["low"]
    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    data["ma_10"] = close.rolling(10).mean()
    data["ma_20"] = close.rolling(20).mean()
    data["ma_30"] = close.rolling(30).mean()
    data["atr_14"] = true_range.rolling(14).mean()
    data["dollar_volume"] = close * data["volume"]
    data["dollar_volume_20"] = data["dollar_volume"].rolling(20).mean()
    data["return_4"] = close.pct_change(4)
    data["return_8"] = close.pct_change(8)
    data["return_12"] = close.pct_change(12)
    data["high_52"] = high.rolling(252, min_periods=20).max()
    return data
