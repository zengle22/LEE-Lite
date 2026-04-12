---
id: FEAT-SRC-RAW-TO-SRC-ADR048-001
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
epic_ref: EPIC-RAW-TO-SRC-ADR048
title: 主链候选提交与交接流
status: frozen
frozen_at: '2026-04-11T06:31:35.355867+00:00'
---

# 主链候选提交与交接流

Feature: 主链候选提交与交接流

## 背景

Governed skill 产出 candidate package（包含 proposal、evidence、handoff）后，需要通过统一的 handoff runtime 提交到主链 gate 进行审核。本 FEAT 定义 candidate 如何从 producer 侧交接给 gate 侧，形成可被 gate evaluate 消费的单一 authoritative handoff 对象。

## 用户故事

### US-001: Producer 提交 candidate package

**作为** governed skill 的 executor
**我希望** 将 candidate package（proposal + evidence + handoff）通过统一 IO 边界提交到主链
**以便** 它能进入 gate 审核流程

**验收标准**:
- AC-001: 提交前验证 handoff_ref、proposal_ref、payload_ref 三者都存在且一致
- AC-002: 提交后生成唯一的 handoff 对象，包含 producer_ref、proposal_ref、payload_ref、pending_state
- AC-003: 重复提交相同 handoff_ref + proposal_ref 时返回 duplicate_submission 错误
- AC-004: 提交失败时保留原始 candidate 数据，允许重试

### US-002: Gate 接收 candidate 并准备 brief

**作为** gate evaluator
**我希望** 收到 candidate 后自动生成 GateBriefRecord
**以便** human reviewer 能快速理解 candidate 内容和审核要点

**验收标准**:
- AC-001: GateBriefRecord 包含 handoff_ref、proposal_ref、evidence_refs 摘要
- AC-002: Brief 生成失败时保留 handoff 但阻止 decision issuance
- AC-003: Brief 生成幂等（同一 handoff_ref + brief_round 返回相同结果）

### US-003: 下游消费方读取 handoff 状态

**作为** downstream consumer
**我希望** 查询 handoff 的 pending 状态和 brief 摘要
**以便** 了解 candidate 当前处于审核链的哪个阶段

**验收标准**:
- AC-001: pending handoff 列表按提交时间排序
- AC-002: 每个 pending 项包含 proposal_ref、producer_ref、pending_state

## 状态模型

- 主状态流: `candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued`
- 回流路径: `decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`
- 重试路径: `decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`
- 失败信号: `invalid_state`（非 prepared 状态提交）、`missing_payload`（payload_ref 不存在）、`duplicate_submission`（重复提交）、`brief_build_failed`（brief 生成失败）
- 恢复路径: 重复提交时返回已有 handoff 而非报错；brief_build_failed 保留 handoff 允许重试

## 主时序

1. Producer 组装 candidate package（proposal + evidence + handoff）
2. Producer 调用 handoff runtime 提交到 gate pending
3. 系统验证 handoff 完整性（refs 存在、无重复、状态合法）
4. 系统生成 GateBriefRecord 和 human-facing projection
5. 系统持久化 handoff 对象到 artifacts/active/gates/handoffs/
6. 系统注册 handoff 到 pending 列表
7. 返回 handoff_ref 给 producer

## 边界约束

- **入边界**: candidate package 必须包含 proposal_ref、producer_ref、payload_ref
- **出边界**: 返回 handoff_ref、gate_pending_ref、evidence_refs
- **不做什么**: 不执行 gate 决策、不触发 formal 发布、不修改 candidate 内容
- **向后兼容**: 现有 business skill 继续产出 candidate/proposal/evidence，不需要直接 formal write 路径

## 关键不变量

- Gate decision path 必须唯一且显式：不得出现并行决策入口
- Candidate 不得绕过 gate 直接成为 downstream formal input
- Handoff 一旦提交不可修改（append-only），revision 通过新建 candidate 实现
