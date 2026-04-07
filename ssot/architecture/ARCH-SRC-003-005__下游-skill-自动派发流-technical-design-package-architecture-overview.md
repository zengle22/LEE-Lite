---
id: ARCH-SRC-003-005
ssot_type: ARCH
arch_ref: ARCH-SRC-003-005
tech_ref: TECH-SRC-003-005
feat_ref: FEAT-SRC-003-005
title: 下游 Skill 自动派发流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-005-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-005-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-005-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-005
- TECH-SRC-003-005
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-005
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-005

## Boundary Placement

- Boundary to intake: dispatch 只在 claimed job 进入 running ownership 后启动，不重新定义 claim semantics。
- Boundary to feedback: 本 FEAT 负责 next-skill invocation 与 execution attempt record，不直接决定 done/failed/retry outcome。
- Dedicated dispatch placement is required so target skill resolution, authoritative input binding, and invocation lineage stay authoritative.

## System Topology

```text
[Claimed Job] -> [Target Skill Resolver] -> [Invocation Adapter] -> [Governed Skill Invocation]
                                                  |
                                                  +--> [Execution Attempt Record]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界, path.

## Out of Scope

- 自动推进不得回退为人工第三会话接力。
