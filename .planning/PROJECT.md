# ADR-047 双链测试技能实施 + 骨架补全

## What This Is

为 LEE-Lite-skill-first 项目的 11 个空壳/半空技能补上 Prompt-first 运行时骨架，并选一个真实 feat 跑通 ADR-047 双链治理全流程（API 链：plan → manifest → spec → exec → evidence → settlement → gate），同时产出统一的 QA schema 定义。

## Core Value

用最小可行实现验证 ADR-047 的双链治理设计是否真正可执行——跑通一条链，证明"测试编译链"不是纸上谈兵。

## Requirements

### Validated

- ✓ CLI 命令体系可工作（gate、skill、evidence 等子命令已注册）
- ✓ 代码库映射已完成（7 份 codebase 文档）
- ✓ 20+ 技能已有 Python 运行时实现（ll-product-*、ll-dev-* 核心管线）
- ✓ Playwright E2E 执行器已就绪（动态脚手架）
- ✓ CI 治理体系已跑通（7 个并行检查 job）
- ✓ QA Schema 定义 + validator + fixtures（ADR-047 Phase 1）
- ✓ 设计层 6 个技能补全（ADR-047 Phase 2）
- ✓ 结算/执行层 5 个技能补全（ADR-047 Phase 3）
- ✓ API 链试点跑通（ADR-047 Phase 4）
- ✓ 生成层与执行层补全（ADR-047 Phase 5）

### Active

- [ ] ADR-049 体验修正层落地：Patch 目录 + schema + 验证 + 登记 skill + 结算 skill
- [ ] PreToolUse hook 自动触发 Patch 登记
- [ ] Patch 冲突检测 + 索引/查询
- [ ] 24h blocking 机制
- [ ] Patch-aware Harness 集成

### Out of Scope

- [Python 生产级 CLI 运行时] — 本轮只做 Prompt-first，Python 运行时留给后续里程碑
- [E2E 链全流程] — 本轮优先跑通 API 链，E2E 链作为后续扩展
- [兼容层 render-testset-view] — 旧 testset 兼容视图非本轮重点
- [生成层 api-spec-to-tests / e2e-spec-to-tests] — 本轮通过 Prompt-first 实现，不建独立技能

## Context

- 代码库是 Python 3.13 CLI 工具，通过 Claude Code 子进程驱动技能工作流
- 零外部 Python 依赖（仅 pytest/pyyaml/coverage），标准库驱动
- 文件系统（JSON/YAML/Markdown）是主要存储机制
- ADR-047 定义了完整的"双链治理"测试体系（API 链锚定 feat，E2E 链锚定 prototype）
- ADR-049 定义了体验修正层（Experience Patch Layer），冻结于 v2.1
- ADR-047 里程碑已完成，11 个技能全部补全

## Constraints

- **技术栈**: Python 3.13 标准库，不引入新外部依赖
- **运行时**: 通过 Claude Code CLI 子进程驱动，不是直接 API 调用
- **Schema**: 统一的 YAML schema 定义，`ssot/schemas/qa/` 作为真理源
- **文件模式**: 每个 skill 需补 4 个文件（run.sh + executor.md + validate_input.sh + validate_output.sh）

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Prompt-first 试点，不做 Python 运行时 | 快速验证 ADR-047 设计，避免过度工程化 | ✓ Good |
| 先跑通 API 链，E2E 链后续 | API 链锚定 feat（已有实现），不依赖前端 | ✓ Good |
| 统一 schema 放 `ssot/schemas/qa/` | 真理源独立，skills 读取验证 | ✓ Good |
| 11 个技能纳入本轮范围 | ADR-047 (9) + ll-skill-install + ll-dev-feat-to-tech | ✓ Good |
| ADR-049 Patch 层独立目录 | 不破坏现有 FEAT flat 文件结构 | — Pending |
| 24h 窗口期从 validated 开始 | 统一计时起点，超期 blocking | — Pending |

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
*Last updated: 2026-04-14 after initialization*
