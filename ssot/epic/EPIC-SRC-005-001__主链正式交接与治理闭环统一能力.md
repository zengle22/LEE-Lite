---
id: EPIC-SRC-005-001
ssot_type: EPIC
src_ref: SRC-005
title: 主链正式交接与治理闭环统一能力
status: accepted
schema_version: 1.0.0
epic_root_id: EPIC-SRC-005-001
workflow_key: product.src-to-epic
workflow_run_id: adr011-raw2src-fix-20260327-r1
candidate_package_ref: artifacts/src-to-epic/adr011-raw2src-fix-20260327-r1
gate_decision_ref: artifacts/active/gates/decisions/gate-decision.json
depends_on:
- ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。
- 本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。
frozen_at: '2026-03-27T14:07:05Z'
acceptance_summary: Epic acceptance review passed.
---

# 主链正式交接与治理闭环统一能力

## Epic Intent

将《ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 修订版》中的治理问题空间进一步收敛为“主链正式交接与治理闭环统一能力”这一 EPIC 级产品能力块，让下游可以围绕稳定的产品行为切片拆分 FEAT，并把 capability axes 保留在 cross-cutting constraints 层，而不是继续复述 SRC 原则或沿治理对象逐项平移。

## Business Goal

本 EPIC 的核心不是再按 loop、handoff、formalization、IO 这些治理轴分别建规则，而是把主链闭环冻结成一组连续的产品行为切片。下游 FEAT 需要直接围绕 主链候选提交与交接流、主链 gate 审核与裁决流、formal 发布与下游准入流、主链受治理 IO 落盘与读取流、governed skill 接入与 pilot 验证流 这些切片定义产品界面、完成态和业务成品，而不是继续复述 SRC 原则或把产品定义下沉给 TECH。

## Business Value and Problem

- 当前主链的 loop、handoff runtime、gate decision 与 formal publish 仍分散定义。若继续按局部规则理解，下游会把同一条主链拆成多个互不对齐的产品流程。
- 需要现在就把这类治理变化收敛成正式需求源，否则下游消费、审计和交付对象持续不稳定会继续沿后续需求链扩散。
- 关键触发场景：当治理类变更需要被下游 skill 继承时。

## Product Positioning

该 EPIC 位于主链产品行为层，承接上游 bridge SRC，对下定义一条从候选提交、gate 审核裁决、formal 发布与准入、受治理 IO 到 governed skill 接入验证的完整产品线。它对外呈现的是 主链候选提交与交接流、主链 gate 审核与裁决流、formal 发布与下游准入流、主链受治理 IO 落盘与读取流、governed skill 接入与 pilot 验证流 这些可交付的产品流；主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力 只作为这些产品流共享的 cross-cutting constraints 存在。

## Actors and Roles

- workflow / orchestration 设计者：定义主链的产品行为边界、交接角色和下游继承关系。
- governed skill 作者：让业务 skill 在统一主链里提交 candidate、消费 decision，并遵守统一交接规则。
- gate / reviewer / human loop 设计者：定义正式裁决、revision / retry / reject 参与点和审核责任。
- downstream consumer / audit 消费方：消费 formal output、evidence 和审计链，而不是依赖候选对象或路径猜测。
- skill onboarding / rollout owner：定义接入矩阵、迁移波次、pilot 范围与 fallback 规则。

## Capability Scope

- 统一上位产品能力：形成一条可被多 skill 共享继承的主链受治理交接闭环。
- 产品行为切片：主链候选提交与交接流，对业务方交付 给 gate 使用的 authoritative handoff submission，以及给上游 workflow 可见的提交完成结果。
- 产品行为切片：主链 gate 审核与裁决流，对业务方交付 给 execution 或 formal 发布链消费的 authoritative decision result，以及给 reviewer 可追溯的裁决结果。
- 产品行为切片：formal 发布与下游准入流，对业务方交付 给 downstream consumer 正式消费的 formal publication package，以及可验证的 admission result。
- 产品行为切片：主链受治理 IO 落盘与读取流，对业务方交付 给业务动作发起方返回的 governed write/read result，以及可审计的 managed ref / receipt。
- 产品行为切片：governed skill 接入与 pilot 验证流，对业务方交付 给 rollout owner 使用的 onboarding / pilot / cutover package，以及真实链路 evidence。
- Cross-cutting capability constraints：主链协作闭环能力、正式交接与物化能力、对象分层与准入能力、主链文件 IO 与路径治理能力、技能接入与跨 skill 闭环验证能力；这些能力轴只作为约束附着在上述产品行为切片上。

