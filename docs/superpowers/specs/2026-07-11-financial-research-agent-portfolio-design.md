# FinPulse Agent Portfolio Design

## Goal

Build the existing `financial-agent` project into a public interview portfolio for a Financial LLM Agent role.

The target positioning is:

> FinPulse Agent is a market information and investment research assistant that combines deterministic financial data processing, LLM Agent workflows, and benchmark-style evaluation. It is not an auto-trading system.

The project should show that the candidate can connect financial industry backend experience with real LLM Agent product work:

- reliable data pipelines,
- evidence-grounded research workflows,
- quantitative candidate generation,
- agent orchestration,
- benchmark and evaluation design,
- maintainable public repository practices.

## Target Role Fit

The project is designed for roles like "Finance x LLM Agent" where the team needs systems that participate in real financial research, information processing, and decision-support workflows.

The repo should demonstrate four capabilities:

1. Financial domain grounding: market data, news, announcements, fundamentals, themes, and risk notes.
2. Backend engineering: CLI, scheduled jobs, cache-first storage, typed boundaries, tests, and graceful degradation.
3. Agent workflow design: planning, tool use, retrieval, evidence synthesis, structured reports, and fallback behavior.
4. Evaluation and iteration: task cases, scoring rubrics, model/prompt comparisons, failure-case collection, and future SFT/DPO data construction.

## Product Scope

The project evolves from the current weekly breakout screener into a broader financial research agent.

The first public version should support:

- generating a quantitative candidate pool from cached market data,
- enriching top candidates with market context,
- producing a Chinese research report with evidence and risk notes,
- running offline smoke demos without secrets or paid data access,
- documenting the learning path, roadmap, architecture, and interview positioning.

The project should avoid promising live trading performance. It should be presented as a research assistant, market-intelligence workflow, and evaluation platform.

## Learning Roadmap

The learning plan is intentionally tied to repo milestones so that study produces visible commits.

### Stage 1: LLM Agent Basics

Focus:

- tool calling,
- structured JSON output,
- workflow orchestration,
- state machines,
- retry and fallback behavior,
- prompt and context engineering.

Repo outcome:

- document the agent workflow design,
- add a minimal tool registry interface,
- keep an offline deterministic review path.

### Stage 2: Financial Data Engineering

Focus:

- OHLCV data,
- universe membership,
- news and announcements,
- fundamentals,
- entity mapping from text to symbols,
- local cache and data freshness tracking.

Repo outcome:

- keep the current cache-first market-data pipeline,
- add fixture-backed information-source interfaces,
- expose freshness and source status in reports.

### Stage 3: Research Agent Workflow

Focus:

- market hotspot discovery,
- theme explanation,
- related-stock mapping,
- individual-stock research,
- catalyst and risk extraction,
- evidence-grounded report writing.

Repo outcome:

- implement a staged research workflow:
  - collect context,
  - build candidate pool,
  - retrieve evidence,
  - synthesize research notes,
  - render report artifacts.

### Stage 4: Agent Evaluation

Focus:

- task completion,
- factuality,
- evidence citation,
- financial reasoning,
- risk identification,
- hallucination detection,
- LLM-as-judge with human-reviewable rubrics.

Repo outcome:

- add a benchmark folder with 30-50 cases,
- compare baseline prompt, RAG workflow, and agent workflow,
- write a reproducible evaluation report.

### Stage 5: Post-Training Awareness

Focus:

- SFT,
- DPO,
- preference data,
- failure-case mining,
- supervised datasets from research tasks,
- safety and compliance examples.

Repo outcome:

- create sample training-data formats from benchmark failures,
- document how future SFT/DPO would be done,
- avoid claiming trained models unless actual training is run and verified.

## Project Roadmap

### Milestone 0: Public Repo Readiness

Goal: make the project understandable to a recruiter or interviewer in five minutes.

Deliverables:

- `README.md` with positioning, screenshots/report snippets, setup, commands, and disclaimer.
- `docs/learning-roadmap.md`.
- `docs/project-roadmap.md`.
- `docs/architecture.md`.
- `docs/interview-positioning.md`.
- clean `.env.example` and no committed secrets.
- verified test command and smoke command.

### Milestone 1: Quantitative Candidate Engine

Goal: preserve and improve the current weekly breakout screener as the deterministic candidate generator.

Deliverables:

- candidate scoring documentation,
- sample report committed under a public-safe demo path,
- richer score explanation,
- freshness and skipped-symbol diagnostics,
- tests for scoring and report rendering.

### Milestone 2: Market Information Pipeline

Goal: add an extensible source layer for news, announcements, fundamentals, and theme notes.

Deliverables:

- source provider interfaces,
- fixture provider for public offline demos,
- optional real providers through environment configuration,
- source metadata in every report section.

