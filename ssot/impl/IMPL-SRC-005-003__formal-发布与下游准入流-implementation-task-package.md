---
id: IMPL-SRC-005-003
ssot_type: IMPL
impl_ref: IMPL-SRC-005-003
tech_ref: TECH-SRC-005-003
feat_ref: FEAT-SRC-005-003
title: formal 发布与下游准入流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-003--tech-src-005-003
candidate_package_ref: artifacts/tech-to-impl/adr011-raw2src-fix-20260327-r1--feat-src-005-003--tech-src-005-003
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-adr011-raw2src-fix-20260327-r1--feat-src-005-003--tech-src-005-003-impl-bundle-decision.json
frozen_at: '2026-03-30T03:34:55Z'
---

# formal 发布与下游准入流 Implementation Task Package

## Selected Upstream

- feat_ref: `FEAT-SRC-005-003`
- tech_ref: `TECH-SRC-005-003`
- arch_ref: `ARCH-SRC-005-003`
- api_ref: `API-SRC-005-003`
- title: formal 发布与下游准入流
- goal: 冻结 approved decision 之后如何形成 formal output、formal ref 与 lineage，并让下游只通过正式准入链消费。

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: 发布, gate, io, path.
- migration_required: False
  - No migration, cutover, rollback, or compat-mode surface was detected.

## Implementation Task

- 1. Freeze upstream refs and touch set: The implementation entry references frozen upstream objects only and the concrete file/module touch set is explicit.
- 2. Implement frozen runtime units: The listed units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.
- 3. Integrate, evidence, and handoff: The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.

## Integration Plan

- 调用方：downstream consumer 在正式读取前调用 admission checker；registry 负责提供 formal refs 与 lineage。
- 挂接点：file-handoff 完成后先 resolve formal refs，再决定 consumer admission。
- 旧系统兼容：现有路径猜测读取必须逐步迁移到 formal-ref based access，兼容模式只允许只读告警，不允许默认放行。
- Boundary to 正式交接与物化能力: 本 FEAT 从 approved decision 之后开始，定义 formal publication package 和 downstream admission，而不是定义 gate 审核动作本身。
- Boundary to 主链文件 IO 与路径治理能力: 本 FEAT 定义对象资格与引用方向，path / mode 规则留给 IO 治理 FEAT。
- 按已冻结主时序接线：1. normalize requested ref and consumer identity; 2. resolve lineage and authoritative formal ref; 3. verify requested layer and consumer eligibility。

## Evidence Plan

- AC-001: backend-verification, smoke-review-input
- AC-002: backend-verification, smoke-review-input
- AC-003: backend-verification, smoke-review-input

## Smoke Gate Subject

- See `smoke-gate-subject.json` for the current `status`, `decision`, and `ready_for_execution` state.

## Delivery Handoff

- target_template_id: `template.dev.feature_delivery_l2`
- primary_artifact_ref: `impl-bundle.json`
- phase_inputs: implementation_task, backend, integration, evidence, upstream_design

## Traceability

- dev.feat-to-tech::adr011-raw2src-fix-20260327-r1--feat-src-005-003
- FEAT-SRC-005-003
- TECH-SRC-005-003
- product.epic-to-feat::adr011-raw2src-fix-20260327-r1
- EPIC-SRC-005-001
- SRC-005
- product.raw-to-src::adr011-raw2src-fix-20260327-r1
- ADR-011
- ADR-001
- ADR-003
- ADR-004
- ADR-005
- ADR-006
- ADR-008
- ADR-009
- product.src-to-epic::adr011-raw2src-fix-20260327-r1
