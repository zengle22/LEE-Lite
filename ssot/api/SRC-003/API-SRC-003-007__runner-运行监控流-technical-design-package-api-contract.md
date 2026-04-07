---
id: API-SRC-003-007
ssot_type: API
api_ref: API-SRC-003-007
tech_ref: TECH-SRC-003-007
feat_ref: FEAT-SRC-003-007
title: Runner 运行监控流 Technical Design Package API Contract
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-007-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-007-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-007-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-007
- TECH-SRC-003-007
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-007
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-007
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# API-SRC-003-007

## Contract Scope

- runner observability snapshot contract
- runner status query contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll loop show-status / show-backlog`
- Surface: `ll loop show-status|show-backlog --request <loop_show_*.request.json> --response-out <...response.json>` via `cli/commands/loop/command.py`
- Request schema:
  - `runner_scope_ref: string`
  - `status_filter?: enum<ready|running|failed|deadletter|waiting_human>`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`observability_snapshot_ref`, `ready_backlog`, `running_items`, `failed_items`, `waiting_human_items`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `observability_snapshot_ref` points to one authoritative snapshot of runner state across queue, running ownership, and outcomes.
- Enum / domain:
  - `status_filter ∈ {ready, running, failed, deadletter, waiting_human}`
- Invariants:
  - observability must read authoritative runner records instead of directory guessing
- Canonical refs:
  - `observability_snapshot_ref`
- Errors:
  - `runner_scope_missing`
  - `status_projection_failed`
- Idempotency key: `runner_scope_ref + status_filter`
- Preconditions:
  - `runner_scope_ref` resolves to an existing execution runner scope

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
