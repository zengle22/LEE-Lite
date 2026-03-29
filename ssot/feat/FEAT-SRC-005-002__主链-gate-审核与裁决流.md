---
id: FEAT-SRC-005-002
ssot_type: FEAT
feat_ref: FEAT-SRC-005-002
epic_ref: EPIC-SRC-005-001
title: 主链 gate 审核与裁决流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T14:27:58Z'
---

# 主链 gate 审核与裁决流

## Goal
冻结 gate 如何审核 candidate、形成单一 decision object，并把结果明确返回 execution 或 formal 发布链。

## Scope
- 定义 approve / revise / retry / handoff / reject 的业务语义和输出物。
- 定义每种裁决的返回去向和对上游的业务结果。
- 定义 decision object 如何成为后续 formal 发布的唯一触发来源。

## Constraints
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Downstream preservation rules：candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Candidate 不得绕过 gate 直接升级为 downstream formal input。
- Formal 发布只能由 authoritative decision object 触发，不得出现并列正式化入口。

## Acceptance Checks
1. Gate decision path is single and explicit
   Then: The FEAT must define one explicit handoff -> gate decision chain and one authoritative decision object without parallel shortcuts.
2. Candidate cannot bypass gate
   Then: The FEAT must prevent that candidate from being treated as a formal downstream source.
3. Formal publication is only triggered by the decision object
   Then: The FEAT must make the decision object the only business-level trigger for formal publication and keep approval authority outside the business skill body.
