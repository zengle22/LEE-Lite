---
id: IMPL-SRC-003-008
ssot_type: IMPL
impl_ref: IMPL-SRC-003-008
tech_ref: TECH-SRC-003-008
feat_ref: FEAT-SRC-003-008
title: governed skill 接入与 pilot 验证流 Implementation Task Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: src003-adr042-impl-008-20260407-r2
candidate_package_ref: artifacts/tech-to-impl/src003-adr042-impl-008-20260407-r2
gate_decision_ref: artifacts/active/gates/decisions/tech-to-impl-src003-adr042-impl-008-20260407-r2-impl-bundle-decision.json
frozen_at: '2026-04-07T06:06:55Z'
---

# IMPL-SRC-003-008

## 1. 任务标识

- impl_ref: `IMPL-SRC-003-008`
- title: governed skill 接入与 pilot 验证流 Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `src003-adr042-impl-008-20260407-r2`
- status: `execution_ready`
- derived_from: `FEAT-SRC-003-008`, `TECH-SRC-003-008`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- 完成标准: 5 个 required steps、5 条 ordered tasks、3 条 acceptance mappings 与 handoff artifacts 全部齐备。
- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。

## 3. 范围与非目标

### In Scope

- 定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。
- 定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。
- 定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。
- cli/lib/protocol.py (extend)
- cli/lib/ready_job_dispatch.py (new)
- cli/lib/job_queue.py (new)

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 4. 上游收敛结果