## Upstream and Downstream

- Upstream：承接 `product.raw-to-src::adr011-raw2src-fix-20260327-r1` 冻结后的 SRC 包，而不是原始需求或单个 ADR 原文。
- Downstream：产出一个可继续拆分为多个 FEAT 的单一主 EPIC，并交接给 `product.epic-to-feat`。
- 上游输入形态：统一继承源中的问题陈述、业务动因、治理对象和硬约束。
- 下游消费形态：主链候选提交、gate 裁决、formal 物化、准入、IO 落盘与 governed skill 接入验证等产品级 FEAT 切片。
- Rollout 约束：仍保持单一主 EPIC，但要求下游同时覆盖 foundation 与 adoption_e2e 两类 FEAT track。

## Epic Success Criteria

- 下游 FEAT 能完整覆盖 主链候选提交与交接流、主链 gate 审核与裁决流、formal 发布与下游准入流、主链受治理 IO 落盘与读取流、governed skill 接入与 pilot 验证流 这些产品行为切片，且每个 FEAT 都对应独立可验收的产品完成态，而不是原则复述。
- candidate 提交、gate 裁决、formal 发布、下游准入与受治理 IO 的产品边界在下游 FEAT 层不再歧义，业务 skill、gate 与 formal publish 职责不再混层。
- 至少一条 producer -> consumer -> audit -> gate pilot 主链可被真实验证，不再只停留在原则描述。
- 至少一组 approved decision -> formal publish -> downstream admission 流程在真实 governed skill 链路中启用并保留证据。
- 当 rollout_required 为 true 时，至少一组 adoption / cutover / fallback 策略被验证。
- 下游 FEAT 必须产出可执行的 governed skill integration matrix、迁移波次规则与至少一条真实跨 skill pilot 闭环 evidence。
- 治理主链是否成立，不以组件内自测为唯一依据，而以真实 producer / consumer 接入后的 handoff / gate / E2E 证据为准。

## Non-Goals

- 本 EPIC 不负责下游 EPIC/FEAT/TASK 分解与实现细节。
- 本 EPIC 不要求一次性完成所有现有 governed skill 的全量迁移或全仓 cutover。
- 本 EPIC 不要求覆盖所有 producer/consumer 组合场景，只要求在下游 FEAT 中显式定义 onboarding 范围、迁移波次和至少一条真实跨 skill pilot 主链。
- 本 EPIC 不负责把 onboarding / migration_cutover 扩大为仓库级全局文件治理改造。
- 本 EPIC 不重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只消费其已交付能力。

## Decomposition Rules

- 按独立验收的产品行为切片拆分 FEAT，不按实现顺序、能力轴名称或单一任务切分。
- 每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs。
- 保留 business skill、handoff runtime、external gate 的职责分层，不得在 FEAT 层重新混层。
- FEAT 的 primary decomposition unit 是产品行为切片；capability axes 只作为 cross-cutting constraints 保留，不直接等同于 FEAT。
- 每个 FEAT 都必须冻结对业务方可见的产品界面、完成态和 authoritative deliverable，避免把产品定义下沉给 TECH。
- required_feat_families / rollout families 是 mandatory overlays，必须叠加到对应产品切片上，而不是替代主轴。
- 涉及路径与目录治理的 FEAT 只能覆盖主链 handoff、formal materialization 与 governed skill IO 边界，不得外扩成全局文件治理。
- 涉及主链文件 IO / 路径治理的 FEAT 只定义对 ADR-005 前置基础的接入与消费边界，不重新实现底层模块。
- 建议产品行为切片：
  - 主链候选提交与交接流 <- 主链协作闭环能力
  - 主链 gate 审核与裁决流 <- 正式交接与物化能力, 主链协作闭环能力
  - formal 发布与下游准入流 <- 对象分层与准入能力, 正式交接与物化能力
  - 主链受治理 IO 落盘与读取流 <- 主链文件 IO 与路径治理能力
  - governed skill 接入与 pilot 验证流 <- 技能接入与跨 skill 闭环验证能力

