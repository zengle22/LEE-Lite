---
id: TECH-SRC-RAW-TO-SRC-ADR048-001
ssot_type: TECH
title: Technical Design - Formal Publication and Downstream Admission
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-003
---

# Technical Design - Formal Publication and Downstream Admission

## Design Summary

Define how approved gate decisions are materialized into formal publication refs with state management, and how downstream consumers are dispatched based on formal_ref type.

## Runtime Carriers

- `cli/lib/formalization.py` (extend): Formal materialization logic and state management
- `cli/lib/ready_job_dispatch.py` (extend): Downstream dispatch based on formal_ref type
- `cli/lib/gate_collaboration_actions.py` (extend): Gate collaboration handlers for formal publication
- `cli/lib/protocol.py` (extend): Formal record protocol definitions
- `cli/commands/gate/command.py` (extend): Gate formal publication and dispatch entry points

## State Transitions

- `formal_pending` -> `formal_materialized` -> `dispatch_ready`
- Failure transitions: `materialization_failed`, `dispatch_blocked`, `downstream_rejected`
- Recovery: retry materialization on state conflict
