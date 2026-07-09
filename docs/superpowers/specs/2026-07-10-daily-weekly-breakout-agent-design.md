# Daily Weekly Breakout Agent Design

## Goal

Build a daily after-close stock selection agent that finds likely weekly main uptrend candidates from the S&P 500, Nasdaq 100, and Russell 2000 universes.

The first version uses ETF component lists as practical proxies:

- `SPY.US` for S&P 500
- `QQQ.US` for Nasdaq 100
- `IWM.US` for Russell 2000

The system is a research and ranking tool, not an auto-trading system. It should produce a daily report with ranked candidates, evidence, key levels, and follow-up tracking.

## Data Sources

The primary market data source is LongPort OpenAPI through the Python SDK.

LongPort capabilities needed for v1:

- OAuth 2.0 authentication through the SDK.
- Index or ETF component lookup through `MarketContext.index_components`.
- Historical daily candlesticks through `QuoteContext.history_candlesticks_by_date` or `history_candlesticks_by_offset`.
- Per-symbol news through `ContentContext.news`, used only for shortlisted candidates.
- Optional screener support through `ScreenerContext.screener_search` if useful after the local scoring pipeline is working.

Secrets must not be committed. The repository should include `.env.example` only. Real credentials belong in a local `.env` or system environment variables. The user-provided OAuth registration access token must not be persisted.

## Operating Rhythm

The pipeline runs once per US trading day after the market close.

Each run should:

1. Refresh the universe membership for `SPY.US`, `QQQ.US`, and `IWM.US`.
2. Incrementally update daily OHLCV data for symbols that are missing the latest completed trading day.
3. Rebuild weekly bars from cached daily bars.
4. Compute daily and weekly features.
5. Run balanced breakout rules to produce an initial shortlist.
6. Fetch news and richer context only for the shortlist.
7. Run an agent review pass over the shortlist.
8. Write the daily report and store run artifacts.
9. Update candidate tracking and reflection memory from prior picks.

## Cache And Rate Limits

The system must be cache-first because LongPort historical candlestick access has per-month symbol quotas and request rate limits.

Implementation rules:

- Store OHLCV data locally by symbol and interval.
- Never redownload full history for a symbol when an incremental update can fill missing days.
- Derive weekly candles locally from daily candles.
- Track the last successful update date per symbol.
- Track API failures, quota failures, and no-data symbols separately.
- Limit history requests with a conservative scheduler even if the SDK handles part of the throttling.
- Fetch news only for the top candidates after quantitative filtering.

## Balanced Weekly Breakout Definition

The v1 selection style is balanced: early enough to catch a weekly main uptrend, but strict enough to avoid many weak breakouts.

Core features:

- Trend quality: close above the 10-week and 30-week moving averages, with the 10-week average rising.
- Relative strength: 4-week, 8-week, and 12-week performance versus `SPY.US` and the symbol's source universe.
- Position: close near a 52-week high, or breaking out from an 8-16 week consolidation range.
- Volume confirmation: breakout-week volume above the 10-week average volume.
- Daily confirmation: price not excessively extended from the 10-day or 20-day moving average.
- Liquidity filter: average dollar volume must be high enough for practical trading.
- Risk filter: penalize extreme one-day spikes, very high ATR expansion, obvious low-liquidity moves, and earnings-event gap risk.

The first rule engine should produce numeric component scores rather than a single opaque pass/fail result.

## Quantitative Scoring

Each symbol receives a rule-based score before any LLM review:

- `trend_score`: weekly moving-average alignment and slope.
- `relative_strength_score`: multi-window outperformance.
- `breakout_score`: proximity to highs and breakout structure.
- `volume_score`: volume expansion and accumulation quality.
- `extension_risk_score`: how overextended the current price is.
- `liquidity_score`: trading practicality.
- `technical_total_score`: weighted aggregate used to pick the shortlist.

The initial shortlist target is 50-100 symbols per day. If the market is weak, the shortlist can be smaller rather than forcing low-quality names into the report.

## Agent Review

The agent layer borrows FinAgent's structure but adapts it from daily buy/sell/hold decisions to weekly candidate review.

Agent modules:

- Market intelligence: summarize recent news, earnings, analyst changes, sector context, and unusual market attention for shortlisted names.
- Diverse retrieval: retrieve similar historical setups from local candidate memory, including successful breakouts, failed breakouts, late-stage moves, and post-gap traps.
- Low-level reflection: compare current price/volume structure with later outcomes from prior runs.
- High-level reflection: review which previous recommendations worked, which failed, and what rule or news pattern caused the error.
- Decision synthesis: produce rank, confidence, catalyst notes, risk notes, key level, and invalidation level.

The agent should not be used on the full universe. It only reviews symbols that already pass the quantitative shortlist.

## Report Output

Each daily run writes a report under `reports/YYYY-MM-DD/`.

Required outputs:

- `daily_breakout_report.md`: human-readable Chinese report.
- `candidates.csv`: ranked candidate table.
- `candidates.json`: structured output for future automation.
- `run_summary.json`: data freshness, symbols scanned, skipped symbols, quota/failure notes, and model usage.

The report should include:

- Top 20 weekly main uptrend candidates.
- Top 50 observation pool.
- Universe membership labels: S&P 500 proxy, Nasdaq 100 proxy, Russell 2000 proxy.
- Component scores and final rank.
- Breakout level, invalidation level, extension status, and major risk notes.
- Candidate changes versus the prior run.
- Tracking table for previous candidates over 1, 2, 4, and 8 week windows.

## Repository Shape

Recommended Python package layout:

```text
src/financial_agent/
  config/
  data/
  longport/
  universe/
  features/
  scoring/
  agent/
  reporting/
  storage/
  cli.py
tests/
docs/
reports/
data/
```

Key commands:

- `financial-agent auth login`: start LongPort OAuth setup.
- `financial-agent universe refresh`: refresh ETF component universes.
- `financial-agent data update --incremental`: update cached daily candles.
- `financial-agent screen run`: run scoring and agent review.
- `financial-agent report latest`: print or open the latest report.

## Error Handling

The pipeline should degrade gracefully:

- If universe refresh fails, use the latest cached universe and mark the report stale.
- If a symbol fails to update, skip it and record the error.
- If news fetch fails, keep the quantitative score and mark catalyst evidence missing.
- If the LLM or agent review fails, still output the quantitative shortlist.
- If LongPort quota is exceeded, stop new historical fetches and report the exact quota blocker.

## Testing Strategy

Testing should focus on determinism and data correctness:

- Unit tests for daily-to-weekly resampling.
- Unit tests for each scoring component.
- Fixture-based tests for breakout, failed breakout, overextended, low-liquidity, and weak-market cases.
- Integration smoke test with a small fixed symbol set, such as `AAPL.US`, `MSFT.US`, `NVDA.US`, and `IWM.US`.
- Report rendering test that verifies required sections and fields are present.

## Non-Goals For V1

The first version will not:

- Place trades automatically.
- Optimize portfolio sizing.
- Support intraday signals.
- Run LLM review across the entire stock universe.
- Depend on official paid index constituent feeds unless needed later.
- Persist registration access tokens or other secret credentials in the repository.

## Acceptance Criteria

V1 is ready when:

- A local command can refresh or reuse the three proxy universes.
- Cached daily OHLCV data can be incrementally updated without full redownload.
- Weekly bars and feature scores are reproducible from cached data.
- A daily report is generated from a small smoke-test universe.
- The report explains why each top candidate qualifies and what would invalidate it.
- The system records skipped symbols, stale data, API failures, and quota issues clearly.
