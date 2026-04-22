---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: Task Pack Mapping
status: Defining requirements
last_updated: "2026-04-22T11:57:57.759Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 16
  completed_plans: 4
  percent: 25
---

# Project State

**Project:** v2.1 双链双轴测试强化
**Status:** Defining requirements
**Core value:** 实现测试需求轴治理基础设施 — 声明性资产分层与枚举冻结，确保"测什么"由 SSOT 管理
**Current focus:** Defining requirements and roadmap

## Roadmap Summary

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 12 | Schema 定义层 | 3 个 YAML schema (TESTSET/Environment/Gate) | SCHEMA-01~06 |
| 13 | 枚举守卫 | enum_guard.py 实现 6 个枚举字段校验 | ENUM-01~03 |
| 14 | 治理对象验证器 | governance_validator.py 11 个对象字段校验 | GOV-01~03 |
| 15 | 集成与追溯 | enum_guard 集成 SSOT 写入路径 + FC 追溯 | FC-01~03, INT-01~03 |
| 16 | 测试验证 | 完整测试套件 + 证据产出 | TEST-01~05 |

## Accumulated Context

### Previous Milestone: v2.0 ADR-050/051 SSOT 语义治理升级 (Shipped: 2026-04-22)

Delivered:

- FRZ 冻结层结构 + MSC 5维验证
- SSOT 语义抽取链（FRZ → SRC → EPIC → FEAT）
- 执行层语义稳定规则
- 变更分级机制与 ADR-049 协同
- Task Pack 结构 + 顺序执行循环

### Previous Milestone: v1.0 ADR-047 双链测试 (Shipped: 2026-04-17)

Delivered:

- QA Schema 定义（plan/manifest/spec/settlement 四层资产结构）
- 11 个 QA 技能 Prompt-first 运行时
- 结算层/执行层技能补全
- Patch 基础设施（schema, context injector, auto-register）
- CLAUDE.md rules for automatic patch context injection

### Previous Milestone: v1.1 ADR-049 体验修正层 (Code Complete)

Delivered:

- ll-patch-capture skill with dual-path execution
- Patch-aware context resolver + AI Context Injection
- PreToolUse Hook 集成

### Pending Todos

- [ ] 2026-04-22: ADR-052 在v2.1没有进入scope的内容 — FEAT-009-E (状态机执行/三层断言/故障分类), FEAT-009-A (独立验证/违规检测/事故包), FEAT-009-S (Skill编排/DAG), FC-002 (需求轴/实施轴分离契约)

## Artifacts

- `.planning/PROJECT.md` — Project context
- `.planning/config.json` — Workflow preferences
- `.planning/research/` — Domain research (pending)
- `.planning/REQUIREMENTS.md` — Scoped requirements (22 items, v2.1)
- `.planning/ROADMAP.md` — Phase structure (5 phases, 12-16, created 2026-04-22)
- `.planning/codebase/` — Codebase map (7 docs)

---
*Last updated: 2026-04-22 after v2.1 milestone initialization*
