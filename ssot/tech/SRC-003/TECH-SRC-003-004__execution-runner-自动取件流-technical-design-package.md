---
id: TECH-SRC-003-004
ssot_type: TECH
tech_ref: TECH-SRC-003-004
feat_ref: FEAT-SRC-003-004
title: Execution Runner 自动取件流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-004-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-004-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-004-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
---

# Execution Runner 自动取件流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-003-004`
- title: Execution Runner 自动取件流
- axis_id: execution-runner-intake
- resolved_axis: runner_intake
- epic_freeze_ref: `EPIC-SRC-003-001`
- src_root_id: `SRC-003`
- goal: 冻结 Execution Loop Job Runner 如何从 ready queue 自动取件、claim job 并进入 running，而不是继续依赖第三会话人工接力。
- authoritative_artifact: claimed execution job
- upstream_feat: FEAT-SRC-003-003
- downstream_feat: FEAT-SRC-003-005, FEAT-SRC-003-007
- gate_decision_dependency_feat_refs: FEAT-SRC-003-001
- admission_dependency_feat_refs: None

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界, path.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: queue, handoff.
- integration_context_sufficient: True
  - integration_context sufficient
- stateful_design_present: True
  - state_machine=present
  - io_matrix=present
  - canonical_ownership=present

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for Execution Runner 自动取件流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Execution Loop Job Runner 必须自动消费 ready queue。
  - claim 语义必须是 single-owner。
  - runner intake 不得回退到人工接力或临时脚本触发。
  - claim 和 running ownership 必须留下证据。
  - Ready queue is auto-consumed: the runner must claim the job and record running ownership without human relay.
  - Claim semantics are single-owner: only one runner ownership record may succeed.
  - Ready queue remains the authoritative intake: the FEAT must use the ready queue and runner claim path instead of directory guessing or ad hoc invocation.
- Non-functional requirements:
  - Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
  - Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
  - Keep the package freeze-ready by recording execution evidence and supervision evidence.
  - Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

### Implementation Carrier View
- Execution loop、gate loop、human review 通过文件化 handoff runtime 协作；authoritative handoff submission、pending visibility、decision-return intake 都以结构化对象驱动。
- Runtime 在收到 gate decision object 后，只负责可见性回写与 revise/retry re-entry routing；decision vocabulary 仍由 gate decision FEAT authoritative freeze。
- Formal publication、approve/handoff 的最终发布语义不在本 FEAT 内实现，本 FEAT 只保留对相邻 publication FEAT 的 authoritative boundary handoff。

```text
[cli/commands/job/command.py]
              |
              v
[cli/lib/job_queue.py] --> [cli/lib/job_state.py] --> [Claimed Job]
              |
              +--> [cli/lib/protocol.py]
```

### State Model
- `ready_job_visible` -> `job_claimed` -> `running_ownership_recorded`
- `job_claimed(conflict)` -> `claim_rejected`

### State Machine
- states: prepared -> executing -> recorded
- guards: input validated before execution; evidence written before handoff
- field mapping: lifecycle_state tracks runtime progression and must not be owned by IMPL

### Module Plan
- Ready queue scanner：负责发现可消费的 ready execution job。
- Single-owner claimer：负责 claim ready job 并生成 running ownership record。
- Running state publisher：负责把 claimed job 暴露给后续 dispatch flow。

### Implementation Strategy
- 先实现 ready queue scan 和 single-owner claim，再补 running ownership publication。
- 把 claim 冲突和 replay guard 放在同一条队列消费路径上，避免多 runner 并发漂移。
- 最后用真实 ready queue 样例验证 claim 只会成功一次。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `JobClaimRequest`、`ClaimedExecutionJob`、`RunningOwnershipRecord` 结构。
- `cli/lib/job_queue.py` (`new`): 扫描 ready queue 并 claim ready execution job。
- `cli/lib/job_state.py` (`new`): 写入 single-owner running ownership。
- `cli/commands/job/command.py` (`new`): 暴露 `claim` 命令并返回 claimed job receipt。

### Interface Contracts
- `JobClaimRequest`: input=`runner_context_ref`, `ready_job_ref`; output=`claimed_job_ref`, `ownership_ref`, `running_state_ref`; errors=`job_not_ready`, `already_claimed`; idempotent=`yes by runner_context_ref + ready_job_ref`; precondition=`ready job visible in queue`。
- `RunningOwnershipRecord`: input=`claimed_job_ref`; output=`runner_context_ref`, `claimed_at`, `ownership_ref`; errors=`ownership_missing`; idempotent=`yes`; precondition=`job claimed by runner`。

### Main Sequence
- 1. scan ready queue for visible jobs
- 2. claim one ready execution job
- 3. record running ownership
- 4. publish claimed job to dispatch stage

```text
Job Queue        -> Queue Scanner         : find ready execution jobs
Queue Scanner    -> Single-owner Claimer  : attempt claim
Claimer          -> Job State             : publish running ownership record
```

### Exception and Compensation
- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。
- boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。

### Integration Points
- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。

### Algorithm Constraints
- decision rule: preserve FEAT acceptance and inherited constraints before selecting runtime shape
- determinism: design derivation must stay deterministic for the same FEAT and integration context
- compatibility anchor: Epic-level constraints：本 EPIC 直接负责 gate approve 后的自动推进运行时，不把 approve 停在 formal publication 或人工接力。
- compatibility anchor: Epic-level constraints：自动推进主链固定为：approve -> ready execution job -> runner claim -> next skill dispatch -> execution outcome。

