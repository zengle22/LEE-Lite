---
id: TECH-SRC-005-002
ssot_type: TECH
tech_ref: TECH-SRC-005-002
feat_ref: FEAT-SRC-005-002
title: 主链 gate 审核与裁决流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-002
candidate_package_ref: artifacts/feat-to-tech/adr011-raw2src-fix-20260327-r1--feat-src-005-002
gate_decision_ref: artifacts/active/gates/decisions/feat-to-tech-adr011-raw2src-fix-20260327-r1--feat-src-005-002-tech-design-bundle-decision.json
frozen_at: '2026-03-29T14:26:53Z'
---

# 主链 gate 审核与裁决流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-005-002`
- title: 主链 gate 审核与裁决流
- axis_id: handoff-formalization
- resolved_axis: formalization
- epic_freeze_ref: `EPIC-SRC-005-001`
- src_root_id: `SRC-005`
- goal: 冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。
- authoritative_artifact: authoritative decision object
- upstream_feat: FEAT-SRC-005-001
- downstream_feat: FEAT-SRC-005-003
- gate_decision_dependency_feat_refs: None
- admission_dependency_feat_refs: FEAT-SRC-005-003

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界, path.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: request, decision, handoff, consumer.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for 主链 gate 审核与裁决流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
  - Downstream preservation rules：candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。
  - Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
  - Candidate 不得绕过 gate 直接升级为 downstream formal input。
  - Gate decision path is single and explicit: The FEAT must define one explicit handoff -> gate decision chain and one authoritative decision object without parallel shortcuts.
  - Candidate cannot bypass gate: The FEAT must prevent that candidate from being treated as a formal downstream source.
  - Formal publication is only triggered by the decision object: The FEAT must make the decision object the only business-level trigger for formal publication and keep approval authority outside the business skill body.
- Non-functional requirements:
  - Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
  - Keep the package freeze-ready by recording execution evidence and supervision evidence.
  - Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
  - Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

### Implementation Carrier View
- Business skill 只产出 candidate package / proposal / evidence，由 handoff runtime 承接进入 external gate。
- External gate 先把 handoff 压缩成 `gate-brief-record` 与 `gate-pending-human-decision`，再由 reviewer 给出 approve / revise / retry / handoff / reject 决策。
- 本 FEAT 只负责 decision issuance、trace persistence 与 downstream dispatch trigger；formal publication 由相邻 FEAT 消费 decision object 后继续完成。

```text
[cli/commands/gate/command.py]
              |
              +--> [cli/lib/protocol.py]
              |
              +--> [cli/lib/registry_store.py]
              |
              +--> [Gate Brief Record / Pending Human Decision / Gate Decision]
```

### State Model
- `candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued` -> `execution_returned|delegated|publication_triggered|rejected`
- `decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`
- `decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`

### Module Plan
- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Gate brief builder：负责把 handoff submission 压缩成 `gate-brief-record` 与 `gate-pending-human-decision`。
- Gate decision processor：解析 approve / revise / retry / handoff / reject，并产出带 `decision_target` 与 `decision_basis_refs` 的唯一 authoritative decision object。
- Dispatch router：负责把 decision object 回交给 execution、delegated handler 或 formal publication trigger，而不是直接执行 formal publish。

### Implementation Strategy
- 先固化 candidate -> brief -> pending human -> decision 的对象链与 decision vocabulary。
- 实现 revise / retry / handoff 回流时，必须先打通 structured decision 回写，并确保 `decision_target` 与 `decision_basis_refs` 完整。
- 最后把 approve decision 只作为 dispatch trigger 暴露给相邻 formal publication FEAT，不在本 FEAT 内直接 publish。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `GateBriefRecord`、`GatePendingHumanDecision`、`GateDecision` 结构。
- `cli/lib/registry_store.py` (`extend`): 写入 brief/decision trace、`decision_target`、`decision_basis_refs` 与 dispatch receipt。
- `cli/commands/gate/command.py` (`extend`): 接入 `evaluate` / `dispatch` 语义，生成 brief record、decision object 与回交流水。

### Interface Contracts
- `GateBriefRecord`: input=`handoff_ref`, `proposal_ref`, `evidence_refs`; output=`brief_record_ref`, `pending_human_decision_ref`, `priority`, `merge_group`, `human_projection`; errors=`invalid_state`, `brief_build_failed`; idempotent=`yes by handoff_ref + brief_round`; precondition=`handoff 已进入 gate pending`。
- `GateDecision`: input=`brief_record_ref`, `pending_human_decision_ref`, `human_action`, `decision_target`, `decision_basis_refs`; output=`decision_ref`, `decision`, `decision_reason`, `decision_target`, `decision_basis_refs`, `dispatch_target`; errors=`invalid_state`, `unknown_target`, `missing_basis_refs`, `policy_reject`; idempotent=`yes by pending_human_decision_ref + decision_round`; precondition=`pending human decision is active and uniquely claimed`。

