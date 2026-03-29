---
id: FEAT-SRC-005-005
ssot_type: FEAT
feat_ref: FEAT-SRC-005-005
epic_ref: EPIC-SRC-005-001
title: governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
frozen_at: '2026-03-27T14:27:58Z'
---

# governed skill 接入与 pilot 验证流

## Goal
冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。

## Scope
- 定义哪些 governed skill 先接入以及 scope 外对象如何处理。
- 定义 pilot 主链如何选定、扩围和形成真实 evidence。
- 定义 cutover / fallback 如何判断，以及 adoption 成立需要交付哪些真实 evidence。

## Constraints
- Epic-level constraints：当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。
- Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- 真实闭环成立必须以 pilot E2E evidence 证明，不得把组件内自测当成唯一成立依据。

## Acceptance Checks
1. Onboarding scope and migration waves are explicit
   Then: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
2. At least one real pilot chain is required
   Then: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
3. Adoption scope does not expand into repository-wide governance
   Then: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
