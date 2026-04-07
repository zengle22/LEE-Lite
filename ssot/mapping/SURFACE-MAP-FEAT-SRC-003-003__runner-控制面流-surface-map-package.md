---
id: SURFACE-MAP-FEAT-SRC-003-003
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-003
feat_ref: FEAT-SRC-003-003
title: Surface Map for Runner 控制面流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - UI-RUNNER-OPERATOR-SHELL
  - PROTO-RUNNER-OPERATOR-MAIN
  - TECH-SRC-003-003
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-003
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
# Surface Map Bundle for Runner 控制面流

## Selected FEAT

- feat_ref: FEAT-SRC-003-003
- title: Runner 控制面流
- goal: 冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。
- scope: 定义 CLI control surface：ll loop run-execution、ll job claim、ll job run、ll job complete、ll job fail。, 定义各控制命令与 runner lifecycle / job lifecycle 的映射关系。, 定义控制面输出的结构化状态，而不是把操作结果留成隐式终端副作用。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: runner_control_surface_boundary
  - reason: runner 控制面流属于 execution runner 主架构的控制面扩展。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: runner_control_commands, runner_status_projection
  - reason: 控制面需要复用并扩展 runner 控制命令与状态投影契约。

### Ui
- owner: UI-RUNNER-OPERATOR-SHELL
  - action: update
  - scope: runner_control_panel, decision_controls
  - reason: 控制面是既有 runner operator shell 上的增量面板。

### Prototype
- owner: PROTO-RUNNER-OPERATOR-MAIN
  - action: update
  - scope: runner_control_flow
  - reason: 控制面流程是在已有 runner operator 主流程上的扩展。

### Tech
- owner: TECH-SRC-003-003
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: control_surface_state_machine, manual_override_rules
  - reason: 控制面需要独立实现策略包来约束状态切换与人工干预。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- ui: UI-RUNNER-OPERATOR-SHELL (update)
- prototype: PROTO-RUNNER-OPERATOR-MAIN (update)
- tech: TECH-SRC-003-003 (create)

## Create Justification

- tech: TECH-SRC-003-003 -> 控制面需要独立实现策略包来约束状态切换与人工干预。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-003
- feat_ref: FEAT-SRC-003-003

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-003
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
