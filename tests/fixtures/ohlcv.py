from __future__ import annotations

import pandas as pd

from financial_agent.data.sample_ohlcv import make_sample_ohlcv


def make_ohlcv_fixture(symbol: str, days: int = 260) -> pd.DataFrame:
    return make_sample_ohlcv(symbol, days)
