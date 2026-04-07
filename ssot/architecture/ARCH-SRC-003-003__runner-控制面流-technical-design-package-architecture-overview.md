---
id: ARCH-SRC-003-003
ssot_type: ARCH
arch_ref: ARCH-SRC-003-003
tech_ref: TECH-SRC-003-003
feat_ref: FEAT-SRC-003-003
title: Runner 控制面流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-003-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-003-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-003-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-003
- TECH-SRC-003-003
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-003
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-003
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-003

## Boundary Placement

- Boundary to operator entry: 本 FEAT 依赖 runner skill entry，但不重新定义 start/resume 入口本身。
- Boundary to dispatch/outcome: 本 FEAT 冻结 runner 的控制面和 state transition，不直接拥有 next-skill invocation 或 final outcome semantics。
- Dedicated runner control placement is required so lifecycle commands, ownership guards, and control evidence share one authoritative carrier.

## System Topology

```text
[CLI Control Command] -> [Runner Command Router] -> [Ownership Guard] -> [Control Evidence Writer]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界.

## Out of Scope

- runner control surface 必须提供统一的 CLI verbs，而不是分散在多个无治理脚本里。
- control surface 必须与 runner skill entry 对齐，不能绕开 authoritative run context。
- control verbs 不得直接替代 next-skill invocation 结果或篡改 execution outcome。
