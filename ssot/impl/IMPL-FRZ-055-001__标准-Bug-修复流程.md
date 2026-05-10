---
id: "IMPL-FRZ-055-001"
ssot_type: IMPL
title: 标准 Bug 修复流程
status: execution_ready
schema_version: 1.0.0
workflow_key: "dev.tech-to-impl"
workflow_run_id: "frz-055-bug-lifecycle-20260507--feat-frz-055-001--tech-frz-055-001"
source_refs:
- "dev.feat-to-tech::frz-055-bug-lifecycle-20260507--feat-frz-055-001"
- "FEAT-FRZ-055-001"
- "TECH-FRZ-055-001"
- "ARCH:ARCH-FRZ-055-001"
- "EPIC:EPIC-FRZ-055-20260507"
- "SRC:FRZ-055"
- "SURFACE:SURFACE-MAP-FEAT-FRZ-055-001"
- "product.epic-to-feat::frz-055-bug-lifecycle-20260507"
- "EPIC-FRZ-055-20260507"
- "FRZ-055"
- "SURFACE-MAP-FEAT-FRZ-055-001"
- "ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md"
- "ssot/frz/FRZ-055/frz.yaml"
- "SRC-FRZ-055-20260507"
- "ADR-055"
- "ADR-034"
- "ARCH-FRZ-055-001"
candidate_artifact_ref: "artifacts/tech-to-impl/frz-055-bug-lifecycle-20260507--feat-frz-055-001--tech-frz-055-001/impl-task.md"
gate_decision_ref: "artifacts/active/gates/decisions/frz055-chain-manual-approval-20260507.json"
parent_id: "FEAT-FRZ-055-001"
tech_ref: "TECH-FRZ-055-001"
candidate_package_ref: "artifacts/tech-to-impl/frz-055-bug-lifecycle-20260507--feat-frz-055-001--tech-frz-055-001"
---

# IMPL-FRZ-055-001

## 1. 任务标识

