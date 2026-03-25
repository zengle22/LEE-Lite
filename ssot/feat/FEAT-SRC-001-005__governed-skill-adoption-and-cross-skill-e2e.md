---
id: FEAT-SRC-001-005
ssot_type: FEAT
title: 技能接入与跨 skill 闭环验证能力
status: frozen
version: v2
schema_version: 0.1.0
feat_root_id: feat-root-feat-src-001-005
workflow_key: workflow.product.task.epic_to_feat
workflow_run_id: src001-from-frozen-src-20260324
source_refs:
  - EPIC-001
  - SRC-001
  - ADR-005
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-004
  - ARCH-SRC-001-001
epic_ref: EPIC-001
epic_root_id: epic-root-epic-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-24T12:30:00Z'
---

# 技能接入与跨 skill 闭环验证能力

## 目标

让治理底座通过真实 governed skill onboarding、迁移切换和跨 skill E2E 闭环验证落到主链里，而不是停留在组件内自测或口头假设。

## 范围

- 定义现有 governed skill 的 onboarding 边界、接入矩阵与分批纳入规则，明确哪些 producer、consumer、gate consumer 在 scope 内。
- 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，但不要求一次性完成全量 skill 迁移。
- 要求至少选择一条真实 `producer -> consumer -> audit -> gate` pilot 主链，形成跨 skill E2E 闭环 evidence。
- 明确本 FEAT 只面向本主链治理能力涉及的 governed skill 接入与验证，不扩大为仓库级全局文件治理改造。

## 输入

- authoritative `EPIC-001`
- foundation FEAT 的能力边界
- governed skill onboarding / migration / pilot validation 的 rollout 要求

## 处理

- 建立 integration matrix，定义现有 governed skill 的接入范围与优先级。
- 为迁移波次、cutover、fallback 设定规则，而不是假定一次性全量切换。
- 通过真实 producer / consumer 链路生成跨 skill E2E evidence，证明治理主链不是只在组件内自测成立。

## 输出

- governed skill integration matrix
- migration wave / cutover / fallback 策略
- 至少一条真实 pilot 主链的 E2E evidence

## 依赖

- 边界依赖 foundation FEATs：本 FEAT 只负责接入、迁移与真实链路验证，不重写 Gateway / Policy / Registry / Audit / Gate 的能力定义。
- 边界依赖 release/test planning：本 FEAT 负责定义 adoption/E2E 能力边界和 pilot 目标，不替代后续 release orchestration 或 test reporting。

## 非目标

- 不重新定义 Gateway / Policy / Registry / Audit / Gate 的 technical contracts。
- 不要求一次性迁移所有 governed skill，也不要求穷举所有 producer/consumer 组合。

## 约束

- `onboarding / migration_cutover` 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- 真实闭环成立必须以 pilot E2E evidence 证明，不得把组件内自测当成唯一成立依据。
- 本 FEAT 只对真实接入与验证负责，不吸收 foundation 能力的定义职责。

## 验收检查

### AC-01 onboarding 范围与迁移波次必须明确

- scenario: adoption readiness review
- given: `EPIC-001` 要求真实 governed skill landing
- when: 评审本 FEAT 是否可下传
- then: 必须定义 onboarding scope、migration waves、cutover / fallback 规则，而不是假装所有 governed skill 会同时迁移

### AC-02 至少要有一条真实 pilot 主链

- scenario: foundation FEATs implemented in isolation
- given: 底座能力已经建立
- when: 判断 adoption readiness
- then: 本 FEAT 必须要求至少一条真实 `producer -> consumer -> audit -> gate` pilot 主链，而不是只接受 component-local tests

### AC-03 adoption 不得膨胀成仓库级治理

- scenario: 团队提议把所有 file-governance cleanup 一并塞进本 FEAT
- given: 本 FEAT 已经包含 onboarding / migration / E2E
- when: 对照本 FEAT 边界
- then: 必须把 scope 限定在本主链治理能力涉及的 governed skills，拒绝 repository-wide governance expansion

## 来源追溯

- 本文件物化自 [feat-freeze-bundle.md](E:/ai/LEE-Lite-skill-first/artifacts/epic-to-feat/src001-epic-to-feat-20260324-v3/feat-freeze-bundle.md) 中 `FEAT-SRC-001-005` 对应段落。
