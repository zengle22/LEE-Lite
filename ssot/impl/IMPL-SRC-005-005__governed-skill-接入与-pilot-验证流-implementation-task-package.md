---
id: IMPL-SRC-005-005
ssot_type: IMPL
impl_ref: IMPL-SRC-005-005
tech_ref: TECH-SRC-005-005
feat_ref: FEAT-SRC-005-005
title: governed skill 接入与 pilot 验证流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-005--tech-src-005-005
candidate_package_ref: artifacts/tech-to-impl/adr011-raw2src-fix-20260327-r1--feat-src-005-005--tech-src-005-005
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-adr011-raw2src-fix-20260327-r1--feat-src-005-005--tech-src-005-005-impl-bundle-decision.json
frozen_at: '2026-03-30T03:34:55Z'
---

# governed skill 接入与 pilot 验证流 Implementation Task Package

## Selected Upstream

- feat_ref: `FEAT-SRC-005-005`
- tech_ref: `TECH-SRC-005-005`
- arch_ref: `ARCH-SRC-005-005`
- api_ref: `API-SRC-005-005`
- title: governed skill 接入与 pilot 验证流
- goal: 冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: gate, io, runtime, registry.
- migration_required: True
  - Detected migration/cutover language: cutover, fallback, migration, rollout.

## Implementation Task

- 1. Freeze upstream refs and touch set: The implementation entry references frozen upstream objects only and the concrete file/module touch set is explicit.
- 2. Implement frozen runtime units: The listed units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.
- 3. Prepare migration and cutover controls: Migration prerequisites, guardrails, and fallback actions are explicit enough for downstream execution.
- 4. Integrate, evidence, and handoff: The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.

## Integration Plan

- 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。
- 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。
- 旧系统兼容：先接入选定 pilot skill，再按 wave 扩大；未在 onboarding matrix 内的旧 skill 保持现状不切换。
- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 foundation FEAT 与 ADR-005 前置基础的能力定义。
- Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。
- 按已冻结主时序接线：1. resolve onboarding directive and targeted wave; 2. verify foundation readiness and compat mode; 3. bind selected skill to mainline runtime / gate hooks。

## Evidence Plan

- AC-001: backend-verification, migration-verification, smoke-review-input
- AC-002: backend-verification, migration-verification, smoke-review-input
- AC-003: backend-verification, migration-verification, smoke-review-input
- AC-004: backend-verification, migration-verification, smoke-review-input

## Smoke Gate Subject

- See `smoke-gate-subject.json` for the current `status`, `decision`, and `ready_for_execution` state.

## Delivery Handoff

- target_template_id: `template.dev.feature_delivery_l2`
- primary_artifact_ref: `impl-bundle.json`
- phase_inputs: implementation_task, backend, migration, integration, evidence, upstream_design

## Traceability

- dev.feat-to-tech::adr011-raw2src-fix-20260327-r1--feat-src-005-005
- FEAT-SRC-005-005
- TECH-SRC-005-005
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
