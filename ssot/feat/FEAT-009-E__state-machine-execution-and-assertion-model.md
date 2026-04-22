---
id: FEAT-009-E
ssot_type: FEAT
feat_ref: FEAT-009-E
epic_ref: EPIC-009
title: 测试执行框架 — 状态机执行与三层断言模型
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-EPIC-FEAT-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# 测试执行框架 — 状态机执行与三层断言模型

## Goal

定义状态机执行器和三层断言模型，为 AI 执行提供结构化约束，确保"结果可信"而非仅"脚本能跑"。

## Scope

- 定义 StateMachine 有限状态执行器：9 状态（Phase 1 简化 5 状态），逐节点执行产出结构化证据
- 定义三层断言模型：A:交互断言 / B:页面结果断言 / C:业务状态断言
- 定义 8 类故障分类：ENV/DATA/SCRIPT/ORACLE/BYPASS/PRODUCT/FLAKY/TIMEOUT
- 定义 L0-L3 分层执行模型
- 定义 RunManifest 绑定执行时的世界快照（版本/环境/账号/数据）
- 定义 6 条黄金路径（G1-G6）按产品核心价值主张排序
- 定义 4 阶段实施计划（1a/1b/2/3/4）

## Acceptance Criteria

- StateMachine 有 states / transitions / on_fail_behavior 定义
- 三层断言模型中 A/B 层必须定义，C 层按阶段要求执行
- 黄金路径 C 层断言 100% 覆盖前 Gate 不得返回 pass（FC-003）
- Phase 1 Gate 结论上限为 provisional_pass（FC-005）
- RunManifest 包含 run_id / app_commit / base_url / browser / generated_at
