---
id: API-SRC-003-002
ssot_type: API
api_ref: API-SRC-003-002
tech_ref: TECH-SRC-003-002
feat_ref: FEAT-SRC-003-002
title: Runner 用户入口流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-002-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-002-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-002-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-002
- TECH-SRC-003-002
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-002
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-002
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-002

## Contract Scope

- runner skill entry contract
- runner start/resume contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll loop run-execution`
- Surface: `ll loop run-execution --request <loop_run_execution.request.json> --response-out <loop_run_execution.response.json>` via `cli/commands/loop/command.py`
- Request schema:
  - `runner_scope_ref: string`
  - `entry_mode: enum<start|resume>`
  - `queue_ref: string?`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`runner_run_ref`, `runner_context_ref`, `entry_receipt_ref`, `entry_mode`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `runner_run_ref` identifies one authoritative execution-loop run owned by the runner skill entry.
  - `runner_context_ref` binds subsequent control and observability commands to the same governed run context.
- Enum / domain:
  - `entry_mode ∈ {start, resume}`
- Invariants:
  - one run-execution command must create or resume exactly one runner context
  - entry must not directly invoke downstream skills outside the runner lifecycle
- Canonical refs:
  - `runner_run_ref`
  - `runner_context_ref`
  - `entry_receipt_ref`
- Errors:
  - `runner_scope_missing`
  - `runner_context_conflict`
  - `resume_target_not_found`
- Idempotency key: `runner_scope_ref + entry_mode`
- Preconditions:
  - `runner_scope_ref` resolves to a governed execution-runner scope

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
