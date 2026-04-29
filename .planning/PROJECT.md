# ADR-050/051: SSOT 语义治理升级

## What This Is

建立完整的 SSOT 语义治理闭环，将 SSOT 从"生成链"转型为"语义抽取链"。FRZ 冻结层作为唯一真相源，执行层只能补全不能改写语义，所有变更通过分级机制回流治理，由 Task Pack 驱动顺序执行循环。

## Core Value

确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义，所有变更通过分级机制回流治理。

## Current Milestone: v2.3 ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成

**Goal:** 在 ADR-054 测试执行闭环基础上，建立 Bug 发现→验收确认→修复→再验证的完整流转机制，并与 GSD execute-phase 研发流程无缝集成

**Target features:**
- Bug 注册表与状态机（bug_registry.py, bug_phase_generator.py, test_orchestrator.py 集成）
- 验收层集成（gate_remediation.py, gate-evaluate 集成, settlement 消费 bug 注册表）
- GSD 闭环验证（--verify-bugs 模式, bug transition CLI, 集成测试）

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
- ✓ 测试双链执行闭环（v2.2，2026-04-24）
- ✓ Failure Case 修复闭环（v2.2.1，2026-04-28）

## Active Requirements (v2.3)

**Phase A: Bug 注册表与状态机**
- [ ] BUG-REG-01: Bug 注册表模块（cli/lib/bug_registry.py）— 创建、读取、更新 artifacts/bugs/{feat_ref}/bug-registry.yaml
- [ ] BUG-REG-02: Bug 核心状态机流转 — detected → open → fixing → fixed → re_verify_passed → closed
- [ ] BUG-REG-03: Bug 终止状态 — wont_fix, duplicate, not_reproducible（含复活策略：创建新记录而非回退）
- [ ] BUG-PHASE-01: Bug Phase 生成器（cli/lib/bug_phase_generator.py）— 生成 .planning/phases/{N}-bug-fix-*/ 目录结构
- [ ] BUG-PHASE-02: 单 bug 单 phase 生成 + mini-batch 模式（--batch，max 2-3）
- [ ] BUG-INTEG-01: test-run 集成（test_orchestrator.py）— build_bug_bundle() 产出含 status:detected 和 gap_type
- [ ] BUG-INTEG-02: sync_bugs_to_registry() 将 detected bug 持久化到 artifacts/bugs/

**Phase B: 验收层集成**
- [ ] GATE-REM-01: Gate Remediation 模块（cli/lib/gate_remediation.py）— gate FAIL 时读取 bug-registry 和 settlement gap_list
- [ ] GATE-REM-02: detected → open 自动提升 — gate FAIL 后确认真缺陷
- [ ] GATE-INTEG-01: gate-evaluate 集成 — 输出契约包含 bug 关联信息
- [ ] GATE-INTEG-02: settlement 消费 bug 注册表（input contract 更新）
- [ ] PUSH-MODEL-01: Push model — gate FAIL 后自动创建 draft phase 并通知开发者（T+4h 提醒）

**Phase C: GSD 闭环验证**
- [ ] VERIFY-01: --verify-bugs targeted 模式 — 只运行 status=fixed 关联测试
- [ ] VERIFY-02: --verify-mode=full-suite — 运行完整 suite 并检测回归
- [ ] VERIFY-03: 验证后状态流转 — 通过→re_verify_passed，失败→回退 open
- [ ] VERIFY-04: 2 条件自动关闭 — 满足条件后 closed + 通知开发者
- [ ] CLI-01: Bug transition CLI（ll-bug-transition）— 支持 wont_fix/duplicate/not_reproducible 人工标记
- [ ] CLI-02: ll-bug-remediate --feat-ref — 开发者确认修复计划，生成 phase
- [ ] SHADOW-01: Shadow Fix Detection — commit hook 扫描与 open bug 关联的文件变更
- [ ] AUDIT-01: 审计日志 — 每次状态变更写入 artifacts/bugs/{feat_ref}/audit.log
- [ ] INTEG-TEST-01: 集成测试（tests/integration/test_bug_closure.py）— 完整闭环验证

## Out of Scope (v2.3)

- Autonomy Grant 机制（v2 评估后引入）
- 多 feat 并行冲突策略（MVP 假设单 feat）
- full-suite 强制触发（MVP 开发者手动选择）
- Break-Glass 协议（MVP 无 autonomy 门限可绕）
- ADR-048 Mission Compiler（继续延期）

## Context

- ADR-055 依赖：ADR-047 (双链测试), ADR-054 (实施轴桥接), ADR-053 (需求轴统一入口)
- ADR-055 状态：Draft v1.6-final-2，3 个实现 phase（Bug 注册表→验收层→GSD 闭环）
- MVP 策略：砍半 — 人工确认（autonomous:false）+ 单 bug/mini-batch(max 2-3) + 2 条件自动关闭
- 存储：artifacts/bugs/{feat_ref}/bug-registry.yaml（非 ssot/，bug 是执行观察产物）
- 已有 52 个 ADR 文件在 `ssot/adr/`
- SSOT 主链对象（SRC/EPIC/FEAT 等）存在于 `ssot/` 目录
- v1.0~v2.2.1 已全部交付：QA 技能、Patch 基础设施、语义治理、双轴测试、双链闭环、Failure Case 修复

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
*Last updated: 2026-04-29 after v2.3 milestone started*
