---
id: IMPL-SRC-RAW-TO-SRC-ADR048-001
ssot_type: IMPL
impl_ref: IMPL-SRC-RAW-TO-SRC-ADR048-001
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
title: 主链候选提交与交接流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: raw-to-src-adr048-feat-src-raw-to-src-adr048-001--001-e894a1dd
candidate_package_ref: artifacts/tech-to-impl/raw-to-src-adr048-feat-src-raw-to-src-adr048-001--001-e894a1dd
frozen_at: '2026-04-11T06:28:44.280013+00:00'
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
  tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
  authority_refs:
  - ARCH-SRC-RAW-TO-SRC-ADR048-001
  - API-SRC-RAW-TO-SRC-ADR048-001
  - ADR-048
  - ADR-047
provisional_refs: []
freshness_status: manual_snapshot_requires_rederive_on_upstream_change
rederive_triggers:
- upstream_ref_version_change
- acceptance_contract_change
- ui_api_testset_contract_change
main_sequence:
- step: 1
  task: TASK-001
  name: Freeze refs and repo touch points
  depends_on: []
  parallel: []
  touch_points:
  - cli/lib/protocol.py
  - cli/lib/mainline_runtime.py
  - cli/lib/reentry.py
  - cli/commands/__init__.py
  - cli/commands/audit/command.py
  outputs:
  - frozen upstream refs
  - repo-aware touch set
  - execution boundary baseline
  done_when: The implementation package states exactly where coding may occur and
    which upstream refs remain authoritative.
- step: 2
  task: TASK-002
  name: Embed state, API, UI, and boundary contracts
  depends_on:
  - TASK-001
  parallel: []
  touch_points:
  - cli/lib/protocol.py
  - cli/lib/reentry.py
  outputs:
  - embedded execution contract
  - boundary-safe implementation baseline
  done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API
    documents to recover execution-critical facts.
- step: 3
  task: TASK-003
  name: Implement backend runtime, state, and persistence units
  depends_on:
  - TASK-001
  - TASK-002
  parallel: []
  touch_points:
  - cli/lib/protocol.py
  - cli/lib/mainline_runtime.py
  - cli/commands/__init__.py
  outputs:
  - runtime units
  - state readers/writers
  - contract-aligned responses
  done_when: Backend runtime units satisfy the frozen state machine and interface
    contracts without redefining ownership.
- step: 4
  task: TASK-004
  name: Wire integration guards and downstream handoff
  depends_on:
  - TASK-002
  - TASK-003
  parallel: []
  touch_points:
  - cli/lib/protocol.py
  - cli/lib/mainline_runtime.py
  - cli/lib/reentry.py
  - cli/commands/__init__.py
  - cli/commands/audit/command.py
  outputs:
  - integration wiring
  - guard behavior
  - handoff-ready package
  done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- step: 5
  task: TASK-005
  name: Collect acceptance evidence and close delivery handoff
  depends_on:
  - TASK-004
  parallel: []
  touch_points: []
  outputs:
  - acceptance evidence
  - smoke gate inputs
  - delivery handoff
  done_when: Every acceptance check is implemented by named tasks and backed by explicit
    evidence artifacts.
touch_set:
- path: cli/lib/protocol.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Define HandoffEnvelope, PendingVisibilityRecord, DecisionReturnEnvelope,
    ReentryDirective structures
- path: cli/lib/mainline_runtime.py
  layer: backend
  action: new
  ownership: owned
  responsibility: Manage authoritative submission, pending visibility, decision-return
    intake, and boundary handoff record
- path: cli/lib/reentry.py
  layer: backend
  action: new
  ownership: owned
  responsibility: Handle revise/retry runtime routing, directive writeback, and replay
    guard without owning decision semantics
- path: cli/commands/__init__.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Wire submit-handoff and show-pending paths into gate command consumer
- path: cli/commands/audit/command.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Human review escalation side-consumer writing structured review
    context
implementation_readiness: ready
non_goals:
- formalization semantics
- decision vocabulary
- gate decision issuance
- formal publication triggers
- downstream read eligibility rules
implementation_units:
- unit: protocol.py
  path: cli/lib/protocol.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: HandoffEnvelope, PendingVisibilityRecord, DecisionReturnEnvelope,
    ReentryDirective structures