### Input / Output Matrix and Side Effects
- select_FEAT-SRC-003-004: inputs=feat_freeze_package, feat_ref; outputs=selected_feat snapshot; writes=none; side_effects=none; evidence=input validation; idempotency=repeatable
- derive_design: inputs=selected_feat, integration_context; outputs=TECH/ARCH/API blocks; writes=tech-design-bundle.*; side_effects=markdown/json materialization; evidence=execution-evidence; idempotency=run_id scoped
- handoff_downstream: inputs=frozen tech package; outputs=handoff-to-tech-impl.json; writes=handoff artifact; side_effects=downstream routing metadata; evidence=freeze gate + supervision

### Technical Glossary and Canonical Ownership
- ready execution job: None
- runner skill entry: None
- runner CLI control surface: None
- runner claim: None
- next-skill invocation: None
- execution outcome: None
- runner observability surface: None
- FEAT-SRC-003-001 owns product slice `批准后 Ready Job 生成流` and authoritative artifact `ready execution job`.
- FEAT-SRC-003-002 owns product slice `Runner 用户入口流` and authoritative artifact `runner skill entry invocation record`.
- FEAT-SRC-003-003 owns product slice `Runner 控制面流` and authoritative artifact `runner control action record`.
- FEAT-SRC-003-004 owns product slice `Execution Runner 自动取件流` and authoritative artifact `claimed execution job`.
- FEAT-SRC-003-005 owns product slice `下游 Skill 自动派发流` and authoritative artifact `next-skill invocation record`.
- FEAT-SRC-003-006 owns product slice `执行结果回写与重试边界流` and authoritative artifact `execution outcome record`.
- FEAT-SRC-003-007 owns product slice `Runner 运行监控流` and authoritative artifact `runner observability snapshot`.
- FEAT-SRC-003-008 owns product slice `governed skill 接入与 pilot 验证流` and authoritative artifact `pilot evidence package`.

### Migration Constraints
- mode: extend
- mode: shadow
- mode: cutover
- mode: fallback
- legacy invariant: FEAT remains the product SSOT boundary; TECH must not collapse multiple FEAT slices back into one implementation blob.
- legacy invariant: Authoritative artifact, gate/admission dependencies, and prohibited inference rules must stay explicit across downstream derivation.

### Minimal Code Skeleton
- Happy path:
```python
def advance_mainline(handoff: HandoffEnvelope) -> RuntimeTransition:
    slot = persist_handoff(handoff)
    decision = request_gate_decision(slot.handoff_ref)
    next_state = apply_runtime_transition(slot, decision)
    record_transition_evidence(slot.handoff_ref, next_state)
    return next_state
```

- Failure path:
```python
def advance_mainline_with_reentry(handoff: HandoffEnvelope) -> RuntimeTransition:
    slot = persist_handoff(handoff)
    decision = request_gate_decision(slot.handoff_ref)
    if decision.kind in {'revise', 'retry'}:
        return write_reentry_command(slot.handoff_ref, decision)
    return advance_mainline(handoff)
```

## Optional ARCH

- arch_ref: `ARCH-SRC-003-004`
- summary_topics:
  - Boundary to ready-job emission: intake 只消费 authoritative ready jobs，不重写 approve-to-job materialization。
  - Boundary to operator/control surfaces: intake 负责 queue claim 和 running ownership，不承担 CLI entry 或 broad control-plane 设计。
  - Dedicated queue-intake placement is required so ready queue scan, single-owner claim, and running ownership are authoritative and replay-safe.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-003-004`
- contract_surfaces:
  - ready queue claim contract
  - running ownership contract
- command_refs:
  - `ll job claim`
- response_envelope:
  - success: `{ ok: true, command_ref, trace_ref, result }`
  - error: `{ ok: false, command_ref, trace_ref, error }`
- see: `api-contract.md`

## Cross-Artifact Consistency

- passed: True
- structural_passed: True
- semantic_passed: True
- checks:
  - [structural] TECH mandatory: True (TECH is always emitted for the selected FEAT.)
  - [structural] Integration context sufficient: True (integration_context sufficient)
  - [structural] Traceability present: True (Selected FEAT carries authoritative source refs for downstream design derivation.)
  - [structural] State machine frozen: True (TECH includes explicit state machine, I/O matrix, and canonical ownership sections.)
  - [structural] ARCH coverage: True (ARCH coverage matches the selected FEAT boundary needs.)
  - [structural] API coverage: True (API coverage includes concrete command-level contracts.)
  - [semantic] ARCH / TECH separation: True (ARCH keeps boundary placement while TECH keeps implementation carriers.)
  - [semantic] API contract completeness: True (API contracts carry schema, semantics, invariants, and canonical refs.)
  - [semantic] Integration points explicit: True (TECH carries concrete current-system integration points.)
  - [semantic] Algorithm constraints explicit: True (TECH carries explicit decision and algorithm constraints.)
- issues:
  - None
- minor_open_items:
  - Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.
  - Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.

## Downstream Handoff

- target_workflow: workflow.dev.tech_to_impl
- tech_ref: `TECH-SRC-003-004`
- arch_ref: `ARCH-SRC-003-004`
- api_ref: `API-SRC-003-004`
- integration_context_ref: `integration-context.json`
- state_machine_ref: `tech-design-bundle.json#/tech_design/state_machine`
- canonical_owner_refs: `tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership`
- migration_constraints_ref: `tech-design-bundle.json#/tech_design/migration_constraints`
- algorithm_constraint_refs: `tech-design-bundle.json#/tech_design/algorithm_constraints`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-004, EPIC-SRC-003-001, SRC-003
- TECH Design: goal, scope, constraints <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-004, EPIC-SRC-003-001, SRC-003
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-004, EPIC-SRC-003-001, SRC-003
