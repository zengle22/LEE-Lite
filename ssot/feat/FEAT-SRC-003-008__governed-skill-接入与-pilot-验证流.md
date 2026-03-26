---
id: FEAT-SRC-003-008
ssot_type: FEAT
feat_ref: FEAT-SRC-003-008
epic_ref: EPIC-SRC-003-001
title: governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr018-epic2feat-restart-20260326-r1
candidate_package_ref: artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-26T12:42:30Z'
---

# governed skill 接入与 pilot 验证流

## Goal
把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。

## Scope
- 定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。
- 定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。
- 定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。

## Constraints
- pilot 链必须证明 ready job、runner、next-skill dispatch 和 execution outcome 这条自动推进链真实可用。
- 接入验证不得回退为人工第三会话接力。
- cutover / fallback 必须围绕 runner 自动推进结果定义。
- pilot evidence 必须绑定真实 approve -> runner -> next skill 链路。

## Acceptance Checks
1. Onboarding scope and migration waves are explicit
   Then: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
2. At least one real pilot chain is required
   Then: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
3. Adoption scope does not expand into repository-wide governance
   Then: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
