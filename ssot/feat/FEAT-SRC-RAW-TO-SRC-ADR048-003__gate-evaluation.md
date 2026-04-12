---
id: FEAT-SRC-RAW-TO-SRC-ADR048-003
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-003
epic_ref: EPIC-SRC-RAW-TO-SRC-ADR048
title: Gate Evaluation —— Settlement 计算与里程碑决策
status: frozen
frozen_at: '2026-04-12T17:56:00.000000+00:00'
---

# Gate Evaluation —— Settlement 计算与里程碑决策

## 背景

Droid Runtime 完成所有验证后，产出 validation-state.yaml。Gate Evaluation 负责消费这些状态，计算 settlement 统计，产出里程碑决策（release / conditional_release / block）。如果是 block，则创建 Fix Feature 重新进入闭环。

## 用户故事

### US-001: Settlement 计算

**作为** Gate Settlement Computer
**我希望** 读取 API 和 E2E 的 validation-state
**以便** 计算通过/失败/阻塞/未覆盖的统计

**验收标准**:
- AC-001: API chain 统计: total, passed, failed, blocked, uncovered, waiver_refs
- AC-002: E2E chain 统计: total, passed, failed, blocked, uncovered, waiver_refs
- AC-003: 统计口径遵循 ADR-048 Section 2.4 Settlement/Gate 规范
- AC-004: 产出 release_gate_input.yaml

### US-002: Gate 决策

**作为** Gate Evaluator
**我希望** 根据 settlement 结果和 waiver 状态做决策
**以便** 产出 release / conditional_release / block

**验收标准**:
- AC-001: 无失败 + 无未覆盖 → release
- AC-002: 有 waiver 批准的未覆盖 → conditional_release
- AC-003: 有未批准的失败 → block，创建 Fix Feature
- AC-004: 决策包含完整的 decision_basis_refs

### US-003: 里程碑决策映射

**作为** Milestone Mapper
**我希望** 将 gate 决策映射为里程碑决策
**以便** 下游消费方理解进度

**验收标准**:
- AC-001: release → milestone: feature_complete
- AC-002: conditional_release → milestone: feature_complete_with_waivers
- AC-003: block → milestone: blocked，包含 fixes_for 链接

### US-004: Fix Feature 创建

**作为** Fix Feature Creator
**我希望** 为每个 block 项创建 Fix Feature
**以便** 回流到 Mission Compiler 重新进入闭环

**验收标准**:
- AC-001: Fix Feature 是新建，非修改原 feat
- AC-002: 包含 fixes_for 链接指向失败的 validation-contract
- AC-003: Fix Feature 通过 Job Runner 派发回 Mission Compiler 重新编译

## 状态模型

- 主状态流: `eval_idle` -> `settlement_computed` -> `decision_issued` -> `milestone_recorded`
- 恢复路径: `settlement_failed` -> 记录计算失败原因，等待人工介入
- 恢复路径: `decision_conflict` -> 检测到与现有状态冲突，升级到人工审核
- 恢复路径: `fix_feature_creation_failed` -> 记录失败，不完成 decision
- 失败信号: `settlement_failed`、`decision_conflict`、`fix_feature_creation_failed`
- Fail-closed: settlement 计算失败不产出决策，要求人工介入

## 主时序

1. Droid Job Runner 派发 Gate Evaluation Job（target_skill: "workflow.adr048.gate-evaluation"）
2. Settlement Computer 读取 validation-state.yaml
3. 计算 API 和 E2E 统计
4. Gate Evaluator 根据 settlement 做决策
5. Milestone Mapper 映射为里程碑决策
6. 如果是 block → Fix Feature Creator 创建 Fix Feature
7. Fix Feature 通过 Job Runner 回流到 Mission Compiler
8. 如果是 release/conditional_release → 触发 formal publication

## 边界约束

- **入边界**: 只消费 Droid Runtime 产出的 validation-state.yaml 和 waiver 记录
- **出边界**: 产出 gate decision（release/conditional_release/block）、milestone decision、（可选）Fix Feature
- **不做什么**: 不执行测试、不修改 SSOT 文档、不定义运行时执行语义
- **向后兼容**: 不影响现有 gate human orchestrator 的人工审核流程

## 关键不变量

- Settlement 计算必须基于完整的 validation-state，不得跳过未完成的 contract
- Gate 决策必须包含完整的 decision_basis_refs，可追溯到每个 validation-contract
- Fix Feature 必须是新建，不得修改原 feat 文档
- waiver 必须经过人工批准，不得自动批准

## 集成点

- 被 Droid Job Runner 通过 `target_skill: "workflow.adr048.gate-evaluation"` 调用
- 读取 Droid Runtime 产出的 validation-state.yaml
- 产出 gate decision 到 artifacts/gates/
- block 时通过 ready_job_dispatch.py 创建 Fix Feature Job
- release 时通过 ready_job_dispatch.py 创建 Formal Publication Job
- 包含 4 个新模块: settlement_computer.py, gate_evaluator.py, milestone_mapper.py, fix_feature_creator.py
