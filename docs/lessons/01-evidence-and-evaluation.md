# 第一课：证据、时间与评测

学习目标：能解释一条信息为什么进入报告，以及一条带引用的结论为什么仍然可能不合格。预计一次学习完成，不需要 GPU 或 API key。

## 练习 1：读懂一次研究任务

在仓库根目录运行：

```powershell
.\.venv\Scripts\financial-agent.exe research demo
.\.venv\Scripts\financial-agent.exe evaluate research
```

打开 `reports/research/brief.md` 和 `brief.json`，找到标的、`as_of`、原文摘录、证据 ID 和 `trace`。沿着 `chip-order` 找到 `src/financial_agent/sources/fixtures/market.json` 中的记录。

你应当能解释：报告来自合成记录；催化/风险类别是预先标注；系统没有调用模型。

## 练习 2：已经发布，为什么还不能用

```powershell
.\.venv\Scripts\financial-agent.exe research demo --as-of "2026-10-01T12:00:00+08:00" --report-dir reports/noon
```

`chip-risk` 在当天 11 点公开，但 14 点才可获得。因此中午报告只含 `chip-order`。如果只比较 `published_at`，历史实验会误用尚未拿到的资料。

把查询时点改成 14 点，观察风险证据进入报告。再用不含时区的时间运行，观察输入被拒绝。你应当能区分信息公开、系统可获得和研究时点三个概念。

## 练习 3：引用真的能证明答案吗

先运行默认 `research demo`。在生成的 `reports/research/brief.json` 中，把第一条 `findings` 的 `text` 改成“示例芯片公司利润将翻倍”，保留原来的 `evidence_id`。该文件是本地演示产物，可以随时重新生成。

```powershell
.\.venv\Scripts\financial-agent.exe evaluate research --brief reports/research/brief.json --case-id chip-full-context --report-dir reports/tampered
```

预期退出码为 1，并生成诊断。`citation_validity` 仍可能为 1，因为 ID 存在且时间正确；`quote_support` 会下降，因为原文不支持这段摘录。

再把随附 `evidence` 的文字也改成相同内容。评测仍应失败，因为它重新读取可信源；`evidence_integrity` 也会变为 0。不能让生成答案的一方同时定义自己的正确答案。

## 练习 4：加一个时间边界测试

参考 `tests/test_market_research.py` 的例子，增加一个查询时点比 `available_at` 早 1 秒的测试，并断言返回空列表。再验证等于 `available_at` 时该记录可以返回。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_market_research.py -q
```

验收：你能自己写出断言，解释如果删除可获得时间过滤，这个测试为什么会失败。

## 本课自测

1. 没有找到风险资料，能不能推断标的没有风险？
2. 摘录逐字正确，是否说明发布者的原始信息一定真实？
3. 6 个合成案例全部通过，是否说明模型投研能力已经足够？
4. 保存了工具日志，是否意味着已经完成强化学习？

参考答案均为“不能/不意味着”。分别缺少完整资料、原始信息核实、独立真实任务检验和模型参数更新。下一课再把一个只读工具交给模型选择调用。