- unit: mainline_runtime.py
  path: cli/lib/mainline_runtime.py
  layer: backend
  action: new
  ownership: owned
  responsibility: Authoritative submission, pending visibility, decision-return intake,
    boundary handoff record
- unit: reentry.py
  path: cli/lib/reentry.py
  layer: backend
  action: new
  ownership: owned
  responsibility: Revise/retry runtime routing, directive writeback, replay guard
- unit: gate_command.py
  path: cli/commands/__init__.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Wire submit-handoff / show-pending paths
- unit: audit_command.py
  path: cli/commands/audit/command.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Human review escalation structured review context
---




# 主链候选提交与交接流 Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Freeze refs and repo touch points | depends_on: none | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/lib/reentry.py, cli/commands/__init__.py, cli/commands/audit/command.py | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- Step 2: TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | touch_points: cli/lib/protocol.py, cli/lib/reentry.py | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- Step 3: TASK-003 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/commands/__init__.py | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- Step 4: TASK-004 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003 | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/lib/reentry.py, cli/commands/__init__.py, cli/commands/audit/command.py | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- Step 5: TASK-005 Collect acceptance evidence and close delivery handoff | depends_on: TASK-004 | touch_points: none | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## Implementation Unit Mapping Snapshot

- `cli/lib/protocol.py` [backend | extend | owned]: Define HandoffEnvelope, PendingVisibilityRecord, DecisionReturnEnvelope, ReentryDirective structures.
- `cli/lib/mainline_runtime.py` [backend | new | owned]: Manage authoritative submission, pending visibility, decision-return intake, and boundary handoff record.
- `cli/lib/reentry.py` [backend | new | owned]: Handle revise/retry runtime routing, directive writeback, and replay guard without owning decision semantics.
- `cli/commands/__init__.py` [backend | extend | owned]: Wire submit-handoff and show-pending paths into gate command consumer.
- `cli/commands/audit/command.py` [backend | extend | owned]: Human review escalation side-consumer writing structured review context.

## State Model Snapshot

- State transitions: `handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`
- Re-entry: `decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`
- Terminal: `decision_returned(approve|handoff|reject)` -> `boundary_handoff_recorded` -> downstream consumption
- Completion signals: handoff_submitted, decision_returned, reentry_directive_written, boundary_handoff_recorded
- Failure signals: invalid_state (handoff submission from non-prepared state), missing_payload (handoff references non-existent payload), duplicate_submission (handoff already exists), decision_conflict (gate decision contradicts existing state), handoff_missing (decision return without prior handoff)
- Recovery: revise/retry routing via runtime reentry directive, fail-closed on visibility build failure

## Integration Points Snapshot

- producer skill -> cli/commands/gate/command.py -> cli/lib/mainline_runtime.py: authoritative handoff submission
- gate loop -> decision_returned -> runtime re-entry routing: revise/retry/approve/handoff/reject dispatch
- cli/commands/audit/command.py: human review escalation side-consumer for structured review context
- Backward compat: old skills without re-entry routing observe pending visibility in compat mode only

## Selected Upstream

- feat_ref: `FEAT-SRC-RAW-TO-SRC-ADR048-001`
- tech_ref: `TECH-SRC-RAW-TO-SRC-ADR048-001`
- arch_ref: `ARCH-SRC-RAW-TO-SRC-ADR048-001`
- api_ref: `API-SRC-RAW-TO-SRC-ADR048-001`
- title: 主链候选提交与交接流
- goal: 冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-048, ADR-047` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-SRC-RAW-TO-SRC-ADR048-001` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-RAW-TO-SRC-ADR048-001` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-RAW-TO-SRC-ADR048-001` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-RAW-TO-SRC-ADR048-001` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-RAW-TO-SRC-ADR048-001` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

## Package Semantics

- IMPL is the canonical execution package / execution-time single entrypoint for this run.
- IMPL is not the business, design, or test truth source.
- freshness_status: `fresh_on_generation`
- provisional_refs: 0
- repo_discrepancy_status: `placement_projected_from_repo_root`
- self-contained policy: `strong_self_contained_execution_contract`.
- execution-critical expansions: repo_touch_points, embedded_execution_contract, implementation_task_breakdown, acceptance_to_task_mapping, acceptance_trace, critical_interfaces_and_boundaries, deliverables.

