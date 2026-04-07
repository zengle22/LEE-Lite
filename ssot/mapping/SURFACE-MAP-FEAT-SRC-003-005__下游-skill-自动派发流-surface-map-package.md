---
id: SURFACE-MAP-FEAT-SRC-003-005
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-005
feat_ref: FEAT-SRC-003-005
title: Surface Map for 下游 Skill 自动派发流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - TECH-SRC-003-005
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-005
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
# Surface Map Bundle for 下游 Skill 自动派发流

## Selected FEAT

- feat_ref: FEAT-SRC-003-005
- title: 下游 Skill 自动派发流
- goal: 冻结 claimed execution job 如何自动派发到下一个 governed skill，并保持 authoritative input / target skill / execution intent 一致。
- scope: 定义 next skill target、输入包引用和调用边界。, 定义 runner 把 claimed job 交给下游 skill 时的 authoritative invocation 记录。, 定义执行启动失败时如何回写 runner 结果而不是静默丢失。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: downstream_dispatch_boundary
  - reason: 自动派发流是 execution runner 的下游派发边界扩展。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: skill_dispatch_contract
  - reason: 下游 skill 自动派发需要扩展 dispatch 契约与 next skill binding。

### Ui
[none]

### Prototype
[none]

### Tech
- owner: TECH-SRC-003-005
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: dispatch_routing_rules, skill_resolution_strategy
  - reason: 自动派发需要单独的路由与 skill 解析实现策略。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- tech: TECH-SRC-003-005 (create)

## Create Justification

- tech: TECH-SRC-003-005 -> 自动派发需要单独的路由与 skill 解析实现策略。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-005
- feat_ref: FEAT-SRC-003-005

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-005
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
