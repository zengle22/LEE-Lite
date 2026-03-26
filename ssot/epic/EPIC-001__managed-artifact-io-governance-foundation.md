---
id: EPIC-001
ssot_type: EPIC
title: 主链正式交接与治理闭环统一能力
status: frozen
version: v2
schema_version: 0.1.0
epic_root_id: epic-root-epic-001
workflow_key: workflow.product.task.src_to_epic
workflow_run_id: src001-from-frozen-src-20260324
source_refs:
  - SRC-001
  - ADR-005
  - ADR-001
  - ADR-002
  - ADR-003
  - ADR-004
  - ARCH-SRC-001-001
source_freeze_ref: SRC-001
src_root_id: src-root-src-001
frozen_at: '2026-03-24T12:30:00Z'
---

# 主链正式交接与治理闭环统一能力

## 概述

本 EPIC 不再把问题拆成若干彼此孤立的 Gateway、Registry、Audit 单点建设项，而是把 `SRC-001` 收敛成一条可被多 skill 共享继承的主链受治理交接闭环。它要求下游同时建立主链协作、正式交接与物化、对象分层与准入、主链文件 IO 与路径治理，以及真实 skill 接入与跨 skill E2E 闭环验证五类能力面，使治理主链的成立不依赖口头约定、组件内自测或局部私有实现。

## 范围

- 统一上位能力：形成一条可被多 skill 共享继承的主链受治理交接闭环。
- 主链协作闭环能力：定义 execution loop、gate loop、human loop 在 governed skill 主链中的协作责任、交接界面与回流边界，使不同 FEAT 不再各自重写等价 loop 规则。
- 正式交接与物化能力：统一 handoff、gate decision、formal materialization 的正式推进链路，使 candidate 到 formal 的升级路径可以被下游稳定继承。
- 对象分层与准入能力：固定 candidate package、formal object 与 downstream consumption 的层级规则、准入条件和引用约束，防止业务 skill 再次混入裁决职责。
- 主链文件 IO 与路径治理能力：约束主链交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。
- 技能接入与跨 skill 闭环验证能力：定义现有 governed skill 的 onboarding、迁移切换与跨 skill E2E 验证边界，使治理主链的成立不依赖口头假设、组件内自测或一次性全仓切换。

## 非目标

- 不负责下游 EPIC/FEAT/TECH/IMPL/TESTSET 分解与实现细节。
- 不要求一次性完成所有现有 governed skill 的全量迁移或全仓 cutover。
- 不要求覆盖所有 producer/consumer 组合场景，只要求在下游 FEAT 中显式定义 onboarding 范围、迁移波次和至少一条真实跨 skill pilot 主链。
- 不负责把 onboarding / migration_cutover 扩大为仓库级全局文件治理改造。

## 成功标准

- 下游 FEAT 能完整覆盖主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力五个主轴，且每个 FEAT 都对应独立可验收的能力面。
- candidate 到 formal 的流转边界在下游 FEAT 层不再歧义，业务 skill、gate 与 materialization 职责不再混层。
- 至少一条 `producer -> consumer -> audit -> gate` pilot 主链可被真实验证，不再只停留在原则描述。
- 至少一组 `candidate -> formal materialization` 流程在真实 governed skill 链路中启用并保留证据。
- 当 `rollout_required = true` 时，至少一组 adoption / cutover / fallback 策略被验证。

## 拆分原则

- 按独立验收能力边界拆分 FEAT，不按实现顺序或单一任务切分。
- 每个下游 FEAT 都必须继承 `src_root_id`、`epic_freeze_ref` 和 authoritative `source_refs`。
- 保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。
- 四个 foundation capability axes 是 primary decomposition axis；`required_feat_families / rollout families` 是 mandatory cross-cutting overlays，必须叠加到对应 capability FEAT 上，而不是替代主轴。
- 建议 FEAT 轴映射：
  - 主链协作闭环能力 -> loop / handoff / gate 协作边界
  - 正式交接与物化能力 -> gate decision 与 formal materialization
  - 对象分层与准入能力 -> candidate / formal object 准入与层级规则
  - 主链文件 IO 与路径治理能力 -> 文件 IO / 路径 / 目录治理
  - 技能接入与跨 skill 闭环验证能力 -> skill onboarding / migration cutover / cross-skill E2E validation

## Rollout 与 Adoption

- `rollout_required = true`
- 本 EPIC 不另起第二个 rollout EPIC，而是在当前主 EPIC 内显式保留 adoption / E2E 能力面，并要求 `epic-to-feat` 强制拆出独立 FEAT。
- foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 `source_refs` 和治理约束，不得形成并行真相。
- default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。
- required feat families:
  - `skill_onboarding`：建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。
  - `migration_cutover`：定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。
  - `cross_skill_e2e_validation`：至少选定一条真实 `producer -> consumer -> audit -> gate` 的 pilot 主链，并形成跨 skill E2E evidence。

## 约束与依赖

- 本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- 主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界。
- 主链文件 IO 与路径治理只覆盖交接对象的 IO 入口、出口、物化落点与引用稳定性，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。
- 当 `rollout_required = true` 时，foundation 与 `adoption_e2e` 必须同时落成，并至少保留一条真实 `producer -> consumer -> audit -> gate` pilot 主链。
- 以下来源约束来自 authoritative SRC，downstream must preserve where applicable，但它们不重新定义本 EPIC 的 primary capability boundary：
  - 正式文件读写必须围绕 Artifact IO Gateway、Path Policy 的统一边界建模，不得在下游恢复自由路径写入。
  - 下游 skill 必须继承 Artifact IO Gateway 的统一约束，不得在本链路中重新发明等价规则。
  - 下游 skill 必须继承 Path Policy 的统一约束，不得在本链路中重新发明等价规则。
  - 下游 skill 必须继承路径与目录治理的统一约束，不得在本链路中重新发明等价规则。

## 验收形态

- 上游 acceptance: `approve`
- 上游 semantic review: `pass`
- 本 EPIC 被视为成立的最小条件，是五类 FEAT 主轴都已具备明确边界，并共同支撑真实 governed skill 主链的接入与验证。
- 若后续产出仍依赖各 skill 自行拼接 loop、猜 formal 边界、自由写路径或没有真实跨 skill pilot 证据，则不应视为本 EPIC 已完成。

## 来源追溯

- 本文件物化自 [epic-freeze.md](E:/ai/LEE-Lite-skill-first/artifacts/src-to-epic/src001-frozen-src-to-epic-20260324-v2/epic-freeze.md) 与 [epic-freeze.json](E:/ai/LEE-Lite-skill-first/artifacts/src-to-epic/src001-frozen-src-to-epic-20260324-v2/epic-freeze.json)。
- `概述`、`范围`、`非目标`、`成功标准` 来自新版 `src-to-epic` 对 `SRC-001` 的单 EPIC 收敛结果。
- `Rollout 与 Adoption`、`拆分原则`、`约束与依赖` 直接继承该运行产物中的 `rollout_requirement`、`rollout_plan` 与 `constraints_and_dependencies`。
