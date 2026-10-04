from __future__ import annotations

import importlib
import asyncio
import math
import re
from collections.abc import Callable
from datetime import date
from zoneinfo import ZoneInfo

import pandas as pd

from financial_agent.config.settings import Settings


class LongPortError(RuntimeError):
    """Configuration or read-only Longbridge API failure."""


def validate_request(symbol: str, start: date | None = None, end: date | None = None) -> None:
    if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:[.-][A-Z0-9]+)*\.US", symbol):
        raise ValueError("Use a US symbol such as AAPL.US or BRK.B.US")
    if start is not None and end is not None:
        if start > end or (end - start).days > 365:
            raise ValueError("Date range must be ordered and at most 366 calendar days")


class LongPortClient:
    def __init__(self, settings: Settings, on_open_url: Callable[[str], None] | None = None) -> None:
        self.settings = settings
        self.on_open_url = on_open_url
        self._context = None
        self._openapi = None

    @property
    def is_configured(self) -> bool:
        if self.settings.effective_auth_mode == "api_key":
            return all((self.settings.longport_app_key, self.settings.longport_app_secret, self.settings.longport_access_token))
        return bool(self.settings.longport_client_id)

    def require_configured(self) -> None:
        if not self.is_configured:
            raise LongPortError("Longbridge credentials are not configured; use --env-file or LONGBRIDGE_* variables.")

    def _safe_error(self, exc: Exception) -> str:
        message = str(exc)
        values = [self.settings.longport_access_token, self.settings.longport_app_secret,
                  self.settings.longport_app_key, self.settings.longport_client_id]
        for value in sorted((value for value in values if value), key=len, reverse=True):
            message = message.replace(value, "[redacted]")
        return f"Longbridge request failed ({type(exc).__name__}): {message}"

    @staticmethod
    async def _cached_oauth(builder):
        loop = asyncio.get_running_loop()
        login_required = loop.create_future()

        def notify_login_required(url: str) -> None:
            def signal() -> None:
                if not login_required.done():
                    login_required.set_result(True)
            loop.call_soon_threadsafe(signal)

        # The SDK's blocking builder ignores callback exceptions and keeps waiting.
        pending_oauth = asyncio.ensure_future(builder.build_async(notify_login_required))
        try:
            done, _ = await asyncio.wait({pending_oauth, login_required}, timeout=30, return_when=asyncio.FIRST_COMPLETED)
            if login_required in done:
                raise LongPortError("OAuth authorization required; run financial-agent auth oauth-login with the same --env-file.")
            if pending_oauth not in done:
                raise LongPortError("OAuth initialization timed out after 30 seconds")
            return pending_oauth.result()
        finally:
            pending_oauth.cancel()
            login_required.cancel()
            await asyncio.gather(pending_oauth, return_exceptions=True)

    def _quote_context(self):
        if self._context is not None:
            return self._context
        self.require_configured()
        try:
            self._openapi = importlib.import_module("longbridge.openapi")
        except ImportError:
            raise LongPortError('Install the SDK with python -m pip install -e ".[longport]"') from None
        sdk = self._openapi
        settings = self.settings
        try:
            if settings.effective_auth_mode == "api_key":
                config = sdk.Config.from_apikey(settings.longport_app_key, settings.longport_app_secret, settings.longport_access_token)
            else:
                args = [settings.longport_client_id]
                if settings.longport_oauth_callback_port is not None:
                    args.append(settings.longport_oauth_callback_port)
                builder = sdk.OAuthBuilder(*args)
                oauth = builder.build(self.on_open_url) if self.on_open_url else asyncio.run(self._cached_oauth(builder))
                config = sdk.Config.from_oauth(oauth)
            self._context = sdk.QuoteContext(config)
        except Exception as exc:
            raise LongPortError(self._safe_error(exc)) from None
        return self._context

    def verify(self, symbol: str = "AAPL.US") -> dict[str, str | int]:
        validate_request(symbol)
        context = self._quote_context()
        try:
            records = context.static_info([symbol])
            if not records:
                raise LongPortError("static_info returned an empty response")
        except Exception as exc:
            raise LongPortError(self._safe_error(exc)) from None
        return {"symbol": symbol, "records": len(records)}

    def daily_candles(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        validate_request(symbol, start, end)
        context = self._quote_context()
        columns = ["date", "open", "high", "low", "close", "volume", "turnover"]
        try:
            records = context.history_candlesticks_by_date(
                symbol, self._openapi.Period.Day, self._openapi.AdjustType.NoAdjust, start=start, end=end,
            )
            rows = []
            for item in records:
                timestamp = item.timestamp
                if timestamp.tzinfo is None:
                    raise ValueError("OHLCV timestamp must include timezone")
                row = {"date": timestamp.astimezone(ZoneInfo("America/New_York")).date()}
                row.update({key: float(getattr(item, key)) for key in columns[1:]})
                if not all(math.isfinite(row[key]) for key in columns[1:]) or not (
                    0 < row["low"] <= min(row["open"], row["close"])
                    <= max(row["open"], row["close"]) <= row["high"]
                    and row["volume"] >= 0 and row["turnover"] >= 0
                ):
                    raise ValueError("Invalid OHLCV values")
                if start <= row["date"] <= end:
                    rows.append(row)
            return pd.DataFrame(rows, columns=columns).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
        except Exception as exc:
            raise LongPortError(self._safe_error(exc)) from None
