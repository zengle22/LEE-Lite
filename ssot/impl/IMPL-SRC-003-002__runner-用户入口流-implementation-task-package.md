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
workflow_run_id: src003-adr042-impl-002-20260407-r2
candidate_package_ref: artifacts/tech-to-impl/src003-adr042-impl-002-20260407-r2
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-src003-adr042-impl-002-20260407-r2-impl-bundle-decision.json
frozen_at: '2026-04-07T06:04:29Z'
---

# IMPL-SRC-003-002

## 1. 任务标识

- impl_ref: `IMPL-SRC-003-002`
- title: Runner 用户入口流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `src003-adr042-impl-002-20260407-r2`
- status: `execution_ready`
- derived_from: `FEAT-SRC-003-002`, `TECH-SRC-003-002`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。
- 完成标准: 5 个 required steps、5 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 定义独立 skill 入口：Execution Loop Job Runner。
- 定义入口 skill 的最小输入、启动时机和与 ready queue 的绑定边界。
- 定义 operator 通过入口 skill 触发 runner 的责任，而不是继续依赖人工接力或隐式后台。
- cli/lib/protocol.py (extend)
- cli/lib/runner_entry.py (new)
- cli/lib/execution_runner.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-003` / `EPIC-SRC-003-001` / `FEAT-SRC-003-002` -> 冻结一个用户可显式调用的 Execution Loop Job Runner 入口 skill，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。
- TECH: `TECH-SRC-003-002` -> Freeze a concrete TECH design for Runner 用户入口流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。; 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- ARCH: `ARCH-SRC-003-002` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-003-002` -> `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。; `RunnerEntryReceipt`: input=`runner_run_ref`; output=`entry_mode`, `runner_context_ref`, `started_at`; errors=`receipt_missing`; idempotent=`yes`; precondition=`runner entry already accepted`。; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-002` (expected `UI-FEAT-SRC-003-002`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `TESTSET-SRC-003-002` -> Acceptance and evidence must remain mapped to TESTSET-SRC-003-002.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-SRC-003-002` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-003-002` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-003-002` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-003-002` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`bound` ref=`TESTSET-SRC-003-002` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: none

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-003-002` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for Runner 用户入口流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。
- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
- 入口调用必须保留 authoritative run context 与 lineage。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `runner_entry_requested` -> `runner_context_initialized` -> `runner_entry_published`
- `runner_entry_requested(resume)` -> `runner_context_restored` -> `runner_entry_published`

### Main Sequence Snapshot

- 1. accept start/resume request from Claude/Codex CLI
- 2. bootstrap or restore runner context
- 3. publish runner invocation receipt
- 4. hand off to queue consumption lifecycle

### Integration Points Snapshot

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。

### Implementation Unit Mapping Snapshot

- cli/lib/protocol.py (extend): 定义 ExecutionRunnerStartRequest、ExecutionRunnerRunRef、RunnerEntryReceipt 结构。
- cli/lib/runner_entry.py (new): 提供 runner skill start/resume 的入口适配层。
- cli/lib/execution_runner.py (new): 管理 runner context bootstrap 与恢复逻辑。
- cli/commands/loop/command.py (new): 暴露 run-execution / resume-execution 入口。

### API Contract Snapshot

- `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。
- `RunnerEntryReceipt`: input=`runner_run_ref`; output=`entry_mode`, `runner_context_ref`, `started_at`; errors=`receipt_missing`; idempotent=`yes`; precondition=`runner entry already accepted`。

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-002` (expected `UI-FEAT-SRC-003-002`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `runner_entry_requested` -> `runner_context_initialized` -> `runner_entry_published`
- `runner_entry_requested(resume)` -> `runner_context_restored` -> `runner_entry_published`

#### API Contracts

- `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。
- `RunnerEntryReceipt`: input=`runner_run_ref`; output=`entry_mode`, `runner_context_ref`, `started_at`; errors=`receipt_missing`; idempotent=`yes`; precondition=`runner entry already accepted`。

#### UI Entry

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。

#### UI Success Exit

- 4. hand off to queue consumption lifecycle

#### UI Failure Exit

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。

#### Invariants

- Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。
- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
- 入口调用必须保留 authoritative run context 与 lineage。
- Runner exposes a named skill entry: the product flow must expose a named runner skill entry instead of hiding start-up inside abstract background automation.
- Entry remains user-invokable: the entry must stay invokable by Claude/Codex CLI rather than requiring direct file edits or out-of-band orchestration.
- Runner skill entry is explicit: The FEAT must define one dedicated runner skill entry for Claude/Codex CLI instead of relying on implicit background behavior or manual downstream relays.

#### Boundary Guardrails

- Boundary to ready-job emission: 本 FEAT 不生成 ready job，只提供 operator 可见的 runner 启动/恢复入口。
- Boundary to control surface: 本 FEAT 只冻结 runner skill entry 与 run context bootstrap，不定义 job claim/run/complete/fail verbs。
- Dedicated runner entry placement is required so Claude/Codex CLI entry, run context bootstrap, and invocation receipt stay in one authoritative surface.
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。
- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
- 入口调用必须保留 authoritative run context 与 lineage。
- Runner exposes a named skill entry: the product flow must expose a named runner skill entry instead of hiding start-up inside abstract background automation.
- Entry remains user-invokable: the entry must stay invokable by Claude/Codex CLI rather than requiring direct file edits or out-of-band orchestration.
- Runner skill entry is explicit: The FEAT must define one dedicated runner skill entry for Claude/Codex CLI instead of relying on implicit background behavior or manual downstream relays.

### Informative / Context Only

- None.

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 ExecutionRunnerStartRequest、ExecutionRunnerRunRef、RunnerEntryReceipt 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/runner_entry.py` [backend | new | existing_match] <- `cli/lib/runner_entry.py`: 提供 runner skill start/resume 的入口适配层。; nearby matches: cli/lib/reentry.py, cli/lib/runner_monitor.py
- `cli/lib/execution_runner.py` [backend | new | existing_match] <- `cli/lib/execution_runner.py`: 管理 runner context bootstrap 与恢复逻辑。; nearby matches: cli/lib/runner_entry.py, cli/lib/runner_monitor.py
- `cli/commands/loop/command.py` [backend | new | existing_match] <- `cli/commands/loop/command.py`: 暴露 run-execution / resume-execution 入口。; nearby matches: cli/commands/loop/__init__.py, cli/commands/__init__.py

### Repo Touch Points

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 ExecutionRunnerStartRequest、ExecutionRunnerRunRef、RunnerEntryReceipt 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/runner_entry.py` [backend | new | existing_match] <- `cli/lib/runner_entry.py`: 提供 runner skill start/resume 的入口适配层。; nearby matches: cli/lib/reentry.py, cli/lib/runner_monitor.py
- `cli/lib/execution_runner.py` [backend | new | existing_match] <- `cli/lib/execution_runner.py`: 管理 runner context bootstrap 与恢复逻辑。; nearby matches: cli/lib/runner_entry.py, cli/lib/runner_monitor.py
- `cli/commands/loop/command.py` [backend | new | existing_match] <- `cli/commands/loop/command.py`: 暴露 run-execution / resume-execution 入口。; nearby matches: cli/commands/loop/__init__.py, cli/commands/__init__.py

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Boundary to ready-job emission: 本 FEAT 不生成 ready job，只提供 operator 可见的 runner 启动/恢复入口。
- Boundary guardrail: Boundary to control surface: 本 FEAT 只冻结 runner skill entry 与 run context bootstrap，不定义 job claim/run/complete/fail verbs。
- Boundary guardrail: Dedicated runner entry placement is required so Claude/Codex CLI entry, run context bootstrap, and invocation receipt stay in one authoritative surface.

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

- testset_ref: `TESTSET-SRC-003-002`
- mapping_policy: `TESTSET_over_IMPL_when_present`
### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `ExecutionRunnerStartRequest`、`ExecutionRunnerRunRef`、`RunnerEntryReceipt` 结构。, `cli/lib/runner_entry.py` (`new`): 提供 runner skill start/resume 的入口适配层。, `cli/lib/execution_runner.py` (`new`): 管理 runner context bootstrap 与恢复逻辑。, `cli/commands/loop/command.py` (`new`): 暴露 `run-execution` / `resume-execution` 入口。. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-002`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。 Main sequence evidence covers: 1. accept start/resume request from Claude/Codex CLI; 2. bootstrap or restore runner context; 3. publish runner invocation receipt. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-002`
- AC-003: Execution-runner lifecycle remains boundary-safe and ready for feature delivery. -> The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready. Integration evidence covers: 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。; 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `TESTSET-SRC-003-002`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `ExecutionRunnerStartRequest`、`ExecutionRunnerRunRef`、`RunnerEntryReceipt` 结构。, `cli/lib/runner_entry.py` (`new`): 提供 runner skill start/resume 的入口适配层。, `cli/lib/execution_runner.py` (`new`): 管理 runner context bootstrap 与恢复逻辑。, `cli/commands/loop/command.py` (`new`): 暴露 `run-execution` / `resume-execution` 入口。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。 Main sequence evidence covers: 1. accept start/resume request from Claude/Codex CLI; 2. bootstrap or restore runner context; 3. publish runner invocation receipt.
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

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/execution_runner.py, cli/commands/loop/command.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/execution_runner.py, cli/commands/loop/command.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-004 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/runner_entry.py, cli/lib/execution_runner.py, cli/commands/loop/command.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。
- boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。
- Execution Loop Job Runner 必须以独立 skill 入口暴露给 Claude/Codex CLI 用户。
- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
