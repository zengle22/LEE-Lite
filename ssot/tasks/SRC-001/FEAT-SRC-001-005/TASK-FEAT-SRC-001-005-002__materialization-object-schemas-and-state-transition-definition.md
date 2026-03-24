---
id: TASK-FEAT-SRC-001-005-002
ssot_type: task
title: Materialization 对象 Schema 与状态推进定义
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
  - ADR-006#9. Materialization 规则
  - ADR-006#10. 最小对象字段
  - ADR-006#8. 状态机
owner: contract-architect
tags: [materialization, schema, state-machine]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: specification
  workstream: contract-specification
  responsible_role: contract-architect
  priority: P0
  milestone: M1-Materialization-Schema
  estimated_effort: 1 day
  lifecycle_status: frozen
  acceptance_criteria:
    - gate-decision、materialized-ssot、materialized-handoff、materialized-job、run-closure、revision-request 的最小字段已冻结
    - approve/revise/retry/handoff/reject 对 run/job/handoff 的状态推进与 lineage 约束已冻结
  definition_of_done:
    - materialization object schemas 冻结
    - run/job/handoff 状态推进规则冻结
  inputs:
    - TASK-FEAT-SRC-001-005-001 decision model
    - ADR-006 materialization and state rules
  outputs:
    - materialization object schemas
    - state transition specification
frozen_at: '2026-03-24T09:35:00+08:00'
---

# Objective

冻结 External Gate 所产出的正式对象 schema 与状态推进规则，使 decision、formalization、dispatch 和 run closure 的关系可被稳定审计。

# Description

该任务把 external gate 的输出对象从口头约定变成正式 schema，并明确每一种 decision_type 对 run、job、handoff 状态以及 lineage 派生的影响。它的重点不是实现写文件，而是把“会写什么对象、写完后状态怎么变”收敛成稳定规范。

## Acceptance Mapping

- FEAT-SRC-001-005 / AC-02: formal object 只能在 gate 后物化。
- FEAT-SRC-001-005 / AC-03: run closure 与 follow-up dispatch 必须一致。

## Prerequisites

- TASK-FEAT-SRC-001-005-001 已冻结

## Dependencies

- TASK-FEAT-SRC-001-005-001

## Inputs

- external gate decision model
- ADR-006 的 materialization 规则、最小对象字段与状态机
- formal SSOT、formal handoff、formal job 与 run closure 的治理边界

## Outputs

- gate-decision schema
- materialized-ssot / handoff / job / run-closure / revision-request schemas
- run/job/handoff state transition specification

## Definition Of Done

- 六类正式对象最小字段完整且互相可追溯
- approve / revise / retry / handoff / reject 的对象产出约束写清
- run/job/handoff 状态推进与 lineage 继承规则可直接驱动 reviewer 和 runtime
- formal object 只能在 gate 后物化的边界已写入 schema 说明与消费约束

## Observability

```yaml
execution_unit: task
log_scope: materialization-schema-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - object_type
  - decision_type
  - terminal_state
  - spawned_refs
  - schema_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-005-001
  - ADR-006
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - contracts/gate_decision_schema.yaml
  - contracts/materialized_ssot_schema.yaml
  - contracts/materialized_handoff_schema.yaml
  - contracts/materialized_job_schema.yaml
  - contracts/run_closure_schema.yaml
  - contracts/revision_request_schema.yaml
preconditions:
  - 先备份当前对象字段草案与状态图，避免回滚后失去比对锚点
```
