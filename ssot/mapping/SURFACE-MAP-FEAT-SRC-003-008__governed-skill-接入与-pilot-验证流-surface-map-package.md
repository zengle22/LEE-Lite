---
id: SURFACE-MAP-FEAT-SRC-003-008
ssot_type: SURFACE_MAP
surface_map_ref: SURFACE-MAP-FEAT-SRC-003-008
feat_ref: FEAT-SRC-003-008
title: Surface Map for governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-surface-map
workflow_run_id: src003-adr042-bootstrap-20260407-r2
design_impact_required: true
owner_binding_status: bound
related_owner_refs:
  - ARCH-EXECUTION-RUNNER-CORE
  - API-EXECUTION-RUNNER
  - TECH-SRC-003-008
source_refs:
  - product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
  - FEAT-SRC-003-008
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
# Surface Map Bundle for governed skill 接入与 pilot 验证流

## Selected FEAT

- feat_ref: FEAT-SRC-003-008
- title: governed skill 接入与 pilot 验证流
- goal: 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- scope: 定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。, 定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。, 定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。

## Design Impact

- design_impact_required: true
- owner_binding_status: bound
- bypass_rationale: 

## Surface Map

### Architecture
- owner: ARCH-EXECUTION-RUNNER-CORE
  - action: update
  - scope: governed_skill_integration_boundary
  - reason: governed skill 接入与 pilot 验证流属于 execution runner 的集成边界扩展。

### Api
- owner: API-EXECUTION-RUNNER
  - action: update
  - scope: governed_skill_binding_contract, pilot_validation_contract
  - reason: 接入 governed skill 需要扩展 skill binding 与 pilot 验证契约。

### Ui
[none]

### Prototype
[none]

### Tech
- owner: TECH-SRC-003-008
  - action: create
  - create_signals: new reusable implementation strategy package, future multi-feat reuse
  - scope: governed_skill_registry_strategy, pilot_validation_rules
  - reason: governed skill 接入需要独立实现策略来处理 registry 绑定与 pilot 校验。

## Ownership Summary

- architecture: ARCH-EXECUTION-RUNNER-CORE (update)
- api: API-EXECUTION-RUNNER (update)
- tech: TECH-SRC-003-008 (create)

## Create Justification

- tech: TECH-SRC-003-008 -> governed skill 接入需要独立实现策略来处理 registry 绑定与 pilot 校验。 | signals: new reusable implementation strategy package, future multi-feat reuse

## Downstream Handoff

- target_workflows: workflow.dev.feat_to_tech, workflow.dev.feat_to_proto, workflow.dev.proto_to_ui, workflow.dev.tech_to_impl
- surface_map_ref: SURFACE-MAP-FEAT-SRC-003-008
- feat_ref: FEAT-SRC-003-008

## Traceability

- product.epic-to-feat::src003-adr042-bootstrap-20260407-r2
- FEAT-SRC-003-008
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
