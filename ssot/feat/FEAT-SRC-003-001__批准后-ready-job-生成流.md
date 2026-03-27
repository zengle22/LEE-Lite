---
id: FEAT-SRC-003-001
ssot_type: FEAT
feat_ref: FEAT-SRC-003-001
epic_ref: EPIC-SRC-003-001
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
冻结 gate approve 如何根据 progression policy 生成 ready execution job 或 hold job，并把 approve 继续绑定到受治理的下游推进而不是 formal publication。

## Scope
- 定义 approve 后可产出的 ready execution job / hold job 及其最小字段。
- 定义 ready job 的 authoritative refs、next skill target 和队列落点。
- 定义 approve 后 `progression_mode = auto-continue | hold` 的最小治理语义。
- 定义 revise / retry / reject / handoff 与 ready job 生成的边界，避免 approve 语义漂移。

## Constraints
- approve 必须稳定落成受治理的下游 dispatch 结果，而不是停在 formal publication。
- `progression_mode = auto-continue` 时必须写入 `artifacts/jobs/ready`。
- `progression_mode = hold` 时不得泄漏 ready queue item，而应停在 hold / waiting-human 队列。
- revise / retry / reject / handoff 不得冒充 next-skill ready job。
- approve-to-job 关系必须可追溯。

## Acceptance Checks
1. Approve emits one governed dispatch result
   Then: approve must materialize exactly one authoritative downstream dispatch result, and that result must respect `progression_mode`.
2. Approve is not rewritten as formal publication
   Then: approve must continue into ready-job emission rather than being described as formal publication or admission.
3. Non-approve decisions do not emit next-skill jobs
   Then: the product flow must keep those outcomes out of the next-skill ready queue.
