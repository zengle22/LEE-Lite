---
id: "API-SRC-ADR036-RAW2SRC-20260402-R9-005"
ssot_type: API
title: governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005/api-contract.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
---

# API-SRC-ADR036-RAW2SRC-20260402-R9-005

## Contract Scope

- skill onboarding contract
- pilot evidence submission contract

## Response Envelope

- Success envelope: `{ ok: true, command_ref, trace_ref, result }`
- Error envelope: `{ ok: false, command_ref, trace_ref, error }`

## Command Contracts

### `ll rollout onboard-skill`
- Surface: `ll rollout onboard-skill --request <rollout_onboard_skill.request.json> --response-out <rollout_onboard_skill.response.json>` via `cli/commands/rollout/command.py`
- Request schema:
  - `skill_ref: string`
  - `wave_id: string`
  - `scope: string`
  - `compat_mode: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`status`, `runtime_binding_ref`, `cutover_guard_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `compat_mode` freezes the transition mode used before full cutover.
- Enum / domain:
  - None
- Invariants:
  - onboarding must keep a cutover guard ref for every accepted wave
- Canonical refs:
  - `runtime_binding_ref`
  - `cutover_guard_ref`
- Errors:
  - `unknown_skill`
  - `scope_invalid`
  - `foundation_missing`
- Idempotency key: `skill_ref + wave_id`
- Preconditions:
  - foundation features are freeze-ready

### `ll audit submit-pilot-evidence`
- Surface: `ll audit submit-pilot-evidence --request <audit_submit_pilot_evidence.request.json> --response-out <audit_submit_pilot_evidence.response.json>` via `cli/commands/audit/command.py`
- Request schema:
  - `pilot_chain_ref: string`
  - `producer_ref: string`
  - `consumer_ref: string`
  - `audit_ref: string`
  - `gate_ref: string`
- Response schema:
  - success envelope=`{ ok: true, command_ref, trace_ref, result }`
  - result fields=`evidence_status`, `cutover_recommendation`, `evidence_ref`
  - error envelope=`{ ok: false, command_ref, trace_ref, error }`
- Field semantics:
  - `cutover_recommendation` is a rollout recommendation, not a foundation design rewrite.
- Enum / domain:
  - None
- Invariants:
  - pilot evidence must trace one complete producer -> consumer -> audit -> gate path
- Canonical refs:
  - `pilot_chain_ref`
  - `evidence_ref`
- Errors:
  - `missing_chain_step`
  - `audit_not_traceable`
- Idempotency key: `pilot_chain_ref`
- Preconditions:
  - pilot chain has executed at least once

## Compatibility and Versioning

- 新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。
- command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。
- onboarding/cutover 命令必须保留 compat_mode 开关，并把 fallback 结果显式记录到 receipt。
