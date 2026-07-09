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
