from typer.testing import CliRunner

from financial_agent.cli import app


def test_cli_help_renders() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Daily weekly breakout agent" in result.output
