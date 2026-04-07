---
id: ARCH-SRC-003-002
ssot_type: ARCH
arch_ref: ARCH-SRC-003-002
tech_ref: TECH-SRC-003-002
feat_ref: FEAT-SRC-003-002
title: Runner 用户入口流 Technical Design Package Architecture Overview
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: src003-adr042-tech-002-20260407-r1
candidate_package_ref: artifacts/feat-to-tech/src003-adr042-tech-002-20260407-r1
gate_decision_ref: artifacts/active/gates/decisions/src003-adr042-tech-002-formalize.json
frozen_at: '2026-04-07T02:09:10Z'
source_refs:
- product.epic-to-feat::src003-adr042-bootstrap-20260407-r1
- FEAT-SRC-003-002
- TECH-SRC-003-002
- EPIC-SRC-003-001
- SRC-003
- SURFACE-MAP-FEAT-SRC-003-002
- product.raw-to-src::adr018-raw2src-restart-20260326-r1
- ADR-018
- ADR-001
- ADR-003
- ADR-005
- ADR-006
- ADR-009
- TESTSET-SRC-003-002
- product.src-to-epic::adr018-src2epic-lineage-20260326-r1
- product.src-to-epic::adr018-src2epic-restart-20260326-r1
---

# ARCH-SRC-003-002

## Boundary Placement

- Boundary to ready-job emission: 本 FEAT 不生成 ready job，只提供 operator 可见的 runner 启动/恢复入口。
- Boundary to control surface: 本 FEAT 只冻结 runner skill entry 与 run context bootstrap，不定义 job claim/run/complete/fail verbs。
- Dedicated runner entry placement is required so Claude/Codex CLI entry, run context bootstrap, and invocation receipt stay in one authoritative surface.

## System Topology

```text
[Claude/Codex CLI] -> [Runner Skill Entry] -> [Runner Context Bootstrapper] -> [Runner Run Context]
```

## Responsibility Split



## Dedicated Runtime Placement

- ARCH required by boundary/runtime placement.
- Keyword hits: 边界.

## Out of Scope

- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
