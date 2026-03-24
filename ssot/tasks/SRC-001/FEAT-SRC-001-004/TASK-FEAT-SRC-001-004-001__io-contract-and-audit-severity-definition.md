---
id: TASK-FEAT-SRC-001-004-001
ssot_type: task
title: IO Contract 与审计分级模型定义
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260323
parent_id: FEAT-SRC-001-004
derived_from_ids:
  - id: FEAT-SRC-001-004
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-004#验收检查
  - EPIC-001#验收形态
  - SRC-001#关键约束
owner: contract-architect
tags: [io-contract, audit, severity]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: specification
  workstream: contract-specification
  responsible_role: contract-architect
  priority: P1
  milestone: M1-Audit-Definition
  estimated_effort: 0.75 day
  lifecycle_status: frozen
  acceptance_criteria:
    - IO Contract 的 artifact scope、path scope、operation scope 与 staging 晋升边界已明确
    - blocker/warn/info 分级与证据字段已明确，可支持 gate 和 repair 消费
  definition_of_done:
    - IO Contract schema 冻结
    - audit finding schema 与 severity vocabulary 冻结
  inputs:
    - FEAT-SRC-001-004 acceptance checks
    - FEAT-SRC-001-001/002/003 runtime evidence needs
  outputs:
    - io contract schema
    - audit finding schema and severity model
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

冻结 IO Contract 的声明边界与审计 finding 分级模型，使运行期违规能够被结构化识别、阻断和修补。

# Description

该任务负责定义 audit 系统要拿什么做比较、违规结果长什么样，以及不同严重等级如何进入 gate、repair 与监督链路。它需要把 artifact scope、path scope、operation scope、staging 晋升规则和 finding 结构一起冻结，确保后续 auditor 的输出不是自然语言报告，而是可执行证据对象。

## Acceptance Mapping

- FEAT-SRC-001-004 / AC-01: 越权写入必须可见并有违规等级。
- FEAT-SRC-001-004 / AC-02: 未注册 artifact 消费必须被识别并可阻断。
- FEAT-SRC-001-004 / AC-03: 审计结果必须能驱动修补。

## Prerequisites

- FEAT-SRC-001-004 已冻结
- SRC-001 已冻结

## Dependencies

- 无

## Inputs

- FEAT-SRC-001-004 对 contract scope、违规分级和 repair 可消费性的要求
- FEAT-SRC-001-001/002/003 提供的操作、政策和 registry 追溯边界
- EPIC-001 的验收形态与 QA seed 期待

## Outputs

- IO Contract schema
- Audit finding schema
- Severity vocabulary 与 repair targeting 字段定义

## Definition Of Done

- IO Contract 覆盖 artifact scope、path scope、operation scope、staging promotion
- finding 覆盖 object_ref、violation_type、severity、evidence_refs、repair_scope
- blocker/warn/info 分级与 gate/repair/supervision 消费边界清晰
- 未注册消费、越界写入、命名漂移、旁路写入等核心违规可表达

## Observability

```yaml
execution_unit: task
log_scope: audit-contract-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - contract_ref
  - violation_type
  - severity
  - evidence_ref
  - repair_scope
```

## Evidence Requirements

```yaml
required_refs:
  - FEAT-SRC-001-004
  - EPIC-001
  - SRC-001
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - contracts/io_contract_schema.yaml
  - contracts/audit_finding_schema.yaml
preconditions:
  - 先保留历史 audit 输出样式，方便回滚后做兼容比对
```
