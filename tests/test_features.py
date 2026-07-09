from financial_agent.features.indicators import add_indicator_columns
from financial_agent.features.resample import resample_daily_to_weekly
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_resample_daily_to_weekly() -> None:
    daily = make_ohlcv_fixture("AAPL.US", days=30)
    weekly = resample_daily_to_weekly(daily)
    assert {"date", "open", "high", "low", "close", "volume", "turnover"}.issubset(weekly.columns)
    assert 5 <= len(weekly) <= 7
    assert weekly["date"].is_monotonic_increasing


def test_add_indicator_columns() -> None:
    daily = make_ohlcv_fixture("AAPL.US", days=80)
    enriched = add_indicator_columns(daily)
    assert "ma_10" in enriched.columns
    assert "ma_20" in enriched.columns
    assert "atr_14" in enriched.columns
    assert "dollar_volume_20" in enriched.columns
