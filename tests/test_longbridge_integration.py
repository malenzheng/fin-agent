import json
import asyncio
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest

from financial_agent.config.settings import Settings
from financial_agent.longport.client import LongPortClient, LongPortError
from financial_agent.longport.daily import sync_daily


@pytest.fixture
def sdk(monkeypatch):
    calls = []
    candle = SimpleNamespace(
        timestamp=datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc),
        open=Decimal("100"), high=Decimal("103"), low=Decimal("99"), close=Decimal("102"),
        volume=1000, turnover=Decimal("102000"),
    )

    class Config:
        @staticmethod
        def from_apikey(*args):
            calls.append(("api_key", args))
            return "config"

        @staticmethod
        def from_oauth(oauth):
            calls.append(("oauth", oauth))
            return "config"

    class OAuthBuilder:
        def __init__(self, *args):
            calls.append(("builder", args))

        def build(self, callback):
            calls.append(("build",))
            return "cached-oauth"

        async def build_async(self, callback):
            calls.append(("build_async",))
            return "cached-oauth"

    class QuoteContext:
        def __init__(self, config):
            calls.append(("context", config))

        def static_info(self, symbols):
            calls.append(("static_info", symbols))
            return [SimpleNamespace(symbol=symbols[0])]

        def history_candlesticks_by_date(self, symbol, period, adjust, *, start, end):
            calls.append(("daily", symbol, period, adjust, start, end))
            return [candle]

    module = SimpleNamespace(
        Config=Config, OAuthBuilder=OAuthBuilder, QuoteContext=QuoteContext,
        Period=SimpleNamespace(Day="day"), AdjustType=SimpleNamespace(NoAdjust="none"),
    )
    monkeypatch.setitem(sys.modules, "longbridge.openapi", module)
    return module, calls, candle


def test_settings_read_reference_env_without_copying_or_exporting_secrets(tmp_path, monkeypatch):
    for key in list(os.environ):
        if key.startswith(("LONGBRIDGE_", "LONGPORT_")):
            monkeypatch.delenv(key)
    path = tmp_path / "reference.env"
    path.write_text("LONGBRIDGE_AUTH_MODE=oauth\nLONGBRIDGE_CLIENT_ID=demo-client\nLONGBRIDGE_OAUTH_CALLBACK_PORT=60356\n", encoding="utf-8")
    settings = Settings.from_env(path)
    assert settings.longport_client_id == "demo-client"
    assert settings.longport_oauth_callback_port == 60356
    assert "demo-client" not in repr(settings)
    assert "LONGBRIDGE_CLIENT_ID" not in os.environ
    monkeypatch.setenv("LONGBRIDGE_CLIENT_ID", "override")
    assert Settings.from_env(path).longport_client_id == "override"


def test_settings_expand_dotenv_references_with_environment_precedence(tmp_path, monkeypatch):
    for key in list(os.environ):
        if key.startswith(("LONGBRIDGE_", "LONGPORT_")):
            monkeypatch.delenv(key)
    monkeypatch.setenv("TEST_BASE_CLIENT", "environment-client")
    path = tmp_path / "reference.env"
    path.write_text("TEST_BASE_CLIENT=file-client\nTEST_BASE_PORT=60356\nLONGBRIDGE_CLIENT_ID=${TEST_BASE_CLIENT}\nLONGBRIDGE_OAUTH_CALLBACK_PORT=${TEST_BASE_PORT}\n", encoding="utf-8")
    settings = Settings.from_env(path)
    assert settings.longport_client_id == "environment-client"
    assert settings.longport_oauth_callback_port == 60356
    assert "LONGBRIDGE_CLIENT_ID" not in os.environ


def test_api_key_auth_requires_all_three_credentials(sdk):
    settings = Settings(longport_auth_mode="api_key", longport_app_key="key", longport_app_secret="secret", longport_access_token="token")
    client = LongPortClient(settings)
    assert client.is_configured
    assert client.verify("AAPL.US") == {"symbol": "AAPL.US", "records": 1}
    assert ("api_key", ("key", "secret", "token")) in sdk[1]
    assert not LongPortClient(Settings(longport_client_id="id", longport_access_token="token", longport_auth_mode="api_key")).is_configured


def test_oauth_reuses_sdk_flow_and_context(sdk):
    client = LongPortClient(Settings(longport_client_id="id", longport_oauth_callback_port=60356))
    assert client.is_configured
    client.verify("AAPL.US")
    frame = client.daily_candles("AAPL.US", date(2026, 9, 28), date(2026, 9, 30))
    assert len([call for call in sdk[1] if call[0] == "context"]) == 1
    assert ("builder", ("id", 60356)) in sdk[1]
    assert ("daily", "AAPL.US", "day", "none", date(2026, 9, 28), date(2026, 9, 30)) in sdk[1]
    assert frame.iloc[0]["date"] == date(2026, 9, 28)
    assert frame.iloc[0]["close"] == 102


