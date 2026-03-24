---
id: TASK-FEAT-SRC-001-001-002
ssot_type: task
title: Gateway 运行时执行与正式操作收口实现
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
  - FEAT-SRC-001-002#验收检查
  - FEAT-SRC-001-003#验收检查
owner: runtime-engineer
tags: [gateway, runtime, enforcement]
properties:
  epic_ref: EPIC-001
  src_root_id: src-root-src-001
  task_kind: implementation
  workstream: runtime-implementation
  responsible_role: runtime-engineer
  priority: P0
  milestone: M2-Gateway-Runtime
  estimated_effort: 1.5 days
  lifecycle_status: frozen
  implementation_chunks:
    - gateway request normalization and operation dispatch
    - policy/registry invocation and receipt assembly
    - fail-closed write blocking and staging evidence retention
  acceptance_criteria:
    - 正式读写请求通过 Gateway 执行，且不得静默回退为自由路径写入
    - Gateway 能调用 Path Policy 与 Registry 依赖并输出统一回执
  definition_of_done:
    - Gateway 运行时入口完成
    - 失败保留 staging 或 error evidence，未出现 direct write fallback
  inputs:
    - TASK-FEAT-SRC-001-001-001 gateway contract
    - FEAT-SRC-001-002 policy decisions
    - FEAT-SRC-001-003 registry binding requirements
  outputs:
    - gateway runtime entrypoints
    - operation receipts and failure evidence
frozen_at: '2026-03-23T15:10:00+08:00'
---

# Objective

实现 Gateway 运行时入口，把正式 artifact 的读写、提交、晋升与 run-log 追加统一收口到受管执行链路。

# Description

该任务将 `TASK-FEAT-SRC-001-001-001` 冻结的操作契约转成真实运行时能力，并接入 Path Policy 与 Registry 的判定结果。核心要求是正式操作只能走 Gateway；一旦路径、mode 或身份绑定失败，系统只能保留 staging 或错误证据，不得回退到 skill 直接写路径。

## Acceptance Mapping

- FEAT-SRC-001-001 / AC-01: 正式写入经由 Gateway，并输出标准化操作回执。
- FEAT-SRC-001-001 / AC-02: Gateway 失败时不得回退为自由写入。
- FEAT-SRC-001-001 / AC-03: 下游可继承统一操作面。

## Prerequisites

- FEAT-SRC-001-001 已冻结
- TASK-FEAT-SRC-001-001-001 已冻结

## Dependencies

- TASK-FEAT-SRC-001-001-001
- TASK-FEAT-SRC-001-002-002
- TASK-FEAT-SRC-001-003-002

## Inputs

- Gateway 操作契约与回执模型
- Path Policy 的合法性与 mode 判定结果
- Registry 的 identity 与登记接口

## Outputs

- Gateway 运行时入口实现
- 正式操作执行结果与失败证据
- 面向下游 workflow/skill 的统一调用面

## Implementation Chunks

- 收口 Gateway 请求归一化与操作分发，只负责把正式读写语义落到统一入口。
- 接入 Path Policy 与 Registry，组装标准化成功/拒绝/失败回执。
- 实现 fail-closed 保护：失败时保留 staging 或 error evidence，不允许 direct write fallback。

## Orthogonality Guardrails

- 本任务是 Gateway 入口与正式操作编排层，不负责决定 artifact 是否具备正式读取资格；该判断归 `TASK-FEAT-SRC-001-003-002`。
- 本任务可以调用 registry binding / read guard，但不得在 Gateway 内重写 registry identity 规则、formal reference 解析或 registry-backed read eligibility。
- 本任务输出的是操作结果与回执，不替代审计消费、gate decision 或 run closure。

## Definition Of Done

- 正式 `read/write/commit/promote/append_run_log` 均由 Gateway 入口执行
- 路径、mode、registry 失败时输出结构化失败回执
- direct path write 旁路被阻断或转化为显式错误
- 基础集成测试覆盖成功、拒绝、失败三种路径

## Observability

```yaml
execution_unit: task
log_scope: gateway-runtime-execution
audit_fields:
  - run_id
  - task_id
  - feat_id
  - operation
  - request_ref
  - policy_decision
  - registry_ref
  - staging_ref
  - receipt_ref
```

## Evidence Requirements

```yaml
required_refs:
  - TASK-FEAT-SRC-001-001-001
  - TASK-FEAT-SRC-001-002-002
  - TASK-FEAT-SRC-001-003-002
review_required: true
```

## Rollback Strategy

```yaml
mode: feature-flag
restore_targets:
  - src/runtime/managed_artifact_gateway.py
  - src/runtime/managed_artifact_operations.py
fallback: 禁用 Gateway 收口，只保留兼容读路径；写路径禁止自动放开
```
