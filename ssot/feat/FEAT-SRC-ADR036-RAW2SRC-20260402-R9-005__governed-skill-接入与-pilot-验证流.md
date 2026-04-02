---
id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
ssot_type: FEAT
title: governed skill 接入与 pilot 验证流
status: frozen
schema_version: 1.0.0
workflow_key: "product.epic-to-feat"
workflow_run_id: "adr036-src2epic-20260402-r4"
epic_ref: "EPIC-IMPL-IMPLEMENTATION-READINESS"
src_root_id: "SRC-ADR036-RAW2SRC-20260402-R9"
source_refs:
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
candidate_package_ref: "artifacts/epic-to-feat/adr036-src2epic-20260402-r4"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
frozen_at: "2026-04-02T06:54:11.291072+00:00"
---

# governed skill 接入与 pilot 验证流

## 目标

把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。

## 范围

- 定义 governed skill 的接入、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。
- 定义至少一条 producer -> consumer -> audit -> gate pilot 主链如何覆盖真实协作。
- 定义 adoption 成立时业务方拿到的 evidence、integration matrix 与 cutover decision。

## 输入

- Authoritative EPIC package EPIC-IMPL-IMPLEMENTATION-READINESS
- src_root_id SRC-ADR036-RAW2SRC-20260402-R9
- Inherited scope, constraints, rollout requirements, and acceptance semantics

## 处理

- Translate the parent EPIC product behavior slice into one independently acceptable FEAT with a dedicated product interface, completed state, and boundary statement.
- Preserve parent-child traceability while separating this FEAT's concern from adjacent FEATs and rollout overlays.
- Emit FEAT-specific business flow, deliverable, constraints, and acceptance checks that can seed downstream TECH and TESTSET derivation.

## 输出

- Frozen FEAT product slice for FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005
- FEAT-specific acceptance checks for downstream TECH and TESTSET derivation
- Traceable handoff metadata for downstream governed TECH and TESTSET workflows

## 依赖

- Boundary to foundation FEATs: 本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
- Boundary to release/test planning: 本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。

## 非目标

- Do not redefine Gateway / Policy / Registry / Audit / Gate technical contracts that already belong to foundation FEATs.
- Do not require one-shot migration of every governed skill or exhaustive coverage of every producer/consumer combination.

## 约束

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 来源与依赖约束：workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- 真实闭环成立必须以 pilot E2E evidence 证明，不得把组件内自测当成唯一成立依据。

## 验收检查

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005-AC-01

- scenario: Onboarding scope and migration waves are explicit
- given: EPIC-IMPL-IMPLEMENTATION-READINESS requires real governed skill landing
- when: FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005 is reviewed for downstream planning
- then: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005-AC-02

- scenario: At least one real pilot chain is required
- given: Foundation FEATs are implemented in isolation
- when: Adoption readiness is evaluated
- then: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.

### FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005-AC-03

- scenario: Adoption scope does not expand into repository-wide governance
- given: A team proposes folding all file-governance cleanup into this FEAT
- when: The proposal is checked against FEAT boundaries
- then: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.

## 来源追溯

- 物化来源：`artifacts/epic-to-feat/adr036-src2epic-20260402-r4/feat-freeze-bundle.json`
- gate 决策：`artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json`
