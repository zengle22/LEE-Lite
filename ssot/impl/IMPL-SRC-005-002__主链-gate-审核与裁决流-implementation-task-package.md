---
id: IMPL-SRC-005-002
ssot_type: IMPL
impl_ref: IMPL-SRC-005-002
tech_ref: TECH-SRC-005-002
feat_ref: FEAT-SRC-005-002
title: 主链 gate 审核与裁决流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-002--tech-src-005-002
candidate_package_ref: artifacts/tech-to-impl/adr011-raw2src-fix-20260327-r1--feat-src-005-002--tech-src-005-002
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-adr011-raw2src-fix-20260327-r1--feat-src-005-002--tech-src-005-002-impl-bundle-decision.json
frozen_at: '2026-03-30T03:34:55Z'
---

# 主链 gate 审核与裁决流 Implementation Task Package

## Selected Upstream

- feat_ref: `FEAT-SRC-005-002`
- tech_ref: `TECH-SRC-005-002`
- arch_ref: `ARCH-SRC-005-002`
- api_ref: `API-SRC-005-002`
- title: 主链 gate 审核与裁决流
- goal: 冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: gate, 发布, io, runtime.
- migration_required: False
  - No migration, cutover, rollback, or compat-mode surface was detected.

## Implementation Task

- 1. Freeze upstream refs and touch set: The implementation entry references frozen upstream objects only and the concrete file/module touch set is explicit.
- 2. Implement frozen runtime units: The listed units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.
- 3. Integrate, evidence, and handoff: The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.

## Integration Plan

- 调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。
- 挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。
- 旧系统兼容：business skill 保持只产出 candidate/proposal/evidence，不新增直接 formal write 路径。
- Boundary to 主链协作闭环能力: 本 FEAT 消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。
- Boundary to 对象分层与准入能力: 本 FEAT 定义 candidate 到 decision 以及 decision 到 formal 发布 trigger 的推进链，不定义 consumer admission 与读取资格。
- 按已冻结主时序接线：1. normalize handoff and proposal refs; 2. validate gate-pending state and build `gate-brief-record`; 3. persist `gate-pending-human-decision` and human-facing projection。

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

- dev.feat-to-tech::adr011-raw2src-fix-20260327-r1--feat-src-005-002
- FEAT-SRC-005-002
- TECH-SRC-005-002
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
