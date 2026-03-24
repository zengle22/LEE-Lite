---
id: FEAT-SRC-001-005
ssot_type: FEAT
title: External Gate Decision 与正式物化
status: frozen
version: v1
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-005
workflow_key: workflow.product.task.epic_to_feat
source_refs:
  - EPIC-001
  - SRC-001
  - ADR-006
epic_ref: EPIC-001
epic_root_id: epic-root-epic-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-24T09:20:00Z'
---

# External Gate Decision 与正式物化

## 目标

建立独立的 External Gate Decision 与 Materialization 能力，使 governed skill 在产出 candidate package、proposal 与 evidence 之后，能够由统一 consumer 完成互斥单选裁决、正式对象物化、下游 job / handoff 派发与 run closure，而不是把这些职责散落在各业务 skill 的尾部逻辑里。

## 范围

- 定义 external gate 的最小输入集、decision model 与 target 约束矩阵，包括 `approve`、`revise`、`retry`、`handoff`、`reject` 五类互斥决策。
- 定义 `gate-decision`、`materialized-ssot`、`materialized-handoff`、`materialized-job`、`run-closure` 与 `revision-request` 等正式对象边界。
- 定义 gate-ready job 消费、formal materialization、下游 queue routing 与 human-review dispatch 的最小运行链路。
- 定义 approve、revise、retry、handoff、reject 对 run/job/handoff 状态推进与 lineage 继承的约束。

## 输入

- 上游 governed skill 产出的 candidate package
- result summary、acceptance 结论、execution / supervision evidence、retry budget 与 proposal
- 由 FEAT-SRC-001-001 / 002 / 003 / 004 提供的 Gateway、Path Policy、Registry 与 Audit 约束

## 处理

- 校验 gate-ready package 的完整性与推进前置条件。
- 形成唯一 `decision_type`，并根据 target 约束矩阵判断推进、修订、重试、交接或拒绝。
- 通过受管写入将正式 decision、formalized object、dispatch job 与 run closure 落入正式链路。

## 输出

- `gate-decision`
- `materialized-ssot` / `materialized-handoff` / `materialized-job`
- `revision-request`
- `run-closure`

## 依赖

- 依赖 `FEAT-SRC-001-001` 提供正式读写 Gateway 入口。
- 依赖 `FEAT-SRC-001-002` 提供路径与 mode 的合法性判定。
- 依赖 `FEAT-SRC-001-003` 提供 formal reference、registry 登记与受管读资格判定。
- 依赖 `FEAT-SRC-001-004` 提供 execution / audit evidence 与阻断证据。

## 非目标

- 不在本 FEAT 内重新进行业务语义评审或重写上游 candidate 内容。
- 不在本 FEAT 内替代 human gate、审批人或业务 owner 的最终判断责任。
- 不在本 FEAT 内要求立即建设重型 daemon、事件总线或数据库 runtime。
- 不在本 FEAT 内展开每一个上游 workflow 的逐项迁移计划。

## 约束

- External Gate 必须作为独立 consumer / 独立 skill 存在，不得回落为业务 skill 的附属脚本。
- proposal 与 materialized object 必须分层；formal SSOT、formal handoff、formal job 与 run closure 只能在 gate 批准或分流后物化。
- `decision_type` 必须互斥单选，并满足 target 字段约束；不得出现多 flag 并列批准。
- 原 run 一旦被 gate 消费，必须立即结案；`revise` 与 `retry` 一律新建 follow-up run / job，不得改写原 run。

## 验收检查

### AC-01 gate decision 必须互斥且可追溯

- scenario: external gate 消费一个 gate-ready package
- given: candidate package、proposal、evidence 与 budget 信息完整
- when: external gate 形成决策
- then: 系统必须生成唯一 `decision_type`，并满足 target 字段约束矩阵
- trace_hints: gate-decision, decision_type, approved_target, followup_target

### AC-02 formal object 只能在 gate 后物化

- scenario: freeze-ready candidate 需要被晋升为正式对象
- given: package 已通过 gate 前置校验
- when: external gate 决定 approve 或 handoff
- then: formal SSOT、handoff、job 或 closure 必须由 gate materialization 写入，不得由上游 skill 直接落盘
- trace_hints: materialized-ssot, materialized-handoff, materialized-job, managed write

### AC-03 run closure 与 follow-up dispatch 必须一致

- scenario: gate 需要推进、修订、重试、交接或拒绝
- given: 已有最终 decision
- when: external gate 结束当前消费
- then: 原 run 必须进入终态并写出 `run-closure`，同时只生成与该决策一致的 follow-up object
- trace_hints: run-closure, spawned_job_refs, spawned_handoff_refs, terminal_state

## 来源追溯

- `目标` 与 `范围` 派生自 `EPIC-001` 的 `范围` 第 5 条、`约束`、`拆分原则` 与 `验收形态`。
- `处理`、`约束` 与 `验收检查` 映射 `ADR-006` 的 `Decision 模型`、`Materialization 规则`、`状态机` 与 `最小对象字段`。
