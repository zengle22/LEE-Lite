---
id: TASK-FEAT-SRC-001-005-004
ssot_type: task
title: 正式物化与 follow-up dispatch 集成
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260324
parent_id: FEAT-SRC-001-005
derived_from_ids:
  - id: FEAT-SRC-001-005
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-005#验收检查
  - FEAT-SRC-001-002#依赖
  - FEAT-SRC-001-003#依赖
owner: workflow-integrator
tags: [materialization, dispatch, run-closure]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: integration
  workstream: workflow-integration
  responsible_role: workflow-integrator
  priority: P0
  milestone: M3-Materialization-Dispatch
  estimated_effort: 1.5 days
  lifecycle_status: frozen
  implementation_chunks:
    - formal object write plan by decision_type
    - queue dispatch and handoff/job routing
    - run closure and spawned lineage recording
  acceptance_criteria:
    - approve/revise/retry/handoff/reject 各自产出与决策一致的 formal object，并通过受管写入落盘
    - run closure、follow-up job / handoff dispatch 与 lineage 继承保持一致
  definition_of_done:
    - formal materialization 集成完成
    - follow-up dispatch 与 run closure 一致性可验证
  inputs:
    - TASK-FEAT-SRC-001-005-002 schemas
    - TASK-FEAT-SRC-001-005-003 decision results
    - path policy and registry constraints
  outputs:
    - materialized formal objects
    - follow-up jobs or handoffs
    - run closure records
frozen_at: '2026-03-24T09:35:00+08:00'
---

# Objective

把 External Gate 的 decision 结果转成正式物化对象、下游 dispatch 和 run closure，使 approve / revise / retry / handoff / reject 都有一致的正式落盘和推进语义。

# Description

该任务负责 external gate 的 materialization phase。它依据唯一 decision_type，通过 Gateway、Path Policy 与 Registry 的正式链路写出 `gate-decision`、`materialized-ssot`、`materialized-handoff`、`materialized-job`、`run-closure` 或 `revision-request`，并把新 job / human-review handoff 路由到正确队列。重点是 formal object 与 follow-up dispatch 的一致性，而不是业务内容再加工。

## Acceptance Mapping

- FEAT-SRC-001-005 / AC-02: formal object 只能在 gate 后物化。
- FEAT-SRC-001-005 / AC-03: run closure 与 follow-up dispatch 必须一致。

## Prerequisites

- TASK-FEAT-SRC-001-005-002 与 TASK-FEAT-SRC-001-005-003 已具备 schema 和 decision 输出

## Dependencies

- TASK-FEAT-SRC-001-002-002
- TASK-FEAT-SRC-001-003-002
- TASK-FEAT-SRC-001-005-002
- TASK-FEAT-SRC-001-005-003

## Inputs

- materialization object schemas
- 唯一 gate decision result
- Path Policy 的合法性判定与 Registry 的 formal reference 约束

## Outputs

- formal materialized objects
- downstream execution jobs / human-review jobs
- run closure and lineage records

## Implementation Chunks

- 按 decision_type 选择要写出的 formal object 集合，并通过受管写入完成落盘。
- 生成 follow-up execution job / human-review job / materialized handoff，并路由到正确队列。
- 写出 run closure，记录 terminal_state、spawned refs 与 lineage 继承。

## Orthogonality Guardrails

- 本任务只消费 `TASK-FEAT-SRC-001-005-003` 给出的唯一 decision result，不重新评估 package completeness、budget 或 evidence。
- 本任务只消费 `TASK-FEAT-SRC-001-004-003` 提供的 gate-facing audit mapping，不重写 audit severity 解释或 repair targeting。
- 本任务负责 formal object 物化与 dispatch，不负责 Gateway surface、Registry read eligibility 或 finding 生产。

## Definition Of Done

- approve / revise / retry / handoff / reject 各自产出与 ADR-006 规则一致
- formal objects 均通过受管写入和 registry-backed reference 进入正式链路
- run closure 记录 terminal_state、spawned refs 与 gate decision 绑定
- 队列路由覆盖 ready / gate-ready / human-review / done 等正式去向

## Observability

```yaml
execution_unit: task
log_scope: gate-materialization-dispatch
audit_fields:
  - run_id
  - task_id
  - feat_id
  - decision_ref
  - materialized_object_refs
  - spawned_job_refs
  - spawned_handoff_refs
  - terminal_state
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-002-002
  - TASK-FEAT-SRC-001-003-002
  - TASK-FEAT-SRC-001-005-002
  - TASK-FEAT-SRC-001-005-003
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - skills/ll-gate-decision-materializer/scripts/gate_materialize.py
  - src/runtime/gate_materialization_dispatch.py
  - src/runtime/run_closure_writer.py
fallback: 停用 formal materialization phase；不得回退为上游 skill 直接落 formal object
```
