---
id: IMPL-SRC-005-004
ssot_type: IMPL
impl_ref: IMPL-SRC-005-004
tech_ref: TECH-SRC-005-004
feat_ref: FEAT-SRC-005-004
title: 主链受治理 IO 落盘与读取流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-004--tech-src-005-004
candidate_package_ref: artifacts/tech-to-impl/adr011-raw2src-fix-20260327-r1--feat-src-005-004--tech-src-005-004
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-adr011-raw2src-fix-20260327-r1--feat-src-005-004--tech-src-005-004-impl-bundle-decision.json
frozen_at: '2026-03-30T03:34:55Z'
---

# 主链受治理 IO 落盘与读取流 Implementation Task Package

## Selected Upstream

- feat_ref: `FEAT-SRC-005-004`
- tech_ref: `TECH-SRC-005-004`
- arch_ref: `ARCH-SRC-005-004`
- api_ref: `API-SRC-005-004`
- title: 主链受治理 IO 落盘与读取流
- goal: 冻结主链业务动作在什么时候必须 governed write/read，以及这些正式读写会为业务方留下什么 authoritative receipt 和 managed ref。

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: io, registry, gate, path.
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
- Boundary to 对象分层与准入能力: 本 FEAT 定义对象落盘边界，不定义对象层级与消费资格本身。
- Boundary to 正式交接与物化能力: 本 FEAT 约束 formalization 的 IO/path 边界，但 formalization 决策语义仍属于正式交接 FEAT。
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

- dev.feat-to-tech::adr011-raw2src-fix-20260327-r1--feat-src-005-004
- FEAT-SRC-005-004
- TECH-SRC-005-004
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
