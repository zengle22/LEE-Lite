---
id: IMPL-<SRC|FEAT>-<ID>
ssot_type: IMPL
impl_ref: IMPL-<SRC|FEAT>-<ID>
tech_ref: TECH-<REF>
feat_ref: FEAT-<REF>
title: <Implementation Task Package Title>
status: draft
schema_version: 1.0.0
workflow_key: manual.impl.from-tech
workflow_run_id: manual-impl-<run-id>
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-<REF>
  tech_ref: TECH-<REF>
  authority_refs:
    - ADR-014
    - ADR-034
    - ARCH-<REF>
    - API-<REF>
    - UI-<REF>
    - TESTSET-<REF>
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

# <Implementation Task Package Title>

> 本文档本身就是本次 run 的主执行契约。
> coder / tester 应优先直接消费本文档开工。
> sidecar、release、bundle brief、handoff summary 只能辅助审计与追溯，不能替代本文档承担 execution contract 角色。

## Package Semantics

- `package_semantics`: canonical execution package / execution-time single entrypoint
- `authority_scope`: execution input only，不是业务、设计或测试事实源
- `selected_upstream_refs`: 只消费已冻结 `FEAT / TECH / ARCH / API / UI / TESTSET / ADR` 约束
- `freshness_status`: 上游 ref、验收口径或 touch set 变化时必须重派生或重审
- `repo_discrepancy_status`: repo 现状只能暴露差异，不能静默替代上游冻结真相
- `self_contained_policy`: 收敛执行最小充分信息，不镜像上游全文

## Selected Upstream

- feat_ref: `FEAT-<REF>`
- tech_ref: `TECH-<REF>`
- arch_ref: `ARCH-<REF>`
- api_ref: `API-<REF>`
- ui_ref: `UI-<REF>` or `N/A`
- testset_ref: `TESTSET-<REF>` or `N/A`
- title: <upstream feat or tech title>
- goal: <execution goal>

## Upstream Contract Snapshots

### TECH Contract Snapshot

- <design focus / key implementation rules>

### ARCH Constraint Snapshot

- <layering / ownership / runtime attachment constraints>

### State Model Snapshot

- <critical state transitions>

### Main Sequence Snapshot

- <critical execution sequence>

### Integration Points Snapshot

- <caller / attachment points / compat hooks>

### Implementation Unit Mapping Snapshot

- <module -> responsibility mapping>

### API Contract Snapshot

- <input / output / errors / idempotency / preconditions>

### UI Constraint Snapshot

- <directly execution-relevant UI constraints, or `N/A`>

## Applicability Assessment

- frontend_required: <True|False>
- backend_required: <True|False>
- migration_required: <True|False>

## Implementation Task

### Required

- Freeze selected upstream refs and declared touch set.
- Implement only frozen carriers, interfaces, and evidence hooks.
- Keep acceptance and handoff aligned to `TESTSET` and upstream contracts.

### Suggested

- Record optional sequencing hints for coder/tester handoff.
- Record provisional follow-up actions when some upstream objects are not fully frozen.

## Integration Plan

- 调用方：<caller / workflow>
- 挂接点：<runtime or module touchpoints>
- 兼容性：<compat / migration notes>
- 边界：<what this IMPL does not redefine>

## Evidence Plan

- AC-001: <verification slice>
- AC-002: <verification slice>

## Smoke Gate Subject

- status: <pending|blocked|ready>
- decision: <ready|revise>
- ready_for_execution: <True|False>

## Delivery Handoff

- target_template_id: `template.dev.feature_delivery_l2`
- primary_artifact_ref: `impl-bundle.json` or manual equivalent
- phase_inputs: implementation_task, integration, evidence, upstream_design

## Traceability

- `dev.feat-to-tech::<run-id>`
- `FEAT-<REF>`
- `TECH-<REF>`
- `ARCH-<REF>`
- `API-<REF>`
- `UI-<REF>`
- `TESTSET-<REF>`
- `ADR-014`
- `ADR-034`

## Usage Boundary

- `001-005` 这类分阶段上游文档仍然负责定义 authority / truth source
- 本文档负责把本次执行所需 truth 收敛成单次 execution contract
- 不得要求 coder / tester 为补齐关键状态机、接口、集成点而回查 sidecar 或 release 文档