- ADR refs: ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009 -> Freeze execution-bundle governance under ADR-034 and retain any domain ADR refs that remain authoritative for this FEAT.
- SRC / EPIC / FEAT: `SRC-003` / `EPIC-SRC-003-001` / `FEAT-SRC-003-008` -> 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- TECH: `TECH-SRC-003-008` -> Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.; pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。; 接入验证不得回退为人工第三会话接力。
- ARCH: `ARCH-SRC-003-008` -> Architecture boundaries constrain layering, ownership, and runtime attachment points.
- API: `API-SRC-003-008` -> `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。; `ReadyQueueRecord`: input=`ready_job_ref`; output=`queue_slot_ref`, `ready_visible`, `trace_ref`; errors=`queue_write_failed`; idempotent=`yes by ready_job_ref`; precondition=`ready execution job already materialized`。; API contract changes remain governed by upstream API truth.
- UI: `missing_authority` -> No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-008` (expected `UI-FEAT-SRC-003-008`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.
- TESTSET: `missing_authority` -> No explicit TESTSET ref selected and no accepted TESTSET authority was discoverable for `FEAT-SRC-003-008` (expected `TESTSET-SRC-003-008`). Acceptance trace is only a temporary execution proxy; freeze or revise TESTSET authority before final execution/signoff.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-034, ADR-018, ADR-001, ADR-003, ADR-005, ADR-006, ADR-009` | required_for: execution-bundle governance and authority precedence | execution_effect: coder/tester inherit execution-bundle governance from frozen ADR refs | follow_up: none
- `SURFACE_MAP` status=`bound` ref=`SURFACE-MAP-FEAT-SRC-003-008` | required_for: shared design ownership and downstream update/create routing when design impact is present | execution_effect: IMPL inherits surface ownership decisions from the frozen surface-map package when it is available. | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-003-008` | required_for: layering and ownership constraints when ARCH applies | execution_effect: IMPL inherits architecture boundaries only when ARCH was selected upstream | follow_up: none
- `API` status=`bound` ref=`API-SRC-003-008` | required_for: interface contract snapshots and response invariants when API applies | execution_effect: IMPL inherits API truth only when API was selected upstream | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-003-008` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-003-008` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### Controlled Authority Gaps

- `UI` status=`missing` ref=`UI-FEAT-SRC-003-008` | required_for: UI entry/exit constraints and user-facing acceptance wording | execution_effect: coder may rely on embedded UI contract only within the declared IMPL boundary | follow_up: freeze_or_revise_ui_before_final_execution
- `TESTSET` status=`missing` ref=`TESTSET-SRC-003-008` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace remains a proxy until TESTSET authority is frozen | follow_up: freeze_or_revise_testset_before_final_execution

### TECH Contract Snapshot

- Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
- 接入验证不得回退为人工第三会话接力。
- cutover / fallback 必须围绕 runner 自动推进结果定义。
- pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。

### ARCH Constraint Snapshot

- Architecture boundaries constrain layering, ownership, and runtime attachment points.

### State Model Snapshot

- `decision_approved` -> `dispatch_resolved` -> `ready_job_materialized` -> `ready_queue_published`
- `decision_not_approved` must never transition into `ready_queue_published`.

### Main Sequence Snapshot

- 1. resolve approve decision and next-skill target
- 2. materialize ready execution job and approve-to-job lineage
- 3. write job into artifacts/jobs/ready
- 4. publish ready queue receipt

### Integration Points Snapshot

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。

### Implementation Unit Mapping Snapshot

- cli/lib/protocol.py (extend): 定义 ReadyExecutionJob、ApproveToJobLineage 结构。
- cli/lib/ready_job_dispatch.py (new): 解析 approve decision 并物化 ready execution job。
- cli/lib/job_queue.py (new): 写入 artifacts/jobs/ready 并返回 queue receipt。
- cli/commands/gate/command.py (extend): 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。

### API Contract Snapshot

- `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。
- `ReadyQueueRecord`: input=`ready_job_ref`; output=`queue_slot_ref`, `ready_visible`, `trace_ref`; errors=`queue_write_failed`; idempotent=`yes by ready_job_ref`; precondition=`ready execution job already materialized`。

### UI Constraint Snapshot

- No explicit UI ref selected and no accepted UI authority was discoverable for `FEAT-SRC-003-008` (expected `UI-FEAT-SRC-003-008`). Treat this as a controlled authority gap; coder may follow only embedded UI entry/exit constraints until UI authority is frozen or revised.

### Embedded Execution Contract

#### State Machine

- `decision_approved` -> `dispatch_resolved` -> `ready_job_materialized` -> `ready_queue_published`
- `decision_not_approved` must never transition into `ready_queue_published`.

#### API Contracts

- `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。
- `ReadyQueueRecord`: input=`ready_job_ref`; output=`queue_slot_ref`, `ready_visible`, `trace_ref`; errors=`queue_write_failed`; idempotent=`yes by ready_job_ref`; precondition=`ready execution job already materialized`。

#### UI Entry

- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。

#### UI Success Exit

- 4. publish ready queue receipt

#### UI Failure Exit

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。

#### Invariants

- pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
- 接入验证不得回退为人工第三会话接力。
- cutover / fallback 必须围绕 runner 自动推进结果定义。
- pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。
- Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
- At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
- Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.

#### Boundary Guardrails

- Boundary to gate decision: 本 FEAT 消费 approve decision 并物化 ready execution job，不重写 decision vocabulary。
- Boundary to runner entry/control: 本 FEAT 只负责 ready job emission，不承担 runner 的用户入口、控制面或运行 ownership。
- Dedicated dispatch placement is required so approve-to-job lineage、ready queue write 和 next skill target stay authoritative.
- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.

## 5. 规范性约束

### Normative / MUST

- pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
- 接入验证不得回退为人工第三会话接力。
- cutover / fallback 必须围绕 runner 自动推进结果定义。
- pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。
- Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
- At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
- Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.

### Informative / Context Only

- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
- Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 ReadyExecutionJob、ApproveToJobLineage 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/ready_job_dispatch.py` [backend | new | existing_match] <- `cli/lib/ready_job_dispatch.py`: 解析 approve decision 并物化 ready execution job。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/fs.py` [backend | new | existing_match] <- `cli/lib/job_queue.py`: 写入 artifacts/jobs/ready 并返回 queue receipt。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/commands/__init__.py` [frontend | extend | existing_match] <- `cli/commands/gate/command.py`: 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Repo Touch Points

- `cli/lib/protocol.py` [backend | extend | existing_match] <- `cli/lib/protocol.py`: 定义 ReadyExecutionJob、ApproveToJobLineage 结构。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/ready_job_dispatch.py` [backend | new | existing_match] <- `cli/lib/ready_job_dispatch.py`: 解析 approve decision 并物化 ready execution job。; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/fs.py` [backend | new | existing_match] <- `cli/lib/job_queue.py`: 写入 artifacts/jobs/ready 并返回 queue receipt。; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/commands/__init__.py` [frontend | extend | existing_match] <- `cli/commands/gate/command.py`: 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。; nearby matches: cli/commands/job/command.py, cli/commands/skill/.gitkeep

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Wire runtime, state, and interface carriers within frozen TECH / ARCH / API boundaries.
- Create new modules only at the declared repo touch points when no existing match is available.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Boundary guardrail: Boundary to gate decision: 本 FEAT 消费 approve decision 并物化 ready execution job，不重写 decision vocabulary。
- Boundary guardrail: Boundary to runner entry/control: 本 FEAT 只负责 ready job emission，不承担 runner 的用户入口、控制面或运行 ownership。
- Boundary guardrail: Dedicated dispatch placement is required so approve-to-job lineage、ready queue write 和 next skill target stay authoritative.

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

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `ReadyExecutionJob`、`ApproveToJobLineage` 结构。, `cli/lib/ready_job_dispatch.py` (`new`): 解析 approve decision 并物化 ready execution job。, `cli/lib/job_queue.py` (`new`): 写入 artifacts/jobs/ready 并返回 queue receipt。, `cli/commands/gate/command.py` (`extend`): 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Implementation evidence proves the frozen contract hooks and state transitions are wired. `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。 Main sequence evidence covers: 1. resolve approve decision and next-skill target; 2. materialize ready execution job and approve-to-job lineage; 3. write job into artifacts/jobs/ready. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`
- AC-003: Execution-runner lifecycle remains boundary-safe and ready for feature delivery. -> The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready. Integration evidence covers: 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。; 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。. | mapping_status: `missing_authority` | mapped_test_units: `none` | mapped_to: `acceptance_trace_only_pending_testset_ref`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-002, TASK-004, TASK-007 | evidence: The declared touch set is updated and evidence-backed: `cli/lib/protocol.py` (`extend`): 定义 `ReadyExecutionJob`、`ApproveToJobLineage` 结构。, `cli/lib/ready_job_dispatch.py` (`new`): 解析 approve decision 并物化 ready execution job。, `cli/lib/job_queue.py` (`new`): 写入 artifacts/jobs/ready 并返回 queue receipt。, `cli/commands/gate/command.py` (`extend`): 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。.
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-002, TASK-004, TASK-005, TASK-007 | evidence: Implementation evidence proves the frozen contract hooks and state transitions are wired. `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。 Main sequence evidence covers: 1. resolve approve decision and next-skill target; 2. materialize ready execution job and approve-to-job lineage; 3. write job into artifacts/jobs/ready.
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

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/ready_job_dispatch.py, cli/lib/fs.py, cli/commands/__init__.py | outputs: frozen upstream refs, repo-aware touch set, execution boundary baseline | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Embed state, API, UI, and boundary contracts into implementation inputs | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/protocol.py, cli/commands/__init__.py | outputs: embedded execution contract, boundary-safe implementation baseline | acceptance: AC-001, AC-002 | done_when: No downstream coder/tester needs to re-open upstream TECH / ARCH / API documents to recover execution-critical facts.
- TASK-004 Implement backend runtime, state, and persistence units | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/ready_job_dispatch.py, cli/lib/fs.py | outputs: runtime units, state readers/writers, contract-aligned responses | acceptance: AC-001, AC-002 | done_when: Backend runtime units satisfy the frozen state machine and interface contracts without redefining ownership.
- TASK-005 Wire integration guards and downstream handoff | depends_on: TASK-002, TASK-004 | parallel: none | touch_points: cli/lib/protocol.py, cli/lib/ready_job_dispatch.py, cli/lib/fs.py, cli/commands/__init__.py | outputs: integration wiring, guard behavior, handoff-ready package | acceptance: AC-002, AC-003 | done_when: The main sequence executes in order and downstream handoff remains boundary-safe.
- TASK-007 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, smoke gate inputs, delivery handoff | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is implemented by named tasks and backed by explicit evidence artifacts.

## 10. 风险与注意事项

- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。
- boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。
- pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
- 接入验证不得回退为人工第三会话接力。
- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
