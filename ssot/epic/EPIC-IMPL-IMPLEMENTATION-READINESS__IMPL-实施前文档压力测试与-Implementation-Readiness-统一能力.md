---
id: "EPIC-IMPL-IMPLEMENTATION-READINESS"
ssot_type: EPIC
title: IMPL 实施前文档压力测试与 Implementation Readiness 统一能力
status: accepted
schema_version: 1.0.0
workflow_key: "product.src-to-epic"
workflow_run_id: "adr036-raw2src-20260402-r10"
source_refs:
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
candidate_artifact_ref: "artifacts/src-to-epic/adr036-raw2src-20260402-r10/epic-freeze.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
src_ref: "SRC-ADR036-RAW2SRC-20260402-R9"
epic_root_id: "EPIC-IMPL-IMPLEMENTATION-READINESS"
candidate_package_ref: "artifacts/src-to-epic/adr036-raw2src-20260402-r10"
frozen_at: "2026-04-02T06:54:11.232473+00:00"
---

# IMPL 实施前文档压力测试与 Implementation Readiness 统一能力

## Epic Intent

将《ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版》中的治理问题空间进一步收敛为“IMPL 实施前文档压力测试与 Implementation Readiness 统一能力”这一 EPIC 级产品能力块，让下游可以围绕稳定的产品行为切片拆分 FEAT，并把 capability axes 保留在 cross-cutting constraints 层，而不是继续复述 SRC 原则或沿治理对象逐项平移。

## Business Goal

本 EPIC 的核心不是新增第二层技术设计，也不是直接执行代码或测试，而是把 implementation start 前的文档压力测试冻结成连续产品能力。下游 FEAT 需要围绕 IMPL 主测试对象 intake 与 authority 绑定流、跨文档一致性与产品行为边界评审流、失败路径与反例推演流、实施 readiness verdict 与修复路由流 这些切片定义 intake、跨文档评审、失败路径推演和 readiness verdict。

## Business Value and Problem

- 当前主链已经具备 `ADR -> SRC -> EPIC -> FEAT -> ARCH / TECH / API / UI / TESTSET -> IMPL` 的上游对象，但 `IMPL` 进入 implementation start 之前仍缺一层独立、完整、可继承的正式需求源，专门回答“这份 IMPL 能不能安全交给 AI coder 开工”。

