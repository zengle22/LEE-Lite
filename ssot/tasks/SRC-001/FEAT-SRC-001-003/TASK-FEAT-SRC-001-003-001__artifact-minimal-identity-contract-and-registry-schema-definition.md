---
id: TASK-FEAT-SRC-001-003-001
ssot_type: task
title: Artifact 最小 Identity Contract 与 Registry Schema 定义
status: frozen
version: v1
workflow_instance_id: manual-feat-to-delivery-prep-epic-001-20260323
parent_id: FEAT-SRC-001-003
derived_from_ids:
  - id: FEAT-SRC-001-003
    version: v1
    required: true
source_refs:
  - FEAT-SRC-001-003#验收检查
  - EPIC-001#范围
  - SRC-001#Bridge Context
owner: contract-architect
tags: [registry, identity, contract]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: specification
  workstream: contract-specification
  responsible_role: contract-architect
  priority: P0
  milestone: M1-Identity-Registry-Definition
  estimated_effort: 0.75 day
  lifecycle_status: frozen
  acceptance_criteria:
    - managed artifact 的最小 identity contract 与唯一性边界已明确
    - registry 核心字段与最小 lineage 指针已明确
  definition_of_done:
    - minimal identity contract 冻结
    - registry record schema 冻结
  inputs:
    - FEAT-SRC-001-003 acceptance checks
    - SRC-001 identity and registry constraints
  outputs:
    - artifact minimal identity schema
    - registry record schema
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

冻结 managed artifact 的最小 identity contract、registry 记录结构与最小 lineage 表达方式，作为正式引用与读取资格判定的共同真相源。

# Description

该任务定义 artifact 如何从“一个文件”转化为“一个可受管消费的正式对象”。它需要先冻结最小 identity contract，明确哪些字段足以判断“这是哪个正式 artifact”；然后冻结 registry 必填字段、最小 lineage 指针与 formal reference 的最小形态。该任务不承载 handoff materialization，只负责 registry 侧的规范源。

## Acceptance Mapping

- FEAT-SRC-001-003 / AC-01: 正式 artifact 必须可登记为唯一身份。
- FEAT-SRC-001-003 / AC-02: 未注册文件不得进入正式链路。
- FEAT-SRC-001-003 / AC-03: lineage 必须可追溯。

## Prerequisites

- FEAT-SRC-001-003 已冻结
- SRC-001 已冻结

## Dependencies

- 无

## Inputs

- FEAT-SRC-001-003 的最小 identity、registry 与最小 lineage 要求
- SRC-001 的治理对象与下游继承约束
- EPIC-001 对受管 artifact 身份与登记的建设边界

## Outputs

- Artifact Minimal Identity schema
- Registry record schema
- Registry-backed formal reference 与 lineage 锚点定义

## Definition Of Done

- minimal identity contract 明确包含 artifact type、logical name、stage、producer scope 与唯一性边界
- registry 记录字段覆盖 path、producer run、inputs、status、source refs、lineage pointers、evidence refs
- registry-backed formal reference 的最小读取形态已定义
- patch、promote、derived artifact 的直接 lineage 表达方式可直接复用

## Observability

```yaml
execution_unit: task
log_scope: registry-model-definition
audit_fields:
  - run_id
  - task_id
  - feat_id
  - artifact_id
  - artifact_type
  - stage
  - lineage_ref
  - registry_schema_ref
```

## Evidence Requirements

```yaml
required_refs:
  - FEAT-SRC-001-003
  - EPIC-001
  - SRC-001
review_required: true
```

## Rollback Strategy

```yaml
mode: revert
restore_targets:
  - contracts/artifact_minimal_identity_schema.yaml
  - contracts/artifact_registry_record.yaml
preconditions:
  - 先导出现有 artifact 引用与 path 绑定散点，避免回滚后丢失迁移对照
```
