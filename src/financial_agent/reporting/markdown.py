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
