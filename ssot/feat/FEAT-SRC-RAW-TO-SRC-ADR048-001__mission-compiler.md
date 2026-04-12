---
id: FEAT-SRC-RAW-TO-SRC-ADR048-001
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
epic_ref: EPIC-SRC-RAW-TO-SRC-ADR048
title: Mission Compiler —— SSOT 与双链资产编译为 Droid Features
status: frozen
frozen_at: '2026-04-12T17:56:00.000000+00:00'
---

# Mission Compiler —— SSOT 与双链资产编译为 Droid Features

## 背景

SSOT 文档（feat / prototype / tech / api）和双链测试资产（manifest + spec）是静态文档。Droid Missions Runtime 需要结构化的 `features.json` 和 `execution-manifest.yaml` 才能执行。Mission Compiler 负责将冻结的 SSOT 和双链资产编译为机器可消费的格式。

## 用户故事

### US-001: SSOT 文档编译为 Droid Feature

**作为** Mission Compiler
**我希望** 读取冻结的 feat/prototype/tech/api 文档
**以便** 产出 features.json 供 Droid Runtime 消费

**验收标准**:
- AC-001: feat 映射为 feature (feature_type: capability)
- AC-002: prototype 映射为 feature (feature_type: ui-travel)
- AC-003: tech/api 映射为 feature (feature_type: technical)
- AC-004: 字段映射严格遵守 ADR-048 Section 2.4 规范
- AC-005: 相同输入必须产出确定性的 features.json

### US-002: 双链资产编译为 Validation Contract

**作为** Mission Compiler
**我希望** 读取 api_coverage_manifest 和 e2e_coverage_manifest 的每个 item
**以便** 每个 coverage item 编译为一个 validation-contract assertion

**验收标准**:
- AC-001: API coverage item 映射包含 coverage_id, capability, endpoint, scenario_type, priority, dimensions_covered
- AC-002: E2E coverage item 映射包含 coverage_id, journey_id, journey_type, priority, user_steps
- AC-003: spec 断言通过 coverage_id 关联补充到 assertion.preconditions/expected/evidence_required
- AC-004: validation-contracts 与 manifest items 1:1 对应

### US-003: 执行清单按优先级调度

**作为** Droid Job Runner
**我希望** 读取 execution-manifest.yaml 确定执行顺序
**以便** P0 功能先于 P1 执行

**验收标准**:
- AC-001: execution-manifest.yaml 包含所有 feature 的调度元数据
- AC-002: P0 排在 P1 之前，P1 排在 P2 之前
- AC-003: 不消费旧 testset 对象作为输入

## 状态模型

- 主状态流: `compiler_idle` -> `compilation_started` -> `features_compiled` -> `manifest_generated`
- 恢复路径: `compilation_failed` -> 记录失败原因，等待上游文档修复后重试
- 失败信号: `compilation_failed`
- Fail-closed: 编译失败不产出 features.json，不触发下游 Droid Runtime

## 主时序

1. 检测到 frozen SSOT 文档和就位的双链 manifest/spec
2. Mission Compiler 启动，读取输入
3. 按 ADR-048 Section 2.4 映射 SSOT 对象到 Droid features
4. 关联 spec 断言补充 validation-contract assertions
5. 产出 features.json
6. 产出 execution-manifest.yaml（按优先级排序）
7. 触发下游 Droid Runtime Job

## 边界约束

- **入边界**: 只消费 frozen 状态的 SSOT 文档和完整的双链资产（manifest + spec 都就位）
- **出边界**: 产出 features.json + execution-manifest.yaml，触发 target_skill="workflow.adr048.mission-compiler" 的下游 Job
- **不做什么**: 不执行任何测试、不修改 SSOT 文档、不定义运行时执行语义
- **向后兼容**: 不消费旧 testset 对象

## 关键不变量

- Compiler 不得在冻结输入之外发明业务真相或设计真相
- 字段映射必须严格遵守 ADR-048 Section 2.4，不得偏离
- 相同输入必须产出相同输出（确定性）
- 编译失败时不得产出部分 features.json

## 集成点

- 被 Droid Job Runner 通过 `target_skill: "workflow.adr048.mission-compiler"` 调用
- 产出 features.json 到 `ssot/tests/compiled/features.json`
- 产出 execution-manifest.yaml 到 `ssot/tests/compiled/execution-manifest.yaml`
- 下游触发: ready_job_dispatch.py 创建 Droid Runtime Job
