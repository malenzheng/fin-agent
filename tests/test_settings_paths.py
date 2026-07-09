from financial_agent.config.settings import Settings
from financial_agent.storage.paths import ProjectPaths


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("FINANCIAL_AGENT_DATA_DIR", raising=False)
    monkeypatch.delenv("FINANCIAL_AGENT_REPORT_DIR", raising=False)
    settings = Settings.from_env()
    assert settings.data_dir == "data"
    assert settings.report_dir == "reports"
    assert settings.longport_region == "cn"


def test_paths_from_settings(tmp_path) -> None:
    settings = Settings(data_dir=str(tmp_path / "data"), report_dir=str(tmp_path / "reports"))
    paths = ProjectPaths.from_settings(settings)
    assert paths.data_dir.name == "data"
    assert paths.report_dir.name == "reports"
    assert paths.ohlcv_dir.name == "ohlcv"
