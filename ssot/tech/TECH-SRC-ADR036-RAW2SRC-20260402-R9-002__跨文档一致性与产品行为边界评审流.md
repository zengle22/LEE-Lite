---
id: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-002"
ssot_type: TECH
title: 跨文档一致性与产品行为边界评审流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-002"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-002"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-002/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-002"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-002"
candidate_package_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-002"
---

# TECH-SRC-ADR036-RAW2SRC-20260402-R9-002

## Overview

冻结 IMPL 与联动 authority 之间的功能逻辑、状态、API、UI、旅程和测试可观测性检查。

## Design Focus

- Freeze a concrete TECH design for 跨文档一致性与产品行为边界评审流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 跨文档一致性与产品行为边界评审流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 跨文档一致性与产品行为边界评审流 的完成态必须与“关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。”对齐，不能只输出中间态、占位态或内部处理结果。
- 跨文档一致性与产品行为边界评审流 happy path reaches the declared completed state: 关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。
- 跨文档一致性与产品行为边界评审流 keeps its declared product boundary: 该 FEAT 只覆盖“functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。”及其直接完成结果，不吸收相邻产品切片、实现任务或测试执行细节。
- 跨文档一致性与产品行为边界评审流 hands downstream one authoritative product deliverable: 下游必须围绕 cross-artifact issue inventory 继承该 FEAT 的产品语义，而不是重新猜测完成条件、补写边界或改写验收口径。
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

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

- Need Assessment: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- TECH Design: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- Cross-Artifact Consistency: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
