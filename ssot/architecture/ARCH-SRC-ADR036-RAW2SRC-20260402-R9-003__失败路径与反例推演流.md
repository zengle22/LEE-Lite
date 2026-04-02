---
id: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003"
ssot_type: ARCH
title: 失败路径与反例推演流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-003"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-003/arch-design.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-003"
---

# ARCH-SRC-ADR036-RAW2SRC-20260402-R9-003

## Boundary Placement

- Boundary to object layering: 本 FEAT 冻结受治理 IO/path 边界，但不决定对象层级与 admission policy。
- Boundary to gate decision / publication: 本 FEAT 约束 write/read carrier 与 receipt/registry 行为，不定义 approve/reject 等 decision semantics。
- Dedicated gateway placement is required so policy、IO execution、registry bind 与 receipt publication use one governed carrier.

## System Topology

```text
[Governed Skill / Runtime]
          |
          v
[Gateway Integration Adapter] --> [Path Policy] --> [Artifact IO Gateway] --> [Artifact Registry] --> [Managed Artifact Ref] --> [Gate / Consumer]
```

## Responsibility Split

- Path policy owns allow/deny and mode decisions before any governed read/write executes.
- Gateway owns write/read orchestration, registry prerequisite checks, receipt generation, and managed ref publication.
- Callers do not bypass Gateway with direct filesystem writes once the operation is declared governed.

## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: path, 边界, boundary.

## Out of Scope

- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 失败路径与反例推演流 必须保持为独立可验收的产品切片，不能退化为页面字段清单、接口清单或实现任务。
- 失败路径与反例推演流 的完成态必须与“高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。”对齐，不能只输出中间态、占位态或内部处理结果。
- 下游继承 失败路径与反例推演流 时必须保留 counterexample coverage result 这一 authoritative product deliverable，不能自行改写产品边界。
