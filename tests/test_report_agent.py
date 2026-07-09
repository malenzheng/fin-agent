from datetime import date

from financial_agent.agent.review import review_candidates
from financial_agent.reporting.markdown import render_daily_report
from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_review_and_report_render_chinese_sections() -> None:
    score = score_weekly_breakout(
        "NVDA.US",
        make_ohlcv_fixture("NVDA.US", days=280),
        make_ohlcv_fixture("SPY.US", days=280),
        "Nasdaq 100 proxy",
    )
    reviewed = review_candidates([score])
    report = render_daily_report(date(2026, 7, 10), reviewed)
    assert "# 每日周线主升浪候选报告" in report
    assert "NVDA.US" in report
    assert "失效位" in report