def test_uncached_oauth_fails_fast_without_login_permission(sdk):
    class NeedsLogin:
        def __init__(self, *args):
            pass

        def build(self, callback):
            raise AssertionError("Blocking OAuth build must not be used for non-interactive verification")

        async def build_async(self, callback):
            callback("https://example.test/authorize")
            await asyncio.Event().wait()
    sdk[0].OAuthBuilder = NeedsLogin
    with pytest.raises(LongPortError, match="oauth-login"):
        LongPortClient(Settings(longport_client_id="id")).verify()


def test_empty_static_info_is_not_reported_as_verified(sdk):
    sdk[0].QuoteContext.static_info = lambda self, symbols: []
    with pytest.raises(LongPortError, match="empty"):
        LongPortClient(Settings(longport_client_id="id")).verify()


def test_sdk_errors_do_not_expose_credentials(sdk):
    def fail(*args):
        raise RuntimeError("request failed: access-token-secret")
    sdk[0].Config.from_apikey = fail
    settings = Settings(longport_auth_mode="api_key", longport_app_key="key", longport_app_secret="secret", longport_access_token="access-token-secret")
    with pytest.raises(LongPortError) as error:
        LongPortClient(settings).verify()
    assert "access-token-secret" not in str(error.value)


@pytest.mark.parametrize("symbol,start,end", [
    ("../AAPL.US", date(2026, 9, 1), date(2026, 9, 2)),
    ("AAPL.US", date(2026, 9, 2), date(2026, 9, 1)),
    ("AAPL.US", date(2025, 1, 1), date(2026, 9, 1)),
])
def test_invalid_request_never_calls_sdk(sdk, symbol, start, end):
    with pytest.raises(ValueError):
        LongPortClient(Settings(longport_client_id="id")).daily_candles(symbol, start, end)
    assert not sdk[1]


def test_invalid_ohlcv_is_rejected(sdk):
    sdk[2].close = Decimal("NaN")
    with pytest.raises(LongPortError, match="OHLCV"):
        LongPortClient(Settings(longport_client_id="id")).daily_candles("AAPL.US", date(2026, 9, 28), date(2026, 9, 30))


def test_daily_sync_reuses_exact_range_cache_without_auth(tmp_path, sdk):
    client = LongPortClient(Settings(longport_client_id="id"))
    start, end = date(2026, 9, 28), date(2026, 9, 30)
    first = sync_daily(client, tmp_path, "AAPL.US", start, end)
    assert first.origin == "api" and first.rows == 1
    meta = json.loads(first.path.with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["source"] == "longbridge" and meta["adjustment"] == "NoAdjust"
    second = sync_daily(LongPortClient(Settings()), tmp_path, "AAPL.US", start, end)
    assert second.origin == "cache" and second.rows == 1
    sync_daily(client, tmp_path, "AAPL.US", start, end, refresh=True)
    assert len([call for call in sdk[1] if call[0] == "daily"]) == 2
    assert pd.read_parquet(first.path).iloc[0]["close"] == 102


@pytest.mark.parametrize("field,value", [
    ("symbol", "MSFT.US"), ("start", "2026-09-01"), ("end", "2026-09-02"),
    ("source", "fixture"), ("adjustment", "ForwardAdjust"),
])
def test_daily_cache_rejects_wrong_request_identity(tmp_path, sdk, field, value):
    client = LongPortClient(Settings(longport_client_id="id"))
    start, end = date(2026, 9, 28), date(2026, 9, 30)
    first = sync_daily(client, tmp_path, "AAPL.US", start, end)
    path = first.path.with_suffix(".json")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata[field] = value
    path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="Cache"):
        sync_daily(client, tmp_path, "AAPL.US", start, end)


def test_daily_cache_rejects_dates_outside_requested_range(tmp_path, sdk):
    import hashlib
    client = LongPortClient(Settings(longport_client_id="id"))
    start, end = date(2026, 9, 28), date(2026, 9, 30)
    first = sync_daily(client, tmp_path, "AAPL.US", start, end)
    frame = pd.read_parquet(first.path)
    frame["date"] = date(2026, 8, 1)
    frame.to_parquet(first.path, index=False)
    path = first.path.with_suffix(".json")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["sha256"] = hashlib.sha256(first.path.read_bytes()).hexdigest()
    path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="Cache"):
        sync_daily(client, tmp_path, "AAPL.US", start, end)
