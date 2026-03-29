---
id: FEAT-SRC-005-003
ssot_type: FEAT
feat_ref: FEAT-SRC-005-003
epic_ref: EPIC-SRC-005-001
title: formal 发布与下游准入流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T14:27:58Z'
---

# formal 发布与下游准入流

## Goal
冻结 approved decision 之后如何形成 formal output、formal ref 与 lineage，并让下游只通过正式准入链消费。

## Scope
- 定义 approved decision 之后的 formal 发布动作和 formal output 完成态。
- 定义 formal ref / lineage 如何成为 authoritative downstream input。
- 定义 consumer admission 边界，阻止 candidate 或旁路对象被正式消费。

## Constraints
- Epic-level constraints：当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Consumer 准入必须沿 formal refs 与 lineage 判断，不得通过路径猜测获得读取资格。
- 对象分层必须阻止业务 skill 在 candidate 层承担 gate 或 formal admission 职责。

## Acceptance Checks
1. Approved decision leads to one explicit formal publication path
   Then: The FEAT must define one explicit approved decision -> formal publication -> admission chain without bypassing formal refs or lineage.
2. Consumer admission is formal-ref based
   Then: The FEAT must require formal refs and lineage-based admission rather than path guessing or adjacent file discovery.
3. Candidate and intermediate objects cannot pose as formal deliverables
   Then: The FEAT must prevent candidate or intermediate objects from being treated as the formal publication package.
