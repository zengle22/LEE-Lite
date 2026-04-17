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

### Active

_None — milestone v1.0 complete. Remaining skill hardening deferred to v1.1._

### Deferred to v1.1

- [ ] ADR-047 的 9 个 QA 技能补上 Prompt-first 运行时（scripts/agents/validate）
- [ ] ll-skill-install 技能补全实现
- [ ] ll-dev-feat-to-tech 技能补充测试覆盖
- [ ] 统一 QA schema 定义（plan/manifest/spec/settlement 四层资产结构）
- [ ] 选一个真实 feat 跑通 API 链全流程（plan → spec → exec → settlement → gate）
- [ ] 产出 schema 定义文件放入 `ssot/schemas/qa/`

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
- 当前有 9 个 QA 技能空壳 + 2 个其他空壳技能需要补全
- 方案讨论文档已生成：`.planning/ADR047-IMPLEMENTATION-PROPOSAL.md`

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
| 统一 schema 放 `ssot/schemas/qa/` | 真理源独立，skills 读取验证 | ✓ Deferred to v1.1 (ADR-049 provides patch/manifest schemas) |
| 11 个技能纳入本轮范围 | ADR-047 (9) + ll-skill-install + ll-dev-feat-to-tech | ✓ Deferred — scope reduced to infrastructure foundation |

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
*Last updated: 2026-04-17 after v1.0 milestone completion (ADR-047 双链测试基础设施)*
