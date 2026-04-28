# ADR-050/051: SSOT 语义治理升级

## What This Is

建立完整的 SSOT 语义治理闭环，将 SSOT 从"生成链"转型为"语义抽取链"。FRZ 冻结层作为唯一真相源，执行层只能补全不能改写语义，所有变更通过分级机制回流治理，由 Task Pack 驱动顺序执行循环。

## Core Value

确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义，所有变更通过分级机制回流治理。

## Current Milestone: v2.2.1 Failure Case Resolution

**Goal:** 修复 `tests/defect/failure-cases/` 目录下记录的所有缺陷，同时系统性改进相关技能的质量和稳健性

**Target fixes:**
- P0: 修复 SRC003 SSOT 多维度漂移（API authority 重复、surface-map 所有权漂移、TECH/IMPL 语义与仓库不匹配）
- P0: 修复 FEAT 分解按 UI 表面而非能力边界的问题（ll-product-epic-to-feat）
- P1: 修复 PROTO 相关缺陷（ll-dev-feat-to-proto 的低保真问题、菜单遮罩默认遮挡、页面泛化、旅程闭环拆分）
- P1: 修复 TECH/IMPL 缺陷（ll-dev-feat-to-tech 主语漂移、模板过度共享；ll-dev-tech-to-impl 执行层漂移）
- P1: 修复 TESTSET/治理技能缺陷（TESTSET 套用 gate 模板、governance-failure-capture 位置错误、UI-spec 输出结构）
- P1: 修复 impl-spec-test 中文解析问题，增强检测能力

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

## Active Requirements (v2.2.1)

- [ ] FIX-P0-01: 修复 SRC003 SSOT 多维度漂移（API authority 重复、surface-map 所有权漂移、TECH/IMPL 语义与仓库不匹配）
- [ ] FIX-P0-02: 修复 FEAT 分解按 UI 表面而非能力边界的问题（ll-product-epic-to-feat）
- [ ] FIX-P1-01: 修复 ll-dev-feat-to-proto 的低保真问题（菜单遮罩默认遮挡、页面内容泛化占位）
- [ ] FIX-P1-02: 修复 ll-dev-feat-to-proto 的旅程闭环拆分问题（6个FEAT拆成孤立页面）
- [ ] FIX-P1-03: 修复 ll-dev-feat-to-tech 的主语漂移（从工程基线漂移到ADR-005治理）
- [ ] FIX-P1-04: 修复 ll-dev-feat-to-tech 的模板过度共享（每份TECH重复全工程骨架）
- [ ] FIX-P1-05: 修复 ll-dev-tech-to-impl 的执行层系统性漂移（触点回到src/be、吸入.tmp/external）
- [ ] FIX-P1-06: 修复 ll-qa-feat-to-testset 的TESTSET套用gate模板问题
- [ ] FIX-P1-07: 修复 ll-governance-failure-capture 的位置错误（应输出到tests/defect/failure-cases）
- [ ] FIX-P1-08: 修复 ll-dev-proto-to-ui 的UI-spec输出结构问题（应合并为单一文档）
- [ ] FIX-P1-09: 修复 ll-qa-impl-spec-test 的中文解析问题（不识别中文章节标题）
- [ ] ENH-P1-01: 增强 ll-dev-feat-to-tech 的 api_required 判定逻辑（基于能力边界而非关键词）
- [ ] ENH-P1-02: 增强 ll-dev-feat-to-tech 的 ssot_type 声明（强制为TECH/ARCH/API添加ssot_type）
- [ ] ENH-P1-03: 增强 ll-dev-feat-to-tech 的API设计质量（增加前置条件和后置输出章节）
- [ ] ENH-P1-04: 增强 ll-dev-tech-to-impl 的 source_refs 生成（自动包含完整追溯链）
- [ ] ENH-P1-05: 增强 ll-qa-feat-to-testset 的自动触发（feat-to-tech后自动触发）

## Out of Scope (v2.2.1)

- 任何新功能开发（仅bug修复和质量改进）
- 架构重构（保持v2.2架构不变）
- ADR-048 Mission Compiler（继续延期）

## Context

- ADR-050 是总纲，ADR-051 是 Task Pack 的具体实现规范
- 现有 ADR-045/047/049/018 各司其职，ADR-050/051 填补灰色地带
- 已有 51 个 ADR 文件在 `ssot/adr/`
- SSOT 主链对象（SRC/EPIC/FEAT 等）存在于 `ssot/` 目录
- v1.0 (ADR-047) 和 v1.1 (ADR-049) 已交付完整基础设施
- v2.0/v2.1/v2.2 已交付语义治理、双轴测试、双链闭环
- tests/defect/failure-cases/ 记录了 20+ 个需要修复的缺陷

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
*Last updated: 2026-04-27 after v2.2.1 milestone started*
