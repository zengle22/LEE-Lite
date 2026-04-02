---
id: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-002"
ssot_type: ARCH
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
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-002/arch-design.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-002"
---

# ARCH-SRC-ADR036-RAW2SRC-20260402-R9-002

## Boundary Placement

- functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。
- 冻结 跨文档一致性与产品行为边界评审流 这一独立产品行为切片，并把它保持在产品层边界内。

## System Topology

```text
[Boundary Placement] -> [Implementation Carrier] -> [Authoritative Output]
```

## Responsibility Split

- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 跨文档一致性与产品行为边界评审流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 跨文档一致性与产品行为边界评审流 的完成态必须与“关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。”对齐，不能只输出中间态、占位态或内部处理结果。

## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界, path, boundary.

## Out of Scope

- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 跨文档一致性与产品行为边界评审流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 跨文档一致性与产品行为边界评审流 的完成态必须与“关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 跨文档一致性与产品行为边界评审流 时必须保留 cross-artifact issue inventory 这一 authoritative product deliverable，不能自行改写产品边界。
