# ADR-050/051: SSOT 语义治理升级

## What This Is

建立完整的 SSOT 语义治理闭环，将 SSOT 从"生成链"转型为"语义抽取链"。FRZ 冻结层作为唯一真相源，执行层只能补全不能改写语义，所有变更通过分级机制回流治理，由 Task Pack 驱动顺序执行循环。

## Core Value

确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义，所有变更通过分级机制回流治理。

## Current Milestone: v2.0 ADR-050/051 SSOT 语义治理升级

**Goal:** 建立完整的 SSOT 语义治理闭环，从"生成链"转型为"语义抽取链"。

**Target features:**
- FRZ 冻结包结构定义 + MSC 5维验证
- SSOT 语义抽取链（FRZ → SRC → EPIC → FEAT，投影不变性）
- 执行层语义稳定规则（补全不改写，语义漂移检测）
- 变更分级与 ADR-049 协同（visual/interaction/semantic → Minor/Major 回流）
- 三轴管理强度（需求强/实现弱/证据轻）
- Task Pack 结构（PACK YAML, depends_on）+ 顺序执行循环（失败暂停）
- 协同规则更新

## Requirements

### Validated

- ✓ FRZ 冻结层已定义（ADR-045 §2.1-§2.8，ADR-050 §3）
- ✓ 双链测试体系已建立（ADR-047）
- ✓ Experience Patch 层已冻结（ADR-049）
- ✓ SSOT 主链结构已存在（SRC/EPIC/FEAT/TECH/UI/TESTSET）
- ✓ Execution Loop Job Runner 已定义（ADR-018）
- ✓ QA Schema 已交付（v1.0 Phase 1）
- ✓ 11 个 QA 技能 Prompt-first 运行时已交付（v1.0 Phase 2-3）
- ✓ Patch 基础设施已交付（v1.1: patch_schema, patch_context_injector, patch_auto_register）

### Active

- [ ] FRZ 冻结包结构 + MSC 验证
- [ ] SSOT 从生成链改为语义抽取链（ADR-050 §4）
- [ ] 执行层语义稳定规则落地（ADR-050 §5）
- [ ] 变更分级机制与 ADR-049 协同（ADR-050 §6）
- [ ] 三轴管理强度定义（ADR-050 §7）
- [ ] Task Pack 结构 + 顺序执行循环（ADR-050 §8 + ADR-051）
- [ ] 协同规则更新（ADR-050 §9）

### Out of Scope

- [FRZ 生成工具实现] — 本轮仅定义治理规则，FRZ 仍通过 BMAD 等框架产出
- [复杂 DAG 调度] — ADR-050/051 明确采用顺序 loop
- [三轴一律强管理] — ADR-050 §7 明确差异化强度

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
*Last updated: 2026-04-18 after v2.0 milestone initialization*
