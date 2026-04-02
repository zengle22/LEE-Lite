---
id: "IMPL-SRC-ADR036-RAW2SRC-20260402-R9-001"
ssot_type: IMPL
title: IMPL 主测试对象 intake 与 authority 绑定流
status: execution_ready
schema_version: 1.0.0
workflow_key: "dev.tech-to-impl"
workflow_run_id: "adr036-feat001-impl-r2"
source_refs:
- "dev.feat-to-tech::adr036-feat001-tech-r2"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-001"
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
- "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-001"
- "API-SRC-ADR036-RAW2SRC-20260402-R9-001"
candidate_artifact_ref: "artifacts/tech-to-impl/adr036-feat001-impl-r2/impl-task.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001"
tech_ref: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-001"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-001"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-001"
candidate_package_ref: "artifacts/tech-to-impl/adr036-feat001-impl-r2"
---

# IMPL-SRC-ADR036-RAW2SRC-20260402-R9-001

## 1. 任务标识

- impl_ref: `IMPL-SRC-ADR036-RAW2SRC-20260402-R9-001`
- title: IMPL 主测试对象 intake 与 authority 绑定流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `adr036-feat001-impl-r2`
- status: `execution_ready`
- derived_from: `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001`, `TECH-SRC-ADR036-RAW2SRC-20260402-R9-001`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 冻结 IMPL 进入 implementation start 前如何作为主测试对象被 intake，并与 FEAT / TECH / ARCH / API / UI / TESTSET authority 绑定。
- 完成标准: 6 个 required steps、6 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。
- 冻结 IMPL 主测试对象 intake 与 authority 绑定流 这一独立产品行为切片，并把它保持在产品层边界内。
- 该切片继承 main_test_object_priority、authority_binding 的统一约束，但不把 capability axis 直接下沉成实现任务。
- 对外交付 implementation readiness intake result，供下游能力直接继承。
- runtime.py (new)
- contracts.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-036, ADR-014, ADR-033, ADR-035 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-ADR036-RAW2SRC-20260402-R9` / `EPIC-IMPL-IMPLEMENTATION-READINESS` / `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` -> 冻结 IMPL 进入 implementation start 前如何作为主测试对象被 intake，并与 FEAT / TECH / ARCH / API / UI / TESTSET authority 绑定。
- TECH: `TECH-SRC-ADR036-RAW2SRC-20260402-R9-001` -> Freeze a concrete TECH design for IMPL 主测试对象 intake 与 authority 绑定流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。; 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- ARCH: `ARCH-SRC-ADR036-RAW2SRC-20260402-R9-001` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-ADR036-RAW2SRC-20260402-R9-001` -> `genericRequest`: freeze a machine-readable request/response contract before implementation.; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` (expected `TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-001`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-036, ADR-014, ADR-033, ADR-035` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-ADR036-RAW2SRC-20260402-R9-001` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for IMPL 主测试对象 intake 与 authority 绑定流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- IMPL 主测试对象 intake 与 authority 绑定流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- IMPL 主测试对象 intake 与 authority 绑定流 的完成态必须与“reviewer 能明确知道当前测试对象、authority refs 和执行模式。”对齐，不能只输出中间态、占位态或内部处理结果。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `prepared` -> `executed` -> `recorded`

### Main Sequence Snapshot

- 1. normalize request
- 2. execute authoritative carrier
- 3. persist evidence and refs
- 4. return structured result

### Integration Points Snapshot

- Caller enters through the governed CLI/runtime surface.
- Downstream consumers read only authoritative refs emitted by this FEAT.

### Implementation Unit Mapping Snapshot

- runtime.py (new): authoritative carrier
- contracts.py (new): request/response validation

### API Contract Snapshot

- `genericRequest`: freeze a machine-readable request/response contract before implementation.

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001` (expected `UI-FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `prepared` -> `executed` -> `recorded`

#### API Contracts

- `genericRequest`: freeze a machine-readable request/response contract before implementation.

#### UI Entry

- Caller enters through the governed CLI/runtime surface.
- Downstream consumers read only authoritative refs emitted by this FEAT.

#### UI Success Exit

- 4. return structured result

#### UI Failure Exit

- preserve authoritative partial state and return a repairable degraded status instead of fabricating success

#### Invariants

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- IMPL 主测试对象 intake 与 authority 绑定流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- IMPL 主测试对象 intake 与 authority 绑定流 的完成态必须与“reviewer 能明确知道当前测试对象、authority refs 和执行模式。”对齐，不能只输出中间态、占位态或内部处理结果。
- IMPL 主测试对象 intake 与 authority 绑定流 happy path reaches the declared completed state: reviewer 能明确知道当前测试对象、authority refs 和执行模式。
- IMPL 主测试对象 intake 与 authority 绑定流 keeps its declared product boundary: 该 FEAT 只覆盖“主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- IMPL 主测试对象 intake 与 authority 绑定流 hands downstream one authoritative product deliverable: 下游必须围绕 implementation readiness intake result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。
- 下游继承 IMPL 主测试对象 intake 与 authority 绑定流 时必须保留 implementation readiness intake result 这一 authoritative product deliverable，不能自行改写产品边界。

#### Boundary Guardrails

- 主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。
- 冻结 IMPL 主测试对象 intake 与 authority 绑定流 这一独立产品行为切片，并把它保持在产品层边界内。
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- IMPL 主测试对象 intake 与 authority 绑定流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- IMPL 主测试对象 intake 与 authority 绑定流 的完成态必须与“reviewer 能明确知道当前测试对象、authority refs 和执行模式。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 IMPL 主测试对象 intake 与 authority 绑定流 时必须保留 implementation readiness intake result 这一 authoritative product deliverable，不能自行改写产品边界。
- IMPL 主测试对象 intake 与 authority 绑定流 必须继续受 main_test_object_priority、authority_binding 的统一约束约束，而不是在下游重新发明同题语义。
- IMPL 主测试对象 intake 与 authority 绑定流 happy path reaches the declared completed state: reviewer 能明确知道当前测试对象、authority refs 和执行模式。
- IMPL 主测试对象 intake 与 authority 绑定流 keeps its declared product boundary: 该 FEAT 只覆盖“主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- IMPL 主测试对象 intake 与 authority 绑定流 hands downstream one authoritative product deliverable: 下游必须围绕 implementation readiness intake result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。

### Informative / Context Only

- None.

## 6. 实施要求

### Touch Set / Module Plan

- `tools/ci/checks_runtime.py` [backend | new | existing_match] <- `runtime.py`: authoritative carrier; nearby matches: cli/lib/mainline_runtime.py, cli/lib/test_exec_runtime.py
- `skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json` [shared | new | existing_match] <- `contracts.py`: request/response validation; nearby matches: skills/ll-product-raw-to-src/resources/contracts/raw-to-src/job-proposal.schema.json, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/patch-lineage.schema.json

### Repo Touch Points

- `tools/ci/checks_runtime.py` [backend | new | existing_match] <- `runtime.py`: authoritative carrier; nearby matches: cli/lib/mainline_runtime.py, cli/lib/test_exec_runtime.py
- `skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json` [shared | new | existing_match] <- `contracts.py`: request/response validation; nearby matches: skills/ll-product-raw-to-src/resources/contracts/raw-to-src/job-proposal.schema.json, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/patch-lineage.schema.json

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: 主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。
- Boundary guardrail: 冻结 IMPL 主测试对象 intake 与 authority 绑定流 这一独立产品行为切片，并把它保持在产品层边界内。
- Boundary guardrail: 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。

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

## 8. 验收标准与 TESTSET 映射

- testset_ref: `missing_authority`
- mapping_policy: `TESTSET_over_IMPL_when_present`
### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `runtime.py` (`new`): authoritative carrier, `contracts.py` (`new`): request/response validation. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `genericRequest`: freeze a machine-readable request/response contract before implementation. Main sequence evidence covers: 1. normalize request; 2. execute authoritative carrier; 3. persist evidence and refs. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. -> The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: Caller enters through the governed CLI/runtime surface.; Downstream consumers read only authoritative refs emitted by this FEAT.. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `runtime.py` (`new`): authoritative carrier, `contracts.py` (`new`): request/response validation.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `genericRequest`: freeze a machine-readable request/response contract before implementation. Main sequence evidence covers: 1. normalize request; 2. execute authoritative carrier; 3. persist evidence and refs.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-007 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: Caller enters through the governed CLI/runtime surface.; Downstream consumers read only authoritative refs emitted by this FEAT..

## 9. 执行顺序建议

### Required

- 1. Freeze refs and repo touch points: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- 2. Embed state, API, UI, and boundary contracts into implementation inputs: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- 3. Implement frontend entry and exit surfaces: Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.
- 4. Implement backend runtime, state, and persistence units: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- 5. Wire integration guards and downstream handoff: The main sequence executes in order and downstream handoff remains boundary-safe.
- 6. Collect acceptance evidence and close delivery handoff: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

### Suggested

- None.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: tools/ci/checks_runtime.py, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json, tools/ci/checks_runtime.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-003 Implement frontend entry and exit surfaces | depends_on: TASK-001, TASK-002 | parallel: TASK-004 | touch_points: none | outputs: frontend surface, entry/exit behavior, field/error rendering | acceptance: AC-001, AC-002 | done_when: Frontend entry/exit behavior is explicit, bounded, and traceable to acceptance.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: TASK-003 | touch_points: tools/ci/checks_runtime.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003, TASK-004 | parallel: none | touch_points: tools/ci/checks_runtime.py, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- preserve authoritative partial state and return a repairable degraded status instead of fabricating success
- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
