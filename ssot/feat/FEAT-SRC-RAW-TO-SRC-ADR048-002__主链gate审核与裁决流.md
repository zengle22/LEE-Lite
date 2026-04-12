---
id: FEAT-SRC-RAW-TO-SRC-ADR048-002
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-002
epic_ref: EPIC-RAW-TO-SRC-ADR048
title: 主链gate审核与裁决流
status: frozen
frozen_at: '2026-04-11T06:31:35.368720+00:00'
---

# 主链gate审核与裁决流

Feature: 主链gate审核与裁决流

## 背景

主链 candidate 提交到 gate pending 后，需要通过统一的审核与裁决流形成权威 decision object。本 FEAT 定义 gate 如何审核 candidate、生成 GateBriefRecord 供 human reviewer 消费、形成单一 authoritative decision，并把结果明确返回 execution 或 formal 发布链。

## 用户故事

### US-001: Gate 审核 candidate 并生成 brief

**作为** gate evaluator
**我希望** 收到 candidate handoff 后自动生成 GateBriefRecord 和 human-facing projection
**以便** human reviewer 能快速理解 candidate 内容和审核要点

**验收标准**:
- AC-001: GateBriefRecord 包含 handoff_ref、proposal_ref、evidence_refs 摘要
- AC-002: Brief 生成幂等（同一 handoff_ref + brief_round 返回相同结果）
- AC-003: Brief 生成失败时保留 handoff 但阻止 decision issuance，记录 brief_build_failed

### US-002: Human reviewer 做出裁决决策

**作为** human reviewer
**我希望** 基于 GateBriefRecord 做出 approve/revise/retry/reject 决策
**以便** candidate 能进入正确的下游处理路径

**验收标准**:
- AC-001: GateDecision 包含 decision、decision_reason、decision_target、decision_basis_refs、dispatch_target
- AC-002: 决策缺失 decision_target 或 decision_basis_refs 时拒绝落 decision object
- AC-003: 决策幂等（同一 pending_human_decision_ref + decision_round 返回相同结果）

### US-003: 下游消费方接收决策结果

**作为** downstream consumer（execution/formal publisher/delegate handler）
**我希望** 接收结构化的 gate decision 并执行对应动作
**以便** candidate 能按决策结果回流、重试、正式化或被拒绝

**验收标准**:
- AC-001: approve 决策触发 formal publication trigger
- AC-002: revise 决策回流到 returned_for_revision -> candidate_prepared
- AC-003: retry 决策进入 retry_pending -> submitted_to_gate
- AC-004: reject 决策保留证据、无下游副作用

## 状态模型

- 主状态流: `candidate_prepared` -> `submitted_to_gate` -> `brief_prepared` -> `pending_human_decision` -> `decision_issued` -> `execution_returned|delegated|publication_triggered|rejected`
- 回流路径: `decision_issued(revise)` -> `returned_for_revision` -> `candidate_prepared`
- 重试路径: `decision_issued(retry)` -> `retry_pending` -> `submitted_to_gate`
- 失败信号: `invalid_state`（非 pending 状态请求决策）、`brief_build_failed`（brief 生成失败）、`unknown_target`（dispatch target 无法解析）、`missing_basis_refs`（决策缺少依据引用）、`policy_reject`（策略拒绝）
- 恢复路径: invalid_state 时拒绝并允许 candidate 重新准备；brief_build_failed 保留数据允许重试；unknown_target 要求有效 target 解析后重新提交；missing_basis_refs 要求补充依据后重试；policy_reject 路由到拒绝处理器需手动解决后重试

## 主时序

1. Gate evaluator 接收 candidate handoff（handoff_ref + proposal_ref + evidence_refs）
2. 系统验证 gate-pending 状态并构建 GateBriefRecord
3. 系统持久化 GatePendingHumanDecision 和 human-facing projection
4. Human reviewer 基于 brief 做出决策（approve/revise/retry/reject）
5. 系统验证 decision_target 和 decision_basis_refs 完整性
6. 系统生成 GateDecision 并 dispatch 到 execution/delegated handler/formal publication trigger
7. 返回 decision_ref 和 dispatch receipt

## 边界约束

- **入边界**: 必须包含 handoff_ref、proposal_ref、evidence_refs，且 handoff 已进入 gate pending 状态
- **出边界**: 返回 decision_ref、decision、decision_reason、decision_target、decision_basis_refs、dispatch_target
- **不做什么**: 不执行 formal publication（由 FEAT-003 负责）、不重新定义 submission receipt、不实现 UI 组件
- **向后兼容**: business skill 继续产出 candidate/proposal/evidence，不新增直接 formal write 路径

## 关键不变量

- Gate decision path 必须唯一且显式：不得出现并行决策入口
- Candidate 不得绕过 gate 直接升级为 downstream formal input
- Formal 发布只能由 authoritative decision object 触发，不得出现并列正式化入口
- `ll gate evaluate` 与 `ll gate dispatch` 的 decision vocabulary / dispatch_target 必须共享同一份枚举与 target 语义
