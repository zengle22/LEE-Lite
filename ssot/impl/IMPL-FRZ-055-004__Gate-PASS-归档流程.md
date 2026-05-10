---
id: "IMPL-FRZ-055-004"
ssot_type: IMPL
title: Gate PASS 归档流程
status: execution_ready
schema_version: 1.0.0
workflow_key: "dev.tech-to-impl"
workflow_run_id: "frz-055-bug-lifecycle-20260507--feat-frz-055-004--tech-frz-055-004"
source_refs:
- "dev.feat-to-tech::frz-055-bug-lifecycle-20260507--feat-frz-055-004"
- "FEAT-FRZ-055-004"
- "TECH-FRZ-055-004"
- "EPIC:EPIC-FRZ-055-20260507"
- "SRC:FRZ-055"
- "SURFACE:SURFACE-MAP-FEAT-FRZ-055-004"
- "product.epic-to-feat::frz-055-bug-lifecycle-20260507"
- "EPIC-FRZ-055-20260507"
- "FRZ-055"
- "SURFACE-MAP-FEAT-FRZ-055-004"
- "ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md"
- "ssot/frz/FRZ-055/frz.yaml"
- "SRC-FRZ-055-20260507"
- "ADR-055"
- "ADR-034"
candidate_artifact_ref: "artifacts/tech-to-impl/frz-055-bug-lifecycle-20260507--feat-frz-055-004--tech-frz-055-004/impl-task.md"
gate_decision_ref: "artifacts/active/gates/decisions/frz055-chain-manual-approval-20260507.json"
parent_id: "FEAT-FRZ-055-004"
tech_ref: "TECH-FRZ-055-004"
candidate_package_ref: "artifacts/tech-to-impl/frz-055-bug-lifecycle-20260507--feat-frz-055-004--tech-frz-055-004"
---

# IMPL-FRZ-055-004

## 1. 任务标识

- impl_ref: `IMPL-FRZ-055-004`
- title: Gate PASS 归档流程 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `frz-055-bug-lifecycle-20260507--feat-frz-055-004--tech-frz-055-004`
- status: `execution_ready`
- derived_from: `FEAT-FRZ-055-004`, `TECH-FRZ-055-004`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 建立 settlement 分析认为是环境问题/flaky 后，gate PASS 自动归档为 archived 的流程。
- 完成标准: 5 个 required steps、5 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- test-run 发现失败用例 → detected
- settlement 分析认为是环境问题/flaky
- gate-evaluate 输出 PASS verdict
- detected bug 自动降级为 archived
- runtime.py (new)
- contracts.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-055 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-FRZ-055-20260507` / `EPIC-FRZ-055-20260507` / `FEAT-FRZ-055-004` -> 建立 settlement 分析认为是环境问题/flaky 后，gate PASS 自动归档为 archived 的流程。
- TECH: `TECH-FRZ-055-004` -> Freeze a concrete TECH design for Gate PASS 归档流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; archived 状态的 bug 不应触发后续修复流程; 归档操作必须记录审计日志
- ARCH: `not present` -> No explicit ARCH ref selected for this run.
- API: `not present` -> No explicit API ref selected for this run.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-FRZ-055-004` (expected `UI-FEAT-FRZ-055-004`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-FRZ-055-004` (expected `TESTSET-FRZ-055-004`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-055` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-FRZ-055-004` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`not_selected` ref=`unspecified` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`not_selected` ref=`unspecified` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-FRZ-055-004` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-FRZ-055-004` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-FRZ-055-004` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-FRZ-055-004` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for Gate PASS 归档流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- archived 状态的 bug 不应触发后续修复流程
- 归档操作必须记录审计日志
- gate PASS 应将 detected 降级为 archived: bug status 应从 detected 降级为 archived，并记录审计日志。
- archived 状态 bug 不应触发后续修复流程: 系统应跳过该 bug，不生成 draft phase，不触发修复流程。

### ARCH Constraint Snapshot

- No explicit ARCH ref selected for this run.

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

- None.

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-FRZ-055-004` (expected `UI-FEAT-FRZ-055-004`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

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

- archived 状态的 bug 不应触发后续修复流程
- 归档操作必须记录审计日志
- gate PASS 应将 detected 降级为 archived: bug status 应从 detected 降级为 archived，并记录审计日志。
- archived 状态 bug 不应触发后续修复流程: 系统应跳过该 bug，不生成 draft phase，不触发修复流程。
- 归档流程应完整记录审计日志: 审计日志应包含时间戳、bug_id、之前状态 detected、新状态 archived、settlement 分析结论、gate PASS verdict、操作者信息等完整记录。

#### Boundary Guardrails

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- archived 状态的 bug 不应触发后续修复流程
- 归档操作必须记录审计日志
- gate PASS 应将 detected 降级为 archived: bug status 应从 detected 降级为 archived，并记录审计日志。
- archived 状态 bug 不应触发后续修复流程: 系统应跳过该 bug，不生成 draft phase，不触发修复流程。
- 归档流程应完整记录审计日志: 审计日志应包含时间戳、bug_id、之前状态 detected、新状态 archived、settlement 分析结论、gate PASS verdict、操作者信息等完整记录。

### Informative / Context Only

- 依赖 gate-evaluate 提供 PASS verdict

## 6. 实施要求

### Touch Set / Module Plan

- `tools/ci/checks_runtime.py` [backend | new | existing_match] <- `runtime.py`: authoritative carrier; nearby matches: cli/lib/mainline_runtime.py, cli/lib/qa_skill_runtime.py
- `cli/lib/contracts.py` [shared | new | existing_match] <- `contracts.py`: request/response validation; nearby matches: tests/test_ui_derivation_contracts.py, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json

### Repo Touch Points

- `tools/ci/checks_runtime.py` [backend | new | existing_match] <- `runtime.py`: authoritative carrier; nearby matches: cli/lib/mainline_runtime.py, cli/lib/qa_skill_runtime.py
- `cli/lib/contracts.py` [shared | new | existing_match] <- `contracts.py`: request/response validation; nearby matches: tests/test_ui_derivation_contracts.py, skills/ll-product-raw-to-src/resources/contracts/raw-to-src/run-state.schema.json

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Boundary guardrail: Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Boundary guardrail: Do not expand touch set beyond declared modules without re-derive or revision review.

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

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `runtime.py` (`new`): authoritative carrier, `contracts.py` (`new`): request/response validation. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `genericRequest`: freeze a machine-readable request/response contract before implementation. Main sequence evidence covers: 1. normalize request; 2. execute authoritative carrier; 3. persist evidence and refs. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. -> The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: Caller enters through the governed CLI/runtime surface.; Downstream consumers read only authoritative refs emitted by this FEAT.. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `runtime.py` (`new`): authoritative carrier, `contracts.py` (`new`): request/response validation.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `genericRequest`: freeze a machine-readable request/response contract before implementation. Main sequence evidence covers: 1. normalize request; 2. execute authoritative carrier; 3. persist evidence and refs.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-007 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: Caller enters through the governed CLI/runtime surface.; Downstream consumers read only authoritative refs emitted by this FEAT..

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

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: tools/ci/checks_runtime.py, cli/lib/contracts.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/contracts.py, tools/ci/checks_runtime.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: tools/ci/checks_runtime.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-004 | parallel: none | touch_points: tools/ci/checks_runtime.py, cli/lib/contracts.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- preserve authoritative partial state and return a repairable degraded status instead of fabricating success
- archived 状态的 bug 不应触发后续修复流程
- 归档操作必须记录审计日志
- 依赖 gate-evaluate 提供 PASS verdict
