---
id: FEAT-SRC-005-001
ssot_type: FEAT
feat_ref: FEAT-SRC-005-001
epic_ref: EPIC-SRC-005-001
title: 主链候选提交与交接流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T14:27:58Z'
---

# 主链候选提交与交接流

## Goal
冻结 governed skill 如何把 candidate package 提交为 authoritative handoff，并把候选交接正式送入 gate 消费链。

## Scope
- 定义 candidate package、proposal、evidence 在什么触发场景下被提交。
- 定义提交后形成什么 authoritative handoff object。
- 定义提交完成后对上游和 gate 分别暴露什么业务结果。

## Constraints
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Epic-level constraints：FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。
- Loop 协作语义必须显式说明哪类对象触发 gate、哪类 decision 允许回流、哪类状态允许继续推进。
- 该 FEAT 只负责 loop 协作边界，不得把 formalization 细则混入 loop 责任定义。

## Acceptance Checks
1. Loop responsibility split is explicit
   Then: The FEAT must define which loop owns which transition, input object, and return path without overlapping formalization responsibilities.
2. Submission completion is visible without implying approval
   Then: The FEAT must make clear which authoritative handoff and pending-intake results become visible, while keeping approval and re-entry semantics outside this FEAT.
3. Downstream flows do not redefine collaboration rules
   Then: It must inherit the same collaboration rules instead of inventing a parallel queue or handoff model.