- `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 之间的隐性冲突，经常要到编码或联调阶段才暴露。
- 单文档看似成立，但功能链、用户旅程、状态机、数据模型和 API 契约拼接后可能断裂。
- happy path 往往先被描述，失败路径、恢复动作、兼容迁移与 partial failure 容易漏掉。
- AI coder / tester / reviewer 可能从同一组文档中读出不同理解，最终实现出另一套系统。

因此需要在 implementation start 前新增一条专门的 implementation spec testing workflow，把 `IMPL` 作为纸面系统原型做实施前文档压力测试，而不是继续依赖零散 review 习惯。
- 需要把“编码前文档压力测试”提升为正式 workflow，而不是零散 review 习惯，否则 AI 实施会继续因歧义、空洞和冲突发生返工。
- 关键触发场景：当 `feature_impl_candidate_package` 已生成，准备进入 implementation start 时。

## Product Positioning

该 EPIC 位于 implementation start 前的 readiness 产品能力层，承接上游 implementation-readiness SRC，对下定义一条从 IMPL intake、跨文档一致性评审、失败路径推演到 readiness verdict 与修复路由的完整产品线。它对外呈现的是 IMPL 主测试对象 intake 与 authority 绑定流、跨文档一致性与产品行为边界评审流、失败路径与反例推演流、实施 readiness verdict 与修复路由流 这些可交付的 readiness 产品流；ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版 能力包 1、ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版 能力包 2 只作为这些产品流共享的 cross-cutting constraints 存在。

## Actors and Roles

- implementation reviewer：在 implementation start 前消费 readiness report 并判断是否允许继续。
- AI coder / tester：消费主测试对象、authority、修复目标和 verdict，而不是自行补出新的 truth。
- workflow / orchestration 设计者：保持 readiness 流程与 implementation start、external gate、downstream consumer 的职责边界。
- upstream artifact owner：根据 repair_target_artifact 接收修订任务并更新 FEAT / TECH / ARCH / API / UI / TESTSET / IMPL。

## Capability Scope

- 统一上位产品能力：形成一条 implementation start 前可被多方稳定消费的 readiness 产品线。
- 产品行为切片：IMPL 主测试对象 intake 与 authority 绑定流，对业务方交付 implementation readiness intake result。
- 产品行为切片：跨文档一致性与产品行为边界评审流，对业务方交付 cross-artifact issue inventory。
- 产品行为切片：失败路径与反例推演流，对业务方交付 counterexample coverage result。
- 产品行为切片：实施 readiness verdict 与修复路由流，对业务方交付 implementation-readiness verdict package。
- Cross-cutting capability constraints：ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版 能力包 1、ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版 能力包 2；这些能力轴只作为约束附着在上述产品行为切片上。

## Upstream and Downstream

- Upstream：承接 `product.raw-to-src::adr036-raw2src-20260402-r9` 冻结后的 SRC 包，而不是原始需求或单个 ADR 原文。
- Downstream：产出一个可继续拆分为多个 FEAT 的单一主 EPIC，并交接给 `product.epic-to-feat`。
- 上游输入形态：关于 implementation start 前 readiness 压力测试的 bridge SRC，而不是具体代码实现或 TECH 方案本体。
- 下游消费形态：IMPL intake、cross-artifact consistency、counterexample simulation、readiness verdict 与 repair routing 等 FEAT 切片。

## Epic Success Criteria

- 下游 FEAT 能完整覆盖 IMPL 主测试对象 intake 与 authority 绑定流、跨文档一致性与产品行为边界评审流、失败路径与反例推演流、实施 readiness verdict 与修复路由流 这些 readiness 产品切片，而不是把能力塌缩成单一 review 步骤。
- 至少一条 IMPL intake -> cross-artifact consistency review -> counterexample simulation -> readiness verdict -> repair routing 的链路可被验证。
- 主测试对象、authority non-override、deep mode 触发、score-to-verdict 与 repair_target_artifact 在下游 FEAT 层不再歧义。
- implementation consumer 可在不回读 ADR 的前提下理解能否开工、哪里要修、以及修复责任落点。

## Non-Goals

- 不把 `qa.impl-spec-test` 定义为 external gate 的替代。
- 不要求该 workflow 直接运行代码或替代执行测试。
- 不允许该 workflow 越权补出新的 FEAT / TECH / API / UI truth。
- 不把该 workflow 降级为纯文档 lint 或格式检查器。
- 本 EPIC 不新增第二层技术设计 truth，也不替代 FEAT / TECH / ARCH / API / UI / TESTSET / IMPL 的权威边界。
- 本 EPIC 不直接执行代码、跑真实测试或替代 external gate 的最终审批职责。
- 本 EPIC 不把 implementation readiness 降级为纯文档 lint 或格式检查器。

## Decomposition Rules

- 按独立验收的产品行为切片拆分 FEAT，不按实现顺序、能力轴名称或单一任务切分。
- 每个下游 FEAT 都必须继承 src_root_id、epic_freeze_ref 和 authoritative source_refs。
- 优先将多个触发场景共享的主链能力放在同一 EPIC，下游再按场景或边界拆 FEAT。
- FEAT 的 primary decomposition unit 是 IMPL intake、cross-artifact consistency review、counterexample simulation、readiness verdict / repair routing 这些产品行为切片。
- 任何 FEAT 都不得把 implementation readiness 重写成第二层技术设计、代码实现计划或纯文档 lint。
- 下游 FEAT 必须保持主测试对象优先级、authority non-override、deep mode 触发和 score-to-verdict 绑定的单一路径。
- repair_target_artifact 与 missing_information 必须留在产品级输出，而不是推迟到 TECH 层再补定义。
- 建议产品行为切片：
  - IMPL 主测试对象 intake 与 authority 绑定流 <- main_test_object_priority, authority_binding
  - 跨文档一致性与产品行为边界评审流 <- conflict_detection, product_behavior_boundary
  - 失败路径与反例推演流 <- failure_path_simulation, counterexample_coverage
  - 实施 readiness verdict 与修复路由流 <- score_to_verdict, repair_target_routing

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
- required_feat_families:
  - skill_onboarding: 建立现有 governed skill 的 integration matrix，明确 producer、consumer、gate consumer 与暂不接入对象。
  - migration_cutover: 定义迁移波次、cutover rule、fallback rule 与 guarded rollout 边界，而不是一次性全仓硬切。
  - cross_skill_e2e_validation: 至少选定一条真实 producer -> consumer -> audit -> gate 的 pilot 主链，并形成跨 skill E2E evidence。

## Constraints and Dependencies

### 来源与依赖约束

- `IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- workflow 必须输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict。
- 深度模式必须覆盖失败路径推演与 counterexample family；高风险维度至少命中 1 个反例场景。
- `implementation_executability`、`testability`、`blocking_issue`、`severe_design_conflict` 必须能稳定驱动 verdict。
- `self_contained_readiness` 必须相对于 execution mode 解释，不能脱离 `strong_self_contained` / `upstream_follow_allowed` 单独成立。
- `repair_target_artifact` 必须明确回到 `IMPL / FEAT / TECH / ARCH / API / UI / TESTSET / MULTI`。
- 正式文件读写必须围绕 ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界 的统一边界建模，不得在下游恢复自由路径写入。
- 下游需求链必须将 ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- 下游继承约束必须显式声明主测试对象优先级、authority non-override、score-to-verdict 绑定、repair_target_artifact 与 counterexample coverage。
- Authoritative source refs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Upstream package: E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr036-raw2src-20260402-r9

## Acceptance and Review

- Upstream acceptance: approve (Acceptance review passed.)
- Upstream semantic review: pass (No semantic issue detected.)
- Epic review: pass
- Epic acceptance: approve

## Downstream Handoff

- Next workflow: `product.epic-to-feat`
- epic_freeze_ref: `EPIC-IMPL-IMPLEMENTATION-READINESS`
- src_root_id: `SRC-ADR036-RAW2SRC-20260402-R9`
- Required carry-over: source refs, decomposition rules, constraints, acceptance evidence

## Traceability

- Epic Intent: problem_statement, trigger_scenarios, business_drivers <- ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Business Value and Problem: problem_statement, business_drivers, trigger_scenarios <- ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Actors and Roles: target_users, trigger_scenarios, bridge_context.downstream_inheritance_requirements <- SRC-ADR036-RAW2SRC-20260402-R9, ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Capability Scope: in_scope, governance_change_summary, bridge_context.governance_objects <- SRC-ADR036-RAW2SRC-20260402-R9, ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Constraints and Dependencies: key_constraints, bridge_context.downstream_inheritance_requirements <- product.raw-to-src::adr036-raw2src-20260402-r9, ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Epic Success Criteria: business_drivers, bridge_context.acceptance_impact, trigger_scenarios <- product.raw-to-src::adr036-raw2src-20260402-r9, ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
