---
id: SURFACE-MAP-FEAT-SRC-003-002
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-002
feat_ref: FEAT-SRC-003-002
title: Surface Map for Runner 用户入口流
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
  - TECH-SRC-003-002
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-002
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
# Surface Map Bundle for Runner 用户入口流

## Selected FEAT

- feat_ref: FEAT-SRC-003-002
- title: Runner 用户入口流
- goal: 冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。
- scope: 定义独立 skill 入口：Execution Loop Job Runner。, 定义入口 skill 的最小输入、启动时机和与 ready queue 的绑定边界。, 定义 operator 通过入口 skill 触发 runner 的责任，而不是继续依赖人工接力或隐式后台。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: runner_operator_entry_boundary
  - reason: runner 用户入口流属于 execution runner 主架构的操作入口扩展。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: runner_entry_invocation_contract
  - reason: runner 用户入口需要沿用并扩展 execution runner 调用契约。

### Ui
- owner: UI-RUNNER-OPERATOR-SHELL
  - action: create
  - create_signals: new independent UI shell or panel family, future multi-feat reuse
  - scope: runner_entry_panel, entry_cta_cluster
  - reason: 需要新增 runner 操作入口可视壳层，供后续控制面和监控面复用。

### Prototype
- owner: PROTO-RUNNER-OPERATOR-MAIN
  - action: create
  - create_signals: new independent main flow skeleton, future multi-feat reuse
  - scope: runner_entry_flow
  - reason: 需要定义 runner 用户入口主流程原型，作为 UI 壳层的体验骨架。

### Tech
- owner: TECH-SRC-003-002
  - action: update
  - scope: runner_entry_strategy, operator_prompt_resolution
  - reason: 已有 TECH-SRC-003-002 需按 ADR042 继续承接 runner 用户入口实现策略。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- ui: UI-RUNNER-OPERATOR-SHELL (create)
- prototype: PROTO-RUNNER-OPERATOR-MAIN (create)
- tech: TECH-SRC-003-002 (update)

## Create Justification

- ui: UI-RUNNER-OPERATOR-SHELL -> 需要新增 runner 操作入口可视壳层，供后续控制面和监控面复用。 | signals: new independent UI shell or panel family, future multi-feat reuse
- prototype: PROTO-RUNNER-OPERATOR-MAIN -> 需要定义 runner 用户入口主流程原型，作为 UI 壳层的体验骨架。 | signals: new independent main flow skeleton, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-002
- feat_ref: FEAT-SRC-003-002

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-002
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
