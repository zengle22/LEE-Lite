---
id: API-SRC-003-001
ssot_type: API
api_ref: API-SRC-003-001
tech_ref: TECH-SRC-003-001
feat_ref: FEAT-SRC-003-001
title: 批准后 Ready Job 生成流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-001-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-001-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-001-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-001
- TECH-SRC-003-001
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-001
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

# API-SRC-003-001

## Contract Scope

- ready execution job materialization contract
- approve-to-job lineage contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll gate dispatch`
- Surface: `ll gate dispatch --request <gate_dispatch.request.json> --response-out <gate_dispatch.response.json>` via `cli/commands/gate/command.py`
- Request schema:
  - `decision_ref: string`
  - `dispatch_target: string`
  - `next_skill_ref: string`
  - `authoritative_input_ref: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`ready_job_ref`, `ready_queue_path`, `approve_to_job_lineage_ref`, `next_skill_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `ready_job_ref` is the authoritative job emitted for runner consumption after approve.
  - `approve_to_job_lineage_ref` binds the gate approve decision to the emitted ready execution job.
- Enum / domain:
  - `dispatch_target ∈ {ready_execution_queue}`
- Invariants:
  - one approve decision emits at most one authoritative ready execution job
  - non-approve decisions must not allocate a ready queue record
- Canonical refs:
  - `ready_job_ref`
  - `approve_to_job_lineage_ref`
  - `ready_queue_path`
- Errors:
  - `decision_not_dispatchable`
  - `next_skill_missing`
  - `job_materialization_failed`
- Idempotency key: `decision_ref + next_skill_ref + authoritative_input_ref`
- Preconditions:
  - `decision_ref` already resolves to an approve decision
  - `authoritative_input_ref` is readable by the runner pipeline

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
