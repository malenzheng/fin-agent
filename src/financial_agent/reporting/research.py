from __future__ import annotations

from financial_agent.agent.research import ResearchBrief
from financial_agent.evaluation.research import BenchmarkResult


def render_research_brief(brief: ResearchBrief) -> str:
    task = brief.task
    status = "信息不足" if brief.status == "insufficient_evidence" else "已整理可用资料"
    lines = [
        "# 金融市场信息与投研辅助简报", "",
        "数据性质：合成资料；工作流：确定性原文摘录基线，未调用 LLM。", "",
        f"- 标的：{task.symbol}", f"- 研究时点：{task.as_of.isoformat()}",
        f"- 新鲜度窗口：{task.max_age_days} 天（按发布时间）", f"- 信息源：{brief.provider}",
        f"- 状态：{status}", "",
    ]
    for kind, label in [("catalyst", "催化线索"), ("risk", "风险线索"), ("context", "背景信息")]:
        lines.extend([f"## {label}（原文摘录）", ""])
        findings = [item for item in brief.findings if item.kind == kind]
        lines.extend(f"- {item.text} [{item.evidence_id}]" for item in findings)
        if not findings:
            lines.append("本次检索未获得该类证据。")
        lines.append("")
    lines.extend(["## 证据清单", ""])
    for item in brief.evidence:
        lines.extend([
            f"### [{item.id}] {item.title}", "",
            f"- 发布者：{item.publisher}；类型：{item.source_type}",
            f"- 公开时间：{item.published_at.isoformat()}",
            f"- 可获得时间：{item.available_at.isoformat()}",
            f"- 样例定位：`{item.uri}`", "",
        ])
    lines.extend(["## 执行轨迹", ""])
    for index, step in enumerate(brief.trace, start=1):
        lines.append(f"{index}. `{step.tool}`，证据：{', '.join(step.evidence_ids) or '无'}")
    lines.extend(["", "## 局限", "", *[f"- {item}" for item in brief.limitations], ""])
    lines.append("仅供研究与工程演示，不构成投资建议。")
    return "\n".join(lines) + "\n"


def render_benchmark_report(result: BenchmarkResult) -> str:
    lines = [
        "# 投研工作流规则基线评测", "", result.limitations, "",
        f"通过：{result.passed}/{result.total}；通过率：{result.pass_rate:.1%}", "",
        "所有分项均为 1 才通过；总分是 7 个规则分项的等权平均，不是金融能力评分。", "",
        "| Case | 通过 | 规则分数 |", "| --- | --- | ---: |",
    ]
    lines.extend(f"| {item.case_id} | {'是' if item.passed else '否'} | {item.score:.2f} |" for item in result.results)
    for item in result.results:
        lines.extend(["", f"## {item.case_id}", ""])
        lines.extend(f"- {key}：{value:.3f}" for key, value in item.metrics.items())
        lines.extend(f"- 失败原因：{failure}" for failure in item.failures)
    return "\n".join(lines) + "\n"