- impl_ref: `IMPL-FRZ-055-001`
- title: 标准 Bug 修复流程 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `frz-055-bug-lifecycle-20260507--feat-frz-055-001--tech-frz-055-001`
- status: `execution_ready`
- derived_from: `FEAT-FRZ-055-001`, `TECH-FRZ-055-001`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 建立从 test-run 失败发现到自动关闭的完整标准 Bug 修复流程，并与 GSD 执行阶段集成。
- 完成标准: 5 个 required steps、5 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- test-run 执行测试，发现失败用例
- build_bug_bundle 生成 detected 状态 bug，写入 bug registry
- gate-evaluate 分析，输出 FAIL verdict
- gate_remediation 将 detected 提升为 open，生成 draft phase
- cli/lib/policy.py (extend)
- cli/lib/fs.py (extend)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-055 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-FRZ-055-20260507` / `EPIC-FRZ-055-20260507` / `FEAT-FRZ-055-001` -> 建立从 test-run 失败发现到自动关闭的完整标准 Bug 修复流程，并与 GSD 执行阶段集成。
- TECH: `TECH-FRZ-055-001` -> Freeze a concrete TECH design for 标准 Bug 修复流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复; 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- ARCH: `ARCH-FRZ-055-001` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `not present` -> No explicit API ref selected for this run.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-FRZ-055-001` (expected `UI-FEAT-FRZ-055-001`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-FRZ-055-001` (expected `TESTSET-FRZ-055-001`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-055` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-FRZ-055-001` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-FRZ-055-001` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`not_selected` ref=`unspecified` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-FRZ-055-001` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-FRZ-055-001` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-FRZ-055-001` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-FRZ-055-001` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for 标准 Bug 修复流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase
- test-run 失败用例应自动生成 detected 状态 bug 写入 registry: 应生成 detected 状态 bug 并写入对应 feat 的 bug registry。

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

- None.

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-FRZ-055-001` (expected `UI-FEAT-FRZ-055-001`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

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

- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase
- test-run 失败用例应自动生成 detected 状态 bug 写入 registry: 应生成 detected 状态 bug 并写入对应 feat 的 bug registry。
- gate FAIL 应自动将 detected 提升为 open: bug status 应从 detected 变为 open，并生成 draft phase。
- ll-bug-remediate 应生成符合 GSD 规范的 bug fix phase: 应生成符合 GSD 规范的 {N}-bug-fix-{bug_id} phase。

#### Boundary Guardrails

- Boundary to object layering: 本 FEAT 冻结受治理 IO/path 边界，但不决定对象层级与 admission policy。
- Boundary to gate decision / publication: 本 FEAT 约束 write/read carrier 与 receipt/registry 行为，不定义 approve/reject 等 decision semantics。
- Dedicated gateway placement is required so policy、IO execution、registry bind 与 receipt publication use one governed carrier.
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase
- test-run 失败用例应自动生成 detected 状态 bug 写入 registry: 应生成 detected 状态 bug 并写入对应 feat 的 bug registry。
- gate FAIL 应自动将 detected 提升为 open: bug status 应从 detected 变为 open，并生成 draft phase。
- ll-bug-remediate 应生成符合 GSD 规范的 bug fix phase: 应生成符合 GSD 规范的 {N}-bug-fix-{bug_id} phase。

### Informative / Context Only

- 依赖 FEAT-FRZ-055-003 的人工终止流程作为可选分支
- 依赖 FEAT-FRZ-055-004 的 gate PASS 归档流程作为可选分支

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/policy.py` [backend | extend | existing_match] <- `cli/lib/policy.py`: 定义 path / mode / overwrite 的 preflight verdict 规则。; nearby matches: cli/lib/spec_reconcile_policy.py, cli/lib/fs.py
- `cli/lib/fs.py` [backend | extend | existing_match] <- `cli/lib/fs.py`: 实现 governed read/write 的底层文件访问与 receipt 落盘。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/managed_gateway.py` [frontend | new | existing_match] <- `cli/lib/managed_gateway.py`: 编排 preflight、gateway commit、registry bind、receipt build。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/bug_registry.py` [frontend | extend | existing_match] <- `cli/lib/registry_store.py`: 记录 managed artifact ref、registry prerequisite 和 publish 状态。; nearby matches: cli/lib/frz_registry.py, cli/lib/registry_store.py
- `cli/commands/artifact/.gitkeep` [backend | extend | existing_match] <- `cli/commands/artifact/command.py`: 暴露 governed artifact commit / read 入口，依赖 cli/lib/managed_gateway.py。; nearby matches: cli/commands/artifact/command.py, cli/commands/artifact/__init__.py

### Repo Touch Points

- `cli/lib/policy.py` [backend | extend | existing_match] <- `cli/lib/policy.py`: 定义 path / mode / overwrite 的 preflight verdict 规则。; nearby matches: cli/lib/spec_reconcile_policy.py, cli/lib/fs.py
- `cli/lib/fs.py` [backend | extend | existing_match] <- `cli/lib/fs.py`: 实现 governed read/write 的底层文件访问与 receipt 落盘。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/managed_gateway.py` [frontend | new | existing_match] <- `cli/lib/managed_gateway.py`: 编排 preflight、gateway commit、registry bind、receipt build。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/bug_registry.py` [frontend | extend | existing_match] <- `cli/lib/registry_store.py`: 记录 managed artifact ref、registry prerequisite 和 publish 状态。; nearby matches: cli/lib/frz_registry.py, cli/lib/registry_store.py
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

- 说明: 本切片的主要实现对象是上文 `Repo Touch Points` 列出的代码/配置/文档路径。
- 说明: 下面列出的多数文件是 workflow 流程产物（evidence / review / handoff），用于审计与交接，不应替代工程对象本身的交付。
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
- backend-workstream.md

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
- backend-workstream.md

## 8. 验收标准与 TESTSET 映射

- testset_ref: `missing_authority`
- mapping_policy: `TESTSET_over_IMPL_when_present`
### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。, `cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。, `cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。, `cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。 Main sequence evidence covers: 1. normalize request; 2. preflight policy check; 3. registry prerequisite check. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. -> The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。; 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/policy.py` (`extend`): 定义 path / mode / overwrite 的 preflight verdict 规则。, `cli/lib/fs.py` (`extend`): 实现 governed read/write 的底层文件访问与 receipt 落盘。, `cli/lib/managed_gateway.py` (`new`): 编排 preflight、gateway commit、registry bind、receipt build。, `cli/lib/registry_store.py` (`extend`): 记录 managed artifact ref、registry prerequisite 和 publish 状态。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `GatewayWriteRequest`: input=`logical_path`, `path_class`, `mode`, `payload_ref`, `overwrite`; output=`managed_ref`, `write_receipt_ref`, `registry_record_ref`; errors=`policy_deny`, `registry_prerequisite_failed`, `write_failed`; idempotent=`conditional by logical_path + payload_digest + mode`; precondition=`path 已归类且 payload 可读`。 Main sequence evidence covers: 1. normalize request; 2. preflight policy check; 3. registry prerequisite check.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-007 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：runtime、formal publication 相关写入、governed skill 的正式写入都通过 `cli/commands/artifact/command.py` 进入 Gateway。; 挂接点：file-handoff 写入发生在 policy preflight 之后、registry bind 之前；external gate 读取 formal refs 时只消费 managed artifact ref。.

## 9. 执行顺序建议

### Required

- 1. Freeze refs and repo touch points: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- 2. Embed state, API, UI, and boundary contracts into implementation inputs: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- 3. Implement backend runtime, state, and persistence units: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- 4. Wire integration guards and downstream handoff: The main sequence executes in order and downstream handoff remains boundary-safe.
- 5. Collect acceptance evidence and close delivery handoff: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

### Suggested

- None.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/lib/managed_gateway.py, cli/lib/bug_registry.py, cli/commands/artifact/.gitkeep | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/managed_gateway.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/commands/artifact/.gitkeep | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-004 | parallel: none | touch_points: cli/lib/policy.py, cli/lib/fs.py, cli/lib/managed_gateway.py, cli/lib/bug_registry.py, cli/commands/artifact/.gitkeep | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- policy pass 但 registry prerequisite fail：拒绝写入，返回 `registry_prerequisite_failed`，不得绕过 registry 直接落盘。
- write success 但 receipt build fail：保留 staged artifact，标记 `receipt_pending`，禁止发布 managed ref 给 consumer。
- staging retention fail：允许主写入成功，但必须追加 degraded evidence，并要求后续 cleanup job 补偿。
- 三层分离原则：执行层（test-run）仅记录，验收层（gate）仅决策，修复层（GSD）仅修复
- 按 feat 隔离：每个 feat 有独立的 bug registry，避免跨 feat 干扰
- 依赖 FEAT-FRZ-055-003 的人工终止流程作为可选分支
