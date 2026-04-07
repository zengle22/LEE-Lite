---
id: SURFACE-MAP-FEAT-SRC-003-006
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-006
feat_ref: FEAT-SRC-003-006
title: Surface Map for 执行结果回写与重试边界流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - TECH-SRC-003-006
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-006
  - product.src-to-epic::adr018-src2epic-lineage-20260326-r1
  - EPIC-SRC-003-001
  - SRC-003
  - product.raw-to-src::adr018-raw2src-restart-20260326-r1
  - ADR-018
  - ADR-001
  - ADR-003
  - ADR-005
  - ADR-006
  - ADR-009
---
# Surface Map Bundle for 执行结果回写与重试边界流

## Selected FEAT

- feat_ref: FEAT-SRC-003-006
- title: 执行结果回写与重试边界流
- goal: 冻结 runner 执行后的 done / failed / retry-reentry 结果，让自动推进链在下一跳后仍可审计、可回流。
- scope: 定义 execution result、failure reason 和 retry / reentry directive 的 authoritative 结果。, 定义 job 从 running 进入 done / failed / retry_return 的状态边界。, 定义 runner 输出如何服务上游审计、下游继续推进和失败恢复。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: feedback_and_retry_boundary
  - reason: 执行结果回写与重试边界属于 execution runner 核心闭环的一部分。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: execution_feedback_contract, retry_state_contract
  - reason: 结果回写与重试需要扩展执行反馈与 retry 契约。

### Ui
[none]

### Prototype
[none]

### Tech
- owner: TECH-SRC-003-006
  - action: update
  - scope: result_writeback_rules, retry_boundary_strategy
  - reason: 已有 TECH-SRC-003-006 需按 ADR042 继续承接回写与重试边界实现策略。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- tech: TECH-SRC-003-006 (update)

## Create Justification

- [none]

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-006
- feat_ref: FEAT-SRC-003-006

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-006
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- EPIC-SRC-003-001
- SRC-003
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
