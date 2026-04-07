---
id: SURFACE-MAP-FEAT-SRC-003-001
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-001
feat_ref: FEAT-SRC-003-001
title: Surface Map for 批准后 Ready Job 生成流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - TECH-SRC-003-001
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-001
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
# Surface Map Bundle for 批准后 Ready Job 生成流

## Selected FEAT

- feat_ref: FEAT-SRC-003-001
- title: 批准后 Ready Job 生成流
- goal: 冻结 gate approve 如何生成 ready execution job，并把 approve 继续绑定到自动推进而不是 formal publication。
- scope: 定义 approve 后必须产出的 ready execution job 及其最小字段。, 定义 ready job 的 authoritative refs、next skill target 和队列落点。, 定义 revise / retry / reject / handoff 与 ready job 生成的边界，避免 approve 语义漂移。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: create
  - create_signals: new long-lived owner, new subsystem boundary
  - scope: approve_to_ready_job_transition, ready_job_authority_boundary
  - reason: SRC-003 首次定义 execution runner 的 approve-to-ready-job 主边界。

### Api
- owner: API-EXECUTION-RUNNER
  - action: create
  - create_signals: new service or contract family, future multi-feat reuse
  - scope: ready_job_emission_contract
  - reason: 需要新增 ready execution job 的出件契约与 authoritative refs。

### Ui
[none]

### Prototype
[none]

### Tech
- owner: TECH-SRC-003-001
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: ready_job_generation_rules, approve_dispatch_persistence
  - reason: 需要单独冻结 approve 后 ready job 生成规则与落盘策略。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (create)
- api: API-EXECUTION-RUNNER (create)
- tech: TECH-SRC-003-001 (create)

## Create Justification

- architecture: ARCH-EXECUTION-RUNNER-CORE -> SRC-003 首次定义 execution runner 的 approve-to-ready-job 主边界。 | signals: new long-lived owner, new subsystem boundary
- api: API-EXECUTION-RUNNER -> 需要新增 ready execution job 的出件契约与 authoritative refs。 | signals: new service or contract family, future multi-feat reuse
- tech: TECH-SRC-003-001 -> 需要单独冻结 approve 后 ready job 生成规则与落盘策略。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-001
- feat_ref: FEAT-SRC-003-001

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-001
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
