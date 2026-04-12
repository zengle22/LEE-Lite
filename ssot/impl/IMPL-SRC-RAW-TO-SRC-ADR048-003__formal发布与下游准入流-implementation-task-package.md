---
id: IMPL-SRC-RAW-TO-SRC-ADR048-003
ssot_type: IMPL
title: "Formal发布与下游准入流 Implementation Task Package"
status: execution_ready
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-003
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-003
arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-003
api_ref: API-SRC-RAW-TO-SRC-ADR048-003
main_sequence:
  - step: 1
    task: TASK-001
    title: Extract execution-critical contracts from upstream TECH/ARCH/API
    depends_on: none
    done_when: All frozen contracts are embedded in the implementation package
  - step: 2
    task: TASK-002
    title: Define formal publication types and downstream eligibility rules
    depends_on: TASK-001
    done_when: Each formal type has clear publication triggers and read eligibility
  - step: 3
    task: TASK-003
    title: Implement formal materialization carriers with state management
    depends_on: TASK-001, TASK-002
    done_when: Formal refs are written with correct state transitions
  - step: 4
    task: TASK-004
    title: Wire downstream dispatch triggers based on formal_ref type
    depends_on: TASK-002, TASK-003
    done_when: Correct downstream dispatch for src, epic, feat, tech, testset
  - step: 5
    task: TASK-005
    title: Collect acceptance evidence and close delivery handoff
    depends_on: TASK-004
    done_when: Every acceptance check backed by explicit evidence artifacts
implementation_units:
  - path: cli/lib/formalization.py
    type: backend
    action: extend
    purpose: Formal materialization logic, state management, and ref assignment
  - path: cli/lib/ready_job_dispatch.py
    type: backend
    action: extend
    purpose: Downstream dispatch routing based on formal_ref type prefix
  - path: cli/lib/gate_collaboration_actions.py
    type: backend
    action: extend
    purpose: Gate collaboration handlers for formal publication dispatch
  - path: cli/lib/protocol.py
    type: backend
    action: extend
    purpose: Formal record and downstream dispatch protocol definitions
  - path: cli/commands/gate/command.py
    type: backend
    action: extend
    purpose: Gate formal publication and dispatch CLI entry points
non_goals:
  - Does not redefine gate decision semantics
  - Does not handle execution return routing
  - Does not define FEAT/TECH derivation rules
  - Does not manage UI surface or user testing
implementation_readiness: ready
---

# Formal发布与下游准入流 Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Extract execution-critical contracts | depends_on: none | done_when: All frozen contracts are embedded in the implementation package
- Step 2: TASK-002 Define formal publication types | depends_on: TASK-001 | done_when: Each formal type has clear publication triggers and read eligibility
- Step 3: TASK-003 Implement formal materialization | depends_on: TASK-001, TASK-002 | done_when: Formal refs are written with correct state transitions
- Step 4: TASK-004 Wire downstream dispatch triggers | depends_on: TASK-002, TASK-003 | done_when: Correct downstream dispatch for src, epic, feat, tech, testset
- Step 5: TASK-005 Collect acceptance evidence | depends_on: TASK-004 | done_when: Every acceptance check backed by explicit evidence artifacts

## Implementation Unit Mapping Snapshot

- `cli/lib/formalization.py` [backend | extend | owned]: Formal materialization logic, state management, and ref assignment
- `cli/lib/ready_job_dispatch.py` [backend | extend | owned]: Downstream dispatch routing based on formal_ref type prefix
- `cli/lib/gate_collaboration_actions.py` [backend | extend | owned]: Gate collaboration handlers for formal publication dispatch
- `cli/lib/protocol.py` [backend | extend | owned]: Formal record and downstream dispatch protocol definitions
- `cli/commands/gate/command.py` [backend | extend | owned]: Gate formal publication and dispatch CLI entry points

## State Model Snapshot

- State transitions: `formal_pending` -> `formal_materialized` -> `dispatch_triggered` -> `downstream_published`
- Recovery paths: `materialization_failed` -> retry with idempotent guard -> `formal_materialized`
- Recovery paths: `dispatch_blocked` -> retry with backoff -> `dispatch_triggered`
- Recovery paths: `downstream_rejected` -> log rejection, fail-closed -> manual review escalation
- Completion signals: formal_materialized, dispatch_triggered, downstream_published
- Failure signals: materialization_failed, dispatch_blocked, downstream_rejected
- Fail-closed: if materialization fails, do not emit formal_ref; require manual resolution

## Integration Points Snapshot

- gate approve decision -> formal materialization -> downstream dispatch
- formal_ref type prefix determines dispatch target (formal.src -> src dispatch, formal.epic -> epic dispatch, formal.feat -> feat dispatch)
- backward compat: existing skills without formal dispatch observe published refs via registry only
- Boundary: this FEAT does not redefine gate decision or execution return semantics

## Selected Upstream

- feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-003
- tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-003
- arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-003
- api_ref: API-SRC-RAW-TO-SRC-ADR048-003
