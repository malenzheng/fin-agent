# FinPulse Agent：金融市场信息处理与投研辅助

面向金融 LLM Agent 岗位的中文工程作品集，主线是：**市场信息处理 -> 可追溯的投研辅助 -> Agent 评测与迭代**。

当前已实现无需密钥的离线研究与评测基线。研究工作流使用合成资料和人工分类，按规则摘录原文，**尚未接入 LLM、实时资讯或 RL 训练**。原有量价筛选器作为独立模块保留。

## 五分钟运行

需要 Python 3.11+，在仓库根目录运行。首次安装需要访问 Python 包源，下面的演示不访问外部信息源。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\financial-agent.exe research demo
.\.venv\Scripts\financial-agent.exe evaluate research
.\.venv\Scripts\python.exe -m pytest -q
```

Linux/macOS 对应执行 `.venv/bin/python` 和 `.venv/bin/financial-agent`。

生成文件：

- `reports/research/brief.md`：中文研究简报，包含催化、风险、背景、证据与执行轨迹。
- `reports/research/brief.json`：机器可读的任务、原文摘录、时间戳及轨迹。
- `reports/evaluation/results.md` 与 `results.json`：逐案例分数和失败原因。

演示固定研究时点为 **2026-10-02 12:00 +08:00**。`DEMO.CHIP`、`DEMO.AUTO` 均为虚构标的，`fixture://` 是本地样例定位符。结果不是当前市场资讯。

## 已有能力

| 方向 | 当前实现 | 下一步 |
| --- | --- | --- |
| 市场信息处理 | 统一 schema、发布时间与可获得时间、标的过滤、时间窗口、ID 去重 | 公开公告接入、内容去重、缓存和失败重试 |
| 投研辅助 | 原文摘录、证据追溯、风险分类、信息不足状态、执行轨迹 | LLM 工具调用、结构化分析、对立证据核验 |
| Agent 评测 | 6 个合成回归案例、7 个规则分项、独立证据校验、错误样本测试 | 30-50 个独立标注任务、语义核验、模型与 Prompt 对比 |
| 量价候选池 | 既有周线评分和合成行情 smoke | 与真实数据、研究任务建立关联 |

规则基线在 6 个合成案例上通过，只证明这组回归场景符合预期，不代表真实投研质量或大模型能力。分类是人工标注，当前没有自动识别市场热点。

## 常用命令

```powershell
# 换一个合成标的
.\.venv\Scripts\financial-agent.exe research demo --symbol DEMO.AUTO

# 历史时点：已公开但尚未入库的资料也会排除
.\.venv\Scripts\financial-agent.exe research demo --as-of "2026-10-01T12:00:00+08:00"

# 评测一份已有简报，先重新生成默认任务
.\.venv\Scripts\financial-agent.exe research demo
.\.venv\Scripts\financial-agent.exe evaluate research --brief reports/research/brief.json --case-id chip-full-context

# 原有量价演示
.\.venv\Scripts\financial-agent.exe screen smoke
```

命令会覆盖目标目录下的同名报告；需要保留多次实验时，使用不同的 `--report-dir`。评测全部通过返回 0；评分未通过返回 1 并保留报告；输入或文件错误返回 2。`--as-of` 必须包含时区。未知标的正常输出“信息不足”。

## 怎么判断输出可靠

评测器以 case 指定的标的、时间和可信资料为准，重新检查简报。它不会仅因为报告附上了一段“证据”就认可该段内容。

| 分项 | 检查内容 |
| --- | --- |
| `task_alignment` | 标的、研究时点和时间窗口是否一致 |
| `citation_validity` | 引用是否存在、匹配标的且当时可获得 |
| `quote_support` | 摘录文字及类别是否与可信原文严格一致 |
| `evidence_integrity` | 随附证据是否被篡改、重复或遗漏 |
| `evidence_coverage` | 是否覆盖人工预期证据 |
| `risk_coverage` | 是否覆盖预期风险证据 |
| `status_correctness` | 是否在信息不足时正确返回该状态 |

每项 0-1，全部为 1 才通过。总分是等权平均乘以 100，仅用来定位规则回归。当前 `quote_support` 是逐字核验，不支持把模型自由生成的推理或改写直接判成事实正确；语义核验和人工评价是下一阶段工作。轨迹目前用于审计，不作为独立评分项。

## 学习与面试

- [学习路线](docs/learning-roadmap.md)：每阶段学什么、做什么、怎样验收。
- [第一课：证据、时间与评测](docs/lessons/01-evidence-and-evaluation.md)：今天就能做的练习。
- [项目路线](docs/project-roadmap.md)：区分已完成与未来计划。
- [架构与数据流](docs/architecture.md)：从后端视角理解各个模块。
- [面试讲述](docs/interview-positioning.md)：如何准确描述当前实现。
- [合成 Benchmark](benchmarks/research_cases.json)：可检查的任务与预期证据。

## 维护约定

直接在 `main` 小步开发。每次行为变更增加相关测试，保留失败样本，运行现有流程；GitHub Actions 在推送和 PR 时运行测试及离线演示。`.env`、本地 `data/`、`reports/` 与付费数据不提交。

本项目用于学习与研究辅助，不自动下单，不构成投资建议。
