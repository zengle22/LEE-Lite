---
id: FEAT-SRC-001-002
ssot_type: FEAT
title: 正式交接与物化能力
status: frozen
version: v2
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-002
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

# 正式交接与物化能力

## 目标

让 handoff、gate decision 与 formal materialization 形成单一路径的正式升级链，而不是让 candidate 与 formal 流转并存。

## 范围

- 定义 handoff object、gate decision object、formal materialization object 在主链中的单向升级顺序。
- 明确 candidate 只能作为 gate 消费对象，不能绕过 gate 直接成为 downstream formal input。
- 明确本 FEAT 负责正式推进链路，不负责对象准入判定与读取资格细则。
- 要求下游继承同一套 `approve / revise / retry / handoff / reject` 语义，不得并列批准语义。

## 输入

- authoritative `EPIC-001`
- 主链协作产物
- 上游 candidate package、proposal 与 gate 语义约束

## 处理

- 将 handoff、gate decision 与 formal materialization 收敛成单一路径推进链。
- 固定 candidate 与 formal 的升级顺序。
- 为下游定义可继承的正式交接与物化边界。

## 输出

- handoff -> gate decision -> formal materialization 正式推进规则
- candidate / formal 单一路径边界
- 下游统一 decision 语义

## 依赖

- 边界依赖 `主链协作闭环能力`：消费 loop 协作产物，但不重写 execution / gate / human 的责任分工、状态流转与回流条件。
- 边界依赖 `对象分层与准入能力`：定义 candidate 到 formal 的推进链，不定义 consumer admission 与读取资格。

## 非目标

- 不重新定义 execution / gate / human loop 的 responsibility split 或 re-entry conditions。
- 不定义 consumer admission、formal-ref eligibility 或 path enforcement policy。

## 约束

- Candidate 不得绕过 gate 直接升级为 downstream formal input。
- Formal materialization 语义必须单一路径推进，不得出现并列正式化入口。
- 本 FEAT 只定义正式推进链，不吸收对象准入或 path/mode 规则。

## 验收检查

### AC-01 正式升级路径必须唯一

- scenario: candidate outputs awaiting approval
- given: 上游产出了待审批 candidate
- when: 主链从 candidate 进入 formal 状态
- then: 必须沿 handoff -> gate decision -> formal materialization 的单一路径推进，不得存在并行 shortcut

### AC-02 candidate 不得绕过 gate

- scenario: downstream consumer 请求正式输入
- given: candidate package 已存在但 gate approval 尚未发生
- when: 试图把 candidate 当作 formal input
- then: 系统必须拒绝该旁路，把 candidate 与 formal 严格分层

### AC-03 formalization 不得回流进业务 skill

- scenario: business skill emits proposal and evidence
- given: 业务 skill 已完成自身职责
- when: 需要执行 formalization
- then: formalization decision 与 materialization action 必须保持在业务 skill 之外

## 来源追溯

- 本文件物化自 [feat-freeze-bundle.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-to-feat/src001-epic-to-feat-20260324-v3/feat-freeze-bundle.md) 中 `FEAT-SRC-001-002` 对应段落。