## Applicability Assessment

- frontend_required: False
  - No explicit UI/page/component implementation surface was detected.
- backend_required: True
  - Detected runtime/service/contract surface: gate, io, runtime.
- migration_required: False
  - No migration, cutover, rollback, or compat-mode surface was detected.

## Implementation Task

### Concrete Touch Set

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 HandoffEnvelope、PendingVisibilityRecord、DecisionReturnEnvelope、ReentryDirective 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/mainline_runtime.py` [backend | new | existing_match] <- `cli/lib/mainline_runtime.py`: 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/reentry.py` [frontend | new | existing_match] <- `cli/lib/reentry.py`: 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/commands/__init__.py` [backend | extend | existing_match] <- `cli/commands/gate/command.py`: 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 cli/lib/mainline_runtime.py 消费。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep
- `cli/commands/audit/command.py` [frontend | extend | existing_match] <- `cli/commands/audit/command.py`: 作为 human review escalation 的旁路消费方，回写 structured review context 而非 formalization result。; nearby matches: cli/commands/audit/__init__.py, cli/commands/__init__.py

### Repo-Aware Placement

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 HandoffEnvelope、PendingVisibilityRecord、DecisionReturnEnvelope、ReentryDirective 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/mainline_runtime.py` [backend | new | existing_match] <- `cli/lib/mainline_runtime.py`: 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/reentry.py` [frontend | new | existing_match] <- `cli/lib/reentry.py`: 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/commands/__init__.py` [backend | extend | existing_match] <- `cli/commands/gate/command.py`: 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 cli/lib/mainline_runtime.py 消费。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep
- `cli/commands/audit/command.py` [frontend | extend | existing_match] <- `cli/commands/audit/command.py`: 作为 human review escalation 的旁路消费方，回写 structured review context 而非 formalization result。; nearby matches: cli/commands/audit/__init__.py, cli/commands/__init__.py

### Embedded Frozen Contracts

#### State Machine

- `handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`
- `decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`
- `decision_returned(approve|handoff|reject)` -> `boundary_handoff_recorded`，由 formalization / downstream runtime 消费后续推进

#### API Contracts

