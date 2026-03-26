---
id: FEAT-SRC-003-006
ssot_type: FEAT
feat_ref: FEAT-SRC-003-006
epic_ref: EPIC-SRC-003-001
title: 执行结果回写与重试边界流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# 执行结果回写与重试边界流

## Goal
冻结 runner 执行后的 done / failed / retry-reentry 结果，让自动推进链在下一跳后仍可审计、可回流。

## Scope
- 定义 execution result、failure reason 和 retry / reentry directive 的 authoritative 结果。
- 定义 job 从 running 进入 done / failed / retry_return 的状态边界。
- 定义 runner 输出如何服务上游审计、下游继续推进和失败恢复。

## Constraints
- done / failed / retry-reentry outcome 必须显式记录。
- 失败证据必须和 execution attempt 绑定。
- retry 必须回到 execution semantics，不得改写成 publish-only 状态。
- approve 不是自动推进链的终态。

## Acceptance Checks
1. Execution outcomes are explicit
   Then: the product flow must emit explicit done, failed, or retry/reentry outcomes with evidence.
2. Retry returns to execution semantics
   Then: the result must return through retry / reentry semantics instead of being rewritten as publish-only status.
3. Approve is not treated as terminal
   Then: the chain must continue through runner execution and result feedback rather than ending at approve itself.
