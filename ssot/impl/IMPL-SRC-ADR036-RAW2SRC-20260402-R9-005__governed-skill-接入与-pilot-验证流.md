---
id: "IMPL-SRC-ADR036-RAW2SRC-20260402-R9-005"
ssot_type: IMPL
title: governed skill 接入与 pilot 验证流
status: execution_ready
schema_version: 1.0.0
workflow_key: "dev.tech-to-impl"
workflow_run_id: "adr036-feat005-impl-r1"
source_refs:
- "dev.feat-to-tech::adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
- "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "API-SRC-ADR036-RAW2SRC-20260402-R9-005"
candidate_artifact_ref: "artifacts/tech-to-impl/adr036-feat005-impl-r1/impl-task.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
tech_ref: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-005"
candidate_package_ref: "artifacts/tech-to-impl/adr036-feat005-impl-r1"
---

# IMPL-SRC-ADR036-RAW2SRC-20260402-R9-005

## 1. 任务标识

- impl_ref: `IMPL-SRC-ADR036-RAW2SRC-20260402-R9-005`
- title: governed skill 接入与 pilot 验证流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `adr036-feat005-impl-r1`
- status: `execution_ready`
- derived_from: `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005`, `TECH-SRC-ADR036-RAW2SRC-20260402-R9-005`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- 完成标准: 7 个 required steps、7 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。
- 定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。
- 定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。
- cli/lib/protocol.py (extend)
- cli/lib/rollout_state.py (new)
- cli/lib/pilot_chain.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-036, ADR-014, ADR-033, ADR-035 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-ADR036-RAW2SRC-20260402-R9` / `EPIC-IMPL-IMPLEMENTATION-READINESS` / `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` -> 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- TECH: `TECH-SRC-ADR036-RAW2SRC-20260402-R9-005` -> Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。; 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- ARCH: `ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-ADR036-RAW2SRC-20260402-R9-005` -> `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。; `PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` (expected `TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-005`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-036, ADR-014, ADR-033, ADR-035` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-005` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 来源与依赖约束：workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `skill_registered` -> `pilot_enabled` -> `cutover_guarded` -> `e2e_verified` -> `wave_accepted`
- `cutover_guarded(fail)` -> `fallback_triggered` -> `pilot_enabled`

### Main Sequence Snapshot

- 1. resolve onboarding directive and targeted wave
- 2. verify foundation readiness and compat mode
- 3. bind selected skill to mainline runtime / gate hooks
- 4. run pilot chain and capture producer -> consumer -> audit -> gate evidence
- 5. evaluate cutover guard and emit fallback recommendation when needed
- 6. persist wave status and rollout evidence

### Integration Points Snapshot

- 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。
- 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。
- 旧系统兼容：先接入选定 pilot skill，再按 wave 扩大；未在 onboarding matrix 内的旧 skill 保持现状不切换。

### Implementation Unit Mapping Snapshot

- cli/lib/protocol.py (extend): 定义 OnboardingMatrix、CutoverDirective、PilotEvidenceRef 结构。
- cli/lib/rollout_state.py (new): 保存 onboarding wave、cutover state 和 fallback marker。
- cli/lib/pilot_chain.py (new): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。
- cli/commands/rollout/command.py (extend): 提供 onboarding wave、cutover、fallback 操作，依赖 cli/lib/rollout_state.py。
- cli/commands/audit/command.py (extend): 消费 pilot evidence 并把 findings 回交给 cutover decision。

### API Contract Snapshot

- `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。
- `PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `skill_registered` -> `pilot_enabled` -> `cutover_guarded` -> `e2e_verified` -> `wave_accepted`
- `cutover_guarded(fail)` -> `fallback_triggered` -> `pilot_enabled`

#### API Contracts

- `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。
- `PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。

#### UI Entry

- 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。
- 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。

#### UI Success Exit

- 6. persist wave status and rollout evidence

#### UI Failure Exit

- pilot chain 中任一步 evidence 缺失：cutover 直接 fail closed，维持 compat mode。
- cutover success 但 audit handoff fail：允许 partial success，但 wave 状态标记 `audit_pending`，禁止扩大 rollout。

#### Invariants

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 来源与依赖约束：workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
- At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
- Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

#### Boundary Guardrails

- Boundary to foundation FEATs: 本 FEAT 只定义 onboarding/pilot/cutover 挂接边界，不重写 collaboration、gate decision/publication、IO foundation internals。
- Boundary to audit/gate consumption: 本 FEAT 组织 pilot evidence 与 cutover routing，不新建平行 decision 体系。
- Dedicated rollout placement is required so wave state、compat mode 与 fallback remain authoritative across skill adoption.
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- onboarding/cutover 命令必须保留 compat_mode 开关，并把 fallback 结果显式记录到 receipt。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.

## 5. 规范性约束

### Normative / MUST

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 来源与依赖约束：workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- 真实闭环成立必须以 pilot E2E evidence 证明，不得把组件内自测当成唯一成立依据。
- Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
- At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
- Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

### Informative / Context Only

- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
- Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 OnboardingMatrix、CutoverDirective、PilotEvidenceRef 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/rollout_state.py` [backend | new | existing_match] <- `cli/lib/rollout_state.py`: 保存 onboarding wave、cutover state 和 fallback marker。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/pilot_chain.py` [backend | new | existing_match] <- `cli/lib/pilot_chain.py`: 校验 producer -> consumer -> audit -> gate 的真实闭环证据。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/commands/rollout/command.py` [backend | extend | existing_match] <- `cli/commands/rollout/command.py`: 提供 onboarding wave、cutover、fallback 操作，依赖 cli/lib/rollout_state.py。; nearby matches: cli/commands/rollout/__init__.py, cli/commands/__init__.py
- `cli/commands/audit/command.py` [backend | extend | existing_match] <- `cli/commands/audit/command.py`: 消费 pilot evidence 并把 findings 回交给 cutover decision。; nearby matches: cli/commands/audit/__init__.py, cli/commands/__init__.py

### Repo Touch Points

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 OnboardingMatrix、CutoverDirective、PilotEvidenceRef 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/rollout_state.py` [backend | new | existing_match] <- `cli/lib/rollout_state.py`: 保存 onboarding wave、cutover state 和 fallback marker。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/pilot_chain.py` [backend | new | existing_match] <- `cli/lib/pilot_chain.py`: 校验 producer -> consumer -> audit -> gate 的真实闭环证据。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/commands/rollout/command.py` [backend | extend | existing_match] <- `cli/commands/rollout/command.py`: 提供 onboarding wave、cutover、fallback 操作，依赖 cli/lib/rollout_state.py。; nearby matches: cli/commands/rollout/__init__.py, cli/commands/__init__.py
- `cli/commands/audit/command.py` [backend | extend | existing_match] <- `cli/commands/audit/command.py`: 消费 pilot evidence 并把 findings 回交给 cutover decision。; nearby matches: cli/commands/audit/__init__.py, cli/commands/__init__.py

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Boundary to foundation FEATs: 本 FEAT 只定义 onboarding/pilot/cutover 挂接边界，不重写 collaboration、gate decision/publication、IO foundation internals。
- Boundary guardrail: Boundary to audit/gate consumption: 本 FEAT 组织 pilot evidence 与 cutover routing，不新建平行 decision 体系。
- Boundary guardrail: Dedicated rollout placement is required so wave state、compat mode 与 fallback remain authoritative across skill adoption.

### Execution Boundary

- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。
- discrepancy handling: 若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准。

## 7. 交付物要求

- impl-bundle.md
- impl-bundle.json
- impl-task.md
- upstream-design-refs.json
- integration-plan.md
- dev-evidence-plan.json
- smoke-gate-subject.json
- impl-review-report.json
- impl-acceptance-report.json
- impl-defect-list.json
- handoff-to-feature-delivery.json
- execution-evidence.json
- supervision-evidence.json
- frontend-workstream.md
- backend-workstream.md
- migration-cutover-plan.md

### Handoff Artifacts

- impl-bundle.md
- impl-bundle.json
- impl-task.md
- upstream-design-refs.json
- integration-plan.md
- dev-evidence-plan.json
- smoke-gate-subject.json
- impl-review-report.json
- impl-acceptance-report.json
- impl-defect-list.json
- handoff-to-feature-delivery.json
- execution-evidence.json
- supervision-evidence.json
- frontend-workstream.md
- backend-workstream.md
- migration-cutover-plan.md

## 8. 验收标准与 TESTSET 映射

- testset_ref: `missing_authority`
- mapping_policy: `TESTSET_over_IMPL_when_present`
### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `OnboardingMatrix`、`CutoverDirective`、`PilotEvidenceRef` 结构。, `cli/lib/rollout_state.py` (`new`): 保存 onboarding wave、cutover state 和 fallback marker。, `cli/lib/pilot_chain.py` (`new`): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。, `cli/commands/rollout/command.py` (`extend`): 提供 onboarding wave、cutover、fallback 操作，依赖 `cli/lib/rollout_state.py`。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。 Main sequence evidence covers: 1. resolve onboarding directive and targeted wave; 2. verify foundation readiness and compat mode; 3. bind selected skill to mainline runtime / gate hooks. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. -> The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。; 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `OnboardingMatrix`、`CutoverDirective`、`PilotEvidenceRef` 结构。, `cli/lib/rollout_state.py` (`new`): 保存 onboarding wave、cutover state 和 fallback marker。, `cli/lib/pilot_chain.py` (`new`): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。, `cli/commands/rollout/command.py` (`extend`): 提供 onboarding wave、cutover、fallback 操作，依赖 `cli/lib/rollout_state.py`。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。 Main sequence evidence covers: 1. resolve onboarding directive and targeted wave; 2. verify foundation readiness and compat mode; 3. bind selected skill to mainline runtime / gate hooks.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-006, TASK-007 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。; 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。.

## 9. 执行顺序建议

### Required

- 1. Freeze refs and repo touch points: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- 2. Embed state, API, UI, and boundary contracts into implementation inputs: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- 3. Implement frontend entry and exit surfaces: Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.
- 4. Implement backend runtime, state, and persistence units: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- 5. Wire integration guards and downstream handoff: The main sequence executes in order and downstream handoff remains boundary-safe.
- 6. Make migration and cutover controls explicit: Migration and fallback behavior is concrete enough to execute without keyword-based guesswork.
- 7. Collect acceptance evidence and close delivery handoff: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

### Suggested

- None.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/rollout_state.py, cli/lib/pilot_chain.py, cli/commands/rollout/command.py, cli/commands/audit/command.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-003 Implement frontend entry and exit surfaces | depends_on: TASK-001, TASK-002 | parallel: TASK-004 | touch_points: none | outputs: frontend surface, entry/exit behavior, field/error rendering | acceptance: AC-001, AC-002 | done_when: Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: TASK-003 | touch_points: cli/lib/protocol.py, cli/lib/rollout_state.py, cli/lib/pilot_chain.py, cli/commands/rollout/command.py, cli/commands/audit/command.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003, TASK-004 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/rollout_state.py, cli/lib/pilot_chain.py, cli/commands/rollout/command.py, cli/commands/audit/command.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-006 Make migration and cutover controls explicit | depends_on: TASK-005 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/rollout_state.py, cli/lib/pilot_chain.py, cli/commands/rollout/command.py, cli/commands/audit/command.py | outputs: migration plan, rollback behavior, compat controls | acceptance: AC-003 | done_when: Migration and fallback behavior is concrete enough to execute without keyword-based guesswork.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005, TASK-006 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- pilot chain 中任一步 evidence 缺失：cutover 直接 fail closed，维持 compat mode。
- cutover success 但 audit handoff fail：允许 partial success，但 wave 状态标记 `audit_pending`，禁止扩大 rollout。
- fallback trigger fail：保留 current wave 冻结，要求人工介入，不允许自动继续下一波次。
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
