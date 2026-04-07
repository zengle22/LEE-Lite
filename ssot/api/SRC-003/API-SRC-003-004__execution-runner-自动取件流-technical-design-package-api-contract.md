---
id: API-SRC-003-004
ssot_type: API
api_ref: API-SRC-003-004
tech_ref: TECH-SRC-003-004
feat_ref: FEAT-SRC-003-004
title: Execution Runner 自动取件流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-004-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-004-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-004-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-004
- TECH-SRC-003-004
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-004
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-004
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-004

## Contract Scope

- ready queue claim contract
- running ownership contract

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
  - result fields=`claimed_job_ref`, `ownership_ref`, `running_state_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `running_state_ref` marks the job as claimed and owned by a single runner.
- Enum / domain:
  - None
- Invariants:
  - claim success implies a single running owner
- Canonical refs:
  - `claimed_job_ref`
  - `ownership_ref`
  - `running_state_ref`
- Errors:
  - `job_not_ready`
  - `already_claimed`
- Idempotency key: `runner_context_ref + ready_job_ref`
- Preconditions:
  - `ready_job_ref` exists in ready queue

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
