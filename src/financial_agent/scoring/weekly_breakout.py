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
    near_high_score = _clamp((close / recent_high) * 100) if recent_high else 0
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
    if liquidity_score < 1:
        liquidity_score = 0

    technical_total_score = (
        trend_score * 0.24
        + relative_strength_score * 0.22
        + breakout_score * 0.20
        + volume_score * 0.14
        + extension_risk_score * 0.10
        + liquidity_score * 0.10
    )
    if liquidity_score < 50:
        technical_total_score = min(technical_total_score, 55)

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
