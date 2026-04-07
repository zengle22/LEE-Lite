---
id: ARCH-SRC-003-008
ssot_type: ARCH
arch_ref: ARCH-SRC-003-008
tech_ref: TECH-SRC-003-008
feat_ref: FEAT-SRC-003-008
title: governed skill 接入与 pilot 验证流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-008-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-008-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-008-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-008
- TECH-SRC-003-008
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-008
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

# ARCH-SRC-003-008

## Boundary Placement

- Boundary to gate decision: 本 FEAT 消费 approve decision 并物化 ready execution job，不重写 decision vocabulary。
- Boundary to runner entry/control: 本 FEAT 只负责 ready job emission，不承担 runner 的用户入口、控制面或运行 ownership。
- Dedicated dispatch placement is required so approve-to-job lineage、ready queue write 和 next skill target stay authoritative.

## System Topology

```text
[Gate Decision] -> [Approve Dispatch Resolver] -> [Ready Job Materializer] -> [artifacts/jobs/ready]
                                                           |
                                                           +--> [Approve-to-Job Lineage]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.

## Out of Scope

- Do not redefine Gateway / Policy / Registry / Audit / Gate technical contracts that already belong to foundation FEATs.
- Do not require one-shot migration of every governed skill or exhaustive coverage of every producer/consumer combination.
- 接入验证不得回退为人工第三会话接力。
