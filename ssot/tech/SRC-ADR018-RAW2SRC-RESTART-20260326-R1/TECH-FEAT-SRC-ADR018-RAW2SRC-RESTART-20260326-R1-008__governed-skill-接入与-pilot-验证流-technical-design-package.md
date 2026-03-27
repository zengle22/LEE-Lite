---
id: TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008
ssot_type: TECH
tech_ref: TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008
title: governed skill 接入与 pilot 验证流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr018-epic2feat-restart-20260326-r1--feat-src-adr018-raw2src-restart-20260326-r1-008
candidate_package_ref: artifacts/feat-to-tech/adr018-epic2feat-restart-20260326-r1--feat-src-adr018-raw2src-restart-20260326-r1-008
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T14:49:30Z'
---

# governed skill 接入与 pilot 验证流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`
- title: governed skill 接入与 pilot 验证流
- axis_id: skill-adoption-e2e
- resolved_axis: runner_ready_job
- epic_freeze_ref: `EPIC-GATE-EXECUTION-RUNNER`
- src_root_id: `SRC-ADR018-RAW2SRC-RESTART-20260326-R1`
- goal: 把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。
- authoritative_artifact: pilot evidence package
- upstream_feat: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-001, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-002, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-003, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-004, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-005, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-006, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
- downstream_feat: None
- gate_decision_dependency_feat_refs: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-001
- admission_dependency_feat_refs: None

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: consumer, decision, handoff, proposal.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
  - 接入验证不得回退为人工第三会话接力。
  - cutover / fallback 必须围绕 runner 自动推进结果定义。
  - pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。
  - Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
  - At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
  - Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
- Non-functional requirements:
  - Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
  - Keep the package freeze-ready by recording execution evidence and supervision evidence.
  - Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
  - Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

### Implementation Carrier View
- Execution loop、gate loop、human review 通过文件化 handoff runtime 协作；authoritative handoff submission、pending visibility、decision-return intake 都以结构化对象驱动。
- Runtime 在收到 gate decision object 后，只负责可见性回写与 revise/retry re-entry routing；decision vocabulary 仍由 gate decision FEAT authoritative freeze。
- Formal publication、approve/handoff 的最终发布语义不在本 FEAT 内实现，本 FEAT 只保留对相邻 publication FEAT 的 authoritative boundary handoff。

```text
[cli/commands/gate/command.py]
              |
              v
[cli/lib/ready_job_dispatch.py] --> [cli/lib/job_queue.py]
              |
              +--> [cli/lib/protocol.py]
```

### State Model
- `decision_approved` -> `dispatch_resolved` -> `ready_job_materialized` -> `ready_queue_published`
- `decision_not_approved` must never transition into `ready_queue_published`.

### Module Plan
- Approve dispatch resolver：负责从 approve decision 解析 next skill target、authoritative input 和 dispatch target。
- Ready job materializer：负责生成 ready execution job 与 approve-to-job lineage。
- Ready queue writer：负责把 ready job 写入 artifacts/jobs/ready 并发布 queue record。

### Implementation Strategy
- 先冻结 approve -> ready job 的 authoritative object 和 lineage 字段，再实现 queue write。
- 把 non-approve path 明确挡在 ready queue 之外，避免 ready job 语义被 formal publication 替代。
- 最后用真实 approve decision 验证 ready execution job 和 approve-to-job lineage。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `ReadyExecutionJob`、`ApproveToJobLineage` 结构。
- `cli/lib/ready_job_dispatch.py` (`new`): 解析 approve decision 并物化 ready execution job。
- `cli/lib/job_queue.py` (`new`): 写入 artifacts/jobs/ready 并返回 queue receipt。
- `cli/commands/gate/command.py` (`extend`): 在 dispatch 路径发出 ready execution job，而不是停在 formal publication trigger。

### Interface Contracts
- `ReadyExecutionJob`: input=`decision_ref`, `next_skill_ref`, `authoritative_input_ref`; output=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`; errors=`decision_not_dispatchable`, `job_materialization_failed`; idempotent=`yes by decision_ref + next_skill_ref`; precondition=`decision is approve and dispatchable`。
- `ReadyQueueRecord`: input=`ready_job_ref`; output=`queue_slot_ref`, `ready_visible`, `trace_ref`; errors=`queue_write_failed`; idempotent=`yes by ready_job_ref`; precondition=`ready execution job already materialized`。

### Main Sequence
- 1. resolve approve decision and next-skill target
- 2. materialize ready execution job and approve-to-job lineage
- 3. write job into artifacts/jobs/ready
- 4. publish ready queue receipt

```text
Gate Decision        -> Dispatch Resolver : resolve approve target
Dispatch Resolver    -> Job Materializer  : build ready execution job
Job Materializer     -> Job Queue         : write artifacts/jobs/ready
Job Queue            -> Lineage Store     : persist approve-to-job lineage
```

### Exception and Compensation
- authoritative handoff 已提交但 pending visibility build fail：不得重复创建 handoff；保留 handoff object，标记 `visibility_pending` 并要求补写 receipt。
- decision return consumed 但 re-entry directive write fail：返回 `reentry_pending`，要求修复写入后重放，不允许业务 skill 绕回。
- boundary handoff record persist fail：不得偷跑 formalization；保持 decision visible but `downstream_handoff_pending`，等待 runtime repair。

### Integration Points
- 调用方：producer skill 通过 `cli/commands/gate/command.py` / `cli/lib/mainline_runtime.py` 写入 authoritative handoff；gate loop 和 human review 在返回 decision object 时仍沿现有 mainline loop 挂接。
- 挂接点：file-handoff 发生在 producer 提交之后；external gate 作为现有 loop 的独立阶段消费 proposal 并返回 structured decision object。
- 旧系统兼容：旧 skill 若未接入统一 re-entry routing，只能以 compat mode 观察 pending visibility，不允许自定义 revise/retry 回流规则。

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

- arch_ref: `ARCH-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`
- summary_topics:
  - Boundary to gate decision: 本 FEAT 消费 approve decision 并物化 ready execution job，不重写 decision vocabulary。
  - Boundary to runner entry/control: 本 FEAT 只负责 ready job emission，不承担 runner 的用户入口、控制面或运行 ownership。
  - Dedicated dispatch placement is required so approve-to-job lineage、ready queue write 和 next skill target stay authoritative.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`
- contract_surfaces:
  - ready execution job materialization contract
  - approve-to-job lineage contract
- command_refs:
  - `ll gate dispatch`
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
  - [structural] Traceability present: True (Selected FEAT carries authoritative source refs for downstream design derivation.)
  - [structural] ARCH coverage: True (ARCH coverage matches the selected FEAT boundary needs.)
  - [structural] API coverage: True (API coverage includes concrete command-level contracts.)
  - [semantic] ARCH / TECH separation: True (ARCH keeps boundary placement while TECH keeps implementation carriers.)
  - [semantic] API contract completeness: True (API contracts carry schema, semantics, invariants, and canonical refs.)
- issues:
  - None
- minor_open_items:
  - Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.
  - Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.

## Downstream Handoff

- target_workflow: workflow.dev.tech_to_impl
- tech_ref: `TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`
- arch_ref: `ARCH-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`
- api_ref: `API-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-008, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
