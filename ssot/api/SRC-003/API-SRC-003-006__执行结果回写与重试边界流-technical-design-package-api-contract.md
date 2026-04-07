---
id: API-SRC-003-006
ssot_type: API
api_ref: API-SRC-003-006
tech_ref: TECH-SRC-003-006
feat_ref: FEAT-SRC-003-006
title: 执行结果回写与重试边界流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-006-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-006-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-006-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-006
- TECH-SRC-003-006
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-006
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-006
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-006

## Contract Scope

- execution outcome contract
- retry-reentry contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll job complete / fail`
- Surface: `ll job complete|fail --request <job_complete.request.json|job_fail.request.json> --response-out <...response.json>` via `cli/commands/job/command.py`
- Request schema:
  - `execution_attempt_ref: string`
  - `outcome: enum<done|failed|retry_reentry>`
  - `failure_evidence_ref?: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`execution_outcome_ref`, `retry_reentry_ref?`, `failure_evidence_ref?`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `execution_outcome_ref` freezes the authoritative post-dispatch result for one execution attempt.
- Enum / domain:
  - `outcome ∈ {done, failed, retry_reentry}`
- Invariants:
  - every finished execution attempt must emit exactly one authoritative outcome
- Canonical refs:
  - `execution_outcome_ref`
  - `retry_reentry_ref`
  - `failure_evidence_ref`
- Errors:
  - `attempt_missing`
  - `invalid_outcome_transition`
- Idempotency key: `execution_attempt_ref + outcome`
- Preconditions:
  - `execution_attempt_ref` exists and belongs to a runner-owned dispatch

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
