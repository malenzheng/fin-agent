from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from financial_agent.longport.client import LongPortClient, validate_request
from financial_agent.storage.parquet_store import OhlcvStore


@dataclass(frozen=True)
class DailySyncResult:
    path: Path
    rows: int
    origin: str


def sync_daily(client: LongPortClient, root: Path, symbol: str, start: date, end: date, *, refresh: bool = False) -> DailySyncResult:
    validate_request(symbol, start, end)
    store = OhlcvStore(Path(root) / "longbridge" / "no-adjust" / f"{start}_{end}")
    path = store.root / "daily" / f"{symbol}.parquet"
    metadata_path = path.with_suffix(".json")
    identity = {
        "source": "longbridge", "endpoint": "history_candlesticks_by_date", "symbol": symbol,
        "start": start.isoformat(), "end": end.isoformat(), "adjustment": "NoAdjust",
    }
    if path.exists() and metadata_path.exists() and not refresh:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict) or any(metadata.get(key) != value for key, value in identity.items()):
            raise ValueError("Cache request identity does not match; inspect data or use --refresh")
        if metadata.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("Cache integrity check failed; inspect data or use --refresh")
        frame = store.read_daily(symbol)
        if metadata.get("records") != len(frame) or not frame["date"].between(start, end).all():
            raise ValueError("Cache dates or record count do not match the request")
        return DailySyncResult(path, len(frame), "cache")
    frame = client.daily_candles(symbol, start, end)
    path = store.write_daily(symbol, frame)
    metadata = {
        **identity,
        "fetched_at": datetime.now(timezone.utc).isoformat(), "records": len(frame),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return DailySyncResult(path, len(frame), "api")
