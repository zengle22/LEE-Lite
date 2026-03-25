---
id: FEAT-SRC-001-001
ssot_type: FEAT
title: 主链协作闭环能力
status: frozen
version: v2
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-001
workflow_key: product.epic-to-feat
workflow_run_id: src001-from-frozen-src-20260324
source_refs:
  - EPIC-001
  - SRC-001
  - ADR-005
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-004
  - ARCH-SRC-001-001
epic_ref: EPIC-001
epic_root_id: epic-root-epic-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-24T12:30:00Z'
---

# 主链协作闭环能力

## 目标

让 execution、gate、human 三类 loop 在同一条主链里形成稳定协作闭环，而不是由各 skill 分别拼接回流规则。

## 范围

- 定义 execution loop 应提交什么对象、在何时进入 gate loop，以及哪些状态允许回流到 `revision / retry`。
- 定义 gate loop 与 human loop 的衔接界面，包括谁消费 proposal、谁返回 decision、谁触发后续推进。
- 明确 loop 协作只覆盖推进责任、交接界面与回流条件，不定义 formal materialization 对象本身。
- 显式约束下游不得再为 queue、handoff、gate 关系发明第二套等价规则。

## 输入

- authoritative `EPIC-001`
- `SRC-001` 与相关 ADR 的治理边界
- 上游对 execution / gate / human loop 的协作要求

## 处理

- 将主链协作边界收敛成单一 FEAT 能力面。
- 明确对象交接、状态推进与回流条件由谁负责。
- 为下游 `workflow.dev.feat_to_tech` / `workflow.qa.feat_to_testset` 提供可独立验收的 loop 协作定义，并为后续 `TECH -> IMPL` 保持稳定协作语义。

## 输出

- 主链协作边界定义
- loop responsibility split
- 可被下游继承的回流与推进规则

## 依赖

- 边界依赖 `正式交接与物化能力`：本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。
- 边界依赖 `对象分层与准入能力`：本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。

## 非目标

- 不定义 candidate -> formal 的升级语义、gate decision authority 或 materialization outputs。
- 不定义 object admission、formal-read eligibility 或 path governance policy。

## 约束

- Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。
- 本 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。
- 本 FEAT 继承 `EPIC-001` 的主能力轴与 source refs，不得单独发明平行 queue / handoff 规则。

## 验收检查

### AC-01 协作责任必须明确

- scenario: review `FEAT-SRC-001-001`
- given: 主链需要 execution、gate、human loops 协同
- when: 评审该 FEAT 是否可独立验收
- then: 必须能明确谁拥有哪类 transition、输入对象与返回路径，且不与 formalization 职责重叠

### AC-02 回流条件必须有边界

- scenario: 出现 revise 或 retry
- given: gate 返回需要回流 execution 的 decision
- when: 判断主链如何重入
- then: 必须明确返回什么对象、由谁消费、在什么 loop 状态下允许重入

### AC-03 下游不得重造协作规则

- scenario: downstream workflow 继承本 FEAT
- given: 下游需要 queue、handoff、gate 协同语义
- when: 下游定义自己的推进链
- then: 必须继承本 FEAT 的协作规则，而不是再发明并行 handoff / queue 模型

## 来源追溯

- 本文件物化自 [feat-freeze-bundle.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-to-feat/src001-epic-to-feat-20260324-v3/feat-freeze-bundle.md) 中 `FEAT-SRC-001-001` 对应段落。
