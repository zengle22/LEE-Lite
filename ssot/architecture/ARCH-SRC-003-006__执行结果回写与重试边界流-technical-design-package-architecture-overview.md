---
id: ARCH-SRC-003-006
ssot_type: ARCH
arch_ref: ARCH-SRC-003-006
tech_ref: TECH-SRC-003-006
feat_ref: FEAT-SRC-003-006
title: 执行结果回写与重试边界流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-006-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-006-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-006-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-006
- TECH-SRC-003-006
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-006
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-006
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-006

## Boundary Placement

- Boundary to dispatch: feedback 只消费 execution attempt 结果，不重写 next-skill invocation 本身。
- Boundary to control/observability: 本 FEAT 冻结 outcome 与 retry-reentry 语义，监控面只读取这些结果而不重新定义它们。
- Dedicated feedback placement is required so execution outcome, retry-reentry directive, and failure evidence stay authoritative.

## System Topology

```text
[Execution Attempt] -> [Outcome Collector] -> [Outcome Writer] -> [Execution Outcome]
                                               |
                                               +--> [Failure Evidence Binder]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界.

## Out of Scope

- retry 必须回到 execution semantics，不得改写成 publish-only 状态。
- approve 不是自动推进链的终态。
