---
id: FEAT-SRC-003-005
ssot_type: FEAT
feat_ref: FEAT-SRC-003-005
epic_ref: EPIC-SRC-003-001
title: 下游 Skill 自动派发流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# 下游 Skill 自动派发流

## Goal
冻结 claimed execution job 如何在 gate 已允许 `auto-continue` 时自动派发到下一个 governed skill，并保持 authoritative input / target skill / execution intent 一致。

## Scope
- 定义 next skill target、输入包引用和调用边界。
- 定义 gate `progression_mode` 如何控制自动派发与 hold。
- 定义 runner 把 claimed job 交给下游 skill 时的 authoritative invocation 记录。
- 定义执行启动失败时如何回写 runner 结果而不是静默丢失。

## Constraints
- claimed execution job 必须调用声明的 next skill。
- 未被 gate 放行为 `auto-continue` 的 approve，不得被 runner 自动拉起。
- dispatch 必须保留 authoritative input refs 和 target skill lineage。
- 自动推进不得回退为人工第三会话接力。
- dispatch 失败必须回写 execution outcome。

## Acceptance Checks
1. Claimed job invokes the declared next skill
   Then: the invocation must target the declared next governed skill with the authoritative input package.
2. Dispatch preserves lineage
   Then: the execution attempt must preserve upstream refs, job refs, and target-skill lineage.
3. Holdable approvals are not auto-dispatched
   Then: the FEAT must show that `progression_mode = hold` keeps the job out of the ready queue until operator preconditions are satisfied.
