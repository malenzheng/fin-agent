# Daily Weekly Breakout Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily after-close weekly breakout screening agent for `SPY.US`, `QQQ.US`, and `IWM.US` proxy universes.

**Architecture:** The system is a Python CLI package with cache-first LongPort data ingestion, deterministic technical scoring, and an optional FinAgent-style review layer. The first implementation must work without live credentials by using fixtures and cached data, then degrade gracefully when LongPort or LLM access is unavailable.

**Tech Stack:** Python 3.11+, `typer`, `pydantic`, `pandas`, `pyarrow`, `pytest`, `python-dotenv`, optional `longport`, optional OpenAI-compatible LLM client.

## Global Constraints

- Secrets must not be committed. Only `.env.example` is allowed.
- The user-provided OAuth registration access token must not be persisted.
- Use `SPY.US`, `QQQ.US`, and `IWM.US` ETF components as v1 universe proxies.
- Run daily after the US market close, but compute weekly breakout evidence from cached daily bars.
- Fetch news only for shortlisted candidates.
- If LongPort quota is exceeded, stop new historical fetches and report the quota blocker.
- If LLM review fails, still output the quantitative shortlist.

---

## File Structure

- `pyproject.toml`: package metadata, dependencies, CLI entry point, pytest settings.
- `.gitignore`: ignore local secrets, caches, data, reports, and Python build outputs.
- `.env.example`: non-secret environment variable names.
- `src/financial_agent/config/settings.py`: typed settings loaded from env.
- `src/financial_agent/storage/paths.py`: repository-relative data/report path helpers.
- `src/financial_agent/storage/parquet_store.py`: read/write cached OHLCV data.
- `src/financial_agent/domain/models.py`: shared dataclass models for universe members, candidates, scores, and run summaries.
- `src/financial_agent/data/sample_ohlcv.py`: deterministic sample OHLCV data for smoke runs.
- `src/financial_agent/features/resample.py`: daily-to-weekly OHLCV resampling.
- `src/financial_agent/features/indicators.py`: moving averages, returns, ATR, dollar volume.
- `src/financial_agent/scoring/weekly_breakout.py`: balanced weekly breakout scoring.
- `src/financial_agent/universe/static.py`: fixture-backed universe provider for offline tests and smoke runs.
- `src/financial_agent/longport/client.py`: LongPort SDK adapter with local no-credential behavior.
- `src/financial_agent/agent/review.py`: deterministic fallback agent review and future LLM boundary.
- `src/financial_agent/reporting/markdown.py`: Chinese Markdown report rendering.
- `src/financial_agent/cli.py`: Typer commands.
- `tests/fixtures/ohlcv.py`: deterministic OHLCV fixture generator.
- `tests/test_*.py`: focused unit and smoke tests.

---

### Task 1: Project Scaffold And Secret Hygiene

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/financial_agent/__init__.py`
- Create: `src/financial_agent/cli.py`
- Test: `tests/test_cli_smoke.py`

**Interfaces:**
- Produces: CLI command `financial-agent --help`.
- Produces: package import `import financial_agent`.

- [ ] **Step 1: Write the failing CLI smoke test**

```python
from typer.testing import CliRunner

from financial_agent.cli import app


def test_cli_help_renders() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Daily weekly breakout agent" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_smoke.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'financial_agent'`.

- [ ] **Step 3: Add package scaffold**

Create `pyproject.toml`:

```toml
[project]
name = "financial-agent"
version = "0.1.0"
description = "Daily after-close weekly breakout screening agent"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.2",
  "pyarrow>=15",
  "pydantic>=2.7",
  "python-dotenv>=1.0",
  "typer>=0.12",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-cov>=5.0"]
longport = ["longport>=3.0"]

[project.scripts]
financial-agent = "financial_agent.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.coverage
build/
dist/
*.egg-info/
data/
reports/
*.parquet
*.sqlite
```

Create `.env.example`:

