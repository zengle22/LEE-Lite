---
id: TASK-FEAT-SRC-001-002-002
ssot_type: task
title: 路径与 mode 判定器实现
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
  - FEAT-SRC-001-001#依赖
  - FEAT-SRC-001-004#依赖
owner: runtime-engineer
tags: [path-policy, evaluator, runtime]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: implementation
  workstream: runtime-policy
  responsible_role: runtime-engineer
  priority: P0
  milestone: M2-Policy-Enforcement
  estimated_effort: 1.5 days
  lifecycle_status: frozen
  acceptance_criteria:
    - 路径判定与 mode 判定能输出统一 allow/deny 结果和违规原因
    - Gateway 与 Auditor 可以直接复用同一判定接口或结果对象
  definition_of_done:
    - 判定器实现完成
    - 非法路径、非法 mode、命名漂移三类场景有自动化验证
  inputs:
    - TASK-FEAT-SRC-001-002-001 policy rules
    - gateway requests
    - audit validation needs
  outputs:
    - path and mode evaluator
    - policy decision object
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

实现路径与 mode 判定器，把 Path Policy 规则转成 Gateway 与 Auditor 都可复用的硬判定能力。

# Description

该任务负责落地路径合法性、命名规则和 mode 边界的运行时判定，输出稳定的 allow/deny 结果对象、违规原因和 trace 字段。它不执行写入，只负责给正式链路提供唯一政策判定，避免 Gateway、Auditor 或各 skill 分别计算路径结论。

## Acceptance Mapping

- FEAT-SRC-001-002 / AC-01: 非法路径被阻断并返回明确原因。
- FEAT-SRC-001-002 / AC-02: mode 与 artifact 类型边界可判定。
- FEAT-SRC-001-002 / AC-03: Gateway 与 Auditor 使用同一政策源。

## Prerequisites

- TASK-FEAT-SRC-001-002-001 已冻结

## Dependencies

- TASK-FEAT-SRC-001-002-001

## Inputs

- Path Policy 规则集与 mode 边界矩阵
- Gateway 发起的 artifact 语义请求
- Auditor 对历史操作与路径结论的复核需要

## Outputs

- 路径与 mode 判定器
- 可序列化政策决策对象
- Gateway/Auditor 共用的违规分类结果

## Definition Of Done

- 判定器支持 root、path、name、mode、artifact type 的组合判断
- 输出对象包含 allow/deny、violation_code、policy_ref、explanation、trace fields
- Gateway 与 Auditor 均通过同一入口消费判定结果
- 自动化验证覆盖非法根目录、覆盖越界、命名漂移与 promote 误用

## Observability

```yaml
execution_unit: task
log_scope: path-mode-evaluator
audit_fields:
  - run_id
  - task_id
  - feat_id
  - target_path
  - artifact_type
  - mode
  - decision
  - violation_code
  - policy_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-002-001
  - FEAT-SRC-001-001
  - FEAT-SRC-001-004
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - src/runtime/path_policy_evaluator.py
  - src/runtime/path_mode_policy.py
fallback: 停用统一判定器，仅保留只读兼容检查；正式写入继续保持 fail-closed
```
