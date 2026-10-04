from typer.testing import CliRunner

from financial_agent.cli import app


def test_auth_status_reads_external_env_without_leaking_values(tmp_path):
    path = tmp_path / "reference.env"
    path.write_text("LONGBRIDGE_CLIENT_ID=secret-client-id\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["auth", "status", "--env-file", str(path)])
    assert result.exit_code == 0, result.output
    assert "oauth" in result.output
    assert "secret-client-id" not in result.output


def test_auth_status_rejects_missing_explicit_env(tmp_path):
    result = CliRunner().invoke(app, ["auth", "status", "--env-file", str(tmp_path / "missing.env")])
    assert result.exit_code == 2
    assert "No such command" not in result.output


def test_market_daily_rejects_bad_dates_before_api_use(tmp_path):
    result = CliRunner().invoke(app, ["market", "daily", "--symbol", "AAPL.US", "--start", "bad-date", "--end", "2026-09-30", "--data-dir", str(tmp_path)])
    assert result.exit_code == 2
    assert "日期" in result.output
