# ADR-050/051: SSOT 语义治理升级

## What This Is

建立完整的 SSOT 语义治理闭环，将 SSOT 从"生成链"转型为"语义抽取链"。FRZ 冻结层作为唯一真相源，执行层只能补全不能改写语义，所有变更通过分级机制回流治理，由 Task Pack 驱动顺序执行循环。

## Core Value

确保 SSOT 不再逐层生成，而是从 FRZ 冻结包中分层语义抽取，执行层只能补全不能改写语义，所有变更通过分级机制回流治理。

## Current Milestone: v2.2 双链执行闭环

**Goal:** 废弃 TESTSET 策略层，构建需求轴统一入口 Skill，补齐 spec → 实施的桥接，打通从 feat 到 gate 的完整测试闭环。

**Target features:**
- ADR-053: 废弃 ll-qa-feat-to-testset，构建 ll-qa-api-from-feat + ll-qa-e2e-from-proto 统一入口 Skill
- ADR-053: 补齐 acceptance traceability（acceptance → capability/journey 显式追溯）
- ADR-054: SPEC_ADAPTER_COMPAT 桥接格式（spec → TESTSET 中间格式）
- ADR-054: environment-provision 模块（自动生成 ENV 文件）
- ADR-054: test_orchestrator 编排函数（env → adapter → exec → manifest update）
- ADR-054: ll-qa-test-run Skill（用户入口，支持 --resume 重跑）
- ADR-054: test_exec_runtime 兼容性修改（SPEC_ADAPTER_COMPAT 分支）

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
- ✓ v2.0 SSOT 语义治理已交付（ADR-050/051）
- ✓ ADR-052 测试体系轴化已定义（SRC-009 v1.1 frozen）
- ✓ EPIC-009 / 4 FEATs 已冻结（FEAT-009-D/E/A/S）
- ✓ TECH-009 技术设计已定义（4-layer architecture）
- ✓ TESTSET-009 验收集已定义
- ✓ v2.1 测试双轴治理已交付（Schema/enum_guard/governance_validator/FC追溯/Task Pack 执行）
- ✓ ADR-053 QA 需求轴统一入口设计已完成（v1.1-draft，废弃 TESTSET + 统一入口）
- ✓ ADR-054 实施轴桥接设计已完成（v1.1-draft，SPEC_ADAPTER_COMPAT + env + orchestrator）

### Active

- [ ] ll-qa-api-from-feat Skill（统一入口，编排 api 子链）
- [ ] ll-qa-e2e-from-proto Skill（统一入口，编排 e2e 子链）
- [ ] acceptance traceability（acceptance → capability/journey 追溯表）
- [ ] SPEC_ADAPTER_COMPAT 格式 + spec_adapter.py
- [ ] environment_provision.py（ENV 文件自动生成）
- [ ] test_exec_runtime.py 兼容性修改（SPEC_ADAPTER_COMPAT 分支）
- [ ] test_orchestrator.py（含 StepResult + manifest 更新乐观锁）
- [ ] ll-qa-test-run Skill（用户入口，支持 --resume）
- [ ] Phase 1 集成测试（API chain + E2E chain 端到端）
- [ ] Phase 2: run_manifest_gen + scenario_spec_compile + state_machine_executor
- [ ] Phase 3: independent_verifier + settlement + gate-evaluate

### Out of Scope

- [ADR-048 Mission Compiler] — 替代 SPEC_ADAPTER_COMPAT 的长期方案，Mission Compiler 实现后废弃桥接层
- [FEAT-009-E 状态机执行 P0 升级] — Phase 2 state_machine_executor 为简化版，完整 9 节点模型延期
- [FEAT-009-A 独立验证 P0] — Phase 3 independent_verifier 为基础版，HAR 捕获和独立 API 查询延期
- [多 feat 共享 ENV 粒度管理] — OQ-2，延期到 Phase 2 review

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
*Last updated: 2026-04-24 after v2.2 milestone initialization*