### Main Sequence
- 1. normalize handoff and proposal refs
- 2. validate gate-pending state and build `gate-brief-record`
- 3. persist `gate-pending-human-decision` and human-facing projection
- 4. capture human decision action and persist authoritative decision object
- 5. validate `decision_target` and `decision_basis_refs`
- 6. dispatch structured result to execution, delegated handler, or formal publication trigger

```text
Business Skill -> Runtime         : submit candidate + proposal
Runtime        -> External Gate   : enqueue handoff for decision
External Gate  -> Runtime         : build gate brief + pending human decision
Reviewer       -> External Gate   : approve / revise / retry / handoff / reject
External Gate  -> Runtime         : persist decision object with target/basis
Runtime        -> Execution Loop  : return structured decision on revise/retry/reject
Runtime        -> Delegate/Publish Trigger : dispatch handoff or approve trigger
```

### Exception and Compensation
- brief persisted 但 pending human decision 未建立：保留 `brief_record_ref`，阻止 decision issuance，并记录 `pending_build_failed`。
- decision capture 缺少 `decision_target` 或 `decision_basis_refs`：拒绝落 decision object，保留 active pending human decision，要求补充依据后重试。
- dispatch fail：保留 authoritative decision object，不伪造下游 publish 完成态，并记录 `dispatch_pending` 供后续 repair。

### Integration Points
- 调用方：现有 governed skill 通过 handoff runtime 提交 candidate package，由 `cli/commands/gate/command.py` 负责 evaluate / dispatch。
- 挂接点：file-handoff 发生在 candidate package 写入 runtime 之后；本 FEAT 只把 approve 决策交接为 formal publication trigger，不直接 materialize formal object。
- 旧系统兼容：business skill 保持只产出 candidate/proposal/evidence，不新增直接 formal write 路径。

### Minimal Code Skeleton
- Happy path:
```python
def evaluate_gate_decision(handoff_ref: str) -> GateDecision:
    envelope = load_handoff_envelope(handoff_ref)
    brief = build_gate_brief_record(envelope)
    pending = persist_pending_human_decision(brief)
    action = capture_human_action(pending)
    decision = persist_gate_decision(
        pending_ref=pending.ref,
        human_action=action.kind,
        decision_target=action.target,
        decision_basis_refs=action.basis_refs,
    )
    dispatch_decision(decision)
    return decision
```

- Failure path:
```python
def evaluate_gate_decision_with_repair(handoff_ref: str) -> RepairOutcome:
    envelope = load_handoff_envelope(handoff_ref)
    brief = build_gate_brief_record(envelope)
    pending = persist_pending_human_decision(brief)
    action = capture_human_action(pending)
    if not action.target or not action.basis_refs:
        mark_pending_repair_required(pending.ref)
        return request_basis_completion(pending.ref)
    decision = persist_gate_decision(
        pending_ref=pending.ref,
        human_action=action.kind,
        decision_target=action.target,
        decision_basis_refs=action.basis_refs,
    )
    return dispatch_with_repair(decision)
```

## Optional ARCH

- arch_ref: `ARCH-SRC-005-002`
- summary_topics:
  - Boundary to collaboration runtime: formalization FEAT 消费 authoritative handoff 与 proposal，不重新定义 submission receipt 或 pending visibility。
  - Boundary to downstream publication/admission: 本 FEAT 负责 gate brief、pending human decision、authoritative decision object 与 dispatch trigger，不负责 formal publish / consumer admission policy 本身。
  - Dedicated gate placement is required so brief、pending、decision、dispatch 使用同一 authoritative path，而不是散落在 gate worker 或 business skill 中。
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-005-002`
- contract_surfaces:
  - gate decision contract
  - formal publication contract
- command_refs:
  - `ll gate evaluate`
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
- tech_ref: `TECH-SRC-005-002`
- arch_ref: `ARCH-SRC-005-002`
- api_ref: `API-SRC-005-002`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-002, EPIC-SRC-005-001, SRC-005
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-002, EPIC-SRC-005-001, SRC-005
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-002, EPIC-SRC-005-001, SRC-005
