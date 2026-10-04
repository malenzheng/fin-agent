from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import typer

from financial_agent.agent.review import review_candidates
from financial_agent.agent.research import ResearchBrief, build_research_brief
from financial_agent.data.sample_ohlcv import make_sample_ohlcv
from financial_agent.evaluation.research import BenchmarkResult, evaluate_brief, load_cases, run_benchmark
from financial_agent.longport.commands import auth_app, market_app
from financial_agent.reporting.markdown import render_daily_report
from financial_agent.reporting.research import render_benchmark_report, render_research_brief
from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from financial_agent.sources.market import FixtureMarketSource, ResearchTask

app = typer.Typer(help="Daily weekly breakout agent")
screen_app = typer.Typer(help="Screen weekly breakout candidates")
app.add_typer(screen_app, name="screen")
research_app = typer.Typer(help="市场信息与投研辅助")
evaluation_app = typer.Typer(help="可复现的研究工作流评测")
app.add_typer(research_app, name="research")
app.add_typer(evaluation_app, name="evaluate")
app.add_typer(auth_app, name="auth")
app.add_typer(market_app, name="market")


@app.callback()
def main() -> None:
    """Financial market information, research and evaluation CLI."""


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


@research_app.command("demo")
def research_demo(
    symbol: str = typer.Option("DEMO.CHIP", help="合成标的：DEMO.CHIP 或 DEMO.AUTO"),
    as_of: str = typer.Option("2026-10-02T12:00:00+08:00", help="带时区的 ISO 8601 研究时点"),
    max_age_days: int = typer.Option(7, min=1, max=3650, help="资料新鲜度天数"),
    report_dir: Path = typer.Option(Path("reports"), help="输出目录"),
) -> None:
    try:
        task = ResearchTask(symbol=symbol, as_of=as_of, max_age_days=max_age_days)
        brief = build_research_brief(task, FixtureMarketSource.from_fixture())
        output = report_dir / "research"
        output.mkdir(parents=True, exist_ok=True)
        (output / "brief.json").write_text(brief.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (output / "brief.md").write_text(render_research_brief(brief), encoding="utf-8")
    except (ValueError, OSError) as exc:
        typer.echo(f"输入或数据错误：{exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"已生成合成资料简报：{output / 'brief.md'}")


@evaluation_app.command("research")
def evaluate_research(
    cases: Path = typer.Option(Path("benchmarks/research_cases.json"), help="Benchmark JSON 路径，在仓库根目录运行"),
    report_dir: Path = typer.Option(Path("reports"), help="输出目录"),
    brief: Optional[Path] = typer.Option(None, help="评测已有简报 JSON"),
    case_id: Optional[str] = typer.Option(None, help="与已有简报对应的 Benchmark case ID"),
) -> None:
    try:
        if (brief is None) != (case_id is None):
            raise ValueError("--brief 与 --case-id 必须同时提供")
        benchmark_cases = load_cases(cases)
        source = FixtureMarketSource.from_fixture()
        if brief is None:
            result = run_benchmark(benchmark_cases, source)
        else:
            matched = [case for case in benchmark_cases if case.id == case_id]
            if len(matched) != 1:
                raise ValueError("case-id 必须对应唯一的 Benchmark case")
            saved = ResearchBrief.model_validate_json(brief.read_text(encoding="utf-8"))
            evaluated = evaluate_brief(saved, matched[0], source)
            result = BenchmarkResult(
                total=1, passed=int(evaluated.passed), pass_rate=float(evaluated.passed), results=[evaluated],
            )
        output = report_dir / "evaluation"
        output.mkdir(parents=True, exist_ok=True)
        (output / "results.json").write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (output / "results.md").write_text(render_benchmark_report(result), encoding="utf-8")
    except (ValueError, OSError) as exc:
        typer.echo(f"输入或数据错误：{exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"规则基线评测：{result.passed}/{result.total} 通过；{output / 'results.md'}")
    if result.passed != result.total:
        raise typer.Exit(1)
