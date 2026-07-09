from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_score_prefers_strong_trending_symbol() -> None:
    symbol_daily = make_ohlcv_fixture("NVDA.US", days=280)
    benchmark_daily = make_ohlcv_fixture("SPY.US", days=280)
    score = score_weekly_breakout("NVDA.US", symbol_daily, benchmark_daily, "Nasdaq 100 proxy")
    assert score.symbol == "NVDA.US"
    assert score.technical_total_score >= 60
    assert score.trend_score > 0
    assert score.relative_strength_score > 0


def test_score_penalizes_low_liquidity() -> None:
    symbol_daily = make_ohlcv_fixture("THIN.US", days=280)
    symbol_daily["volume"] = 1_000
    symbol_daily["turnover"] = symbol_daily["close"] * symbol_daily["volume"]
    benchmark_daily = make_ohlcv_fixture("SPY.US", days=280)
    score = score_weekly_breakout("THIN.US", symbol_daily, benchmark_daily, "Russell 2000 proxy")
    assert score.liquidity_score == 0
    assert score.technical_total_score < 60
