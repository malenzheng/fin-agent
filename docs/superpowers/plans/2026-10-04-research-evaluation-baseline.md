# 市场信息、投研简报与评测基线实施计划

> 执行方式：在本会话使用 executing-plans 和 TDD 完成。沿用用户已确认的中文作品集设计和直接在 main 开发的约定。

**目标：** 完成无需密钥即可复现的「市场信息 -> 引用式研究简报 -> 确定性评测」闭环。

**设计依据：** [作品集设计](../specs/2026-07-11-financial-research-agent-portfolio-design.md)。本次落实里程碑 0 和里程碑 2-4 的最小离线版本；真实信息源、模型调用和 30-50 题独立评测集仍属后续工作。

**架构：** 在原有筛选器旁增加只读信息源接口、抽取式研究工作流和独立评测器。使用合成公司与人工标注资料，记录公开时间、可获得时间、来源和轨迹。评测器通过可信资料重新核验简报，不能仅信任简报自带的证据。

**技术栈：** Python 3.11+、现有 Pydantic / Typer / pytest，不增加运行时依赖。

## 全局约束

- 保留现有筛选命令；README、教学和报告以中文为主。
- 仅使用明确标注的合成资料；默认演示不访问网络。
- 查询时间必须带时区；公开时间和可获得时间均不得晚于查询时间。
- 资料必须匹配标的且处于指定新鲜度窗口；重复 ID 内容冲突时报错。
- 当前工作流是确定性摘录基线，分类来自样例标注；不声称已接入 LLM 或完成 RL。
- 生成产物写入已忽略的 reports；公开样例仅由合成资料生成。

## 重点验证

1. 资料虽然已经发布，但尚未被系统获得时，不得用于历史报告。
2. 同 ID 内容冲突不能被静默覆盖；完全重复项只返回一次。
3. 无资料、陈旧资料与未知标的必须明确返回信息不足。
4. 存在的引用 ID 配上伪造文本、错误分类或伪造证据也必须评测失败。
5. CLI 对不带时区、非法时间窗口和损坏的 benchmark 给出可读错误及非零退出码。

## 任务 1：信息源和基线工作流

文件：`sources/market.py`、`sources/fixtures/market.json`、`agent/research.py`、`tests/test_market_research.py`。

接口：`ResearchTask(symbol, as_of, max_age_days)`；`FixtureMarketSource.search(task) -> list[MarketEvidence]`；`build_research_brief(task, source) -> ResearchBrief`。

- [x] 先写时间边界、去重、空资料、引用和执行轨迹测试，执行并观察失败。
- [x] 实现严格 JSON schema、基于标的及时间的检索、原文摘录和信息不足状态。
- [x] 运行新增测试并检查原有测试没有回归。

## 任务 2：独立评测与命令

文件：`evaluation/research.py`、`reporting/research.py`、`cli.py`、`benchmarks/research_cases.json`、`tests/test_research_evaluation.py`、`tests/test_research_cli.py`。

接口：`evaluate_brief(brief, case, source) -> EvaluationResult`；`run_benchmark(cases, source) -> BenchmarkResult`；`render_research_brief(brief) -> str`。

- [x] 写伪造引用、遗漏风险、未来资料、benchmark 输入异常及 CLI 测试并观察失败。
- [x] 实现基于可信源的核验、人工预期证据列表、分项分数和失败原因。
- [x] 实现 `research demo` 和 `evaluate research`，输出中文 Markdown 与 JSON。
- [x] 跑通正例和对抗反例；记录样例通过率的适用范围。

## 任务 3：中文学习材料和公开维护

文件：`README.md`、`docs/learning-roadmap.md`、`docs/project-roadmap.md`、`docs/architecture.md`、`docs/interview-positioning.md`、`docs/lessons/01-evidence-and-evaluation.md`、`.github/workflows/tests.yml`。

- [x] 将当前功能、未来计划、学习练习及验收标准分别写清楚。
- [x] 增加自动测试工作流并执行完整测试、CLI smoke、打包资料检查、差异检查。
- [x] 自检实现和文档，并完成独立代码审查与问题修复。

发布方式：验证完成后按既有约定提交并正常推送 main，核对远端提交。推送结果以远端 Git 状态为准。

## 执行记录

- 起点：main 与 origin/main 无差异，工作区干净；原有测试 12 个通过。
- 本次使用既有设计继续实施，无新增外部服务、模型调用和算力开销。
- 任务 1：新增模块不存在时测试失败；实现后完整测试 23 个通过。
- 任务 2：新增命令及评测模块缺失时测试失败；实现后 39 个测试通过。随后补充已有简报评测入口，先观察 2 个测试失败再实现。
- 任务 2 完成：完整测试 41 个通过；默认研究与评测命令通过，6/6 合成案例符合预期。
- 任务 3 验证：旧 screen smoke 通过；wheel 构建成功，直接从 wheel 导入后可以加载合成资料。
- 环境诊断：本地 venv 未安装 setuptools，因此关闭构建隔离的检查失败；使用标准隔离构建后成功，没有更改运行时依赖。
- 独立审查：发现 Typer 0.12.3 无法解析新增的 PEP 604 可选参数，旧 help 命令亦失败。用隔离依赖复现后改为 Optional 注解；当前依赖和 Typer 0.12.3 / Click 8.1.7 两组完整测试均为 41 个通过。
- CI 增加独立兼容性组合；本地文档链接与差异检查通过。远端 CI 状态与本地验证分别报告。
