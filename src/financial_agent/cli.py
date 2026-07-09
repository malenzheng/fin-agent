from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from financial_agent.agent.review import review_candidates
from financial_agent.data.sample_ohlcv import make_sample_ohlcv
from financial_agent.reporting.markdown import render_daily_report
from financial_agent.scoring.weekly_breakout import score_weekly_breakout

app = typer.Typer(help="Daily weekly breakout agent")
screen_app = typer.Typer(help="Screen weekly breakout candidates")
app.add_typer(screen_app, name="screen")


@app.callback()
def main() -> None:
    """Daily after-close weekly breakout research CLI."""


@screen_app.command("smoke")
def screen_smoke(report_dir: Path = typer.Option(Path("reports"), help="Output report directory")) -> None:
    benchmark = make_sample_ohlcv("SPY.US", days=280)
    scores = [
        score_weekly_breakout("AAPL.US", make_sample_ohlcv("AAPL.US", days=280), benchmark, "Nasdaq 100 proxy"),
        score_weekly_breakout("MSFT.US", make_sample_ohlcv("MSFT.US", days=280), benchmark, "Nasdaq 100 proxy"),
        score_weekly_breakout("NVDA.US", make_sample_ohlcv("NVDA.US", days=280), benchmark, "S&P 500 proxy"),
    ]
    reviewed = review_candidates(scores)
    output_dir = report_dir / "smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = render_daily_report(date.today(), reviewed)
    report_path = output_dir / "daily_breakout_report.md"
    report_path.write_text(report, encoding="utf-8")
    typer.echo(f"Wrote {report_path}")
