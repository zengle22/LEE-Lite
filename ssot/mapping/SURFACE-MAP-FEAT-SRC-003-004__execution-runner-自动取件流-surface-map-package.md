---
id: SURFACE-MAP-FEAT-SRC-003-004
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-004
feat_ref: FEAT-SRC-003-004
title: Surface Map for Execution Runner 自动取件流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - TECH-SRC-003-004
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-004
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
# Surface Map Bundle for Execution Runner 自动取件流

## Selected FEAT

- feat_ref: FEAT-SRC-003-004
- title: Execution Runner 自动取件流
- goal: 冻结 Execution Loop Job Runner 如何从 ready queue 自动取件、claim job 并进入 running，而不是继续依赖第三会话人工接力。
- scope: 定义 runner 扫描、claim、running 和防重入边界。, 定义 jobs/ready 到 runner ownership 的状态转移。, 定义 runner 对 job lineage、claim 证据和并发责任的记录方式。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: runner_intake_loop
  - reason: 自动取件流是 execution runner 核心循环的一部分。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: ready_job_intake_contract
  - reason: 自动取件需要复用 ready job intake 读写契约。

### Ui
[none]

### Prototype
[none]

### Tech
- owner: TECH-SRC-003-004
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: intake_polling_rules, queue_claiming_strategy
  - reason: 自动取件需要单独冻结轮询、claim 与去重策略。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- tech: TECH-SRC-003-004 (create)

## Create Justification

- tech: TECH-SRC-003-004 -> 自动取件需要单独冻结轮询、claim 与去重策略。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-004
- feat_ref: FEAT-SRC-003-004

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-004
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
