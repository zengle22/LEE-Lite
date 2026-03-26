---
id: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-001
ssot_type: FEAT
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-001
epic_ref: EPIC-GATE-EXECUTION-RUNNER
title: 批准后 Ready Job 生成流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# 批准后 Ready Job 生成流

## Goal
冻结 gate approve 如何生成 ready execution job，并把 approve 继续绑定到自动推进而不是 formal publication。

## Scope
- 定义 approve 后必须产出的 ready execution job 及其最小字段。
- 定义 ready job 的 authoritative refs、next skill target 和队列落点。
- 定义 revise / retry / reject / handoff 与 ready job 生成的边界，避免 approve 语义漂移。

## Constraints
- approve 必须稳定落成 ready execution job，而不是停在 formal publication。
- ready job 必须写入 artifacts/jobs/ready，并保留 authoritative refs 与目标 skill。
- revise / retry / reject / handoff 不得冒充 next-skill ready job。
- approve-to-job 关系必须可追溯。

## Acceptance Checks
1. Approve emits one ready job
   Then: exactly one authoritative ready execution job must be materialized for runner consumption.
2. Approve is not rewritten as formal publication
   Then: approve must continue into ready-job emission rather than being described as formal publication or admission.
3. Non-approve decisions do not emit next-skill jobs
   Then: the product flow must keep those outcomes out of the next-skill ready queue.
