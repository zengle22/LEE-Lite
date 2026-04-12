---
id: IMPL-SRC-RAW-TO-SRC-ADR048-002
ssot_type: IMPL
impl_ref: IMPL-SRC-RAW-TO-SRC-ADR048-002
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-002
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-002
arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-002
api_ref: API-SRC-RAW-TO-SRC-ADR048-002
title: 主链gate审核与裁决流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: tech-to-impl-adr048-feat002
candidate_package_ref: artifacts/tech-to-impl/tech-to-impl-adr048-feat002
frozen_at: '2026-04-11T15:46:08.000000+00:00'
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-002
  tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-002
  authority_refs:
  - ARCH-SRC-RAW-TO-SRC-ADR048-002
  - API-SRC-RAW-TO-SRC-ADR048-002
  - ADR-034
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
  - cli/lib/registry_store.py
  - cli/commands/__init__.py
  outputs:
  - frozen upstream refs
  - repo-aware touch set
  - execution boundary baseline
  done_when: The implementation package states exactly where coding may occur and
    which upstream refs remain authoritative.
- step: 2
  task: TASK-002
  name: Embed state, API, UI, and boundary contracts into implementation inputs
  depends_on:
  - TASK-001
  parallel: []
  touch_points:
  - cli/lib/protocol.py
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
  - cli/lib/registry_store.py
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
  - cli/lib/registry_store.py
  - cli/commands/__init__.py
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
  responsibility: Define GateBriefRecord, GatePendingHumanDecision, GateDecision structures
- path: cli/lib/registry_store.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Write brief/decision trace, decision_target, decision_basis_refs and dispatch receipt
- path: cli/commands/__init__.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Wire evaluate / dispatch semantics, generate brief record, decision object and return pipeline
implementation_readiness: ready
non_goals:
- formal publication / consumer admission policy
- decision vocabulary redefinition
- migration / cutover / rollback
- UI component implementation
- formal publication semantics
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
  responsibility: GateBriefRecord, GatePendingHumanDecision, GateDecision structures
- unit: registry_store.py
  path: cli/lib/registry_store.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Brief/decision trace, decision_target, decision_basis_refs, dispatch receipt
- unit: gate_command.py
  path: cli/commands/__init__.py
  layer: backend
  action: extend
  ownership: owned
  responsibility: Evaluate / dispatch semantics, brief record, decision object, return pipeline
---



# 主链gate审核与裁决流 Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Freeze refs and repo touch points | depends_on: none | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- Step 2: TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | touch_points: cli/lib/protocol.py | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- Step 3: TASK-003 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- Step 4: TASK-004 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003 | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- Step 5: TASK-005 Collect acceptance evidence and close delivery handoff | depends_on: TASK-004 | touch_points: none | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## Implementation Unit Mapping Snapshot

- `cli/lib/protocol.py` [backend | extend | owned]: Define GateBriefRecord, GatePendingHumanDecision, GateDecision structures.
- `cli/lib/registry_store.py` [backend | extend | owned]: Write brief/decision trace, decision_target, decision_basis_refs and dispatch receipt.
- `cli/commands/__init__.py` [backend | extend | owned]: Wire evaluate / dispatch semantics, generate brief record, decision object and return pipeline.

## State Model Snapshot

- State transitions: `candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued` -> `execution_returned|delegated|publication_triggered|rejected`
- Revision loop: `decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`
- Retry loop: `decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`
- Completion signals: decision_issued_done, execution_returned_done, delegated_done, publication_triggered_done, rejected_done.
- Failure signals: invalid_state, brief_build_failed, unknown_target, missing_basis_refs, policy_reject.
- Recovery: on `invalid_state`, reject with clear error, allow candidate re-preparation and retry.
- Recovery: on `brief_build_failed`, preserve candidate data, log failure detail, allow retry with corrected input.
- Recovery: on `unknown_target`, reject dispatch, require valid target resolution, allow resubmission.
- Recovery: on `missing_basis_refs`, reject decision, require basis ref supplementation, allow retry.
- Recovery: on `policy_reject`, route to rejection handler, preserve evidence, require manual resolution for retry.
- Recovery: revise/retry routing via decision_issued branching, fail-closed on brief build or decision capture failure.

