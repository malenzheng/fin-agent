from typer.testing import CliRunner

from financial_agent.cli import app


def test_screen_smoke_writes_report(tmp_path) -> None:
    result = CliRunner().invoke(app, ["screen", "smoke", "--report-dir", str(tmp_path)])
    assert result.exit_code == 0
    report = tmp_path / "smoke" / "daily_breakout_report.md"
    assert report.exists()
    assert "每日周线主升浪候选报告" in report.read_text(encoding="utf-8")
