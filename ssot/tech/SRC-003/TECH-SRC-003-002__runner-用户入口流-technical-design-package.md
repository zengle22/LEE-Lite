---
id: TECH-SRC-003-002
ssot_type: TECH
tech_ref: TECH-SRC-003-002
feat_ref: FEAT-SRC-003-002
title: Runner 用户入口流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr018-runner-entry-tech-20260327-r3
candidate_package_ref: artifacts/feat-to-tech/adr018-runner-entry-tech-20260327-r3
gate_decision_ref: artifacts/active/gates/decisions/gate-decision-tech-src-003-002.json
frozen_at: '2026-03-27T02:59:38Z'
---

# Runner 用户入口流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-003-002`
- title: Runner 用户入口流
- axis_id: runner-operator-entry
- resolved_axis: runner_operator_entry
- epic_freeze_ref: `EPIC-SRC-003-001`
- src_root_id: `SRC-003`
- goal: 冻结一个用户可显式调用的 Execution Loop Job Runner canonical governed skill bundle，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。
- authoritative_artifact: canonical runner skill bundle + runner invocation receipt
- upstream_feat: FEAT-SRC-003-001
- downstream_feat: FEAT-SRC-003-003
- gate_decision_dependency_feat_refs: FEAT-SRC-003-001
- admission_dependency_feat_refs: None

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: queue, handoff.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for Runner 用户入口流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Execution Loop Job Runner 必须以独立 canonical governed skill bundle 暴露给 Claude/Codex CLI 用户。
  - 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
  - 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
  - 入口调用必须保留 authoritative run context 与 lineage。
  - Runner exposes a named skill entry: the product flow must expose a named runner skill entry via canonical governed skill bundle instead of hiding start-up inside abstract background automation.
  - Entry remains user-invokable: the entry must stay invokable by Claude/Codex CLI through an installed adapter rather than requiring direct file edits or out-of-band orchestration.
  - Runner skill entry is explicit: The FEAT must define one dedicated runner skill authority for Claude/Codex CLI instead of relying on implicit background behavior, repo CLI façade, or manual downstream relays.
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
[skills/l3/ll-execution-loop-job-runner/SKILL.md]
              |
              v
[skills/l3/ll-execution-loop-job-runner/scripts/*]
              |
              +--> [cli/commands/loop/command.py]
              +--> [cli/lib/runner_entry.py] --> [cli/lib/execution_runner.py]
              +--> [cli/lib/protocol.py]
```

### State Model
- `runner_entry_requested` -> `runner_context_initialized` -> `runner_entry_published`
- `runner_entry_requested(resume)` -> `runner_context_restored` -> `runner_entry_published`

### Module Plan
- Canonical runner skill bundle：负责提供 Claude/Codex CLI 可见的 Execution Loop Job Runner authority。
- Installed adapter：负责把 canonical skill bundle 映射到 Claude/Codex runtime。
- Runner context bootstrapper：负责初始化或恢复 authoritative runner context。
- Entry receipt publisher：负责记录 runner invocation receipt 与 run ref。
- Repo CLI control carrier：负责提供 `ll loop run-execution` / `resume-execution` 等 control surface，但不承载 skill authority。

### Implementation Strategy
- 先冻结 canonical governed skill bundle 的名称、层级与路径，再冻结 start/resume 语义。
- 把 operator-facing skill authority 与后台 queue consumption / repo CLI carrier 解耦，避免入口逻辑吞掉运行时边界。
- 最后验证 installed adapter 在 Claude/Codex CLI 中可发现且可触发，并验证 repo CLI control surface 只作为 carrier。

### Implementation Unit Mapping
- `skills/l3/ll-execution-loop-job-runner/SKILL.md` (`new`): 定义 canonical governed skill shell 与用户入口说明。
- `skills/l3/ll-execution-loop-job-runner/ll.contract.yaml` (`new`): 冻结 skill authority、input/output contract 与下游 runtime carrier 关系。
- `skills/l3/ll-execution-loop-job-runner/ll.lifecycle.yaml` (`new`): 冻结 skill lifecycle 与 install-ready 边界。
- `skills/l3/ll-execution-loop-job-runner/input/*` / `output/*` (`new`): 定义 start/resume request 与 receipt/result 的最小 contract。
- `skills/l3/ll-execution-loop-job-runner/agents/<provider>.yaml` (`conditional`): 仅在声明 provider adapter 时存在。
- `cli/lib/protocol.py` (`extend`): 定义 `ExecutionRunnerStartRequest`、`ExecutionRunnerRunRef`、`RunnerEntryReceipt` 结构。
- `cli/lib/runner_entry.py` (`new`): 提供 runner skill start/resume 的入口适配层。
- `cli/lib/execution_runner.py` (`new`): 管理 runner context bootstrap 与恢复逻辑。
- `cli/commands/loop/command.py` (`extend`): 暴露 `run-execution` / `resume-execution` control carrier。

### Interface Contracts
- `CanonicalRunnerSkillEntry`: authority=`skills/l3/ll-execution-loop-job-runner/`; installed_adapter=`required`; repo_cli_carrier=`optional`; precondition=`carrier may not replace skill authority`。
- `ExecutionRunnerStartRequest`: input=`runner_scope_ref`, `entry_mode`, `queue_ref?`; output=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`; errors=`runner_scope_missing`, `runner_context_conflict`; idempotent=`yes by runner_scope_ref + entry_mode`; precondition=`runner scope is authorized`。
- `RunnerEntryReceipt`: input=`runner_run_ref`; output=`entry_mode`, `runner_context_ref`, `started_at`; errors=`receipt_missing`; idempotent=`yes`; precondition=`runner entry already accepted`。

### Main Sequence
- 1. accept start/resume request from Claude/Codex CLI
- 2. bootstrap or restore runner context
- 3. publish runner invocation receipt
- 4. hand off to queue consumption lifecycle

```text
Operator             -> Installed Skill Adapter : invoke Execution Loop Job Runner
Installed Skill Adapter -> Runner Skill Bundle : resolve canonical authority
Runner Skill Bundle  -> Context Bootstrapper: initialize governed run context
Context Bootstrapper -> Entry Receipt       : publish runner invocation receipt
Runner Skill Bundle  -> Repo CLI Carrier    : optionally delegate run/resume control
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

- arch_ref: `ARCH-SRC-003-002`
- summary_topics:
  - Boundary to ready-job emission: 本 FEAT 不生成 ready job，只提供 operator 可见的 runner 启动/恢复入口。
  - Boundary to control surface: 本 FEAT 只冻结 canonical runner skill authority、installed adapter、run context bootstrap 与 CLI carrier 边界，不定义 job claim/run/complete/fail verbs。
  - Dedicated runner entry placement is required so canonical skill authority, installed adapter, run context bootstrap, and invocation receipt stay in one authoritative surface.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-003-002`
- contract_surfaces:
  - canonical runner skill entry contract
  - runner start/resume contract
- command_refs:
  - `ll loop run-execution`
  - `ll loop resume-execution`
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
- tech_ref: `TECH-SRC-003-002`
- arch_ref: `ARCH-SRC-003-002`
- api_ref: `API-SRC-003-002`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-lineage-20260326-r1, FEAT-SRC-003-002, EPIC-SRC-003-001, SRC-003, ADR-020
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr018-epic2feat-lineage-20260326-r1, FEAT-SRC-003-002, EPIC-SRC-003-001, SRC-003, ADR-020
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr018-epic2feat-lineage-20260326-r1, FEAT-SRC-003-002, EPIC-SRC-003-001, SRC-003, ADR-020
