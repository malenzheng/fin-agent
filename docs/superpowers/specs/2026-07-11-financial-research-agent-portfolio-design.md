# FinPulse Agent 作品集设计

## 目标

把现有的 `financial-agent` 项目升级成一个面向「金融 x LLM Agent」岗位的公开求职作品集。

项目定位：

> FinPulse Agent 是一个面向市场信息处理与投研辅助的金融 LLM Agent。它结合确定性的金融数据处理、Agent 工作流和可复现的评测体系，用来展示真实金融研究场景中的工程落地能力。它不是自动交易系统，也不提供投资建议。

这个项目要证明候选人能把金融行业后台开发经验迁移到 LLM Agent 产品中：

- 能做可靠的数据管道；
- 能设计证据可追溯的投研工作流；
- 能用确定性规则生成候选池；
- 能编排 Agent 进行分析和报告生成；
- 能设计 Benchmark 和评测闭环；
- 能维护一个适合公开展示的工程仓库。

## 岗位匹配

这个项目针对的是「Finance x LLM Agent」一类岗位。它们通常不是只要聊天机器人，也不是单纯量化策略，而是希望 Agent 真正参与金融研究、信息处理、决策辅助和评测迭代。

仓库需要展示四类能力：

1. 金融场景理解：行情、新闻、公告、财报、主题、风险提示。
2. 后端工程能力：CLI、定时任务、缓存优先、类型边界、测试、失败降级。
3. Agent 工作流设计：规划、工具调用、检索、证据合成、结构化报告、兜底逻辑。
4. 评测与迭代能力：测试 case、评分 Rubric、模型/Prompt 对比、失败样本收集、未来 SFT/DPO 数据构造。

## 产品范围

项目从当前的「周线突破筛选器」演进成更完整的金融研究 Agent。

第一个公开版本应支持：

- 从缓存行情数据中生成量化候选池；
- 给候选标的补充市场信息和风险上下文；
- 生成中文投研辅助报告，包含证据、逻辑和风险提示；
- 在没有密钥、没有付费数据的情况下运行离线 smoke demo；
- 文档化学习路线、项目路线、架构设计和面试讲述方式。

项目不承诺交易收益，也不包装成自动炒股工具。它应该被描述为金融研究助手、市场信息处理工作流和 Agent 评测平台。

## 学习路线

学习路线要和仓库里程碑绑定。每学一块，都要有对应的代码、文档或评测产出。

### 阶段 1：LLM Agent 基础

重点：

- Tool Calling；
- 结构化 JSON 输出；
- Workflow 编排；
- 状态机；
- 失败重试和兜底；
- Prompt / Context Engineering。

仓库产出：

- 写清楚 Agent 工作流设计；
- 增加最小工具注册接口；
- 保留离线、确定性的 review 路径。

### 阶段 2：金融数据工程

重点：

- OHLCV 行情数据；
- 股票池和指数成分；
- 新闻、公告、财报；
- 文本中的公司/股票实体映射；
- 本地缓存和数据新鲜度追踪。

仓库产出：

- 保留现有缓存优先的行情数据管道；
- 增加基于 fixture 的信息源接口；
- 在报告里展示数据新鲜度和信息源状态。

### 阶段 3：投研 Agent 工作流

重点：

- 市场热点发现；
- 主题逻辑解释；
- 相关个股映射；
- 个股深度研究；
- 催化因素和风险提取；
- 基于证据的报告生成。

仓库产出：

- 实现分阶段研究流程：
  - 收集上下文；
  - 构建候选池；
  - 检索证据；
  - 合成研究结论；
  - 输出报告和结构化产物。

### 阶段 4：Agent 评测

重点：

- 任务完成度；
- 事实准确性；
- 证据引用；
- 金融推理；
- 风险识别；
- 幻觉检测；
- LLM-as-Judge 与人工可复核 Rubric。

仓库产出：

- 增加 benchmark 目录，准备 30-50 个测试 case；
- 对比 baseline prompt、RAG workflow 和 agent workflow；
- 写出可复现的评测报告。

### 阶段 5：后训练意识

重点：

- SFT；
- DPO；
- 偏好数据；
- 从失败案例挖数据；
- 从投研任务构造监督数据；
- 安全和合规样本。

仓库产出：

- 根据 benchmark 失败案例生成样例训练数据格式；
- 文档化未来如何做 SFT/DPO；
- 没有真实训练前，不声称模型已经训练完成。

## 项目路线

### 里程碑 0：公开仓库门面

目标：让面试官 5 分钟内知道这个项目在做什么、为什么贴岗位、怎么运行。

交付物：

- `README.md`：项目定位、演示片段、安装方式、命令、免责声明；
- `docs/learning-roadmap.md`：学习路线；
- `docs/project-roadmap.md`：项目路线；
- `docs/architecture.md`：架构说明；
- `docs/interview-positioning.md`：面试讲述方式；
- 干净的 `.env.example`，不提交任何密钥；
- 可复现的测试命令和 smoke 命令。

### 里程碑 1：量化候选池引擎

目标：把当前周线突破筛选器整理成确定性的候选池生成器。

交付物：

- 候选评分逻辑文档；
- 可以公开展示的示例报告；
- 更清楚的评分解释；
- 数据新鲜度和跳过标的诊断；
- 评分和报告渲染测试。

### 里程碑 2：市场信息管道

目标：增加新闻、公告、财报、主题信息的可扩展信息源层。

交付物：

