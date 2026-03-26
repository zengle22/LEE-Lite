---
id: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-004
ssot_type: FEAT
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-004
epic_ref: EPIC-GATE-EXECUTION-RUNNER
title: Execution Runner 自动取件流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# Execution Runner 自动取件流

## Goal
冻结 Execution Loop Job Runner 如何从 ready queue 自动取件、claim job 并进入 running，而不是继续依赖第三会话人工接力。

## Scope
- 定义 runner 扫描、claim、running 和防重入边界。
- 定义 jobs/ready 到 runner ownership 的状态转移。
- 定义 runner 对 job lineage、claim 证据和并发责任的记录方式。

## Constraints
- Execution Loop Job Runner 必须自动消费 ready queue。
- claim 语义必须是 single-owner。
- runner intake 不得回退到人工接力或临时脚本触发。
- claim 和 running ownership 必须留下证据。

## Acceptance Checks
1. Ready queue is auto-consumed
   Then: the runner must claim the job and record running ownership without human relay.
2. Claim semantics are single-owner
   Then: only one runner ownership record may succeed.
3. Ready queue remains the authoritative intake
   Then: the FEAT must use the ready queue and runner claim path instead of directory guessing or ad hoc invocation.
