---
id: ARCH-SRC-003-007
ssot_type: ARCH
arch_ref: ARCH-SRC-003-007
tech_ref: TECH-SRC-003-007
feat_ref: FEAT-SRC-003-007
title: Runner 运行监控流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-007-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-007-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-007-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-007
- TECH-SRC-003-007
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-007
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-007
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-007

## Boundary Placement

- Boundary to runner control: 监控面只读取 ready/running/failed/waiting-human 状态，不直接执行控制动作。
- Boundary to queue/runtime records: 监控面必须聚合 authoritative ready queue、running ownership、dispatch 和 outcome records，而不是扫目录猜测状态。
- Dedicated observability placement is required so backlog、running、failed、deadletter、waiting-human views share one authoritative query surface.

## System Topology

```text
[Ready Queue / Running / Outcome Records] -> [Runner Status Projector] -> [Observability Snapshot] -> [Operator View]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.

## Out of Scope

- 监控面必须读取 authoritative runner state，而不是靠目录猜测或人工拼接。
- 监控面只负责观察和提示，不直接改写 runner control state。