- 信息源 provider 接口；
- 公开 demo 可用的 fixture provider；
- 通过环境变量启用的真实 provider；
- 报告中的信息源元数据。

### 里程碑 3：金融研究 Agent

目标：让系统从筛选器升级为投研辅助工作流。

交付物：

- 热点发现工作流；
- 主题到个股映射；
- 个股研究工作流；
- 催化因素和风险提取；
- 证据引用；
- 结构化 JSON 输出和 Markdown 报告。

### 里程碑 4：Benchmark 与评测

目标：展示不只看收益率的金融 Agent 评测能力。

交付物：

- benchmark case schema；
- Rubric 定义；
- 必填字段和证据引用的确定性检查；
- 可选 LLM-as-Judge 评分；
- 不同 workflow 版本的对比报告。

### 里程碑 5：面试材料

目标：让项目可以自然地用于面试讲述。

交付物：

- 一页架构讲述；
- 技术深挖笔记；
- 面试自我介绍脚本；
- 已知限制；
- 未来训练和产品化计划。

## 架构设计

项目保持 Python CLI 优先，偏后端工程项目，而不是 Notebook demo。

推荐模块结构：

```text
src/financial_agent/
  config/
  storage/
  data/
  universe/
  features/
  scoring/
  sources/
  retrieval/
  agent/
  evaluation/
  reporting/
  cli.py
```

关键边界：

- `sources`：获取真实或 fixture 形式的市场信息；
- `storage`：负责本地缓存路径和持久化；
- `features`：计算确定性的金融特征；
- `scoring`：生成量化候选池；
- `retrieval`：为 Agent 合成准备证据；
- `agent`：编排研究工作流和兜底 review；
- `evaluation`：运行 benchmark case 和 Rubric 评分；
- `reporting`：渲染 Markdown、CSV、JSON 产物。

## 数据流

主研究流程：

1. 加载配置并检查密钥安全；
2. 刷新或复用股票池；
3. 更新或读取缓存 OHLCV 行情；
4. 构建周线特征和量化评分；
5. 选出候选池；
6. 为候选标的和主题检索 fixture 或真实信息；
7. 运行确定性或 LLM 驱动的研究 review；
8. 输出 Markdown 和结构化产物；
9. 保存运行元数据、数据新鲜度、跳过标的和信息源状态。

评测流程：

1. 加载 benchmark cases；
2. 运行指定 workflow 版本；
3. 检查输出 schema 和证据引用；
4. 进行确定性评分；
5. 可选地使用 LLM-as-Judge；
6. 写出人工可复核的评测总结。

## 公开仓库策略

仓库默认要做到公开安全。

规则：

- 不提交 `.env`、API key、OAuth registration token、账户标识、私人研究笔记或付费数据；
- 本地生成的 `/data/` 和 `/reports/` 保持 ignore；
- 只提交少量 fixture 数据和公开安全的示例输出；
- 明确写出免责声明：项目是研究和工程作品集，不构成投资建议；
- 维护公开 issue 和 milestone，让仓库看起来是持续演进的项目；
- commit 要小而清晰，PR 或 commit notes 里保留测试证据。

## GitHub 设置计划

当前环境没有 `gh` CLI，也没有可直接创建 GitHub 仓库的工具，所以公开仓库使用这个流程：

1. 用户在 GitHub 网页创建一个空的 public repository；
2. 用户把 repo URL 发给 Codex；
3. Codex 在本地配置 `origin`；
4. Codex 推送当前分支；
5. Codex 协助选择默认分支策略：
   - 要么直接推到 `main`；
   - 要么推送 `codex/daily-weekly-breakout-agent`，如果工具允许再开 PR。

repo URL 必须是真实地址，不能由 Codex 编造。

## 测试策略

每个里程碑都必须保持现有单测和 smoke 流程可用。

基础验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\financial-agent.exe screen smoke --report-dir reports
```

后续增加测试：

- 信息源 provider 兜底；
- 证据引用字段；
- Agent workflow schema；
- benchmark case 加载；
- Rubric 确定性评分；
- 面试展示报告的必要章节。

## 错误处理

系统要优雅降级：

- 如果真实行情不可用，使用 fixture demo，并在报告中标记 demo 数据；
- 如果某个信息源失败，保留量化结果，并记录缺失信息源；
- 如果 LLM review 失败，渲染确定性兜底分析；
- 如果 benchmark judge 失败，保留确定性评分；
- 如果 LongPort 或其他数据源触发额度限制，停止新的请求并报告具体 blocker。

## 非目标

本项目不会：

- 自动下单交易；
- 声称有生产级投资收益；
- 提交私人或付费数据集；
- 要求公开 demo 必须有实时密钥；
- 在数据和评测闭环成熟前训练大模型；
- 把模型输出包装成投资建议。

## 验收标准

下一阶段完成时，应满足：

- 中文设计文档和学习路线已经提交；
- README 能说明岗位匹配和 demo 流程；
- 现有测试通过；
- smoke report 可以本地运行；
- 仓库准备好推送到用户创建的 public GitHub repo；
- 下一份实施计划具体到可以逐项执行。

## 自检

- 没有保留未完成章节；
- 公开仓库设置没有假设不可用的 GitHub 创建工具；
- 范围聚焦在作品集级金融研究 Agent，不扩张成完整交易平台；
- 保留现有周线突破筛选器作为候选池引擎；
- 密钥安全、免责声明、测试和兜底行为都已经明确。
