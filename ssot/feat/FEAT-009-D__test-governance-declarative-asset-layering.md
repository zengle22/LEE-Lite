---
id: FEAT-009-D
ssot_type: FEAT
feat_ref: FEAT-009-D
epic_ref: EPIC-009
title: 测试需求轴治理 — 声明性资产分层与枚举冻结
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-EPIC-FEAT-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# 测试需求轴治理 — 声明性资产分层与枚举冻结

## Goal

定义需求轴（SSOT）治理规则：TESTSET/环境/Gate 的声明性资产分层管理、枚举冻结规则、需求轴/实施轴分离契约。确保"测什么"由 SSOT 管理，"在哪测、怎么跑"由实施轴 Artifact 管理。

## Scope

- 定义需求轴资产范围：TESTSET 策略、Environment 定义、Gate verdict 规则
- 定义实施轴资产范围：测试报告、事故包、Run Manifest、执行日志
- 定义 7 条 Frozen Contracts（FC-001 ~ FC-007）
- 定义 6 个枚举字段的冻结值及 forbidden_semantics
- 定义 11 个治理对象的结构化契约（Skill/Module/AssertionLayer/FailureClass/GoldenPath/Gate/StateMachine/RunManifest/Environment/Accident/Verifier）
- 定义需求轴编译规则：声明性资产可从 FEAT/TECH/UI 重新编译
- 定义实施轴只追加规则：证据性资产 append-only，不可改写

## Acceptance Criteria

- TESTSET 不包含 test_case_pack 或 script_pack（FC-006）
- 所有 6 个枚举字段有 allowed_values 和 forbidden_semantics
- 7 条 Frozen Contracts 在 TESTSET/Environment/Gate 定义中可追溯
- 11 个治理对象均有 required_fields / optional_fields / forbidden_fields 定义
