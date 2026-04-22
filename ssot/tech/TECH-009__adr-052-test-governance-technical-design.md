---
id: TECH-009
ssot_type: TECH
tech_ref: TECH-009
src_ref: SRC-009
epic_ref: EPIC-009
feat_refs:
- FEAT-009-D
- FEAT-009-E
- FEAT-009-A
- FEAT-009-S
title: 测试体系双轴治理 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: SRC-009-adr052
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-FEAT-TECH-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# 测试体系双轴治理 Technical Design Package

## Overview

本 TECH 覆盖 4 个 FEAT 的技术设计，共同构成测试体系双轴治理闭环。

| FEAT | Facet | Technical Focus |
|------|-------|----------------|
| FEAT-009-D | test-governance | 需求轴/实施轴分层 schema、枚举守卫、编译规则 |
| FEAT-009-E | test-execution-framework | StateMachine 状态机、三层断言验证器、故障分类器 |
| FEAT-009-A | audit-and-verification | Verifier 独立认证、Bypass 检测、Accident 打包 |
| FEAT-009-S | skill-orchestration | Skill DAG 解析器、模块调度、执行结果聚合 |

## Architecture

### Layer 1: 需求轴（SSOT）

- TESTSET schema 定义（YAML）
- Environment schema 定义（YAML）
- Gate verdict schema 定义
- 枚举守卫：skill_id / assertion_layer / failure_class / gate_verdict / phase

### Layer 2: 实施轴（Artifact）

- RunManifest 生成器：绑定 run_id / app_commit / base_url / browser
- 事故包生成器：结构化收集 screenshots / traces / network_log / console_log
- 故障分类器：8 类分类 + 后处理路由

### Layer 3: 执行引擎

- StateMachine 执行器：9 状态机（Phase 1 简化 5 状态）
- 断言验证器：A/B/C 三层，C 层覆盖率统计
- Bypass 检测器：检测跳步 / API 直调 / 误判

### Layer 4: Skill 编排

- qa.test-plan：需求 → TESTSET 编译链
- qa.test-run：环境 → 执行 → 报告 → Gate 全链路
- DAG 解析器：模块依赖图、拓扑排序、并行执行

## Module Interfaces

### 需求轴模块

| Module | Axis | Input | Output |
|--------|------|-------|--------|
| feat-to-testset | requirement | FEAT ref, test strategy | TESTSET YAML |
| api-plan-compile | requirement | FEAT API contracts | API test plan |
| api-manifest-compile | requirement | API plan | API manifest |
| api-spec-compile | requirement | API manifest | API test spec |
| e2e-plan-compile | requirement | FEAT E2E contracts | E2E test plan |
| e2e-manifest-compile | requirement | E2E plan | E2E manifest |
| e2e-spec-compile | requirement | E2E manifest | E2E test spec |

### 实施轴模块

| Module | Axis | Input | Output |
|--------|------|-------|--------|
| environment-provision | implementation | Environment schema | Managed environment |
| run-manifest-gen | implementation | Runtime state | RunManifest |
| scenario-spec-compile | implementation | TESTSET, RunManifest | Scenario Spec |
| state-machine-executor | implementation | Scenario Spec | Structured evidence |
| bypass-detector | implementation | Execution log | Violation report |
| independent-verifier | implementation | Evidence, Environment | Verdict |
| accident-package | implementation | Failure state | Accident package |
| failure-classifier | implementation | Accident | Classified failure |
| test-data-provision | implementation | Environment schema | Test data snapshot |
| l0-smoke-check | implementation | Environment | Smoke check result |
| settlement | implementation | Results, Verdict | Settlement report |
| gate-evaluation | implementation | Settlement, Verdict | Gate verdict |

## Constraints

- 所有模块接口契约继承 SRC-009 的 7 条 Frozen Contracts
- 枚举值严格遵循 SRC-009 定义的 allowed_values
- verifier 必须使用独立认证上下文（FC-007）
