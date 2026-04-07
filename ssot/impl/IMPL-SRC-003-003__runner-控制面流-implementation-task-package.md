---
id: IMPL-SRC-003-003
ssot_type: IMPL
impl_ref: IMPL-SRC-003-003
tech_ref: TECH-SRC-003-003
feat_ref: FEAT-SRC-003-003
title: Runner 控制面流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: src003-adr042-impl-003-20260407-r2
candidate_package_ref: artifacts/tech-to-impl/src003-adr042-impl-003-20260407-r2
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-src003-adr042-impl-003-20260407-r2-impl-bundle-decision.json
frozen_at: '2026-04-07T06:04:54Z'
---

# IMPL-SRC-003-003

## 1. 任务标识

- impl_ref: `IMPL-SRC-003-003`
- title: Runner 控制面流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `src003-adr042-impl-003-20260407-r2`
- status: `execution_ready`
- derived_from: `FEAT-SRC-003-003`, `TECH-SRC-003-003`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。
- 完成标准: 5 个 required steps、5 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 定义 CLI control surface：ll loop run-execution、ll job claim、ll job run、ll job complete、ll job fail。
- 定义各控制命令与 runner lifecycle / job lifecycle 的映射关系。
- 定义控制面输出的结构化状态，而不是把操作结果留成隐式终端副作用。
- cli/lib/protocol.py (extend)
- cli/lib/runner_control.py (new)
- cli/lib/job_state.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-003` / `EPIC-SRC-003-001` / `FEAT-SRC-003-003` -> 冻结 runner 的 CLI 控制面，让启动、claim、run、complete、fail 等动作形成可设计、可审计的用户操作边界。
- TECH: `TECH-SRC-003-003` -> Freeze a concrete TECH design for Runner 控制面流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。; control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- ARCH: `ARCH-SRC-003-003` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-003-003` -> `RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。; `RunnerStateRecord`: input=`control_action_ref`; output=`state`, `job_ref`, `ownership_ref`; errors=`state_missing`; idempotent=`yes`; precondition=`control action recorded`。; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-003` (expected `UI-FEAT-SRC-003-003`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `TESTSET-SRC-003-003` -> Acceptance and evidence must remain mapped to TESTSET-SRC-003-003.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-SRC-003-003` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-003-003` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-003-003` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-003-003` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`bound` ref=`TESTSET-SRC-003-003` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: none

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-003-003` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for Runner 控制面流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。
- 控制动作必须产生可追踪的 command / state evidence。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `control_requested` -> `ownership_validated` -> `control_action_recorded` -> `runner_state_updated`
- `ownership_validated(fail)` -> `control_rejected`

### Main Sequence Snapshot

- 1. accept runner lifecycle command
- 2. validate runner context and ownership
- 3. apply control-plane state transition
- 4. publish control action record

### Integration Points Snapshot

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。

### Implementation Unit Mapping Snapshot

- cli/lib/protocol.py (extend): 定义 RunnerControlAction、RunnerStateRecord、JobOwnershipRef 结构。
- cli/lib/runner_control.py (new): 解析并执行 runner lifecycle CLI verbs。
- cli/lib/job_state.py (new): 管理 claimed/running/completed/failed 状态与 ownership guard。
- cli/commands/job/command.py (new): 暴露 claim / run / complete / fail 命令。

### API Contract Snapshot

- `RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。
- `RunnerStateRecord`: input=`control_action_ref`; output=`state`, `job_ref`, `ownership_ref`; errors=`state_missing`; idempotent=`yes`; precondition=`control action recorded`。

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-003` (expected `UI-FEAT-SRC-003-003`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `control_requested` -> `ownership_validated` -> `control_action_recorded` -> `runner_state_updated`
- `ownership_validated(fail)` -> `control_rejected`

#### API Contracts

- `RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。
- `RunnerStateRecord`: input=`control_action_ref`; output=`state`, `job_ref`, `ownership_ref`; errors=`state_missing`; idempotent=`yes`; precondition=`control action recorded`。

#### UI Entry

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。

#### UI Success Exit

- 4. publish control action record

#### UI Failure Exit

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。

#### Invariants

- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。
- 控制动作必须产生可追踪的 command / state evidence。
- CLI controls are explicit: start, claim, run, complete, fail or equivalent control commands must be explicit and stable.
- Control results are structured: the control surface must emit structured execution state rather than relying on ambiguous ad hoc logs.
- Runner control verbs are unified: The FEAT must define one unified runner CLI control surface instead of scattering control verbs across ad-hoc scripts or undocumented commands.

#### Boundary Guardrails

- Boundary to operator entry: 本 FEAT 依赖 runner skill entry，但不重新定义 start/resume 入口本身。
- Boundary to dispatch/outcome: 本 FEAT 冻结 runner 的控制面和 state transition，不直接拥有 next-skill invocation 或 final outcome semantics。
- Dedicated runner control placement is required so lifecycle commands, ownership guards, and control evidence share one authoritative carrier.
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。
- 控制动作必须产生可追踪的 command / state evidence。
- CLI controls are explicit: start, claim, run, complete, fail or equivalent control commands must be explicit and stable.
- Control results are structured: the control surface must emit structured execution state rather than relying on ambiguous ad hoc logs.
- Runner control verbs are unified: The FEAT must define one unified runner CLI control surface instead of scattering control verbs across ad-hoc scripts or undocumented commands.

### Informative / Context Only

- None.

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 RunnerControlAction、RunnerStateRecord、JobOwnershipRef 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/runner_entry.py` [backend | new | existing_match] <- `cli/lib/runner_control.py`: 解析并执行 runner lifecycle CLI verbs。; nearby matches: cli/lib/runner_monitor.py, cli/lib/execution_runner.py
- `cli/lib/fs.py` [backend | new | existing_match] <- `cli/lib/job_state.py`: 管理 claimed/running/completed/failed 状态与 ownership guard。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/commands/__init__.py` [backend | new | existing_match] <- `cli/commands/job/command.py`: 暴露 claim / run / complete / fail 命令。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Repo Touch Points

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 RunnerControlAction、RunnerStateRecord、JobOwnershipRef 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/runner_entry.py` [backend | new | existing_match] <- `cli/lib/runner_control.py`: 解析并执行 runner lifecycle CLI verbs。; nearby matches: cli/lib/runner_monitor.py, cli/lib/execution_runner.py
- `cli/lib/fs.py` [backend | new | existing_match] <- `cli/lib/job_state.py`: 管理 claimed/running/completed/failed 状态与 ownership guard。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/commands/__init__.py` [backend | new | existing_match] <- `cli/commands/job/command.py`: 暴露 claim / run / complete / fail 命令。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Boundary to operator entry: 本 FEAT 依赖 runner skill entry，但不重新定义 start/resume 入口本身。
- Boundary guardrail: Boundary to dispatch/outcome: 本 FEAT 冻结 runner 的控制面和 state transition，不直接拥有 next-skill invocation 或 final outcome semantics。
- Boundary guardrail: Dedicated runner control placement is required so lifecycle commands, ownership guards, and control evidence share one authoritative carrier.

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

- testset_ref: `TESTSET-SRC-003-003`
- mapping_policy: `TESTSET_over_IMPL_when_present`
### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `RunnerControlAction`、`RunnerStateRecord`、`JobOwnershipRef` 结构。, `cli/lib/runner_control.py` (`new`): 解析并执行 runner lifecycle CLI verbs。, `cli/lib/job_state.py` (`new`): 管理 claimed/running/completed/failed 状态与 ownership guard。, `cli/commands/job/command.py` (`new`): 暴露 `claim` / `run` / `complete` / `fail` 命令。. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-003`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。 Main sequence evidence covers: 1. accept runner lifecycle command; 2. validate runner context and ownership; 3. apply control-plane state transition. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-003`
- AC-003: Execution-runner lifecycle remains boundary-safe and ready for feature delivery. -> The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready. Integration evidence covers: 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。; 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-003`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `RunnerControlAction`、`RunnerStateRecord`、`JobOwnershipRef` 结构。, `cli/lib/runner_control.py` (`new`): 解析并执行 runner lifecycle CLI verbs。, `cli/lib/job_state.py` (`new`): 管理 claimed/running/completed/failed 状态与 ownership guard。, `cli/commands/job/command.py` (`new`): 暴露 `claim` / `run` / `complete` / `fail` 命令。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `RunnerControlAction`: input=`runner_context_ref`, `command`, `job_ref?`; output=`control_action_ref`, `runner_state_ref`; errors=`invalid_transition`, `ownership_conflict`; idempotent=`yes by runner_context_ref + command + job_ref`; precondition=`runner context active`。 Main sequence evidence covers: 1. accept runner lifecycle command; 2. validate runner context and ownership; 3. apply control-plane state transition.
- AC-003: Execution-runner lifecycle remains boundary-safe and ready for feature delivery. | implemented_by: TASK-005, TASK-007 | evidence: The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready. Integration evidence covers: 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。; 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。.

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

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/fs.py, cli/commands/__init__.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/fs.py, cli/commands/__init__.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-004 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/fs.py, cli/commands/__init__.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。
- boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。
- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
