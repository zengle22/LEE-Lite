# ADR-050/051: SSOT 语义治理升级

## What This Is

建立完整的 SSOT 语义治理闭环，将 SSOT 从"生成链"转型为"语义抽取链"。FRZ 冻结层作为唯一真相源，执行层只能补全不能改写语义，所有变更通过分级机制回流治理，由 Task Pack 驱动顺序执行循环。

## Core Value

确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义，所有变更通过分级机制回流治理。

## Current Milestone: Next Milestone (TBD)

**Goal:** TBD — use `/gsd-new-milestone` to define next milestone

## Validated Requirements

- ✓ v2.2 双链执行闭环已交付（2026-04-24）
  - 需求轴统一入口：ll-qa-api-from-feat, ll-qa-e2e-from-proto
  - 实施轴桥接：SPEC_ADAPTER_COMPAT, spec_adapter.py, test_orchestrator.py
  - 验收闭环：independent_verifier, settlement, gate-evaluate
- ✓ FRZ 冻结层（ADR-045 §2.1-§2.8，ADR-050 §3）
- ✓ 双链测试体系（ADR-047）
- ✓ Experience Patch 层（ADR-049）
- ✓ SSOT 主链结构（SRC/EPIC/FEAT/TECH/UI）
- ✓ Execution Loop Job Runner（ADR-018）
- ✓ QA Schema（v1.0）
- ✓ 11 个 QA 技能 Prompt-first 运行时（v1.0）
- ✓ Patch 基础设施（v1.1）
- ✓ SSOT 语义治理（ADR-050/051，v2.0）
- ✓ 测试双轴治理（v2.1）

## Next Milestone Goals

- /gsd-new-milestone — Define next milestone

## Context

- ADR-050 是总纲，ADR-051 是 Task Pack 的具体实现规范
- 现有 ADR-045/047/049/018 各司其职，ADR-050/051 填补灰色地带
- 已有 51 个 ADR 文件在 `ssot/adr/`
- SSOT 主链对象（SRC/EPIC/FEAT 等）存在于 `ssot/` 目录
- v1.0 (ADR-047) 和 v1.1 (ADR-049) 已交付完整基础设施

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ADR-050 作为总纲，不替代已有 ADR | 已有 ADR 经过详细评审 | 仅填补灰色地带 |
| FRZ 来自外部框架讨论产物 | BMAD/Superpowers 等讨论后冻结 | 不通过 raw-to-src 直接生成 |
| 顺序 loop 替代复杂编排 | 稳定性优先 | ADR-051 具体化 |
| v2.0 = 主版本号升级 | 语义治理是架构根本性转变 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-24 after v2.2 milestone shipped*
