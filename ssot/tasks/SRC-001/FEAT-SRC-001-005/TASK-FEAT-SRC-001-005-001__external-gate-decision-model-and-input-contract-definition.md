---
id: TASK-FEAT-SRC-001-005-001
ssot_type: task
title: External Gate Decision 模型与输入契约定义
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
  - ADR-006#7. Decision 模型
  - ADR-006#6. Gate 输入标准
owner: contract-architect
tags: [external-gate, decision, contract]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: specification
  workstream: contract-specification
  responsible_role: contract-architect
  priority: P0
  milestone: M1-Gate-Decision-Contract
  estimated_effort: 0.75 day
  lifecycle_status: frozen
  acceptance_criteria:
    - gate-ready 最小输入集、decision_type 互斥规则与 target 约束矩阵已冻结
    - gate 只消费治理结论，不重做业务语义审查的边界已明确
  definition_of_done:
    - external gate input contract 冻结
    - decision model 与 target 约束矩阵冻结
  inputs:
    - FEAT-SRC-001-005 acceptance checks
    - ADR-006 gate input and decision rules
  outputs:
    - external gate input contract
    - decision model specification
frozen_at: '2026-03-24T09:35:00+08:00'
---

# Objective

冻结 External Gate 的最小输入契约、互斥单选 decision model 和 target 约束矩阵，作为所有 gate consumer 的共同规范源。

# Description

该任务负责明确 external gate 到底读取哪些对象、按什么决策语义做判断，以及不同 decision_type 对 target 字段的硬约束。它同时要冻结“gate 消费治理结论而不是重做业务语义评审”的边界，防止 gate 漂成新的业务黑盒。

## Acceptance Mapping

- FEAT-SRC-001-005 / AC-01: gate decision 必须互斥且可追溯。
- FEAT-SRC-001-005 / AC-03: run closure 与 follow-up dispatch 必须一致。

## Prerequisites

- FEAT-SRC-001-005 已冻结
- ADR-006 已作为当前决策来源引入

## Dependencies

- 无

## Inputs

- FEAT-SRC-001-005 对 decision、materialization 和 closure 的要求
- ADR-006 中 gate 输入标准、decision_type 与 target 约束矩阵
- 现有 governed skill candidate package 的最小共性结构

## Outputs

- external gate input contract
- decision_type 互斥规则
- approved_target / followup_target 约束矩阵

## Definition Of Done

- 输入契约覆盖 result summary、run state、proposal、evidence、retry budget、freeze readiness
- decision_type 明确包含 approve / revise / retry / handoff / reject
- target 字段约束矩阵可直接驱动 validator、review checklist 与 runtime 判断
- gate 不重做业务语义审查的边界写入 contract 与消费约束

## Observability

```yaml
execution_unit: task
log_scope: external-gate-contract-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - decision_type
  - approved_target
  - followup_target
  - package_ref
  - contract_ref
```

## Evidence Requirements

```yaml
required_refs:
  - FEAT-SRC-001-005
  - ADR-006
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - contracts/external_gate_input_contract.yaml
  - contracts/external_gate_decision_model.yaml
preconditions:
  - 先导出当前 gate-ready package 字段散点，避免回滚后丢失兼容对照
```