### Milestone 3: Financial Research Agent

Goal: turn the system from a screener into a research workflow.

Deliverables:

- hotspot discovery workflow,
- theme-to-symbol mapping,
- individual-stock research workflow,
- catalyst and risk extraction,
- evidence citations,
- structured JSON output plus Markdown report.

### Milestone 4: Benchmark And Evaluation

Goal: show the ability to evaluate financial agents beyond returns.

Deliverables:

- benchmark case schema,
- rubric definitions,
- deterministic checks for required fields and citations,
- optional LLM-as-judge scoring,
- comparison report across workflow versions.

### Milestone 5: Interview Package

Goal: make the repo easy to discuss in interviews.

Deliverables:

- one-page architecture narrative,
- technical deep-dive notes,
- interview speaking script,
- known limitations,
- future training and productization plan.

## Architecture

The project remains a Python CLI-first backend package.

Recommended module shape:

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

Key boundaries:

- `sources`: obtains raw or fixture-backed market information.
- `storage`: owns local cache paths and persistence.
- `features`: computes deterministic financial features.
- `scoring`: builds the quantitative candidate pool.
- `retrieval`: prepares evidence for agent synthesis.
- `agent`: orchestrates research workflows and fallback reviews.
- `evaluation`: runs benchmark tasks and rubric scoring.
- `reporting`: renders Markdown, CSV, and JSON artifacts.

## Data Flow

The main research flow:

1. Load settings and validate secret hygiene.
2. Refresh or reuse universe data.
3. Update or load cached OHLCV data.
4. Build weekly features and quantitative scores.
5. Select a shortlist.
6. Retrieve fixture or real information for shortlisted symbols and themes.
7. Run deterministic or LLM-backed research review.
8. Render Markdown and structured artifacts.
9. Save run metadata, data freshness, skipped symbols, and source status.

The benchmark flow:

1. Load benchmark cases.
2. Run the selected workflow variant.
3. Validate schema and citation requirements.
4. Score with deterministic checks.
5. Optionally score with an LLM judge.
6. Write an evaluation summary that can be reviewed by humans.

## Public Repository Policy

The repository should be public-safe by default.

Rules:

- Never commit `.env`, API keys, OAuth registration tokens, account identifiers, private research notes, or paid data dumps.
- Keep generated local `/data/` and `/reports/` ignored.
- Commit only small fixture data and public-safe sample outputs.
- Add a clear disclaimer that this is a research and engineering portfolio, not investment advice.
- Keep issues and milestones visible so the repo shows active maintenance.
- Prefer small, meaningful commits with test evidence in PR or commit notes.

## GitHub Setup Plan

Because the local environment currently has no `gh` CLI and no direct GitHub repository creation tool, the public repo setup will use this flow:

1. User creates an empty public GitHub repository in the browser.
2. User provides the repo URL.
3. Codex sets `origin` locally.
4. Codex pushes the current branch.
5. Codex helps choose the default branch strategy:
   - either push current work to `main`,
   - or push `codex/daily-weekly-breakout-agent` and open a PR if GitHub tools permit.

The repo URL must be real. Codex must not invent one.

## Testing Strategy

Every milestone should preserve the current smoke and unit test path.

Baseline verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\financial-agent.exe screen smoke --report-dir reports
```

Additional tests should be added for:

- source provider fallbacks,
- evidence citation fields,
- agent workflow schema,
- benchmark case loading,
- deterministic rubric scoring,
- report sections required for interviews.

## Error Handling

The system should degrade gracefully:

- If real market data is unavailable, use fixture demos and mark the report as demo data.
- If a source provider fails, keep quantitative results and record the missing source.
- If LLM review fails, render deterministic fallback analysis.
- If benchmark judge scoring fails, keep deterministic scores.
- If LongPort or other data quotas are hit, stop new requests and report the blocker.

## Non-Goals

This project will not:

- place trades automatically,
- claim production investment performance,
- commit private or paid datasets,
- require live credentials for the public demo,
- train large models before the data and evaluation loop are ready,
- present model outputs as financial advice.

## Acceptance Criteria

The next phase is complete when:

- the design and learning roadmap are committed,
- the README explains the role fit and demo workflow,
- the existing tests pass,
- the smoke report still runs locally,
- the repo is ready to push to a user-created public GitHub repository,
- the next implementation plan is specific enough to execute task by task.

## Spec Self-Review

- No placeholder sections remain.
- The public repo setup does not assume unavailable GitHub creation tooling.
- The scope is focused on a portfolio-grade financial research agent, not a full trading platform.
- The design preserves the existing weekly breakout screener as a candidate engine.
- Secret hygiene, disclaimers, tests, and fallback behavior are explicit.
