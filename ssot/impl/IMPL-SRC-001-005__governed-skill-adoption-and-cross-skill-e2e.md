---
id: IMPL-SRC-001-005
ssot_type: IMPL
title: Governed Skill Adoption and Cross-Skill E2E Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-src-001-005
parent_id: FEAT-SRC-001-005
source_refs:
  - FEAT-SRC-001-005
  - ADR-014
  - ADR-005
  - ADR-006
  - ARCH-SRC-001-001
  - ARCH-SRC-001-003
  - API-SRC-001-005
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-SRC-001-005
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-005-20260325
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-001-005
  tech_ref: TECH-SRC-001-005
  authority_refs:
    - ADR-014
    - ADR-005
    - ADR-006
    - ARCH-SRC-001-001
    - ARCH-SRC-001-003
    - API-SRC-001-005
    - API-SRC-001-001
provisional_refs: []
freshness_status: manual_snapshot_requires_rederive_on_upstream_change
self_contained_policy: minimum_sufficient_information_not_upstream_mirror
rederive_triggers:
  - upstream_ref_version_change
  - acceptance_contract_change
  - ui_api_testset_contract_change
  - touch_set_expands_beyond_declared_scope
repo_discrepancy_status: explicit_discrepancy_handling_required
conflict_policy: upstream_frozen_objects_override_repo_shape_and_manual_impl_text
properties:
  feat_ref: FEAT-SRC-001-005
  tech_ref: TECH-SRC-001-005
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: true
  target_template_id: template.dev.feature_delivery_l2
---

# Governed Skill Adoption and Cross-Skill E2E Implementation Task

## 0. Package Semantics

本对象是本次实施的 `canonical package / execution-time single entrypoint`，用于把上游已冻结的 `FEAT / TECH / API / ADR` 约束收敛成一次可执行输入。

同时明确：

- 它不是业务、设计或测试事实的 SSOT。
- 它不是新的技术设计层。
- 它只收敛执行所需最小充分信息，不镜像上游全文。
- 若上游 ref、验收口径或 touch set 变化，必须重派生或重审 freshness。
- repo 现状只能作为 discrepancy signal，不能反向升格为 truth source。

## 1. 本次目标

实现 governed skill onboarding、pilot 验证、cutover/fallback 与跨 skill E2E evidence，让主链能力从 foundation 进入真实接入阶段。

本次实施不重写 foundation FEAT 的内部实现。

## 2. Selected Upstream

- `FEAT-SRC-001-005`：定义 governed skill onboarding 与 cross-skill E2E 的目标边界。
- `TECH-SRC-001-005`：定义本次实施的主技术设计与模块切分。
- `API-SRC-001-005`：提供 rollout / onboarding contract。
- `API-SRC-001-001`：提供 governed runtime baseline 与 shared revision-return contract。
- `ADR-014`：将 `IMPL` 定义为技术设计下游的正式实施候选冻结层。
- `ADR-005` / `ADR-006`：约束正式对象、gate、pilot 与 publish 主链规则。

### Normative / MUST

- pilot 链必须经过 `gate / formal publish`，不得绕过治理主链。
- 不得重新定义 `Gateway / Gate / Registry contract`。
- repo 现状若与上游冻结对象冲突，不得默认以代码现状为准，必须先做 discrepancy handling。
- touch set 超出当前实现范围时，不得在本 IMPL 内直接扩边，必须回上游重冻或补派生。

### Informative / Context Only

- foundation 尚在稳定期，因此 pilot evidence 的真实性依赖 rollout 节奏。
- compat mode、wave state 与 revision coverage 的治理价值高于一次性迁移速度。

## 3. 实施范围

- 模块范围：
  - `cli/lib/protocol.py`
  - `cli/lib/rollout_state.py`
  - `cli/lib/pilot_chain.py`
  - `cli/commands/rollout/command.py`
  - `cli/commands/audit/command.py`
- 工程范围：
  - onboarding matrix
  - wave state
  - pilot evidence
  - cutover/fallback guard
- 不在范围：
  - 重新定义 Gateway / Gate / Registry contract
  - 一次性迁移所有旧 skill

## 4. 实施要求

### Required

- 定义 `OnboardingMatrix / CutoverDirective / PilotEvidenceRef` 结构与 wave state。
- 实现 onboarding registry 和 rollout state 持久化。
- 实现 pilot chain verifier，至少覆盖 `producer -> gate -> formal -> consumer -> audit`。
- 实现 cutover/fallback 判定与状态写回，且在 evidence 不足时 fail closed。
- 输出 supporting matrix、pilot evidence、cutover recommendation 与 fallback evidence。

### Suggested

- 先固化 onboarding matrix，再推进 runtime state 和 verifier，最后接 cutover/fallback。
- 在 verifier 中优先覆盖最小可闭环 pilot 链，避免一开始追求全量 workflow 覆盖。

## 5. 交付物

- 代码：
  - `cli/lib/rollout_state.py`
  - `cli/lib/pilot_chain.py`
  - rollout/audit command 扩展
- 计划：
  - onboarding matrix: `ssot/impl/IMPL-SRC-001-005-001__governed-skill-integration-matrix-and-onboarding-scope-definition.md`
  - migration wave / cutover / fallback plan
  - revision-module coverage matrix
- 证据：
  - pilot evidence
  - cutover recommendation
  - rollback / fallback evidence

## 6. 验收标准

- 至少一条真实 pilot 主链跑通。
- `compat_mode`、`wave_id`、`cutover_guard_ref` 必须可追溯。
- included workflows 的 `revision-request` coverage 与 excluded rationale 必须在 onboarding matrix 中明确。
- pilot evidence 缺失时必须 fail closed，不能继续 rollout。
- fallback 结果必须记录到 receipt / wave state。

## 7. 风险与注意事项

- 若 foundation 还没稳定，pilot evidence 会失真。
- compat mode 若定义不清，cutover/fallback 会退化成口头流程。
- 若 audit evidence 无法回交 gate，rollout 无法形成闭环。
- 若后续 `TECH / API / TESTSET` 口径变化，本 IMPL 必须重做 freshness check，不能沿用旧快照继续执行。

## 8. Supporting Artifact

- onboarding matrix ref: `ssot/impl/IMPL-SRC-001-005-001__governed-skill-integration-matrix-and-onboarding-scope-definition.md`

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- supporting refs:
  - `TECH-SRC-001-005`
  - `API-SRC-001-005`
