# 金融后端工程师的 Agent 学习路线

目标：你能独立解释、运行和修改一个证据可追溯的研究工作流，再用独立评测证明改进有效。阶段按掌握情况推进，不把学完等同于获得 offer。

| 顺序 | 学习重点 | 仓库实践 | 过关标准 |
| --- | --- | --- | --- |
| 1 | Python 类型、Pydantic、pytest、CLI | 运行 `research demo`，看 `sources/market.py` | 能解释每个时间字段，写出一个边界测试 |
| 2 | 数据采集、幂等、原始文档、实体映射 | 在 provider 接口旁增加一种公开信息源 | 可重放历史查询，不引入未来信息 |
| 3 | Tool Calling、上下文、结构化输出、停止条件 | 给研究任务接入只读工具和一个 LLM | 能指出哪一步由模型决策，哪一步由程序执行 |
| 4 | 检索、证据定位、数值计算、矛盾处理 | 输出事实、分析、风险与未知项 | 任一结论能定位到段落，数值能复算 |
| 5 | Benchmark、数据划分、Rubric、错误分类 | 比较规则、Prompt 和 Agent 三个版本 | 能解释提升来自哪里，并给出失败案例 |
| 6 | PyTorch、梯度、SFT、策略梯度、GRPO | 从执行轨迹开展小规模训练实验 | 区分运行 Agent、生成训练数据和更新模型参数 |

## 今天的学习顺序

1. 从仓库根目录执行 README 的安装与演示命令。
2. 同时查看简报 Markdown 和 JSON，找到一条催化与一条风险的证据。
3. 阅读 [第一课](lessons/01-evidence-and-evaluation.md)，完成时间和篡改实验。
4. 看 `tests/test_market_research.py` 与 `tests/test_research_evaluation.py`，解释一个测试删掉后可能漏掉什么问题。
5. 用自己的话讲清楚：为什么“引用 ID 存在”还不足以证明答案正确？

## 结合你的后端经验

- 工具调用可以先理解为模型提出参数、程序校验并调用接口，再把结果交回模型。
- 研究任务可以先理解为带状态和预算的业务流程；当前是固定流程，后续才加入模型决策。
- 执行轨迹对应业务审计日志，但训练通常还需要模型版本、token、概率及奖励等额外信息。
- Benchmark 类似业务验收集；要防止测试答案进入模型输入，也要防止用开发样例冒充独立评测。

## Agentic RL 放在哪里

目前只有研究工作流与规则评测，没有训练。之后先补 PyTorch 和策略梯度，再理解 PPO/GRPO，最后接多轮工具训练。当前证据评测只能成为奖励设计的候选输入，不能直接当作完整训练奖励：它不衡量自由推理，也没有证明能抵抗所有奖励漏洞。

参考项目沿用此前讨论的 [Search-R1](https://github.com/PeterGriffinJin/Search-R1)、[verl](https://github.com/verl-project/verl)、[Agent Lightning](https://github.com/microsoft/agent-lightning)。这些是后续阅读入口；当前仓库没有依赖或复现它们，也未在本次工作中核验其最新 API。
