---
id: "IMPL-SRC-ADR036-RAW2SRC-20260402-R9-003"
ssot_type: IMPL
title: 失败路径与反例推演流
status: execution_ready
schema_version: 1.0.0
workflow_key: "dev.tech-to-impl"
workflow_run_id: "adr036-feat003-impl-r1"
source_refs:
- "dev.feat-to-tech::adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-003"
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
- "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "API-SRC-ADR036-RAW2SRC-20260402-R9-003"
candidate_artifact_ref: "artifacts/tech-to-impl/adr036-feat003-impl-r1/impl-task.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
tech_ref: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-003"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-003"
candidate_package_ref: "artifacts/tech-to-impl/adr036-feat003-impl-r1"
---

# IMPL-SRC-ADR036-RAW2SRC-20260402-R9-003

## 1. 任务标识

- impl_ref: `IMPL-SRC-ADR036-RAW2SRC-20260402-R9-003`
- title: 失败路径与反例推演流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `adr036-feat003-impl-r1`
- status: `execution_ready`
- derived_from: `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003`, `TECH-SRC-ADR036-RAW2SRC-20260402-R9-003`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 冻结 deep mode 下的失败路径推演、counterexample 覆盖和恢复动作校验。
- 完成标准: 7 个 required steps、7 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。
- 冻结 失败路径与反例推演流 这一独立产品行为切片，并把它保持在产品层边界内。
- 该切片继承 failure_path_simulation、counterexample_coverage 的统一约束，但不把 capability axis 直接下沉成实现任务。
- 对外交付 counterexample coverage result，供下游能力直接继承。
- cli/lib/policy.py (extend)
- cli/lib/fs.py (extend)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-036, ADR-014, ADR-033, ADR-035 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-ADR036-RAW2SRC-20260402-R9` / `EPIC-IMPL-IMPLEMENTATION-READINESS` / `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` -> 冻结 deep mode 下的失败路径推演、counterexample 覆盖和恢复动作校验。
- TECH: `TECH-SRC-ADR036-RAW2SRC-20260402-R9-003` -> Freeze a concrete TECH design for 失败路径与反例推演流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。; 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- ARCH: `ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-ADR036-RAW2SRC-20260402-R9-003` -> `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。; `PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` (expected `TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-003`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-036, ADR-014, ADR-033, ADR-035` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-003` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for 失败路径与反例推演流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 失败路径与反例推演流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 失败路径与反例推演流 的完成态必须与“高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。”对齐，不能只输出中间态、占位态或内部处理结果。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `write_requested` -> `path_validated` -> `gateway_committed` -> `registry_recorded` -> `consumable_ref_published`
- `path_validated(fail)` -> `write_rejected`，不得 silent fallback 到自由写入。

### Main Sequence Snapshot

- 1. normalize request
- 2. preflight policy check
- 3. registry prerequisite check
- 4. execute governed handler
- 5. build receipt and managed ref
- 6. persist staging / evidence / registry record
- 7. return result

### Integration Points Snapshot

- 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。
- 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。
- 旧系统兼容：compat mode 仅允许受控 read fallback；正式 write 不允许 bypass Gateway。

### Implementation Unit Mapping Snapshot

- cli/lib/policy.py (extend): 定义 path / mode / overwrite 的 preflight verdict 规则。
- cli/lib/fs.py (extend): 实现 governed read/write 的底层文件访问与 receipt 落盘。
- cli/lib/managed_gateway.py (new): 编排 preflight、gateway commit、registry bind、receipt build。
- cli/lib/registry_store.py (extend): 记录 managed artifact ref、registry prerequisite 和 publish 状态。
- cli/commands/artifact/command.py (extend): 暴露 governed artifact commit / read 入口，依赖 cli/lib/managed_gateway.py。

### API Contract Snapshot

- `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。
- `PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `write_requested` -> `path_validated` -> `gateway_committed` -> `registry_recorded` -> `consumable_ref_published`
- `path_validated(fail)` -> `write_rejected`，不得 silent fallback 到自由写入。

#### API Contracts

- `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。
- `PolicyVerdict`: input=`logical_path`, `path_class`, `mode`, `caller_ref`; output=`allow`, `reason_code`, `resolved_path`, `mode_decision`; errors=`invalid_path_class`, `mode_forbidden`; idempotent=`yes`; precondition=`request normalized`。

#### UI Entry

- 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。
- 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。

#### UI Success Exit

- 7. return result

#### UI Failure Exit

- policy pass 但 registry prerequisite fail：拒绝写入，返回 `registry_prerequisite_failed`，不得绕过 registry 直接落盘。
- write success 但 receipt build fail：保留 staged artifact，标记 `receipt_pending`，禁止发布 managed ref 给 consumer。

#### Invariants

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 失败路径与反例推演流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 失败路径与反例推演流 的完成态必须与“高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。”对齐，不能只输出中间态、占位态或内部处理结果。
- 失败路径与反例推演流 happy path reaches the declared completed state: 高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。
- 失败路径与反例推演流 keeps its declared product boundary: 该 FEAT 只覆盖“非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- 失败路径与反例推演流 hands downstream one authoritative product deliverable: 下游必须围绕 counterexample coverage result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

#### Boundary Guardrails

- Boundary to object layering: 本 FEAT 冻结受治理 IO/path 边界，但不决定对象层级与 admission policy。
- Boundary to gate decision / publication: 本 FEAT 约束 write/read carrier 与 receipt/registry 行为，不定义 approve/reject 等 decision semantics。
- Dedicated gateway placement is required so policy、IO execution、registry bind 与 receipt publication use one governed carrier.
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- governed IO 命令不得 silent fallback 到自由读写；兼容模式也必须显式返回 warning/code。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.

## 5. 规范性约束

### Normative / MUST

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 失败路径与反例推演流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 失败路径与反例推演流 的完成态必须与“高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 失败路径与反例推演流 时必须保留 counterexample coverage result 这一 authoritative product deliverable，不能自行改写产品边界。
- 失败路径与反例推演流 必须继续受 failure_path_simulation、counterexample_coverage 的统一约束约束，而不是在下游重新发明同题语义。
- 失败路径与反例推演流 happy path reaches the declared completed state: 高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。
- 失败路径与反例推演流 keeps its declared product boundary: 该 FEAT 只覆盖“非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- 失败路径与反例推演流 hands downstream one authoritative product deliverable: 下游必须围绕 counterexample coverage result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

### Informative / Context Only

- None.

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/policy.py` [backend | extend | existing_match] <- `cli/lib/policy.py`: 定义 path / mode / overwrite 的 preflight verdict 规则。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/fs.py` [backend | extend | existing_match] <- `cli/lib/fs.py`: 实现 governed read/write 的底层文件访问与 receipt 落盘。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/managed_gateway.py` [frontend | new | existing_match] <- `cli/lib/managed_gateway.py`: 编排 preflight、gateway commit、registry bind、receipt build。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/registry_store.py` [frontend | extend | existing_match] <- `cli/lib/registry_store.py`: 记录 managed artifact ref、registry prerequisite 和 publish 状态。; nearby matches: cli/lib/execution_return_registry.py, cli/lib/fs.py
- `cli/commands/artifact/.gitkeep` [backend | extend | existing_match] <- `cli/commands/artifact/command.py`: 暴露 governed artifact commit / read 入口，依赖 cli/lib/managed_gateway.py。; nearby matches: cli/commands/artifact/command.py, cli/commands/artifact/__init__.py

### Repo Touch Points

- `cli/lib/policy.py` [backend | extend | existing_match] <- `cli/lib/policy.py`: 定义 path / mode / overwrite 的 preflight verdict 规则。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/fs.py` [backend | extend | existing_match] <- `cli/lib/fs.py`: 实现 governed read/write 的底层文件访问与 receipt 落盘。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/managed_gateway.py` [frontend | new | existing_match] <- `cli/lib/managed_gateway.py`: 编排 preflight、gateway commit、registry bind、receipt build。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/registry_store.py` [frontend | extend | existing_match] <- `cli/lib/registry_store.py`: 记录 managed artifact ref、registry prerequisite 和 publish 状态。; nearby matches: cli/lib/execution_return_registry.py, cli/lib/fs.py
- `cli/commands/artifact/.gitkeep` [backend | extend | existing_match] <- `cli/commands/artifact/command.py`: 暴露 governed artifact commit / read 入口，依赖 cli/lib/managed_gateway.py。; nearby matches: cli/commands/artifact/command.py, cli/commands/artifact/__init__.py

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Boundary to object layering: 本 FEAT 冻结受治理 IO/path 边界，但不决定对象层级与 admission policy。
- Boundary guardrail: Boundary to gate decision / publication: 本 FEAT 约束 write/read carrier 与 receipt/registry 行为，不定义 approve/reject 等 decision semantics。
- Boundary guardrail: Dedicated gateway placement is required so policy、IO execution、registry bind 与 receipt publication use one governed carrier.

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

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。, `cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。, `cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。, `cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。 Main sequence evidence covers: 1. normalize request; 2. preflight policy check; 3. registry prerequisite check. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. -> The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。; 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。, `cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。, `cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。, `cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。 Main sequence evidence covers: 1. normalize request; 2. preflight policy check; 3. registry prerequisite check.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-006, TASK-007 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。; 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。.

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

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/lib/managed_gateway.py, cli/lib/registry_store.py, cli/commands/artifact/.gitkeep | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/managed_gateway.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-003 Implement frontend entry and exit surfaces | depends_on: TASK-001, TASK-002 | parallel: TASK-004 | touch_points: cli/lib/managed_gateway.py, cli/lib/registry_store.py | outputs: frontend surface, entry/exit behavior, field/error rendering | acceptance: AC-001, AC-002 | done_when: Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: TASK-003 | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/commands/artifact/.gitkeep | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003, TASK-004 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/lib/managed_gateway.py, cli/lib/registry_store.py, cli/commands/artifact/.gitkeep | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-006 Make migration and cutover controls explicit | depends_on: TASK-005 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/commands/artifact/.gitkeep | outputs: migration plan, rollback behavior, compat controls | acceptance: AC-003 | done_when: Migration and fallback behavior is concrete enough to execute without keyword-based guesswork.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005, TASK-006 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- policy pass 但 registry prerequisite fail：拒绝写入，返回 `registry_prerequisite_failed`，不得绕过 registry 直接落盘。
- write success 但 receipt build fail：保留 staged artifact，标记 `receipt_pending`，禁止发布 managed ref 给 consumer。
- staging retention fail：允许主写入成功，但必须追加 degraded evidence，并要求后续 cleanup job 补偿。
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- Migration or cutover requires an explicit rollback or compat-mode path.
