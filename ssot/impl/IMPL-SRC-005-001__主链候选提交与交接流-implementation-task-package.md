---
id: IMPL-SRC-005-001
ssot_type: IMPL
impl_ref: IMPL-SRC-005-001
tech_ref: TECH-SRC-005-001
feat_ref: FEAT-SRC-005-001
title: 主链候选提交与交接流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-001--tech-src-005-001
candidate_package_ref: artifacts/tech-to-impl/adr011-raw2src-fix-20260327-r1--feat-src-005-001--tech-src-005-001
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-adr011-raw2src-fix-20260327-r1--feat-src-005-001--tech-src-005-001-impl-bundle-decision.json
frozen_at: '2026-03-30T02:03:48Z'
---

# 主链候选提交与交接流 Implementation Task Package

## Selected Upstream

- feat_ref: `FEAT-SRC-005-001`
- tech_ref: `TECH-SRC-005-001`
- arch_ref: `ARCH-SRC-005-001`
- api_ref: `API-SRC-005-001`
- title: 主链候选提交与交接流
- goal: 冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: gate, io, runtime.
- migration_required: False
  - No migration, cutover, rollback, or compat-mode surface was detected.

## Implementation Task

- 1. Freeze upstream refs and touch set: The implementation entry references frozen upstream objects only and the concrete file/module touch set is explicit.
- 2. Implement frozen runtime units: The listed units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.
- 3. Integrate, evidence, and handoff: The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.

## Integration Plan

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。
- Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。
- Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。
- 按已冻结主时序接线：1. normalize candidate/proposal/evidence submission and producer state; 2. persist authoritative handoff object and emit gate-pending visibility; 3. route proposal into gate loop and escalate to human review when required。

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

- dev.feat-to-tech::adr011-raw2src-fix-20260327-r1--feat-src-005-001
- FEAT-SRC-005-001
- TECH-SRC-005-001
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
