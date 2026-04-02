---
id: SRC-006
ssot_type: SRC
title: ADR 036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线
status: draft
version: v0
schema_version: 1.0.0
src_root_id: src-root-src-006
workflow_key: product.raw-to-src
workflow_run_id: adr036-raw2src-20260402-r6
source_kind: governance_bridge_src
source_refs:
  - ADR-036
  - ADR-014
  - ADR-033
  - ADR-034
  - ADR-035
candidate_package_ref: artifacts/raw-to-src/adr036-raw2src-20260402-r6
---

# ADR 036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线

## 问题陈述

当前主链已经具备 `ADR -> SRC -> EPIC -> FEAT -> ARCH / TECH / API / UI / TESTSET -> IMPL` 的上游对象，但 `IMPL` 进入 implementation start 之前仍缺一层正式、结构化、可继承的 implementation readiness 压力测试能力。

如果继续把这一步留在零散 review 或人工经验层，会持续暴露以下失控行为：

- `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 之间的隐性冲突直到编码或联调阶段才暴露。
- 单文档看似成立，但功能链、用户旅程、状态机、数据模型和 API 契约拼接后出现断裂。
- happy path 被优先描述，但失败路径、恢复动作、兼容迁移与 partial failure 没有闭环。
- AI coder / tester / reviewer 从同一组文档中读出不同理解，最终实现偏离产品行为主语。
- `IMPL` 作为 execution-time single entrypoint 缺少一份可执行的 implementation-readiness verdict。

因此需要把 ADR-036 收敛为一条明确的主链事实：

- `IMPL -> implementation start` 之间必须存在 `qa.impl-spec-test`。
- 该 workflow 必须以 `IMPL` 为主测试对象，以 `FEAT / TECH / ARCH / API / UI / TESTSET` 为联动 authority。
- 该 workflow 必须输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict，而不是摘要式建议。

## 目标用户

- Dev workflow / orchestration 设计者
- `ll-dev-tech-to-impl` 与下游 implementation runtime 作者
- `ll-qa-impl-spec-test` 作者
- human gate / reviewer
- AI coder / tester / implementation consumer

## 触发场景

- 当 `feature_impl_candidate_package` 已生成，准备进入 implementation start 时。
- 当 external gate 前需要确认 `IMPL` 是否具备稳定实施条件时。
- 当 `IMPL` 新引入关键 `UI / API / state` 接缝、迁移约束或跨页面主链时。
- 当需要在编码前发现跨文档冲突、失败路径缺口与测试不可观测性时。

## 业务动因

- 必须把“编码前文档压力测试”提升为正式 workflow，否则 AI 实施会继续因歧义、空洞和冲突发生返工。
- 必须让 `IMPL` readiness 成为结构化 verdict，便于 gate、runner 和 implementation consumer 稳定消费。
- 必须让 `FEAT / TECH / ARCH / API / UI / TESTSET` 的联动 authority 在 implementation start 前被系统性检查，而不是把冲突留到编码与联调阶段暴露。
- 必须在不新增第二层技术设计 truth 的前提下，冻结一套只负责检测、升级和修复建议的 implementation spec testing 层。

## 语义清单

- Actors: Dev workflow / orchestration 设计者; `ll-dev-tech-to-impl` 与下游 implementation runtime 作者; `ll-qa-impl-spec-test` 作者; human gate / reviewer; AI coder / tester / implementation consumer
- Product surfaces: `qa.impl-spec-test`; `ll-qa-impl-spec-test`; `feature_impl_candidate_package`; `impl_spec_test_report_package`; `implementation_readiness_gate_subject`; `pass / pass_with_revisions / block`
- Operator surfaces: `quick_preflight`; `deep_spec_testing`; implementation readiness review surface
- Entry points: `qa.impl-spec-test`; `ll-qa-impl-spec-test`
- Commands: mode select `quick_preflight`; mode select `deep_spec_testing`
- Runtime objects: `feature_impl_candidate_package`; `impl_spec_test_report_package`; `implementation_readiness_gate_subject`
- States: `ready`; `partial`; `not_ready`; `sufficient`; `insufficient`; `pass`; `pass_with_revisions`; `block`
- Observability surfaces: dimension scores; blocking issues; high priority issues; missing information; repair plan; repair target artifact; counterexample coverage summary

## 统一 contract

下游继承时必须把以下字段视为 implementation spec testing 的最小正式 contract：

- `impl_ref`
- `feat_ref`
- `tech_ref`
- `source_refs`
- `execution_mode`
- `verdict`
- `implementation_readiness`
- `self_contained_readiness`
- `dimension_scores`
- `repair_plan`
- `repair_target_artifact`

兼容输入 `arch_ref`、`api_ref`、`ui_refs`、`testset_refs`、`repo_context` 可以存在，但不得替代主测试对象和联动 authority 的固定边界。

其中以下枚举必须被冻结：

- `verdict = pass | pass_with_revisions | block`
- `execution_mode = quick_preflight | deep_spec_testing`
- `repair_target_artifact = IMPL | FEAT | TECH | ARCH | API | UI | TESTSET | MULTI`

## 标准化决策

- `object_precedence_lock`: 主测试对象固定为 `IMPL`，联动 authority 固定为 `FEAT / TECH / ARCH / API / UI / TESTSET`。 (loss_risk=low)
- `authority_non_override`: authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 truth。 (loss_risk=low)
- `deep_mode_mandatory_triggers`: 遇到 migration、canonical/state boundary 敏感 FEAT、跨页面主链+后置增强链、新引入 `UI/API/state`、external gate 前最后 implementation candidate 时，必须跑 `deep_spec_testing`。 (loss_risk=low)
- `score_to_verdict_binding`: `blocking_issue`、`severe_design_conflict`、`implementation_executability < 6`、`testability < 6` 等规则必须直接驱动 verdict。 (loss_risk=low)
- `self_contained_mode_relative_evaluation`: `self_contained_readiness` 必须相对于 `strong_self_contained` 或 `upstream_follow_allowed` 模式解释。 (loss_risk=low)
- `repair_target_authority_routing`: 修复责任必须显式回到 `IMPL / FEAT / TECH / ARCH / API / UI / TESTSET / MULTI` 中的 authoritative target。 (loss_risk=low)
- `high_risk_counterexample_coverage`: 深度模式下每个高风险维度至少命中 1 个反例场景，否则不得宣称 counterexample coverage 充分。 (loss_risk=medium)

## 压缩与省略说明

- Compressed: ADR 论证 prose | why=本 SRC 不重复全部 ADR 论证，而是收敛为下游可继承的 boundary、contract 与 readiness 规则。 | risk=low
- Compressed: example counterexamples | why=本 SRC 冻结 counterexample family 与覆盖规则，不逐条内嵌所有场景实例。 | risk=medium
- Summary: SRC 保留 implementation spec testing 的治理边界、对象边界、触发条件、评分规则与修复责任；具体实现细节仍留给后续 FEAT / TECH / IMPL 链路。

## 治理变更摘要

- 治理对象：`qa.impl-spec-test`; `ll-qa-impl-spec-test`; implementation-readiness verdict; deep mode trigger; repair target routing; counterexample coverage rules
- 现状失控：把 implementation readiness 误当成“文档是否写完”; 只看 `IMPL` 单文档; 只看 happy path; score 与 verdict 脱节; `self_contained_readiness` 语义不清; 未明确 repair target
- 统一原则：implementation start 前必须运行 implementation spec testing；联动 authority 可检测冲突但不得越权改写 truth；verdict、repair target 与深度模式触发条件必须结构化冻结。
- 下游必须继承的约束：不得把 `qa.impl-spec-test` 降级为纯 lint、普通 review 或第二层技术设计；必须继承主测试对象优先级、mode trigger、score-to-verdict、repair target 与 counterexample coverage 规则。

## 下游派生要求

- 围绕 `qa.impl-spec-test` 定义正式 contract、schema、report artifact、gate subject 与 lifecycle。
- 把 8 维度实现为可审阅、可追溯、可驱动 verdict 的 testing contract。
- 确保后续 `EPIC / FEAT / TECH / IMPL / TESTSET` 不丢失主测试对象优先级与 authority non-override 边界。
- 确保 implementation consumer 可以在不回读原始 ADR 的前提下理解 repair target 与阻断逻辑。

## 关键约束

- 主测试对象必须是 `IMPL`，`FEAT / TECH / ARCH / API / UI / TESTSET` 只能作为联动 authority。
- authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- workflow 必须至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- workflow 必须输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict。
- 深度模式必须覆盖失败路径推演与 counterexample family，不得只看 happy path。
- 若 `IMPL` 不能回答改哪些模块、先后顺序、哪些接口 / 状态 / UI 必须实现，则不得视为 implementation ready。

## 范围边界

- In scope: 定义 implementation start 前的 implementation spec testing workflow 边界、模式、输入输出、评分和 verdict 规则。
- In scope: 为后续需求链提供统一继承的 readiness verdict、repair target 与 counterexample coverage 规则。
- Out of scope: 直接评审代码实现质量; 运行代码; 替代 external gate; 重写 FEAT / TECH / API / UI truth。

## 来源追溯

- Source refs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Input type: adr
- Canonical raw-to-src candidate: `artifacts/raw-to-src/adr036-raw2src-20260402-r6`
- Current raw-to-src status: `retry_proposed`
- Open raw-to-src finding: `layer_boundary`
- SSOT policy: 本文件是基于 ADR-036 与 raw-to-src candidate 的人工整理 draft，不应被误认作 external gate 已批准的 frozen SRC。

## Bridge Context

- governed_by_adrs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- change_scope: 将 implementation start 前的文档压力测试、主测试对象优先级、mode trigger、score-to-verdict、repair target 与 counterexample coverage 收敛为统一主链继承边界。
- governance_objects: `qa.impl-spec-test`; `ll-qa-impl-spec-test`; implementation-readiness verdict; deep mode trigger; repair target routing; counterexample coverage
- current_failure_modes: 把 implementation readiness 错当成“文档是否写完”; 只看 `IMPL` 单文档; 只看 happy path; 上游冲突时越权补 truth; score 与 verdict 脱节; `self_contained_readiness` 语义不清; 未明确 repair target; 深度模式反例覆盖流于形式
- downstream_inheritance_requirements: 下游必须继承主测试对象优先级、authority non-override、deep mode 强制触发、score-to-verdict 绑定、repair target 与高风险维度反例覆盖规则。
- expected_downstream_objects: EPIC, FEAT, TECH, IMPL, TESTSET
- acceptance_impact: reviewer 必须能稳定回答 implementation start 是否允许继续; coder/tester 必须能理解修复责任与阻断条件; 审核必须能回答上游冲突时 workflow 只升级冲突、不重写 truth。
- non_goals: 直接评审代码实现质量; 运行代码; 替代 external gate; 重写 FEAT / TECH / API / UI truth