```text
LONGPORT_CLIENT_ID=
LONGPORT_ACCESS_TOKEN=
LONGPORT_REGION=cn
OPENAI_API_KEY=
FINANCIAL_AGENT_DATA_DIR=data
FINANCIAL_AGENT_REPORT_DIR=reports
```

Create `src/financial_agent/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

Create `src/financial_agent/cli.py`:

```python
import typer

app = typer.Typer(help="Daily weekly breakout agent")


@app.callback()
def main() -> None:
    """Daily after-close weekly breakout research CLI."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_smoke.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example src tests
git commit -m "chore: scaffold financial agent package"
```

---

### Task 2: Settings And Path Helpers

**Files:**
- Create: `src/financial_agent/config/__init__.py`
- Create: `src/financial_agent/config/settings.py`
- Create: `src/financial_agent/storage/__init__.py`
- Create: `src/financial_agent/storage/paths.py`
- Test: `tests/test_settings_paths.py`

**Interfaces:**
- Produces: `Settings.from_env() -> Settings`.
- Produces: `ProjectPaths.from_settings(settings: Settings) -> ProjectPaths`.

- [ ] **Step 1: Write failing settings/path tests**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_settings_paths.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement settings and paths**

```python
# src/financial_agent/config/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    data_dir: str = "data"
    report_dir: str = "reports"
    longport_client_id: str | None = None
    longport_access_token: str | None = None
    longport_region: str = "cn"
    openai_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            data_dir=os.getenv("FINANCIAL_AGENT_DATA_DIR", "data"),
            report_dir=os.getenv("FINANCIAL_AGENT_REPORT_DIR", "reports"),
            longport_client_id=os.getenv("LONGPORT_CLIENT_ID") or None,
            longport_access_token=os.getenv("LONGPORT_ACCESS_TOKEN") or None,
            longport_region=os.getenv("LONGPORT_REGION", "cn"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        )
```

```python
# src/financial_agent/storage/paths.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from financial_agent.config.settings import Settings


@dataclass(frozen=True)
class ProjectPaths:
    data_dir: Path
    report_dir: Path
    ohlcv_dir: Path
    universe_dir: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProjectPaths":
        data_dir = Path(settings.data_dir)
        report_dir = Path(settings.report_dir)
        return cls(
            data_dir=data_dir,
            report_dir=report_dir,
            ohlcv_dir=data_dir / "ohlcv",
            universe_dir=data_dir / "universe",
        )

    def ensure(self) -> None:
        for path in [self.data_dir, self.report_dir, self.ohlcv_dir, self.universe_dir]:
            path.mkdir(parents=True, exist_ok=True)
```

Create empty `__init__.py` files for `config` and `storage`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_settings_paths.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/config src/financial_agent/storage tests/test_settings_paths.py
git commit -m "feat: add settings and storage paths"
```

---

### Task 3: OHLCV Models, Fixtures, And Parquet Cache

**Files:**
- Create: `src/financial_agent/domain/__init__.py`
- Create: `src/financial_agent/domain/models.py`
- Create: `src/financial_agent/data/__init__.py`
- Create: `src/financial_agent/data/sample_ohlcv.py`
- Create: `src/financial_agent/storage/parquet_store.py`
- Create: `tests/fixtures/ohlcv.py`
- Test: `tests/test_parquet_store.py`

**Interfaces:**
- Produces: `OhlcvStore.write_daily(symbol: str, frame: pd.DataFrame) -> Path`.
- Produces: `OhlcvStore.read_daily(symbol: str) -> pd.DataFrame`.
- Produces: `make_sample_ohlcv(symbol: str, days: int = 260) -> pd.DataFrame`.

- [ ] **Step 1: Write failing cache test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_parquet_store.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement models, fixture, and store**

```python
# src/financial_agent/domain/models.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseMember:
    symbol: str
    name: str
    source: str
```

```python
# src/financial_agent/data/sample_ohlcv.py
from __future__ import annotations

import pandas as pd


def make_sample_ohlcv(symbol: str, days: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=days)
    base = 50 + (abs(hash(symbol)) % 30)
    rows = []
    for idx, date in enumerate(dates):
        close = base + idx * 0.25
        open_price = close - 0.2
        high = close + 0.8
        low = close - 1.0
        volume = 1_000_000 + idx * 5_000
        rows.append(
            {
                "date": date.date(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "turnover": close * volume,
            }
        )
    return pd.DataFrame(rows)
```

```python
# tests/fixtures/ohlcv.py
from __future__ import annotations

import pandas as pd

from financial_agent.data.sample_ohlcv import make_sample_ohlcv


def make_ohlcv_fixture(symbol: str, days: int = 260) -> pd.DataFrame:
    return make_sample_ohlcv(symbol, days)
```

```python
# src/financial_agent/storage/parquet_store.py
from __future__ import annotations

from pathlib import Path

import pandas as pd


class OhlcvStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _daily_path(self, symbol: str) -> Path:
        safe_symbol = symbol.replace("/", "_")
        return self.root / "daily" / f"{safe_symbol}.parquet"

    def write_daily(self, symbol: str, frame: pd.DataFrame) -> Path:
        path = self._daily_path(symbol)
        path.parent.mkdir(parents=True, exist_ok=True)
        clean = frame.copy()
        clean["date"] = pd.to_datetime(clean["date"]).dt.date
        clean = clean.sort_values("date").drop_duplicates("date", keep="last")
        clean.to_parquet(path, index=False)
        return path

    def read_daily(self, symbol: str) -> pd.DataFrame:
        path = self._daily_path(symbol)
        frame = pd.read_parquet(path)
        frame["date"] = pd.to_datetime(frame["date"]).dt.date
        return frame.sort_values("date").reset_index(drop=True)
```

Create empty `src/financial_agent/domain/__init__.py`, `src/financial_agent/data/__init__.py`, and `tests/fixtures/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_parquet_store.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/domain src/financial_agent/data src/financial_agent/storage/parquet_store.py tests/fixtures tests/test_parquet_store.py
git commit -m "feat: add ohlcv parquet cache"
```

---

### Task 4: Weekly Resampling And Indicators

**Files:**
- Create: `src/financial_agent/features/__init__.py`
- Create: `src/financial_agent/features/resample.py`
- Create: `src/financial_agent/features/indicators.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Produces: `resample_daily_to_weekly(frame: pd.DataFrame) -> pd.DataFrame`.
- Produces: `add_indicator_columns(frame: pd.DataFrame) -> pd.DataFrame`.

- [ ] **Step 1: Write failing feature tests**

```python
from financial_agent.features.indicators import add_indicator_columns
from financial_agent.features.resample import resample_daily_to_weekly
from financial_agent.data.sample_ohlcv import make_sample_ohlcv


def test_resample_daily_to_weekly() -> None:
    daily = make_ohlcv_fixture("AAPL.US", days=30)
    weekly = resample_daily_to_weekly(daily)
    assert {"date", "open", "high", "low", "close", "volume", "turnover"}.issubset(weekly.columns)
    assert 5 <= len(weekly) <= 7
    assert weekly["date"].is_monotonic_increasing


def test_add_indicator_columns() -> None:
    daily = make_ohlcv_fixture("AAPL.US", days=80)
    enriched = add_indicator_columns(daily)
    assert "ma_10" in enriched.columns
    assert "ma_20" in enriched.columns
    assert "atr_14" in enriched.columns
    assert "dollar_volume_20" in enriched.columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_features.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement resampling and indicators**

```python
# src/financial_agent/features/resample.py
from __future__ import annotations

import pandas as pd


def resample_daily_to_weekly(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").set_index("date")
    weekly = data.resample("W-FRI").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "turnover": "sum",
        }
    )
    weekly = weekly.dropna(subset=["open", "high", "low", "close"]).reset_index()
    weekly["date"] = weekly["date"].dt.date
    return weekly
```

```python
# src/financial_agent/features/indicators.py
from __future__ import annotations

import pandas as pd


def add_indicator_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy().sort_values("date").reset_index(drop=True)
    close = data["close"]
    high = data["high"]
    low = data["low"]
    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    data["ma_10"] = close.rolling(10).mean()
    data["ma_20"] = close.rolling(20).mean()
    data["ma_30"] = close.rolling(30).mean()
    data["atr_14"] = true_range.rolling(14).mean()
    data["dollar_volume"] = close * data["volume"]
    data["dollar_volume_20"] = data["dollar_volume"].rolling(20).mean()
    data["return_4"] = close.pct_change(4)
    data["return_8"] = close.pct_change(8)
    data["return_12"] = close.pct_change(12)
    data["high_52"] = high.rolling(252, min_periods=20).max()
    return data
```

Create empty `src/financial_agent/features/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_features.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/features tests/test_features.py
git commit -m "feat: add weekly resampling and indicators"
```

---

### Task 5: Balanced Weekly Breakout Scoring

**Files:**
- Create: `src/financial_agent/scoring/__init__.py`
- Create: `src/financial_agent/scoring/weekly_breakout.py`
- Test: `tests/test_weekly_breakout_scoring.py`

**Interfaces:**
- Produces: `score_weekly_breakout(symbol: str, daily: pd.DataFrame, benchmark_daily: pd.DataFrame, source: str) -> CandidateScore`.
- Produces: dataclass `CandidateScore` with score fields and `technical_total_score`.

- [ ] **Step 1: Write failing scoring tests**

```python
from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_score_prefers_strong_trending_symbol() -> None:
    symbol_daily = make_ohlcv_fixture("NVDA.US", days=280)
    benchmark_daily = make_ohlcv_fixture("SPY.US", days=280)
    score = score_weekly_breakout("NVDA.US", symbol_daily, benchmark_daily, "Nasdaq 100 proxy")
    assert score.symbol == "NVDA.US"
    assert score.technical_total_score >= 60
    assert score.trend_score > 0
    assert score.relative_strength_score > 0


def test_score_penalizes_low_liquidity() -> None:
    symbol_daily = make_ohlcv_fixture("THIN.US", days=280)
    symbol_daily["volume"] = 1_000
    symbol_daily["turnover"] = symbol_daily["close"] * symbol_daily["volume"]
    benchmark_daily = make_ohlcv_fixture("SPY.US", days=280)
    score = score_weekly_breakout("THIN.US", symbol_daily, benchmark_daily, "Russell 2000 proxy")
    assert score.liquidity_score == 0
    assert score.technical_total_score < 60
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_weekly_breakout_scoring.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement scoring**

```python
# src/financial_agent/scoring/weekly_breakout.py
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from financial_agent.features.indicators import add_indicator_columns
from financial_agent.features.resample import resample_daily_to_weekly


@dataclass(frozen=True)
class CandidateScore:
    symbol: str
    source: str
    trend_score: float
    relative_strength_score: float
    breakout_score: float
    volume_score: float
    extension_risk_score: float
    liquidity_score: float
    technical_total_score: float
    close: float
    breakout_level: float
    invalidation_level: float


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_weekly_breakout(
    symbol: str,
    daily: pd.DataFrame,
    benchmark_daily: pd.DataFrame,
    source: str,
) -> CandidateScore:
    weekly = add_indicator_columns(resample_daily_to_weekly(daily))
    benchmark_weekly = add_indicator_columns(resample_daily_to_weekly(benchmark_daily))
    latest = weekly.iloc[-1]
    previous = weekly.iloc[-2]
    benchmark_latest = benchmark_weekly.iloc[-1]

    close = float(latest["close"])
    ma_10 = float(latest["ma_10"]) if pd.notna(latest["ma_10"]) else close
    ma_30 = float(latest["ma_30"]) if pd.notna(latest["ma_30"]) else close
    trend_score = 0.0
    trend_score += 35 if close > ma_10 else 0
    trend_score += 35 if close > ma_30 else 0
    trend_score += 30 if ma_10 > float(previous.get("ma_10", ma_10)) else 0

    rs_symbol = float(latest.get("return_12", 0) or 0)
    rs_benchmark = float(benchmark_latest.get("return_12", 0) or 0)
    relative_strength_score = _clamp(50 + (rs_symbol - rs_benchmark) * 250)

    recent_high = float(weekly["high"].tail(52).max())
    consolidation_high = float(weekly["high"].tail(16).iloc[:-1].max())
    near_high_score = _clamp((close / recent_high) * 100)
    breakout_bonus = 20 if close >= consolidation_high else 0
    breakout_score = _clamp(near_high_score + breakout_bonus - 20)

    avg_volume_10 = float(weekly["volume"].tail(10).mean())
    volume_score = _clamp((float(latest["volume"]) / avg_volume_10) * 70) if avg_volume_10 else 0

    daily_enriched = add_indicator_columns(daily)
    daily_latest = daily_enriched.iloc[-1]
    ma_20_daily = float(daily_latest["ma_20"]) if pd.notna(daily_latest["ma_20"]) else close
    extension = (float(daily_latest["close"]) / ma_20_daily) - 1 if ma_20_daily else 0
    extension_risk_score = _clamp(100 - max(0, extension - 0.08) * 500)

    dollar_volume_20 = float(daily_latest.get("dollar_volume_20", 0) or 0)
    liquidity_score = 100 if dollar_volume_20 >= 20_000_000 else _clamp(dollar_volume_20 / 20_000_000 * 100)

    technical_total_score = (
        trend_score * 0.24
        + relative_strength_score * 0.22
        + breakout_score * 0.20
        + volume_score * 0.14
        + extension_risk_score * 0.10
        + liquidity_score * 0.10
    )

    return CandidateScore(
        symbol=symbol,
        source=source,
        trend_score=round(trend_score, 2),
        relative_strength_score=round(relative_strength_score, 2),
        breakout_score=round(breakout_score, 2),
        volume_score=round(volume_score, 2),
        extension_risk_score=round(extension_risk_score, 2),
        liquidity_score=round(liquidity_score, 2),
        technical_total_score=round(technical_total_score, 2),
        close=round(close, 2),
        breakout_level=round(consolidation_high, 2),
        invalidation_level=round(min(ma_10, close * 0.92), 2),
    )
```

Create empty `src/financial_agent/scoring/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_weekly_breakout_scoring.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/scoring tests/test_weekly_breakout_scoring.py
git commit -m "feat: score balanced weekly breakouts"
```

---

### Task 6: Offline Universe Provider And LongPort Adapter Boundary

**Files:**
- Create: `src/financial_agent/universe/__init__.py`
- Create: `src/financial_agent/universe/static.py`
- Create: `src/financial_agent/longport/__init__.py`
- Create: `src/financial_agent/longport/client.py`
- Test: `tests/test_universe_longport.py`

**Interfaces:**
- Produces: `StaticUniverseProvider.members() -> list[UniverseMember]`.
- Produces: `LongPortClient.is_configured -> bool`.

- [ ] **Step 1: Write failing tests**

```python
from financial_agent.config.settings import Settings
from financial_agent.longport.client import LongPortClient
from financial_agent.universe.static import StaticUniverseProvider


def test_static_universe_has_proxy_members() -> None:
    members = StaticUniverseProvider().members()
    symbols = {member.symbol for member in members}
    assert {"AAPL.US", "MSFT.US", "IWM.US"}.issubset(symbols)


def test_longport_client_reports_unconfigured() -> None:
    client = LongPortClient(Settings(longport_client_id=None, longport_access_token=None))
    assert client.is_configured is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_universe_longport.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement providers**

```python
# src/financial_agent/universe/static.py
from __future__ import annotations

from financial_agent.domain.models import UniverseMember


class StaticUniverseProvider:
    def members(self) -> list[UniverseMember]:
        return [
            UniverseMember("AAPL.US", "Apple", "Nasdaq 100 proxy"),
            UniverseMember("MSFT.US", "Microsoft", "Nasdaq 100 proxy"),
            UniverseMember("NVDA.US", "Nvidia", "S&P 500 proxy"),
            UniverseMember("SPY.US", "SPDR S&P 500 ETF", "S&P 500 proxy"),
            UniverseMember("QQQ.US", "Invesco QQQ ETF", "Nasdaq 100 proxy"),
            UniverseMember("IWM.US", "iShares Russell 2000 ETF", "Russell 2000 proxy"),
        ]
```

```python
# src/financial_agent/longport/client.py
from __future__ import annotations

from financial_agent.config.settings import Settings


class LongPortClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.longport_client_id and self.settings.longport_access_token)

    def require_configured(self) -> None:
        if not self.is_configured:
            raise RuntimeError("LongPort credentials are not configured. Use local .env or environment variables.")
```

Create empty `__init__.py` files for `universe` and `longport`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_universe_longport.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/universe src/financial_agent/longport tests/test_universe_longport.py
git commit -m "feat: add universe and longport boundaries"
```

---

### Task 7: Agent Review Fallback And Markdown Report

**Files:**
- Create: `src/financial_agent/agent/__init__.py`
- Create: `src/financial_agent/agent/review.py`
- Create: `src/financial_agent/reporting/__init__.py`
- Create: `src/financial_agent/reporting/markdown.py`
- Test: `tests/test_report_agent.py`

**Interfaces:**
- Produces: `review_candidates(candidates: list[CandidateScore]) -> list[ReviewedCandidate]`.
- Produces: `render_daily_report(run_date: date, candidates: list[ReviewedCandidate]) -> str`.

- [ ] **Step 1: Write failing report tests**

```python
from datetime import date

from financial_agent.agent.review import review_candidates
from financial_agent.reporting.markdown import render_daily_report
from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from tests.fixtures.ohlcv import make_ohlcv_fixture


def test_review_and_report_render_chinese_sections() -> None:
    score = score_weekly_breakout(
        "NVDA.US",
        make_ohlcv_fixture("NVDA.US", days=280),
        make_ohlcv_fixture("SPY.US", days=280),
        "Nasdaq 100 proxy",
    )
    reviewed = review_candidates([score])
    report = render_daily_report(date(2026, 7, 10), reviewed)
    assert "# 每日周线主升浪候选报告" in report
    assert "NVDA.US" in report
    assert "失效位" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_report_agent.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement fallback review and report**

```python
# src/financial_agent/agent/review.py
from __future__ import annotations

from dataclasses import dataclass

from financial_agent.scoring.weekly_breakout import CandidateScore


@dataclass(frozen=True)
class ReviewedCandidate:
    score: CandidateScore
    confidence: str
    catalyst_note: str
    risk_note: str
    reason: str


def review_candidates(candidates: list[CandidateScore]) -> list[ReviewedCandidate]:
    reviewed: list[ReviewedCandidate] = []
    for candidate in sorted(candidates, key=lambda item: item.technical_total_score, reverse=True):
        confidence = "高" if candidate.technical_total_score >= 75 else "中" if candidate.technical_total_score >= 60 else "低"
        risk_note = "技术面过热风险可控" if candidate.extension_risk_score >= 70 else "价格相对短期均线偏离较大，避免追高"
        reason = (
            f"{candidate.symbol} 周线趋势、相对强度和突破结构综合得分为 "
            f"{candidate.technical_total_score}，关键突破位 {candidate.breakout_level}。"
        )
        reviewed.append(
            ReviewedCandidate(
                score=candidate,
                confidence=confidence,
                catalyst_note="未接入实时资讯复核，当前为量价候选。",
                risk_note=risk_note,
                reason=reason,
            )
        )
    return reviewed
```

```python
# src/financial_agent/reporting/markdown.py
from __future__ import annotations

from datetime import date

from financial_agent.agent.review import ReviewedCandidate


def render_daily_report(run_date: date, candidates: list[ReviewedCandidate]) -> str:
    lines = [
        "# 每日周线主升浪候选报告",
        "",
        f"日期：{run_date.isoformat()}",
        "",
        "## Top 候选",
        "",
    ]
    if not candidates:
        lines.append("今日没有达到均衡型主升浪阈值的候选。")
        return "\n".join(lines) + "\n"

    lines.append("| 排名 | 标的 | 股票池 | 技术总分 | 置信度 | 突破位 | 失效位 | 风险 |")
    lines.append("| --- | --- | --- | ---: | --- | ---: | ---: | --- |")
    for rank, item in enumerate(candidates, start=1):
        score = item.score
        lines.append(
            f"| {rank} | {score.symbol} | {score.source} | {score.technical_total_score:.2f} | "
            f"{item.confidence} | {score.breakout_level:.2f} | {score.invalidation_level:.2f} | {item.risk_note} |"
        )
    lines.extend(["", "## 逐股理由", ""])
    for item in candidates:
        lines.extend(
            [
                f"### {item.score.symbol}",
                "",
                item.reason,
                "",
                f"- 催化：{item.catalyst_note}",
                f"- 风险：{item.risk_note}",
                f"- 失效位：{item.score.invalidation_level:.2f}",
                "",
            ]
        )
    return "\n".join(lines)
```

Create empty `__init__.py` files for `agent` and `reporting`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_report_agent.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/financial_agent/agent src/financial_agent/reporting tests/test_report_agent.py
git commit -m "feat: add fallback agent review and reports"
```

---

### Task 8: End-To-End Smoke Command

**Files:**
- Modify: `src/financial_agent/cli.py`
- Test: `tests/test_screen_smoke.py`

**Interfaces:**
- Produces: `financial-agent screen smoke --report-dir <path>`.

- [ ] **Step 1: Write failing smoke command test**

```python
from typer.testing import CliRunner

from financial_agent.cli import app


def test_screen_smoke_writes_report(tmp_path) -> None:
    result = CliRunner().invoke(app, ["screen", "smoke", "--report-dir", str(tmp_path)])
    assert result.exit_code == 0
    report = tmp_path / "smoke" / "daily_breakout_report.md"
    assert report.exists()
    assert "每日周线主升浪候选报告" in report.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_screen_smoke.py -v`

Expected: FAIL because `screen` command does not exist.

- [ ] **Step 3: Implement smoke command**

```python
# src/financial_agent/cli.py
from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from financial_agent.agent.review import review_candidates
from financial_agent.reporting.markdown import render_daily_report
from financial_agent.scoring.weekly_breakout import score_weekly_breakout
from tests.fixtures.ohlcv import make_ohlcv_fixture

app = typer.Typer(help="Daily weekly breakout agent")
screen_app = typer.Typer(help="Screen weekly breakout candidates")
app.add_typer(screen_app, name="screen")


@app.callback()
def main() -> None:
    """Daily after-close weekly breakout research CLI."""


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
    (output_dir / "daily_breakout_report.md").write_text(report, encoding="utf-8")
    typer.echo(f"Wrote {output_dir / 'daily_breakout_report.md'}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_screen_smoke.py -v`

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/financial_agent/cli.py tests/test_screen_smoke.py
git commit -m "feat: add end-to-end smoke screening command"
```

---

## Self-Review

- Spec coverage: scaffold, secret hygiene, cache boundary, weekly features, balanced scoring, universe proxy, LongPort boundary, fallback agent review, and daily report output are covered.
- Deferred by design: live LongPort OAuth flow, live ETF component refresh, live news, and LLM review are intentionally left behind tested interfaces so the first runnable version can work without credentials.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `CandidateScore`, `ReviewedCandidate`, `Settings`, `ProjectPaths`, and `OhlcvStore` signatures are used consistently across tasks.