## Integration Points Snapshot

- governed skill -> handoff runtime -> cli/commands/gate/command.py: candidate package submission for evaluate / dispatch
- cli/commands/gate/command.py -> cli/lib/protocol.py: GateBriefRecord and GateDecision contract enforcement
- cli/lib/protocol.py -> cli/lib/registry_store.py: persist brief/decision trace and dispatch receipt
- Backward compat: business skill continues producing candidate/proposal/evidence without direct formal write path

## Completion Signals

- **decision_issued_done**: Gate decision (approve/revise/retry/reject) issued with full basis refs and dispatch target.
- **execution_returned_done**: Decision routed back to execution with structured revision or retry directive.
- **delegated_done**: Decision delegated to downstream handler with clear ownership transfer.
- **publication_triggered_done**: Approve decision triggered formal publication with authoritative decision object.
- **rejected_done**: Candidate rejected with clear reason, evidence preserved, no downstream side effects.

## Selected Upstream

- feat_ref: `FEAT-SRC-RAW-TO-SRC-ADR048-002`
- tech_ref: `TECH-SRC-RAW-TO-SRC-ADR048-002`
- arch_ref: `ARCH-SRC-RAW-TO-SRC-ADR048-002`
- api_ref: `API-SRC-RAW-TO-SRC-ADR048-002`
- title: 主链gate审核与裁决流
- goal: 冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-048, ADR-047` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-SRC-RAW-TO-SRC-ADR048-001` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-RAW-TO-SRC-ADR048-002` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-RAW-TO-SRC-ADR048-002` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-RAW-TO-SRC-ADR048-002` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-RAW-TO-SRC-ADR048-002` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

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
  - Detected runtime/service/contract surface: gate, 发布, io, runtime.
- migration_required: False
  - No migration, cutover, rollback, or compat-mode surface was detected.

## Implementation Task

### Concrete Touch Set

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 GateBriefRecord、GatePendingHumanDecision、GateDecision 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/registry_store.py` [backend | extend | existing_match] <- `cli/lib/registry_store.py`: 写入 brief/decision trace、decision_target、decision_basis_refs 与 dispatch receipt。; nearby matches: cli/lib/execution_return_registry.py, cli/lib/fs.py
- `cli/commands/__init__.py` [backend | extend | existing_match] <- `cli/commands/gate/command.py`: 接入 evaluate / dispatch 语义，生成 brief record、decision object 与回交流水。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Repo-Aware Placement

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 GateBriefRecord、GatePendingHumanDecision、GateDecision 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/registry_store.py` [backend | extend | existing_match] <- `cli/lib/registry_store.py`: 写入 brief/decision trace、decision_target、decision_basis_refs 与 dispatch receipt。; nearby matches: cli/lib/execution_return_registry.py, cli/lib/fs.py
- `cli/commands/__init__.py` [backend | extend | existing_match] <- `cli/commands/gate/command.py`: 接入 evaluate / dispatch 语义，生成 brief record、decision object 与回交流水。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Embedded Frozen Contracts

#### State Machine

- `candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued` -> `execution_returned|delegated|publication_triggered|rejected`
- `decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`
- `decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`

#### API Contracts

- `GateBriefRecord`: input=`handoff_ref`, `proposal_ref`, `evidence_refs`; output=`brief_record_ref`, `pending_human_decision_ref`, `priority`, `merge_group`, `human_projection`; errors=`invalid_state`, `brief_build_failed`; idempotent=`yes by handoff_ref + brief_round`; precondition=`handoff 已进入 gate pending`。
- `GateDecision`: input=`brief_record_ref`, `pending_human_decision_ref`, `human_action`, `decision_target`, `decision_basis_refs`; output=`decision_ref`, `decision`, `decision_reason`, `decision_target`, `decision_basis_refs`, `dispatch_target`; errors=`invalid_state`, `unknown_target`, `missing_basis_refs`, `policy_reject`; idempotent=`yes by pending_human_decision_ref + decision_round`; precondition=`pending human decision is active and uniquely claimed`。

#### UI Entry

- 调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。
- 挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。

#### UI Success Exit

- 6. dispatch structured result to execution, delegated handler, or formal publication trigger

#### UI Failure Exit

