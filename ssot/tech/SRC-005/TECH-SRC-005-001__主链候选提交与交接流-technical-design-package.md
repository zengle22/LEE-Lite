---
id: TECH-SRC-005-001
ssot_type: TECH
tech_ref: TECH-SRC-005-001
feat_ref: FEAT-SRC-005-001
title: 主链候选提交与交接流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-001
candidate_package_ref: artifacts/feat-to-tech/adr011-raw2src-fix-20260327-r1--feat-src-005-001
gate_decision_ref: artifacts/active/gates/decisions/feat-to-tech-adr011-raw2src-fix-20260327-r1--feat-src-005-001-tech-design-bundle-decision.json
frozen_at: '2026-03-29T09:41:09Z'
---

# 主链候选提交与交接流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-005-001`
- title: 主链候选提交与交接流
- axis_id: collaboration-loop
- resolved_axis: collaboration
- epic_freeze_ref: `EPIC-SRC-005-001`
- src_root_id: `SRC-005`
- goal: 冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。
- authoritative_artifact: authoritative handoff submission
- upstream_feat: None
- downstream_feat: FEAT-SRC-005-002
- gate_decision_dependency_feat_refs: FEAT-SRC-005-002
- admission_dependency_feat_refs: FEAT-SRC-005-003

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界, boundary.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: handoff, proposal, decision, queue.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for 主链候选提交与交接流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
  - Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
  - Epic-level constraints：FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。
  - Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。
  - Loop responsibility split is explicit: The FEAT must define which loop owns which transition, input object, and return path without overlapping formalization responsibilities.
  - Submission completion is visible without implying approval: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.
  - Downstream flows do not redefine collaboration rules: It must inherit the same collaboration rules instead of inventing a parallel queue or handoff model.
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
[cli/lib/mainline_runtime.py] --> [Gate Pending Receipt / Visibility]
              |
              +--> [cli/lib/protocol.py]
              |
              +--> [cli/lib/reentry.py] (revise/retry routing only)
```

### State Model
- `handoff_prepared` -> `handoff_submitted` -> `gate_pending_visible` -> `decision_returned`
- `decision_returned(revise|retry)` -> `runtime_reentry_directive_written` -> `handoff_prepared`
- `decision_returned(approve|handoff|reject)` -> `boundary_handoff_recorded`，由 formalization / downstream runtime 消费后续推进

### Module Plan
- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Submission coordinator：定义 candidate/proposal/evidence 进入 authoritative handoff 的入口、receipt 与 pending visibility。
- Decision return adapter：消费 gate decision object，并把 revise/retry 映射成 runtime re-entry directive，而不重写 decision semantics。

### Implementation Strategy
- 先冻结 authoritative handoff、pending visibility 和 decision return intake，再接入 human review escalation。
- 把 revise / retry 收敛为 runtime-owned re-entry routing，不允许 business skill 或 gate worker 私下拼接回流路径。
- 最后用至少一条真实 submit -> pending -> decision-return -> re-entry pilot 验证协作闭环成立，同时证明 gate decision issuance / formal publication 仍在本 FEAT 外。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `HandoffEnvelope`、`PendingVisibilityRecord`、`DecisionReturnEnvelope`、`ReentryDirective` 结构。
- `cli/lib/mainline_runtime.py` (`new`): 管理 authoritative submission、pending visibility、decision-return intake 与 boundary handoff record。
- `cli/lib/reentry.py` (`new`): 只处理 revise / retry 的 runtime routing、directive 写回与 replay guard，不拥有 decision semantics。
- `cli/commands/gate/command.py` (`extend`): 接入 submit-handoff / show-pending 路径，并把 returned decision 交给 `cli/lib/mainline_runtime.py` 消费。
- `cli/commands/audit/command.py` (`extend`): 作为 human review escalation 的旁路消费方，回写 structured review context 而非 formalization result。

### Interface Contracts
- `HandoffEnvelope`: input=`producer_ref`, `proposal_ref`, `payload_ref`, `pending_state`, `trace_context_ref`; output=`handoff_ref`, `gate_pending_ref`, `trace_ref`, `canonical_payload_path`; errors=`invalid_state`, `missing_payload`, `duplicate_submission`; idempotent=`yes by producer_ref + proposal_ref + payload_digest`; precondition=`payload 已写入 runtime 可读位置`。
- `DecisionReturnEnvelope` (consumed): input=`handoff_ref`, `decision_ref`, `decision`, `routing_hint`, `trace_ref`; output=`boundary_handoff_record | reentry_directive`; errors=`decision_conflict`, `handoff_missing`; idempotent=`yes by handoff_ref + decision_ref`; precondition=`decision object 已由 external gate authoritative emit`。

### Main Sequence
- 1. normalize candidate/proposal/evidence submission and producer state
- 2. persist authoritative handoff object and emit gate-pending visibility
- 3. route proposal into gate loop and escalate to human review when required
- 4. consume structured decision object when it returns to runtime
- 5. if decision in {revise, retry}, write re-entry directive and replay guard
- 6. if decision in {approve, handoff, reject}, persist boundary handoff record without materializing formal output here

```text
Execution Loop -> Runtime      : submit candidate / proposal / evidence
Runtime        -> Gate Loop    : persist authoritative handoff and publish pending visibility
Gate Loop      -> Human Review : escalate when required
Human Review   -> Gate Loop    : return decision object
Gate Loop      -> Runtime      : return decision object
Runtime        -> Execution Loop: write revise/retry re-entry directive when applicable
Runtime        -> Downstream   : expose boundary handoff record for approve/handoff/reject outcomes
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

- arch_ref: `ARCH-SRC-005-001`
- summary_topics:
  - Boundary to gate decision / publication: 本 FEAT 负责 authoritative handoff submission、gate-pending visibility 与 decision-driven runtime re-entry routing，不负责 decision vocabulary、decision issuance 与 formal publication trigger semantics。
  - Boundary to admission/layering: 本 FEAT 可以提交 candidate / proposal / evidence，但 formal admission、formal refs 与 downstream read eligibility 由对象分层 FEAT 决定。
  - Dedicated runtime placement is required so submission receipt、pending visibility 和 re-entry routing 由同一 authoritative carrier 负责，而不是散落在 producer skill 或 gate worker 中。
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-005-001`
- contract_surfaces:
  - handoff submission contract
  - gate pending visibility contract
- command_refs:
  - `ll gate submit-handoff`
  - `ll gate show-pending`
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
  - [semantic] Collaboration re-entry boundary: True (Collaboration FEATs keep decision-driven runtime routing in scope without claiming gate/publication ownership.)
- issues:
  - None
- minor_open_items:
  - Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.
  - Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.

## Downstream Handoff

- target_workflow: workflow.dev.tech_to_impl
- tech_ref: `TECH-SRC-005-001`
- arch_ref: `ARCH-SRC-005-001`
- api_ref: `API-SRC-005-001`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-001, EPIC-SRC-005-001, SRC-005
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-001, EPIC-SRC-005-001, SRC-005
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-001, EPIC-SRC-005-001, SRC-005
