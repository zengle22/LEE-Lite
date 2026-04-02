---
id: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-001"
ssot_type: TECH
title: IMPL 主测试对象 intake 与 authority 绑定流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-001"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-001"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-001/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-001"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-001"
candidate_package_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-001"
---

# TECH-SRC-ADR036-RAW2SRC-20260402-R9-001

## Overview

冻结 IMPL 进入 implementation start 前如何作为主测试对象被 intake，并与 FEAT / TECH / ARCH / API / UI / TESTSET authority 绑定。

## Design Focus

- Freeze a concrete TECH design for IMPL 主测试对象 intake 与 authority 绑定流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- IMPL 主测试对象 intake 与 authority 绑定流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- IMPL 主测试对象 intake 与 authority 绑定流 的完成态必须与“reviewer 能明确知道当前测试对象、authority refs 和执行模式。”对齐，不能只输出中间态、占位态或内部处理结果。
- IMPL 主测试对象 intake 与 authority 绑定流 happy path reaches the declared completed state: reviewer 能明确知道当前测试对象、authority refs 和执行模式。
- IMPL 主测试对象 intake 与 authority 绑定流 keeps its declared product boundary: 该 FEAT 只覆盖“主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- IMPL 主测试对象 intake 与 authority 绑定流 hands downstream one authoritative product deliverable: 下游必须围绕 implementation readiness intake result 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。

## Non-Functional Requirements

- Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
- Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
- Keep the package freeze-ready by recording execution evidence and supervision evidence.
- Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

## Implementation Carrier View

- Freeze one implementation carrier for the selected FEAT boundary and keep adjacent responsibilities out of scope.

```text
[runtime.py] -> [contracts.py] -> [receipts.py]
```

## State Model

- `prepared` -> `executed` -> `recorded`

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

- Need Assessment: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- TECH Design: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- Cross-Artifact Consistency: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-001, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
