---
id: "ARCH-FRZ-055-001"
ssot_type: ARCH
title: 标准 Bug 修复流程
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "frz-055-bug-lifecycle-20260507--feat-frz-055-001"
source_refs:
- "product.epic-to-feat::frz-055-bug-lifecycle-20260507"
- "FEAT-FRZ-055-001"
- "TECH-FRZ-055-001"
- "EPIC-FRZ-055-20260507"
- "FRZ-055"
- "SURFACE-MAP-FEAT-FRZ-055-001"
- "ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md"
- "ssot/frz/FRZ-055/frz.yaml"
- "SRC-FRZ-055-20260507"
- "ADR-055"
candidate_artifact_ref: "artifacts/feat-to-tech/frz-055-bug-lifecycle-20260507--feat-frz-055-001/arch-design.md"
gate_decision_ref: "artifacts/active/gates/decisions/frz055-chain-manual-approval-20260507.json"
parent_id: "FEAT-FRZ-055-001"
---

# ARCH-FRZ-055-001

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
- Keyword hits: registry.

## Out of Scope

- 不负责验证失败回退流程
- 不负责人工终止流程
- 不负责 gate PASS 归档流程
- 幂等性：多次运行 ll-bug-remediate 不应重复生成相同 phase
