---
id: "TECH-FRZ-055-002"
ssot_type: TECH
title: 验证失败回退流程
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "frz-055-bug-lifecycle-20260507--feat-frz-055-002"
source_refs:
- "product.epic-to-feat::frz-055-bug-lifecycle-20260507"
- "FEAT-FRZ-055-002"
- "TECH-FRZ-055-002"
- "EPIC-FRZ-055-20260507"
- "FRZ-055"
- "SURFACE-MAP-FEAT-FRZ-055-002"
- "ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md"
- "ssot/frz/FRZ-055/frz.yaml"
- "SRC-FRZ-055-20260507"
- "ADR-055"
candidate_artifact_ref: "artifacts/feat-to-tech/frz-055-bug-lifecycle-20260507--feat-frz-055-002/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/frz055-chain-manual-approval-20260507.json"
parent_id: "FEAT-FRZ-055-002"
arch_ref: null
api_ref: null
candidate_package_ref: "artifacts/feat-to-tech/frz-055-bug-lifecycle-20260507--feat-frz-055-002"
---

# TECH-FRZ-055-002

## Overview

建立 --verify-bugs 验证失败后从 fixed 回退到 open 的流程，确保开发者可以重新分析和修复。

## Design Focus

- Freeze a concrete TECH design for 验证失败回退流程, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 回退流程必须记录审计日志
- 回退到 open 后应允许开发者重新运行 ll-bug-remediate
- --verify-bugs 验证失败应将 status 从 fixed 回退到 open: bug status 应从 fixed 回退到 open，并记录审计日志。
- 回退后开发者应能重新运行 ll-bug-remediate: ll-bug-remediate 应正常运行，无错误，能够再次生成修复 plan。
- 回退流程应完整记录审计日志: 审计日志应包含时间戳、bug_id、之前状态 fixed、新状态 open、触发原因 --verify-bugs failed、操作者信息等完整记录。

## Non-Functional Requirements

- Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
- Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
- Keep the package freeze-ready by recording execution evidence and supervision evidence.

## Implementation Carrier View

- Freeze one implementation carrier for the selected FEAT boundary and keep adjacent responsibilities out of scope.

```text
[runtime.py] -> [contracts.py] -> [receipts.py]
```

## State Model

- `prepared` -> `executed` -> `recorded`

## State Machine

- states: prepared -> executing -> recorded
- guards: input validated before execution; evidence written before handoff
- field mapping: lifecycle_state tracks runtime progression and must not be owned by IMPL

## Module Plan

- Runtime carrier module
- Contract/validator module
- Evidence or receipt module

## Implementation Strategy

- Freeze contracts first, implement one authoritative carrier, then validate traceability and replay safety.

## Implementation Unit Mapping

- `runtime.py` (`new`): authoritative carrier
- `contracts.py` (`new`): request/response validation

## Interface Contracts

- `genericRequest`: freeze a machine-readable request/response contract before implementation.

## Main Sequence

- 1. normalize request
- 2. execute authoritative carrier
- 3. persist evidence and refs
- 4. return structured result

```text
caller -> runtime -> authoritative record
```

## Exception and Compensation

- preserve authoritative partial state and return a repairable degraded status instead of fabricating success

## Integration Points

- Caller enters through the governed CLI/runtime surface.
- Downstream consumers read only authoritative refs emitted by this FEAT.

## Algorithm Constraints

- decision rule: preserve FEAT acceptance and inherited constraints before selecting runtime shape
- determinism: design derivation must stay deterministic for the same FEAT and integration context
- compatibility anchor: Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- compatibility anchor: Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界。

## Input / Output Matrix and Side Effects

- select_FEAT-FRZ-055-002: inputs=feat_freeze_package, feat_ref; outputs=selected_feat snapshot; writes=none; side_effects=none; evidence=input validation; idempotency=repeatable
- derive_design: inputs=selected_feat, integration_context; outputs=TECH/ARCH/API blocks; writes=tech-design-bundle.*; side_effects=markdown/json materialization; evidence=execution-evidence; idempotency=run_id scoped
- handoff_downstream: inputs=frozen tech package; outputs=handoff-to-tech-impl.json; writes=handoff artifact; side_effects=downstream routing metadata; evidence=freeze gate + supervision

## Technical Glossary and Canonical Ownership

- bug registry entry: None
- gate decision: None
- GSD phase: None
- verify result: None
- closed notification: None
- FEAT-FRZ-055-001 owns product slice `标准 Bug 修复流程` and authoritative artifact `bug lifecycle closed loop record`.
- FEAT-FRZ-055-002 owns product slice `验证失败回退流程` and authoritative artifact `verification fallback record`.
- FEAT-FRZ-055-003 owns product slice `人工终止流程` and authoritative artifact `manual termination record`.
- FEAT-FRZ-055-004 owns product slice `Gate PASS 归档流程` and authoritative artifact `gate pass archive record`.

## Migration Constraints

- mode: extend
- mode: shadow
- mode: cutover
- mode: fallback
- legacy invariant: FEAT remains the product SSOT boundary; TECH must not collapse multiple FEAT slices back into one implementation blob.
- legacy invariant: Authoritative artifact, gate/admission dependencies, and prohibited inference rules must stay explicit across downstream derivation.

## Minimal Code Skeleton

- Happy path:

```python
def execute(request):
    normalized = normalize(request)
    result = run_authoritative_carrier(normalized)
    return build_result(result)
```

- Failure path:

```python
def execute_or_fail(request):
    normalized = normalize(request)
    if not normalized:
        raise ValueError('invalid_request')
    return execute(request)
```

## Traceability

- Need Assessment: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-002, EPIC-FRZ-055-20260507, FRZ-055
- TECH Design: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-002, EPIC-FRZ-055-20260507, FRZ-055
- Cross-Artifact Consistency: product.epic-to-feat::frz-055-bug-lifecycle-20260507, FEAT-FRZ-055-002, EPIC-FRZ-055-20260507, FRZ-055