- `HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`; errors=`invalid_state`, `missing_payload`, `duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。
- `DecisionReturnEnvelope` (consumed): input=`handoff_ref`, `decision_ref`, `decision`, `routing_hint`, `trace_ref`; output=`boundary_handoff_record | reentry_directive`; errors=`decision_conflict`, `handoff_missing`; idempotent=`yes by handoff_ref + decision_ref`; precondition=`decision object 已由 external gate authoritative emit`。

#### UI Entry

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。

#### UI Success Exit

- 6. if decision in {approve, handoff, reject}, persist boundary handoff record without materializing formal output here

#### UI Failure Exit

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。

#### Invariants

- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Epic-level constraints：FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。
- Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。
- Loop responsibility split is explicit: The FEAT must define which loop owns which transition, input object, and return path without overlapping formalization responsibilities.
- Downstream flows do not redefine collaboration rules: It must inherit the same collaboration rules instead of inventing a parallel queue or handoff model.
- Submission completion only exposes authoritative handoff and pending visibility; decision-driven revise/retry routing stays in runtime while gate decision issuance and formal publication semantics remain outside this FEAT.
- 该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。

#### Boundary Guardrails

- Boundary to gate decision / publication: 本 FEAT 负责 authoritative handoff submission、gate-pending visibility 与 decision-driven runtime re-entry routing，不负责 decision vocabulary、decision issuance 与 formal publication trigger semantics。
- Boundary to admission/layering: 本 FEAT 可以提交 candidate / proposal / evidence，但 formal admission、formal refs 与 downstream read eligibility 由对象分层 FEAT 决定。
- Dedicated runtime placement is required so submission receipt、pending visibility 和 re-entry routing 由同一 authoritative carrier 负责，而不是散落在 producer skill 或 gate worker 中。
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- 提交与 pending 可见性命令不得偷带决策语义；`approve / revise / retry / handoff / reject` 只能留在 gate decision FEAT。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/lib/reentry.py, cli/commands/__init__.py, cli/commands/audit/command.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/reentry.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-003 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/commands/__init__.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-004 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/mainline_runtime.py, cli/lib/reentry.py, cli/commands/__init__.py, cli/commands/audit/command.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-005 Collect acceptance evidence and close delivery handoff | depends_on: TASK-004 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## Integration Plan

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。
- Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。
- Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。
- 按已冻结主时序接线：1. normalize candidate/proposal/evidence submission and producer state; 2. persist authoritative handoff object and emit gate-pending visibility; 3. route proposal into gate loop and escalate to human review when required。

## Evidence Plan

- AC-001: backend-verification, smoke-review-input
- AC-002: backend-verification, smoke-review-input
- AC-003: backend-verification, smoke-review-input

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-003, TASK-005 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`PendingVisibilityRecord`、`DecisionReturnEnvelope`、`ReentryDirective` 结构。, `cli/lib/mainline_runtime.py` (`new`): 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。, `cli/lib/reentry.py` (`new`): 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。, `cli/commands/gate/command.py` (`extend`): 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 `cli/lib/mainline_runtime.py` 消费。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-005 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`; errors=`invalid_state`, `missing_payload`, `duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。 Main sequence evidence covers: 1. normalize candidate/proposal/evidence submission and producer state; 2. persist authoritative handoff object and emit gate-pending visibility; 3. route proposal into gate loop and escalate to human review when required.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-004, TASK-005 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。; 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。.

## Smoke Gate Subject

- See `smoke-gate-subject.json` for the current `status`, `decision`, and `ready_for_execution` state.

## Delivery Handoff

- target_template_id: `template.dev.feature_delivery_l2`
- primary_artifact_ref: `impl-bundle.json`
- phase_inputs: implementation_task, backend, integration, evidence, upstream_design

## Consumption Boundary

- Release summaries and execution evidence are downstream artifacts, not the coder/tester execution contract.
- `impl-bundle.md` must remain self-contained enough for intake review and execution planning.
- `impl-task.md` expands the same package but may not become the only place where execution-critical facts live.
- bundle/task shared execution-critical domains: repo_touch_points, embedded_execution_contract, implementation_task_breakdown, acceptance_to_task_mapping, acceptance_trace, critical_interfaces_and_boundaries, deliverables.

## Traceability

- dev.feat-to-tech::raw-to-src-adr048--feat-src-raw-to-src-adr048-001
- FEAT-SRC-RAW-TO-SRC-ADR048-001
- TECH-SRC-RAW-TO-SRC-ADR048-001
- product.epic-to-feat::raw-to-src-adr048
- EPIC-RAW-TO-SRC-ADR048
- SRC-RAW-TO-SRC-ADR048
- SURFACE-MAP-FEAT-SRC-RAW-TO-SRC-ADR048-001
- product.raw-to-src::raw-to-src-adr048
- ssot/adr/ADR-048-SSOT-与双链测试接入-Droid-Missions-的统一治理架构.md
- ADR-048
- ADR-047
- product.src-to-epic::raw-to-src-adr048
- ADR-034
- ARCH-SRC-RAW-TO-SRC-ADR048-001
- API-SRC-RAW-TO-SRC-ADR048-001

## Completion Signals

- **handoff_submitted**: authoritative handoff object persisted, gate_pending_ref emitted
- **decision_returned**: gate decision consumed, routing hint applied (revise|retry|approve|handoff|reject)
- **reentry_directive_written**: runtime re-entry directive persisted for revise/retry paths
- **boundary_handoff_recorded**: boundary handoff record written for approve/handoff/reject paths

### State Model

- State transitions: `handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`
- Re-entry: `decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`
- Terminal: `decision_returned(approve|handoff|reject)` -> `boundary_handoff_recorded` -> downstream consumption

### Failure Signals

- `invalid_state`: handoff submission attempted from non-prepared state
- `missing_payload`: handoff envelope references non-existent payload
- `duplicate_submission`: handoff already exists for producer_ref + proposal_ref
- `decision_conflict`: gate decision contradicts existing handoff state
- `handoff_missing`: decision return attempted without prior handoff record
