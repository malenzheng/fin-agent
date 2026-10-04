import json

from typer.testing import CliRunner

from financial_agent.cli import app


def test_research_demo_writes_auditable_chinese_report(tmp_path):
    result = CliRunner().invoke(app, ["research", "demo", "--report-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    report = (tmp_path / "research" / "brief.md").read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "research" / "brief.json").read_text(encoding="utf-8"))
    assert "合成" in report and "原文摘录" in report
    assert "chip-order" in report and "chip-future" not in report
    assert "available_at" in payload["evidence"][0]
    assert payload["trace"][0]["tool"] == "market.search"


def test_unknown_symbol_produces_insufficient_evidence_report(tmp_path):
    result = CliRunner().invoke(app, ["research", "demo", "--symbol", "UNKNOWN", "--report-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "信息不足" in (tmp_path / "research" / "brief.md").read_text(encoding="utf-8")


def test_invalid_task_is_a_readable_cli_error(tmp_path):
    result = CliRunner().invoke(app, ["research", "demo", "--as-of", "2026-10-02T12:00:00", "--report-dir", str(tmp_path)])
    assert result.exit_code == 2
    assert "输入或数据错误" in result.output
    assert not (tmp_path / "research").exists()


def test_benchmark_cli_writes_results(tmp_path):
    result = CliRunner().invoke(app, ["evaluate", "research", "--report-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads((tmp_path / "evaluation" / "results.json").read_text(encoding="utf-8"))
    assert payload["total"] == 6 and payload["passed"] == 6
    assert "规则基线" in (tmp_path / "evaluation" / "results.md").read_text(encoding="utf-8")


def test_benchmark_cli_rejects_empty_cases(tmp_path):
    cases = tmp_path / "empty.json"
    cases.write_text("[]", encoding="utf-8")
    result = CliRunner().invoke(app, ["evaluate", "research", "--cases", str(cases), "--report-dir", str(tmp_path)])
    assert result.exit_code == 2
    assert "empty" in result.output


def test_benchmark_cli_rejects_invalid_json(tmp_path):
    cases = tmp_path / "bad.json"
    cases.write_text("invalid-json", encoding="utf-8")
    result = CliRunner().invoke(app, ["evaluate", "research", "--cases", str(cases)])
    assert result.exit_code == 2
    assert "输入或数据错误" in result.output
    assert "json_invalid" in result.output


def test_evaluate_saved_brief_returns_failure_and_writes_diagnostics(tmp_path):
    runner = CliRunner()
    demo = runner.invoke(app, ["research", "demo", "--report-dir", str(tmp_path)])
    assert demo.exit_code == 0
    path = tmp_path / "research" / "brief.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["findings"][0]["text"] = "没有证据支持的利润增长预测。"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = runner.invoke(app, [
        "evaluate", "research", "--brief", str(path), "--case-id", "chip-full-context",
        "--report-dir", str(tmp_path),
    ])
    assert result.exit_code == 1, result.output
    output = json.loads((tmp_path / "evaluation" / "results.json").read_text(encoding="utf-8"))
    assert output["total"] == 1 and output["passed"] == 0
    assert output["results"][0]["metrics"]["quote_support"] < 1
    assert output["results"][0]["failures"]


def test_saved_brief_requires_matching_case_option(tmp_path):
    result = CliRunner().invoke(app, ["evaluate", "research", "--case-id", "chip-full-context"])
    assert result.exit_code == 2
    assert "同时提供" in result.output
