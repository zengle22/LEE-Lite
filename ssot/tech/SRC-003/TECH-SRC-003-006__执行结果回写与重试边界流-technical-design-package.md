---
id: TECH-SRC-003-006
ssot_type: TECH
tech_ref: TECH-SRC-003-006
feat_ref: FEAT-SRC-003-006
title: 执行结果回写与重试边界流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-006-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-006-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-006-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
---

# 执行结果回写与重试边界流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-003-006`
- title: 执行结果回写与重试边界流
- axis_id: execution-result-feedback
- resolved_axis: runner_feedback
- epic_freeze_ref: `EPIC-SRC-003-001`
- src_root_id: `SRC-003`
- goal: 冻结 runner 执行后的 done / failed / retry-reentry 结果，让自动推进链在下一跳后仍可审计、可回流。
- authoritative_artifact: execution outcome record
- upstream_feat: FEAT-SRC-003-005
- downstream_feat: FEAT-SRC-003-007
- gate_decision_dependency_feat_refs: FEAT-SRC-003-001
- admission_dependency_feat_refs: None

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: handoff.
- integration_context_sufficient: True
  - integration_context sufficient
- stateful_design_present: True
  - state_machine=present
  - io_matrix=present
  - canonical_ownership=present

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for 执行结果回写与重试边界流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - done / failed / retry-reentry outcome 必须显式记录。
  - 失败证据必须和 execution attempt 绑定。
  - retry 必须回到 execution semantics，不得改写成 publish-only 状态。
  - approve 不是自动推进链的终态。
  - Execution outcomes are explicit: the product flow must emit explicit done, failed, or retry/reentry outcomes with evidence.
  - Retry returns to execution semantics: the result must return through retry / reentry semantics instead of being rewritten as publish-only status.
  - Approve is not treated as terminal: the chain must continue through runner execution and result feedback rather than ending at approve itself.
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
[cli/lib/job_outcome.py] --> [cli/lib/execution_runner.py]
              |
              +--> [cli/lib/protocol.py]
```

### State Model
- `execution_attempt_open` -> `outcome_recorded` -> `done|failed|retry_reentry`
- `failed` must retain `failure_evidence_bound` before it becomes externally visible.

### State Machine
- states: prepared -> executing -> recorded
- guards: input validated before execution; evidence written before handoff
- field mapping: lifecycle_state tracks runtime progression and must not be owned by IMPL

### Module Plan
- Outcome collector：负责收集 downstream skill result 与 runner state。
- Outcome writer：负责写出 done/failed/retry-reentry 的 authoritative outcome。
- Failure evidence binder：负责把失败证据与 execution attempt/outcome 绑定。

### Implementation Strategy
- 先冻结 done/failed/retry-reentry outcome schema，再实现 outcome writer 和 evidence binder。
- 把 failure evidence 与 execution attempt 强绑定，避免失败状态只留日志不留 authoritative outcome。
- 最后验证 success/fail/retry 三条反馈路径都能回写主链。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `ExecutionOutcomeRecord`、`RetryReentryDirective`、`FailureEvidenceRef` 结构。
- `cli/lib/job_outcome.py` (`new`): 写出 done/failed/retry-reentry authoritative outcome。
- `cli/lib/execution_runner.py` (`new`): 将 execution attempt 结果绑定回 runner lifecycle。
- `cli/commands/job/command.py` (`new`): 暴露 `complete` / `fail` 命令并返回 outcome receipt。

### Interface Contracts
- `ExecutionOutcomeRecord`: input=`execution_attempt_ref`, `outcome`, `failure_evidence_ref?`; output=`execution_outcome_ref`, `retry_reentry_ref?`; errors=`invalid_outcome_transition`; idempotent=`yes by execution_attempt_ref + outcome`; precondition=`execution attempt already opened`。
- `RetryReentryDirective`: input=`execution_outcome_ref`; output=`reentry_target`, `retry_reason`, `lineage_ref`; errors=`retry_not_allowed`; idempotent=`yes`; precondition=`outcome is retry_reentry`。

### Main Sequence
- 1. collect downstream execution result
- 2. emit authoritative execution outcome
- 3. bind failure evidence or retry-reentry directive
- 4. expose post-dispatch result to orchestration and monitoring

```text
Execution Attempt -> Outcome Collector    : collect downstream result
Outcome Collector -> Outcome Writer       : emit done / failed / retry-reentry
Outcome Writer    -> Evidence Binder      : attach failure evidence when needed
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
- select_FEAT-SRC-003-006: inputs=feat_freeze_package, feat_ref; outputs=selected_feat snapshot; writes=none; side_effects=none; evidence=input validation; idempotency=repeatable
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

- arch_ref: `ARCH-SRC-003-006`
- summary_topics:
  - Boundary to dispatch: feedback 只消费 execution attempt 结果，不重写 next-skill invocation 本身。
  - Boundary to control/observability: 本 FEAT 冻结 outcome 与 retry-reentry 语义，监控面只读取这些结果而不重新定义它们。
  - Dedicated feedback placement is required so execution outcome, retry-reentry directive, and failure evidence stay authoritative.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-003-006`
- contract_surfaces:
  - execution outcome contract
  - retry-reentry contract
- command_refs:
  - `ll job complete / fail`
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
- tech_ref: `TECH-SRC-003-006`
- arch_ref: `ARCH-SRC-003-006`
- api_ref: `API-SRC-003-006`
- integration_context_ref: `integration-context.json`
- state_machine_ref: `tech-design-bundle.json#/tech_design/state_machine`
- canonical_owner_refs: `tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership`
- migration_constraints_ref: `tech-design-bundle.json#/tech_design/migration_constraints`
- algorithm_constraint_refs: `tech-design-bundle.json#/tech_design/algorithm_constraints`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-006, EPIC-SRC-003-001, SRC-003
- TECH Design: goal, scope, constraints <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-006, EPIC-SRC-003-001, SRC-003
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1, FEAT-SRC-003-006, EPIC-SRC-003-001, SRC-003
