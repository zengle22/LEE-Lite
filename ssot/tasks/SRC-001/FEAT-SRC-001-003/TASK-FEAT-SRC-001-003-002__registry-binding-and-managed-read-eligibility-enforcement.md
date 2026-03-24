---
id: TASK-FEAT-SRC-001-003-002
ssot_type: task
title: Registry 绑定与受管读资格判定集成
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
  - FEAT-SRC-001-001#依赖
  - FEAT-SRC-001-004#依赖
owner: runtime-engineer
tags: [registry, read, integration]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: implementation
  workstream: runtime-implementation
  responsible_role: runtime-engineer
  priority: P0
  milestone: M2-Registry-Read-Eligibility
  estimated_effort: 1.25 days
  lifecycle_status: frozen
  implementation_chunks:
    - registry binding on commit/promote
    - formal reference resolution and read eligibility checks
    - unmanaged read denial and lineage/status trace exposure
  acceptance_criteria:
    - commit/promote 后完成 registry 登记并生成 registry-backed formal reference
    - 未注册文件在受管读取环节被拒绝
  definition_of_done:
    - registry binding 流程接入 Gateway
    - managed read path 基于 registry 做资格判定
  inputs:
    - TASK-FEAT-SRC-001-003-001 registry model
    - gateway runtime receipts
    - managed read requests
  outputs:
    - registry binding flow
    - managed read eligibility guard
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

把 Artifact Identity 与 Registry 模型接入正式执行链路，使 commit、promote 后的登记和受管读取资格判定都依赖 registry，而不是路径猜测。

# Description

该任务负责在 Gateway 完成合法写入后绑定 artifact identity、写入 registry 记录，并生成 registry-backed formal reference。同时它需要把未注册拒绝机制接入受管读取边界，明确职责分工：Gateway 提供读入口，Registry 负责“能不能作为正式对象被读取”的资格判定，Auditor 只消费结果并形成证据。

## Acceptance Mapping

- FEAT-SRC-001-003 / AC-01: 合法写入后的 managed artifact 能生成唯一身份并完成登记。
- FEAT-SRC-001-003 / AC-02: 未注册文件不得进入正式链路。
- FEAT-SRC-001-003 / AC-03: lineage、派生关系与正式状态可追溯。

## Prerequisites

- TASK-FEAT-SRC-001-003-001 已冻结
- TASK-FEAT-SRC-001-001-002 已具备 Gateway 执行入口

## Dependencies

- TASK-FEAT-SRC-001-001-002
- TASK-FEAT-SRC-001-003-001

## Inputs

- Artifact Identity 与 Registry 模型
- Gateway 成功回执和正式路径结果
- 受管读取对正式引用与资格判定的消费边界

## Outputs

- registry binding 流程
- registry-backed formal reference
- 未注册消费拒绝逻辑

## Implementation Chunks

- 在 commit/promote 后完成 registry binding，把合法写入晋升为正式登记对象。
- 提供 registry-backed formal reference 的解析与受管读资格判断。
- 在未注册或状态不合法时返回显式拒绝，并保留 lineage / status trace。

## Orthogonality Guardrails

- 本任务不负责提供读入口；读入口仍归 `TASK-FEAT-SRC-001-001-002` 的 Gateway surface。
- 本任务不负责审计阻断或 gate decision；Auditor 和 External Gate 只消费这里产出的资格判定结果与 formal reference。
- 本任务不承载 handoff materialization、job dispatch 或 run closure；这些职责归 `FEAT-SRC-001-005`。

## Definition Of Done

- commit/promote 路径触发 registry 登记
- managed read 通过 registry-backed formal reference 定位 artifact
- 未注册文件在受管读取时被拒绝
- lineage 信息可解释 patch、promote 与派生关系
- 读入口、资格判定和审计消费三者的职责边界已明确

## Observability

```yaml
execution_unit: task
log_scope: registry-read-eligibility
audit_fields:
  - run_id
  - task_id
  - feat_id
  - artifact_id
  - registry_ref
  - formal_read_ref
  - read_decision
  - lineage_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-001-002
  - TASK-FEAT-SRC-001-003-001
  - FEAT-SRC-001-004
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - src/runtime/artifact_registry_binding.py
  - src/runtime/managed_artifact_reference.py
  - src/runtime/managed_read_guard.py
fallback: 停用新 registry-backed read guard；受管读取保持 fail-closed，不回退为裸路径消费
```
