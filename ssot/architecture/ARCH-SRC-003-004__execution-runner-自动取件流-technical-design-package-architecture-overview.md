---
id: ARCH-SRC-003-004
ssot_type: ARCH
arch_ref: ARCH-SRC-003-004
tech_ref: TECH-SRC-003-004
feat_ref: FEAT-SRC-003-004
title: Execution Runner 自动取件流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-004-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-004-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-004-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-004
- TECH-SRC-003-004
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-004
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-004
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-004

## Boundary Placement

- Boundary to ready-job emission: intake 只消费 authoritative ready jobs，不重写 approve-to-job materialization。
- Boundary to operator/control surfaces: intake 负责 queue claim 和 running ownership，不承担 CLI entry 或 broad control-plane 设计。
- Dedicated queue-intake placement is required so ready queue scan, single-owner claim, and running ownership are authoritative and replay-safe.

## System Topology

```text
[artifacts/jobs/ready] -> [Ready Queue Scanner] -> [Single-owner Claimer] -> [Running Ownership Record]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界, path.

## Out of Scope

- runner intake 不得回退到人工接力或临时脚本触发。