- brief persisted 但 pending human decision 未建立：保留 `brief_record_ref`，阻止 decision issuance，并记录 `pending_build_failed`。
- decision capture 缺少 `decision_target` 或 `decision_basis_refs`：拒绝落 decision object，保留 active pending human decision，要求补充依据后重试。

#### Invariants

- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Downstream preservation rules：candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Candidate 不得绕过 gate 直接升级为 downstream formal input。
- Gate decision path is single and explicit: The FEAT must define one explicit handoff -> gate decision chain and one authoritative decision object without parallel shortcuts.
- Candidate cannot bypass gate: The FEAT must prevent that candidate from being treated as a formal downstream source.
- Formal publication is only triggered by the decision object: The FEAT must make the decision object the only business-level trigger for formal publication and keep approval authority outside the business skill body.
- Formal 发布只能由 authoritative decision object 触发，不得出现并列正式化入口。

#### Boundary Guardrails

- Boundary to collaboration runtime: formalization FEAT 消费 authoritative handoff 与 proposal，不重新定义 submission receipt 或 pending visibility。
- Boundary to downstream publication/admission: 本 FEAT 负责 gate brief、pending human decision、authoritative decision object 与 dispatch trigger，不负责 formal publish / consumer admission policy 本身。
- Dedicated gate placement is required so brief、pending、decision、dispatch 使用同一 authoritative path，而不是散落在 gate worker 或 business skill 中。
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- `ll gate evaluate` 与 `ll gate dispatch` 的 decision vocabulary / dispatch_target 必须共享同一份枚举与 target 语义，不允许把 human decision actions 漂成 runtime states。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-003 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-004 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-003 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/registry_store.py, cli/commands/__init__.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-005 Collect acceptance evidence and close delivery handoff | depends_on: TASK-004 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## Integration Plan

- 调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。
- 挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。
- 旧系统兼容：business skill 保持只产出 candidate/proposal/evidence，不新增直接 formal write 路径。
- Boundary to 主链协作闭环能力: 本 FEAT 消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。
- Boundary to 对象分层与准入能力: 本 FEAT 定义 candidate 到 decision 以及 decision 到 formal 发布 trigger 的推进链，不定义 consumer admission 与读取资格。
- 按已冻结主时序接线：1. normalize handoff and proposal refs; 2. validate gate-pending state and build `gate-brief-record`; 3. persist `gate-pending-human-decision` and human-facing projection。

## Evidence Plan

- AC-001: backend-verification, smoke-review-input
- AC-002: backend-verification, smoke-review-input
- AC-003: backend-verification, smoke-review-input

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-003, TASK-005 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `GateBriefRecord`、`GatePendingHumanDecision`、`GateDecision` 结构。, `cli/lib/registry_store.py` (`extend`): 写入 brief/decision trace、`decision_target`、`decision_basis_refs` 与 dispatch receipt。, `cli/commands/gate/command.py` (`extend`): 接入 `evaluate` / `dispatch` 语义，生成 brief record、decision object 与回交流水。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-003, TASK-004, TASK-005 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `GateBriefRecord`: input=`handoff_ref`, `proposal_ref`, `evidence_refs`; output=`brief_record_ref`, `pending_human_decision_ref`, `priority`, `merge_group`, `human_projection`; errors=`invalid_state`, `brief_build_failed`; idempotent=`yes by handoff_ref + brief_round`; precondition=`handoff 已进入 gate pending`。 Main sequence evidence covers: 1. normalize handoff and proposal refs; 2. validate gate-pending state and build `gate-brief-record`; 3. persist `gate-pending-human-decision` and human-facing projection.
- AC-003: Downstream handoff remains boundary-safe and ready for feature delivery. | implemented_by: TASK-004, TASK-005 | evidence: The implementation package exposes only the frozen pending visibility / boundary handoff behavior, keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready. Integration evidence covers: 调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。; 挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。.

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

- dev.feat-to-tech::raw-to-src-adr048--feat-src-raw-to-src-adr048-002
- FEAT-SRC-RAW-TO-SRC-ADR048-002
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
- ARCH-SRC-RAW-TO-SRC-ADR048-002
- API-SRC-RAW-TO-SRC-ADR048-002
