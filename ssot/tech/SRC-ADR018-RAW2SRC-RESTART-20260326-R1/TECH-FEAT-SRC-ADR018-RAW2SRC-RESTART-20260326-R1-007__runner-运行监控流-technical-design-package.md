---
id: TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
ssot_type: TECH
tech_ref: TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
feat_ref: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007
title: Runner 运行监控流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr018-epic2feat-restart-20260326-r1--feat-src-adr018-raw2src-restart-20260326-r1-007
candidate_package_ref: artifacts/feat-to-tech/adr018-epic2feat-restart-20260326-r1--feat-src-adr018-raw2src-restart-20260326-r1-007
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T14:39:14Z'
---

# Runner 运行监控流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`
- title: Runner 运行监控流
- axis_id: runner-observability-surface
- resolved_axis: runner_observability
- epic_freeze_ref: `EPIC-GATE-EXECUTION-RUNNER`
- src_root_id: `SRC-ADR018-RAW2SRC-RESTART-20260326-R1`
- goal: 冻结 runner 的观察面，让 ready backlog、running、failed、deadletters 与 waiting-human 成为用户可见的正式产品面。
- authoritative_artifact: runner observability snapshot
- upstream_feat: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-004, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-005, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-006
- downstream_feat: None
- gate_decision_dependency_feat_refs: FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-001
- admission_dependency_feat_refs: None

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: handoff, queue, decision.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for Runner 运行监控流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - runner observability surface 必须覆盖 ready backlog、running、failed、deadletters、waiting-human 等关键状态。
  - 监控面必须读取 authoritative runner state，而不是靠目录猜测或人工拼接。
  - 监控面只负责观察和提示，不直接改写 runner control state。
  - 观测结果必须能关联到 ready job、invocation 和 execution outcome lineage。
  - Core queue states are visible: ready backlog, running jobs, failed jobs, deadletters, and waiting-human jobs must be visible as formal runtime states.
  - Monitoring supports operator action: the product surface must support resume, retry, or handoff decisions instead of acting as a passive log dump.
  - Runner observability covers critical states: The FEAT must make ready backlog, running, failed, deadletters, and waiting-human states visible from one authoritative monitoring surface.
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
[cli/commands/loop/command.py]
              |
              v
[cli/lib/runner_monitor.py] --> [cli/lib/job_queue.py] --> [Observability Snapshot]
              |
              +--> [cli/lib/job_outcome.py]
```

### State Model
- `runner_state_requested` -> `snapshot_projected` -> `status_view_published`
- `snapshot_projected(fail)` -> `observability_unavailable`

### Module Plan
- Runner status projector：负责聚合 ready backlog、running、failed、deadletters 和 waiting-human 状态。
- Snapshot query service：负责按 runner scope 生成 authoritative observability snapshot。
- Operator monitor presenter：负责输出 CLI 可读的 runner status/backlog view。

### Implementation Strategy
- 先冻结 ready/running/failed/deadletter/waiting-human 状态词表，再实现 status projector。
- 监控面只消费 authoritative runner records，不允许从目录结构推断状态。
- 最后验证 operator 能通过统一视图观察 backlog、运行态和异常态。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `RunnerObservabilitySnapshot`、`RunnerStatusItem` 结构。
- `cli/lib/runner_monitor.py` (`new`): 聚合 ready/running/failed/waiting-human 状态。
- `cli/lib/job_queue.py` (`extend`): 提供 backlog/status 查询接口。
- `cli/commands/loop/command.py` (`new`): 暴露 `show-status` / `show-backlog` 监控命令。

### Interface Contracts
- `RunnerObservabilitySnapshot`: input=`runner_scope_ref`, `status_filter?`; output=`observability_snapshot_ref`, `ready_backlog`, `running_items`, `failed_items`, `waiting_human_items`; errors=`status_projection_failed`; idempotent=`yes by runner_scope_ref + status_filter`; precondition=`runner scope exists`。
- `RunnerStatusQuery`: input=`observability_snapshot_ref`; output=`status_items`, `lineage_refs`, `next_operator_action?`; errors=`snapshot_missing`; idempotent=`yes`; precondition=`snapshot already projected`。

### Main Sequence
- 1. collect ready/running/failed/deadletter/waiting-human states
- 2. project authoritative observability snapshot
- 3. render operator-facing backlog / status view
- 4. expose lineage refs for diagnostics and recovery

```text
Queue / Runtime Records -> Status Projector : aggregate ready/running/failed states
Status Projector        -> Snapshot View   : publish runner observability snapshot
Snapshot View           -> Operator        : expose backlog and health view
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

- arch_ref: `ARCH-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`
- summary_topics:
  - Boundary to runner control: 监控面只读取 ready/running/failed/waiting-human 状态，不直接执行控制动作。
  - Boundary to queue/runtime records: 监控面必须聚合 authoritative ready queue、running ownership、dispatch 和 outcome records，而不是扫目录猜测状态。
  - Dedicated observability placement is required so backlog、running、failed、deadletter、waiting-human views share one authoritative query surface.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`
- contract_surfaces:
  - runner observability snapshot contract
  - runner status query contract
- command_refs:
  - `ll loop show-status / show-backlog`
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
- tech_ref: `TECH-FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`
- arch_ref: `ARCH-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`
- api_ref: `API-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-restart-20260326-r1, FEAT-SRC-ADR018-RAW2SRC-RESTART-20260326-R1-007, EPIC-GATE-EXECUTION-RUNNER, SRC-ADR018-RAW2SRC-RESTART-20260326-R1
