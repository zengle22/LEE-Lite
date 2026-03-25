---
id: IMPL-FEAT-SRC-001-003
ssot_type: IMPL
title: Formal Layering and Admission Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-feat-src-001-003
parent_id: FEAT-SRC-001-003
source_refs:
  - FEAT-SRC-001-003
  - ADR-014
  - ADR-006
  - ADR-005
  - ARCH-SRC-001-001
  - ARCH-SRC-001-003
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-003
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-003-20260325
properties:
  feat_ref: FEAT-SRC-001-003
  tech_ref: TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-003
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: false
  target_template_id: template.dev.feature_delivery_l2
---

# Formal Layering and Admission Implementation Task

## 1. 目标

实现 candidate/formal/downstream 三层对象、formal ref/lineage 解析以及 consumer admission，确保下游只能消费 formal layer。

本次实施不包含 gate decision 本身，不包含 Gateway/path policy 重定义。

## 2. 上游依赖

- `ADR-006`：formal object 必须在 gate 后产生
- `ARCH-SRC-001-003`：candidate layer / formal layer / admission checker 组件边界
- 上游 TECH：`TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-003`
- Gate 依赖：来自 `FEAT-SRC-001-002` 的 approve decision object

## 3. 实施范围

- 模块范围：
  - `cli/lib/protocol.py`
  - `cli/lib/lineage.py`
  - `cli/lib/admission.py`
  - `cli/lib/registry_store.py`
  - `cli/commands/registry/command.py`
- 工程范围：
  - formal ref resolve
  - lineage build/query
  - admission verdict
  - audit/read evidence
- 不在范围：
  - gate decision 语义
  - artifact commit / governed IO

## 4. 实施步骤

### Step 1

补 `CandidateRef / FormalRef / AdmissionRequest / AdmissionVerdict` 协议结构。

完成条件：formal / candidate / downstream 层级可机器识别。

### Step 2

实现 `cli/lib/lineage.py`，支撑 lineage 建立、formal ref 解析和 authoritative ref 查询。

完成条件：任意 consumer 请求都能先 resolve authoritative formal ref。

### Step 3

实现 `cli/lib/admission.py`。

完成条件：consumer 读取前必须经过 admission checker。

### Step 4

实现 registry command 侧 `resolve-formal-ref / validate-admission`。

完成条件：CLI 和 runtime 都能统一消费同一 admission contract。

## 5. 风险与阻塞

- 如果 formal ref 和 managed ref 混用，下游 consumer 仍会偷偷依赖路径。
- lineage 缺失时必须 fail closed，否则 candidate/formal 边界会塌。
- 若 gate publish 未提供稳定 `formal_ref`，admission 无法完整落地。

## 6. 交付物

- 代码：
  - `cli/lib/lineage.py`
  - `cli/lib/admission.py`
  - registry command 扩展
- 测试：
  - resolve-formal-ref happy path
  - admission allow
  - `lineage_missing`
  - `layer_violation`
- 证据：
  - admission verdict evidence
  - read traceability evidence

## 7. 验收检查点

- consumer 不得直接读取 candidate layer。
- `lineage_missing` 时必须 deny，不得路径猜测放行。
- admission 只能基于 formal ref / lineage，不得基于目录邻近关系。
- gate 输出的 approve decision 是 formal publication 的唯一前置。

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 不适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- supporting refs:
  - `TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-003`
  - `ARCH-SRC-001-003`
