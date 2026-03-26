---
id: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
ssot_type: FEAT
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
epic_ref: EPIC-GATE-EXECUTION-RUNNER
title: Runner 运行监控流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# Runner 运行监控流

## Goal
冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。

## Scope
- 定义 monitor surface：runner observability surface。
- 定义 ready backlog、running jobs、failed jobs、deadletters、waiting-human jobs 的最小可见集合。
- 定义监控面如何服务 operator 判断继续运行、恢复还是人工介入。

## Constraints
- runner observability surface 必须覆盖 ready backlog、running、failed、deadletters、waiting-human 等关键状态。
- 监控面必须读取 authoritative runner state，而不是靠目录猜测或人工拼接。
- 监控面只负责观察和提示，不直接改写 runner control state。
- 观测结果必须能关联到 ready job、invocation 和 execution outcome lineage。

## Acceptance Checks
1. Core queue states are visible
   Then: ready backlog, running jobs, failed jobs, deadletters, and waiting-human jobs must be visible as formal runtime states.
2. Monitoring supports operator action
   Then: the product surface must support resume, retry, or handoff decisions instead of acting as a passive log dump.
3. Runner observability covers critical states
   Then: The FEAT must make ready backlog, running, failed, deadletters, and waiting-human states visible from one authoritative monitoring surface.
