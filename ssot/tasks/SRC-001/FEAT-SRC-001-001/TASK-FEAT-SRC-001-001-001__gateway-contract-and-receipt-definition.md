---
id: TASK-FEAT-SRC-001-001-001
ssot_type: task
title: Gateway 操作契约与回执模型定义
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260323
parent_id: FEAT-SRC-001-001
derived_from_ids:
  - id: FEAT-SRC-001-001
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-001#验收检查
  - EPIC-001#范围
  - SRC-001#关键约束
owner: contract-architect
tags: [gateway, contract, receipt]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: specification
  workstream: contract-specification
  responsible_role: contract-architect
  priority: P0
  milestone: M1-Gateway-Contract
  estimated_effort: 0.5 day
  lifecycle_status: frozen
  acceptance_criteria:
    - 定义 `read_artifact`、`write_artifact`、`commit_artifact`、`promote_artifact`、`append_run_log` 的统一输入输出语义
    - Gateway 成功、拒绝、失败三类回执可被下游 handoff、gate 与 auditor 直接消费
  definition_of_done:
    - Gateway 操作契约与回执字段边界冻结
    - 错误码、拒绝原因和 trace 字段已明确
  inputs:
    - FEAT-SRC-001-001 acceptance checks
    - SRC-001 governance bridge constraints
  outputs:
    - managed gateway operation contract
    - managed gateway receipt schema
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

冻结 Managed Artifact Gateway 的统一操作契约与标准化回执模型，作为所有正式 artifact 读写入口的唯一规范源。

# Description

该任务负责把 Gateway 的能力面收敛成可执行契约，明确调用方必须提交的 artifact 语义字段、mode、source refs、上下文信息，以及 Gateway 成功、拒绝、失败三类结果的字段结构。目标不是实现运行时逻辑，而是先把操作入口和回执对象冻结成共同依赖，避免后续实现与审计各自解释。

## Acceptance Mapping

- FEAT-SRC-001-001 / AC-01: 正式写入必须经由 Gateway，且结果返回标准化操作回执。
- FEAT-SRC-001-001 / AC-03: 下游 skill 可复用统一操作面，而不是各自再发明等价接口。

## Prerequisites

- FEAT-SRC-001-001 已冻结
- SRC-001 已冻结

## Dependencies

- 无

## Inputs

- FEAT-SRC-001-001 中 Gateway 操作入口、失败边界与回执要求
- SRC-001 中关于统一治理、不得自由写入和必须继承统一入口的约束
- EPIC-001 中关于受管能力底座的边界定义

## Outputs

- Gateway 操作契约字段清单
- 标准回执结构与失败原因分类
- 供运行时实现、审计和 handoff 复用的 trace anchors

## Definition Of Done

- 操作契约覆盖 `read_artifact`、`write_artifact`、`commit_artifact`、`promote_artifact`、`append_run_log`
- 回执字段包含 operation、artifact identity、decision、path result、registry refs、evidence refs
- 拒绝和失败场景的错误分类可直接被 Gateway、auditor、gate 消费
- 契约明确 Gateway 不负责替代 Path Policy 与 Registry 的职责

## Observability

```yaml
execution_unit: task
log_scope: gateway-contract-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - operation
  - artifact_type
  - logical_name
  - decision
  - receipt_ref
  - evidence_refs
```

## Evidence Requirements

```yaml
required_refs:
  - FEAT-SRC-001-001
  - EPIC-001
  - SRC-001
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - contracts/managed_artifact_gateway_contract.yaml
  - contracts/managed_artifact_gateway_receipt.yaml
preconditions:
  - 先保留当前 skill 内部直写入口与调用点清单，避免回滚后遗失兼容信息
```
