---
id: SURFACE-MAP-FEAT-SRC-003-007
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-007
feat_ref: FEAT-SRC-003-007
title: Surface Map for Runner 运行监控流
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
  - TECH-SRC-003-007
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-007
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
# Surface Map Bundle for Runner 运行监控流

## Selected FEAT

- feat_ref: FEAT-SRC-003-007
- title: Runner 运行监控流
- goal: 冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。
- scope: 定义 monitor surface：runner observability surface。, 定义 ready backlog、running jobs、failed jobs、deadletters、waiting-human jobs 的最小可见集合。, 定义监控面如何服务 operator 判断继续运行、恢复还是人工介入。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: runner_observability_boundary
  - reason: 运行监控流属于 execution runner 主架构的观测面扩展。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: runner_metrics_projection, runner_incident_queries
  - reason: 运行监控需要扩展 runner 指标投影与事件查询契约。

### Ui
- owner: UI-RUNNER-OPERATOR-SHELL
  - action: update
  - scope: runner_monitoring_panel, incident_overview_card
  - reason: 运行监控是既有 runner operator shell 上的观测面增量。

### Prototype
- owner: PROTO-RUNNER-OPERATOR-MAIN
  - action: update
  - scope: runner_monitoring_flow
  - reason: 运行监控流程是在已有 runner operator 主流程上的扩展。

### Tech
- owner: TECH-SRC-003-007
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: monitoring_snapshot_rules, incident_summary_strategy
  - reason: 运行监控需要独立实现策略来汇总 runner 状态与异常视图。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- ui: UI-RUNNER-OPERATOR-SHELL (update)
- prototype: PROTO-RUNNER-OPERATOR-MAIN (update)
- tech: TECH-SRC-003-007 (create)

## Create Justification

- tech: TECH-SRC-003-007 -> 运行监控需要独立实现策略来汇总 runner 状态与异常视图。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-007
- feat_ref: FEAT-SRC-003-007

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-007
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
