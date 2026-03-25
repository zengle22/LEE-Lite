---
id: IMPL-FEAT-SRC-001-005
ssot_type: IMPL
title: Governed Skill Adoption and Cross-Skill E2E Implementation Task
status: active
version: v1
schema_version: 0.1.0
impl_root_id: impl-root-feat-src-001-005
parent_id: FEAT-SRC-001-005
source_refs:
  - FEAT-SRC-001-005
  - ADR-014
  - ADR-005
  - ADR-006
  - ARCH-SRC-001-001
  - ARCH-SRC-001-003
  - API-ROLLOUT-001
  - product.epic-to-feat::adr001-003-006-unified-mainline-20260324-rerun13
  - TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-005
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-001-005-20260325
properties:
  feat_ref: FEAT-SRC-001-005
  tech_ref: TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-005
  backend_workstream_applicable: true
  frontend_workstream_applicable: false
  migration_cutover_applicable: true
  target_template_id: template.dev.feature_delivery_l2
---

# Governed Skill Adoption and Cross-Skill E2E Implementation Task

## 1. 目标

实现 governed skill onboarding、pilot 验证、cutover/fallback 与跨 skill E2E evidence，让主链能力从 foundation 进入真实接入阶段。

本次实施不重写 foundation FEAT 的内部实现。

## 2. 上游依赖

- `API-ROLLOUT-001`：rollout / onboarding contract
- `ADR-006`：pilot 链必须经过 gate / formal publish
- `ADR-005`：正式对象和 evidence 仍走治理主链
- 上游 TECH：`TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-005`
- 上游 API：
  - `lee rollout onboard-skill`
  - `lee audit submit-pilot-evidence`

## 3. 实施范围

- 模块范围：
  - `cli/lib/protocol.py`
  - `cli/lib/rollout_state.py`
  - `cli/lib/pilot_chain.py`
  - `cli/commands/rollout/command.py`
  - `cli/commands/audit/command.py`
- 工程范围：
  - onboarding matrix
  - wave state
  - pilot evidence
  - cutover/fallback guard
- 不在范围：
  - 重新定义 Gateway / Gate / Registry contract
  - 一次性迁移所有旧 skill

## 4. 实施步骤

### Step 1

定义 `OnboardingMatrix / CutoverDirective / PilotEvidenceRef` 结构与 wave state。

完成条件：可表达 skill、wave、compat mode、cutover guard。

### Step 2

实现 onboarding registry 和 rollout state 持久化。

完成条件：skill 接入范围、波次和 compat mode 可追溯。

### Step 3

实现 pilot chain verifier。

完成条件：至少能验证 `producer -> gate -> formal -> consumer -> audit` 一条完整链。

### Step 4

实现 cutover/fallback 判定与状态写回。

完成条件：wave 只能在 evidence 足够时推进，否则 fail closed。

## 5. 风险与阻塞

- 若 foundation 还没稳定，pilot evidence 会失真。
- compat mode 若定义不清，cutover/fallback 会变成口头流程。
- 若 audit evidence 无法回交 gate，rollout 无法形成闭环。

## 6. 交付物

- 代码：
  - `cli/lib/rollout_state.py`
  - `cli/lib/pilot_chain.py`
  - rollout/audit command 扩展
- 计划：
  - onboarding matrix
  - migration wave / cutover / fallback plan
- 证据：
  - pilot evidence
  - cutover recommendation
  - rollback / fallback evidence

## 7. 验收检查点

- 至少一条真实 pilot 主链跑通。
- `compat_mode`、`wave_id`、`cutover_guard_ref` 必须可追溯。
- pilot evidence 缺失时必须 fail closed，不能继续 rollout。
- fallback 结果必须记录到 receipt / wave state。

## Workstream 适用性

- frontend: 不适用
- backend/runtime: 适用
- migration/cutover: 适用

## Downstream Handoff

- target template: `template.dev.feature_delivery_l2`
- supporting refs:
  - `TECH-FEAT-SRC-ADR001-003-006-UNIFIED-MAINLINE-20260324-RERUN5-005`
  - `API-ROLLOUT-001`
