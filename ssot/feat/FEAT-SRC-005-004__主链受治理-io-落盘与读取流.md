---
id: FEAT-SRC-005-004
ssot_type: FEAT
feat_ref: FEAT-SRC-005-004
epic_ref: EPIC-SRC-005-001
title: 主链受治理 IO 落盘与读取流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T14:27:58Z'
---

# 主链受治理 IO 落盘与读取流

## Goal
冻结主链业务动作在什么时候必须 governed write/read，以及这些正式读写会为业务方留下什么 authoritative receipt 和 managed ref。

## Scope
- 定义 handoff、decision、formal output、evidence 的正式读写动作。
- 定义业务调用点、正式 receipt / registry record 和 managed ref。
- 定义被拒绝读写时对业务方可见的失败表现。

## Constraints
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Downstream preservation rules：candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- ADR-005 是本 FEAT 的前置基础；本 FEAT 只定义主链如何消费其受治理 IO/path 能力，不重新实现底层模块。
- 主链 IO/path 规则只覆盖 handoff、formal materialization 与 governed skill IO，不得外扩成全局文件治理。
- 任何正式主链写入都必须遵守受治理 path / mode 边界，不允许 silent fallback 到自由写入。

## Acceptance Checks
1. Mainline IO boundary is explicit
   Then: The FEAT must define which IO belongs to mainline handoff / materialization and which IO is out of scope.
2. Path governance does not expand into global file governance
   Then: The FEAT must reject scope expansion beyond governed skill IO, handoff, and materialization boundaries.
3. Formal writes cannot fall back to free writes
   Then: The FEAT must preserve governed path / mode enforcement and block silent fallback to uncontrolled writes.
