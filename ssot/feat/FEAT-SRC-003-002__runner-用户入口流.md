---
id: FEAT-SRC-003-002
ssot_type: FEAT
feat_ref: FEAT-SRC-003-002
epic_ref: EPIC-SRC-003-001
title: Runner 用户入口流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-lineage-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-lineage-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# Runner 用户入口流

## Goal
冻结一个用户可显式调用的 Execution Loop Job Runner canonical governed skill bundle，让 operator 能从 Claude/Codex CLI 启动或恢复自动推进。

## Scope
- 定义独立 canonical governed skill bundle：`skills/l3/ll-execution-loop-job-runner/`。
- 定义入口 skill 的最小输入、启动时机和与 ready queue 的绑定边界。
- 定义 operator 通过 installed skill adapter 与 repo CLI control surface 触发 runner 的责任，而不是继续依赖人工接力或隐式后台。

## Constraints
- Execution Loop Job Runner 必须以独立 canonical governed skill bundle 暴露给 Claude/Codex CLI 用户。
- 入口必须显式声明 start / resume 语义，而不是隐式依赖后台自动进程。
- 入口不得把 approve 后链路退化成手工逐个调用下游 skill。
- 入口调用必须保留 authoritative run context 与 lineage。
- repo CLI control surface 可以承载 start / resume / monitor，但不得替代 skill authority。

## Acceptance Checks
1. Runner exposes a named skill entry
   Then: the product flow must expose a named runner skill entry via canonical governed skill bundle instead of hiding start-up inside abstract background automation.
2. Entry remains user-invokable
   Then: the entry must stay invokable by Claude/Codex CLI through an installed adapter rather than requiring direct file edits or out-of-band orchestration.
3. Runner skill entry is explicit
   Then: The FEAT must define one dedicated runner skill authority for Claude/Codex CLI instead of relying on implicit background behavior, repo CLI façade, or manual downstream relays.
