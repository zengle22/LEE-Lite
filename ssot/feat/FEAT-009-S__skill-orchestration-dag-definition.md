---
id: FEAT-009-S
ssot_type: FEAT
feat_ref: FEAT-009-S
epic_ref: EPIC-009
title: Skill 编排 — 用户入口与内部模块 DAG 定义
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-EPIC-FEAT-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# Skill 编排 — 用户入口与内部模块 DAG 定义

## Goal

定义 2 个用户入口 Skill（qa.test-plan / qa.test-run）及其编排的 17+ 内部模块的 DAG 结构和执行流。

## Scope

- 定义 qa.test-plan Skill：将需求转化为可执行测试计划，编排 feat-to-testset / api-plan-compile / api-manifest-compile / api-spec-compile / e2e-plan-compile / e2e-manifest-compile / e2e-spec-compile
- 定义 qa.test-run Skill：在指定环境上跑测试并生成结果和报告，编排 environment-provision / test-data-provision / l0-smoke-check / run-manifest-gen / scenario-spec-compile / state-machine-executor / bypass-detector / accident-package / failure-classifier / independent-verifier / settlement / gate-evaluation，支持 full / last_failed / report_only 模式
- 定义 Skill 仅作为用户入口，内部模块不注册为 Skill（FC-001）
- 定义 17+ 内部模块的接口契约（module_id / axis / input / output）

## Acceptance Criteria

- 2 个 Skill 均有 skill_id / purpose / orchestrates 定义
- 内部模块仅有 module_id / axis / input / output，无 skill_registration
- qa.test-run 支持 full / last_failed / report_only 模式
- 所有模块 DAG 可执行，无循环依赖
- 模块接口契约明确定义 input 和 output 结构
