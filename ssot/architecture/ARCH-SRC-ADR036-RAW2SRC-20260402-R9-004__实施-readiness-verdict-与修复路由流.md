---
id: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-004"
ssot_type: ARCH
title: 实施 readiness verdict 与修复路由流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-004"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-004"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-004"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-004/arch-design.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-004"
---

# ARCH-SRC-ADR036-RAW2SRC-20260402-R9-004

## Boundary Placement

- dimension score、pass/pass_with_revisions/block verdict、repair target、missing information、repair plan。
- 冻结 实施 readiness verdict 与修复路由流 这一独立产品行为切片，并把它保持在产品层边界内。

## System Topology

```text
[Boundary Placement] -> [Implementation Carrier] -> [Authoritative Output]
```

## Responsibility Split

- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 实施 readiness verdict 与修复路由流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 实施 readiness verdict 与修复路由流 的完成态必须与“implementation consumer 无需回读 ADR 即可知道能否开工、哪里要修、由谁修。”对齐，不能只输出中间态、占位态或内部处理结果。

## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界, path, boundary.

## Out of Scope

- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 实施 readiness verdict 与修复路由流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 实施 readiness verdict 与修复路由流 的完成态必须与“implementation consumer 无需回读 ADR 即可知道能否开工、哪里要修、由谁修。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 实施 readiness verdict 与修复路由流 时必须保留 implementation-readiness verdict package 这一 authoritative product deliverable，不能自行改写产品边界。
