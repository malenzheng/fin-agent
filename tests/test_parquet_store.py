from financial_agent.storage.parquet_store import OhlcvStore
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_write_and_read_daily_ohlcv(tmp_path) -> None:
    store = OhlcvStore(tmp_path)
    frame = make_ohlcv_fixture("AAPL.US", days=30)
    path = store.write_daily("AAPL.US", frame)
    loaded = store.read_daily("AAPL.US")
    assert path.exists()
    assert list(loaded.columns) == ["date", "open", "high", "low", "close", "volume", "turnover"]
    assert loaded["date"].is_monotonic_increasing
    assert len(loaded) == 30
