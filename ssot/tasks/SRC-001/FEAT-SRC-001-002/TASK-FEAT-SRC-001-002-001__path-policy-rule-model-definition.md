---
id: TASK-FEAT-SRC-001-002-001
ssot_type: task
title: Path Policy 规则模型与 mode 边界定义
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260323
parent_id: FEAT-SRC-001-002
derived_from_ids:
  - id: FEAT-SRC-001-002
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-002#验收检查
  - EPIC-001#范围
  - SRC-001#治理变更摘要
owner: governance-engineer
tags: [path-policy, mode, governance]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: governance
  workstream: governance-policy
  responsible_role: governance-engineer
  priority: P0
  milestone: M1-Policy-Definition
  estimated_effort: 0.75 day
  lifecycle_status: frozen
  acceptance_criteria:
    - 允许根目录、禁止区域、命名规则与 artifact type 到目录映射已明确
    - `create/replace/patch/append/promote` 的适用边界与拒绝条件已明确
  definition_of_done:
    - Path Policy 规则模型冻结
    - 违规原因分类可被 Gateway 与 Auditor 复用
  inputs:
    - FEAT-SRC-001-002 acceptance checks
    - ADR-005 path governance constraints
  outputs:
    - path policy rule set
    - mode eligibility matrix
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

冻结 Path Policy 的规则模型和 mode 适用边界，作为路径合法性与覆盖权限的唯一政策源。

# Description

该任务把路径治理从 skill 局部习惯中抽离出来，明确受管 artifact 可以进入哪些根目录、哪些区域绝对禁止、命名和层级如何约束，以及不同 mode 在不同 artifact 类型上的允许与拒绝条件。输出必须足够精确，使 Gateway 和 Auditor 使用同一政策源而非各自解释。

## Acceptance Mapping

- FEAT-SRC-001-002 / AC-01: 非法路径必须被阻断，并返回明确违规原因。
- FEAT-SRC-001-002 / AC-02: mode 与 artifact 类型边界必须可判定。
- FEAT-SRC-001-002 / AC-03: Gateway 与 Auditor 使用同一政策源。

## Prerequisites

- FEAT-SRC-001-002 已冻结
- SRC-001 已冻结

## Dependencies

- 无

## Inputs

- FEAT-SRC-001-002 中关于目录、命名、mode 与政策唯一源的要求
- SRC-001 中关于统一路径治理与不得自由发明等价规则的约束
- ADR-005 中关于 Artifact IO Gateway 与 Path Policy 的治理对象

## Outputs

- Path Policy 规则集
- mode 适用边界矩阵
- 统一违规分类词表

## Definition Of Done

- 明确允许根目录、禁止区域、命名规则与层级边界
- 明确 `create/replace/patch/append/promote` 的允许条件、拒绝条件与失败原因
- 规则模型可被 Gateway 与 Auditor 同步引用
- 不存在依赖 skill 本地判断的隐式例外

## Observability

```yaml
execution_unit: task
log_scope: path-policy-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - artifact_type
  - target_root
  - mode
  - decision
  - violation_code
```

## Evidence Requirements

```yaml
required_refs:
  - FEAT-SRC-001-002
  - EPIC-001
  - SRC-001
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - policies/path_policy.yaml
  - policies/path_mode_matrix.yaml
preconditions:
  - 先记录现有路径写入散点规则，避免回滚后丢失兼容迁移线索
```