## Rollout and Adoption

- rollout_required: `true`
- trigger_score: `4`
- SRC 涉及共享治理底座或共用运行时能力，而不是单一业务功能。
- 功能真正生效依赖现有 skill / workflow 接入，而不是只完成底座建设。
- 效果判定依赖真实 producer / consumer 接入，不能只靠组件内自测证明。
- 需要跨 skill E2E 或 handoff/gate 闭环验证，才能证明治理主链真的成立。
- required_feat_tracks: `foundation, adoption_e2e`
- rollout / adoption / E2E 不另起第二个 EPIC，而是在当前主 EPIC 内显式保留，并在 epic-to-feat 阶段强制拆出独立 FEAT 族。
- foundation FEAT 与 adoption/E2E FEAT 必须共享同一组 source_refs 和治理约束，不得形成并行真相。
- default-active 与 guarded/provisional 切面必须分层表达，避免未冻结 slice 被误当成已默认启用能力。
- prerequisite foundation: ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。
- prerequisite foundation: 本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。
- required_feat_families:
  - skill_onboarding: 建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。
  - migration_cutover: 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。
  - cross_skill_e2e_validation: 至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。

## Constraints and Dependencies

### Epic-level constraints

- 本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
- 主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
- FEAT 的 primary decomposition unit 是产品行为切片；rollout families 是 mandatory cross-cutting overlays，需叠加到对应产品切片上，不替代主轴。
- 主链文件 IO 与路径治理只覆盖交接对象的 IO 入口、出口、物化落点与引用稳定性，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。
- ADR-005 是主链文件 IO / 路径治理前置基础；本 EPIC 只消费其已交付能力，不重新实现 Gateway / Path Policy / Registry 模块。
- 当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。

### Authoritative inherited constraints

- 以下来源约束来自 authoritative SRC，downstream must preserve where applicable，但它们不重新定义本 EPIC 的 primary capability boundary。
- 正式文件读写必须围绕 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 ADR 011 EPIC to FEAT Lite Native Skill 逆向 SSOT 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- Authoritative source refs: ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Upstream package: E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr011-raw2src-fix-20260327-r1

### Downstream preservation rules

- 下游 FEAT 不得改写 src_root_id、epic_freeze_ref 与 authoritative source_refs。
- 下游 FEAT 不得把 EPIC 重新打平为上游 QA test execution 对象清单；source-level object constraints 只能附着到实际受其约束的 FEAT。
- candidate -> formal、loop / gate / handoff 分层与 acceptance semantics 必须继续保持可校验、可追溯。

## Acceptance and Review

- Upstream acceptance: approve (Acceptance review passed.)
- Upstream semantic review: pass (No semantic issue detected.)
- Epic review: pass
- Epic acceptance: approve

## Downstream Handoff

- Next workflow: `product.epic-to-feat`
- epic_freeze_ref: `EPIC-SRC-005-001`
- src_root_id: `SRC-005`
- prerequisite foundation: ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。
- prerequisite foundation: 本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。
- Required carry-over: source refs, decomposition rules, constraints, acceptance evidence

## Traceability

- Epic Intent: problem_statement, trigger_scenarios, business_drivers <- ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Business Value and Problem: problem_statement, business_drivers, trigger_scenarios <- ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Actors and Roles: target_users, trigger_scenarios, bridge_context.downstream_inheritance_requirements <- SRC-005, ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Capability Scope: in_scope, governance_change_summary, bridge_context.governance_objects <- SRC-005, ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Constraints and Dependencies: key_constraints, bridge_context.downstream_inheritance_requirements <- product.raw-to-src::adr011-raw2src-fix-20260327-r1, ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
- Epic Success Criteria: business_drivers, bridge_context.acceptance_impact, trigger_scenarios <- product.raw-to-src::adr011-raw2src-fix-20260327-r1, ADR-011, ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-008, ADR-009
