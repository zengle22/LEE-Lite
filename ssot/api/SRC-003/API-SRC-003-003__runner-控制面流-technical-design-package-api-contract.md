---
id: API-SRC-003-003
ssot_type: API
api_ref: API-SRC-003-003
tech_ref: TECH-SRC-003-003
feat_ref: FEAT-SRC-003-003
title: Runner 控制面流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-003-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-003-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-003-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-003
- TECH-SRC-003-003
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-003
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-003
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-003

## Contract Scope

- runner CLI control contract
- runner lifecycle command contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll job claim`
- Surface: `ll job claim --request <job_claim.request.json> --response-out <job_claim.response.json>` via `cli/commands/job/command.py`
- Request schema:
  - `runner_context_ref: string`
  - `ready_job_ref: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`claimed_job_ref`, `ownership_ref`, `claim_receipt_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `ownership_ref` records the single-owner runtime claim for this job.
- Enum / domain:
  - None
- Invariants:
  - a ready job can only be claimed by one active runner context
- Canonical refs:
  - `claimed_job_ref`
  - `ownership_ref`
  - `claim_receipt_ref`
- Errors:
  - `job_not_ready`
  - `ownership_conflict`
- Idempotency key: `runner_context_ref + ready_job_ref`
- Preconditions:
  - `runner_context_ref` is active
  - `ready_job_ref` resolves inside artifacts/jobs/ready

### `ll job run / complete / fail`
- Surface: `ll job run|complete|fail --request <job_*.request.json> --response-out <job_*.response.json>` via `cli/commands/job/command.py`
- Request schema:
  - `runner_context_ref: string`
  - `claimed_job_ref: string`
  - `execution_attempt_ref?: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`runner_state_ref`, `control_action_ref`, `execution_outcome_ref?`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `control_action_ref` records the authoritative control-plane action taken against one runner job.
- Enum / domain:
  - `command ∈ {run, complete, fail}`
- Invariants:
  - control actions must preserve existing run context and job ownership
- Canonical refs:
  - `control_action_ref`
  - `runner_state_ref`
  - `execution_outcome_ref`
- Errors:
  - `runner_context_missing`
  - `claimed_job_missing`
  - `invalid_transition`
- Idempotency key: `runner_context_ref + claimed_job_ref + command`
- Preconditions:
  - `claimed_job_ref` is already owned by `runner_context_ref`

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
