---
id: IMPL-SRC-003-002
ssot_type: IMPL
impl_ref: IMPL-SRC-003-002
tech_ref: TECH-SRC-003-002
feat_ref: FEAT-SRC-003-002
title: Runner 用户入口流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr018-runner-entry-impl-20260327-r3
candidate_package_ref: artifacts/tech-to-impl/adr018-runner-entry-impl-20260327-r3
gate_decision_ref: artifacts/active/gates/decisions/gate-decision-impl-src-003-002.json
frozen_at: '2026-03-27T02:59:38Z'
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-003-002
  tech_ref: TECH-SRC-003-002
  authority_refs:
    - ARCH-SRC-003-002
    - API-SRC-003-002
    - ADR-014
    - ADR-018
provisional_refs: []
freshness_status: manual_snapshot_requires_rederive_on_upstream_change
rederive_triggers:
  - upstream_ref_version_change
  - acceptance_contract_change
  - ui_api_testset_contract_change
  - touch_set_expands_beyond_declared_scope
repo_discrepancy_status: explicit_discrepancy_handling_required
self_contained_policy: minimum_sufficient_information_not_upstream_mirror
---

# Runner 用户入口流 Implementation Task Package

## Package Semantics

- `package_semantics`: canonical execution package / execution-time single entrypoint
- `authority_scope`: execution input only，不是业务、设计或测试事实源
- `selected_upstream_refs`: 只消费已冻结 `FEAT / TECH / ARCH / API / ADR` 约束
- `freshness_status`: 上游 ref、验收口径或 touch set 变化时必须重派生或重审
- `repo_discrepancy_status`: repo 现状只能暴露差异，不能静默替代上游冻结真相
- `self_contained_policy`: 收敛执行最小充分信息，不镜像上游全文

## Selected Upstream

- feat_ref: `FEAT-SRC-003-002`
- tech_ref: `TECH-SRC-003-002`
- arch_ref: `ARCH-SRC-003-002`
- api_ref: `API-SRC-003-002`
- title: Runner 用户入口流
- goal: 冻结一个用户可显式调用的 Execution Loop Job Runner canonical governed skill bundle，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。

## Applicability Assessment

- frontend_required: False
  - Execution runner implementation is skill/runtime-facing and does not introduce end-user UI/page/component work.
- backend_required: True
  - Execution runner implementation is carried by canonical skill bundle, installed adapter, loop/job commands, queue/runtime modules, and operator-facing backend surfaces.
- migration_required: False
  - Execution runner FEATs do not require rollout/cutover planning inside this IMPL package unless a separate migration FEAT owns that scope.

## Implementation Task

- 1. Freeze upstream refs and touch set: The implementation entry references frozen upstream objects only and the canonical skill path, level, adapter boundary, and concrete file/module touch set are explicit.
- 2. Implement frozen skill authority and runtime carriers: The listed units implement the canonical skill bundle, installed adapter boundary, state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.
- 3. Integrate, evidence, install smoke, and execution handoff: The package can enter template.dev.feature_delivery_l2 while preserving the frozen execution-runner lifecycle and operator/runtime boundary.

## Integration Plan

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。
- 按已冻结主时序接线：1. accept start/resume request from installed runner skill adapter or authorized carrier; 2. bootstrap or restore runner context; 3. publish runner invocation receipt; 4. delegate to repo CLI carrier only as needed。

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

- dev.feat-to-tech::adr018-runner-entry-tech-20260327-r3
- FEAT-SRC-003-002
- TECH-SRC-003-002
- product.epic-to-feat::adr018-epic2feat-lineage-20260326-r1
- EPIC-SRC-003-001
- SRC-003
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-020
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
