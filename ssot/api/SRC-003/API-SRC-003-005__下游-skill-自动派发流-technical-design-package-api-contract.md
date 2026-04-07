---
id: API-SRC-003-005
ssot_type: API
api_ref: API-SRC-003-005
tech_ref: TECH-SRC-003-005
feat_ref: FEAT-SRC-003-005
title: 下游 Skill 自动派发流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-005-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-005-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-005-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-005
- TECH-SRC-003-005
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-005
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-005

## Contract Scope

- next-skill invocation contract
- execution attempt contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll job run`
- Surface: `ll job run --request <job_run.request.json> --response-out <job_run.response.json>` via `cli/commands/job/command.py`
- Request schema:
  - `claimed_job_ref: string`
  - `target_skill_ref: string`
  - `authoritative_input_ref: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`invocation_ref`, `execution_attempt_ref`, `dispatch_lineage_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `invocation_ref` is the authoritative downstream skill invocation record emitted by the runner.
- Enum / domain:
  - None
- Invariants:
  - dispatch must use the declared target skill and authoritative input from the claimed job
- Canonical refs:
  - `invocation_ref`
  - `execution_attempt_ref`
  - `dispatch_lineage_ref`
- Errors:
  - `target_skill_missing`
  - `authoritative_input_missing`
  - `dispatch_failed`
- Idempotency key: `claimed_job_ref + target_skill_ref + authoritative_input_ref`
- Preconditions:
  - `claimed_job_ref` is already in running ownership state

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
