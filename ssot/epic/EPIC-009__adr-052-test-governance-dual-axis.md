---
id: EPIC-009
ssot_type: EPIC
src_ref: SRC-009
title: 测试体系双轴治理 — 需求轴SSOT与实施轴Artifact统一能力
status: accepted
schema_version: 1.0.0
epic_root_id: EPIC-009
workflow_key: product.src-to-epic
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-SRC-EPIC-009.json
depends_on:
- product.raw-to-src::SRC-009-adr052
- SRC-009
- ADR-052
- ADR-047
- ADR-050
- ADR-051
frozen_at: '2026-04-22T00:00:00+08:00'
acceptance_summary: EPIC decomposes SRC-009 into 4 facet-aligned FEATs covering test governance, execution framework, audit/verification, and skill orchestration.
---

# 测试体系双轴治理 — 需求轴SSOT与实施轴Artifact统一能力

## Epic Intent

将《ADR-052 测试体系轴化 — SSOT需求轴与实施轴治理架构》中的治理问题空间收敛为"测试体系双轴治理统一能力"这一 EPIC 级产品能力块，建立需求轴（SSOT 声明性资产）与实施轴（Artifact 证据性资产）的独立治理闭环，确保 E2E 测试从"脚本能跑"升级为"结果可信"。

## Scope

- 定义需求轴/实施轴双模型：声明可覆盖 vs 证据只追加，独立生命周期治理
- 定义 2 个用户入口 Skill（qa.test-plan / qa.test-run）编排 17+ 内部模块的架构
- 定义三层断言模型（A:交互 / B:页面结果 / C:业务状态）及 Gate 判定依赖
- 定义状态机执行器约束 AI 执行路径，8 类故障分类标准化
- 定义独立验证层（verifier）一票否决 Gate 的治理规则
- 定义 GoldenPath schema 和验证标准，用于固化产品侧定义的核心用户旅程验证要求
- 定义 4 阶段实施计划（1a/1b/2/3/4）及每阶段 Gate 结论上限

## Out of Scope

- 具体实现代码编写
- UI 界面设计
- 分布式编排器实现
- 数据库 schema 变更

## FEAT Decomposition

| FEAT | Facet | Focus |
|------|-------|-------|
| FEAT-009-D | test-governance | 需求轴/实施轴分层规则、枚举冻结、关键约束继承 |
| FEAT-009-E | test-execution-framework | 状态机执行、三层断言、8 类故障分类、L0-L3 分层执行 |
| FEAT-009-A | audit-and-verification | independent-verifier 独立认证、bypass-detector 违规检测、事故包标准化 |
| FEAT-009-S | skill-orchestration | 2 个用户 Skill 编排 17+ 内部模块的 DAG 定义与执行流 |

## Key Constraints (inherited from SRC-009)

- FC-001: Skill 仅用户入口，内部模块不注册为 Skill
- FC-002: 需求轴资产声明性可覆盖，实施轴资产证据性只追加
- FC-003: 黄金路径 C 层断言 100% 覆盖前 gate 不得返回 pass
- FC-004: verifier=fail → Gate 必须=fail，不可被 settlement 覆盖
- FC-005: Phase 1 Gate 结论上限为 provisional_pass
- FC-006: TESTSET 中不得嵌入 test_case_pack 或 script_pack
- FC-007: verifier 必须使用独立认证上下文

## Frozen Enums (inherited from SRC-009)

- skill_id: ["qa.test-plan", "qa.test-run"]
- assertion_layer: ["A", "B", "C"]
- failure_class: ["ENV", "DATA", "SCRIPT", "ORACLE", "BYPASS", "PRODUCT", "FLAKY", "TIMEOUT"]
- gate_verdict: ["pass", "conditional_pass", "fail", "provisional_pass"]
- phase: ["1a", "1b", "2", "3", "4"]
