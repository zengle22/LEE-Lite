---
id: FEAT-SRC-001-003
ssot_type: FEAT
title: 对象分层与准入能力
status: frozen
version: v2
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-003
workflow_key: workflow.product.task.epic_to_feat
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

# 对象分层与准入能力

## 目标

让 candidate package、formal object 与 downstream consumption 形成稳定分层，防止业务 skill 混入裁决与准入职责。

## 范围

- 定义 candidate package、formal object、downstream consumption object 的分层职责和允许的引用方向。
- 定义什么对象有资格成为正式输入，以及哪些 consumer 只能读取 formal layer 而不能读取 candidate layer。
- 明确本 FEAT 负责对象层级与准入，不负责 handoff 决策链和 IO/path 落盘策略。
- 要求任何下游消费都必须沿 formal refs 与 lineage 进入，不能以路径猜测或旁路对象读取。

## 输入

- authoritative `EPIC-001`
- candidate / formal / downstream object 边界
- 上游关于 formal refs、lineage 与 consumer admission 的继承约束

## 处理

- 固定对象层级、引用方向与准入规则。
- 阻断业务 skill 在 candidate 层承担 gate 或 formal admission 职责。
- 为下游 delivery、TECH、TASK 和 TESTSET 提供统一的分层准则。

## 输出

- candidate / formal / consumer 分层定义
- formal-ref 与 lineage 导向的准入边界
- consumer admission 约束

## 依赖

- 边界依赖 `正式交接与物化能力`：定义哪些对象可以成为正式输入，而不是定义正式升级动作本身。
- 边界依赖 `主链文件 IO 与路径治理能力`：定义对象资格与引用方向，path / mode 规则留给 IO 治理 FEAT。

## 非目标

- 不定义 handoff -> gate decision -> formal materialization 动作链。
- 不定义 governed artifact paths、write modes 或 repository-level IO enforcement。

## 约束

- Consumer 准入必须沿 formal refs 与 lineage 判断，不得通过路径猜测获得读取资格。
- 对象分层必须阻止业务 skill 在 candidate 层承担 gate 或 formal admission 职责。
- 当 `rollout_required = true` 时，本 FEAT 必须能与 adoption/E2E FEAT 一起支撑真实 pilot 主链验证。

## 验收检查

### AC-01 candidate 与 formal 不能混层

- scenario: consumer resolves upstream inputs
- given: 上游同时存在 candidate 与 formal-stage objects
- when: 判断哪个对象可作为权威输入
- then: 必须明确 formal layer 的权威性，并禁止 layer ambiguity

### AC-02 consumer 准入必须基于 formal refs

- scenario: downstream reader consumes governed object
- given: consumer 需要解析上游正式输入
- when: 判断 eligibility
- then: 必须要求 formal refs 与 lineage-based admission，而不是 path guessing 或 adjacent file discovery

### AC-03 业务 skill 不得静默继承 gate authority

- scenario: 业务 skill 产出 candidate package
- given: 需要判断该 package 是否可直接用于 downstream
- when: 审查对象分层边界
- then: 必须阻止业务 skill 静默充当 gate、approver 或 formal admission authority

## 来源追溯

- 本文件物化自 [feat-freeze-bundle.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-to-feat/src001-epic-to-feat-20260324-v3/feat-freeze-bundle.md) 中 `FEAT-SRC-001-003` 对应段落。
