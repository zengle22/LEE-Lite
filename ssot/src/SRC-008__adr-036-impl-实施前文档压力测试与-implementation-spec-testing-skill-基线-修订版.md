---
id: SRC-008
ssot_type: SRC
title: ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版
status: frozen
version: v1
schema_version: 1.0.0
src_root_id: src-root-src-008
workflow_key: product.raw-to-src
workflow_run_id: adr036-raw2src-20260402-r9
source_kind: governance_bridge_src
source_refs:
- ADR-036
- ADR-014
- ADR-033
- ADR-034
- ADR-035
candidate_package_ref: artifacts/raw-to-src/adr036-raw2src-20260402-r9
gate_decision_ref: artifacts/active/gates/decisions/raw-to-src-adr036-raw2src-20260402-r9-src-candidate-decision.json
frozen_at: '2026-04-09T05:56:15Z'
---

# ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 修订版

## 问题陈述

当前主链已经具备 `ADR -> SRC -> EPIC -> FEAT -> ARCH / TECH / API / UI / TESTSET -> IMPL` 的上游对象，但 `IMPL` 进入 implementation start 之前仍缺一层独立、完整、可继承的正式需求源，专门回答“这份 IMPL 能不能安全交给 AI coder 开工”。 - `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 之间的隐性冲突，经常要到编码或联调阶段才暴露。 - 单文档看似成立，但功能链、用户旅程、状态机、数据模型和 API 契约拼接后可能断裂。 - happy path 往往先被描述，失败路径、恢复动作、兼容迁移与 partial failure 容易漏掉。 - AI coder / tester / reviewer 可能从同一组文档中读出不同理解，最终实现出另一套系统。 因此需要在 implementation start 前新增一条专门的 implementation spec testing workflow，把 `IMPL` 作为纸面系统原型做实施前文档压力测试，而不是继续依赖零散 review 习惯。

## 目标用户

- Dev workflow / orchestration 设计者
- `ll-dev-tech-to-impl` 作者
- `ll-qa-impl-spec-test` 作者
- human gate / reviewer
- AI coder / tester / implementation consumer

## 触发场景

- 当 `feature_impl_candidate_package` 已生成，准备进入 implementation start 时。
- 当 external gate 前需要确认 `IMPL` 是否具备稳定实施条件时。
- 当 `IMPL` 新引入关键 `UI / API / state` 接缝、迁移约束或跨页面主链时。
- 当需要在编码前发现跨文档冲突、失败路径缺口与测试不可观测性时。

## 业务动因

- 需要把“编码前文档压力测试”提升为正式 workflow，而不是零散 review 习惯，否则 AI 实施会继续因歧义、空洞和冲突发生返工。
- 需要让 `IMPL` readiness 成为结构化 verdict，而不是停留在摘要或建议层，便于 gate、runner 和 implementation consumer 稳定消费。
- 需要让 `FEAT / TECH / ARCH / API / UI / TESTSET` 的联动 authority 在 implementation start 前被系统性检查，而不是把冲突留到编码与联调阶段暴露。
- 需要在不新增第二层技术设计 truth 的前提下，冻结一套只负责检测、升级和修复建议的 implementation spec testing 层。

## 冻结输入与需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/adr036-raw2src-20260402-r9/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- lineage_refs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## 内嵌需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/adr036-raw2src-20260402-r9/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- frozen_input_ref: artifacts/raw-to-src/adr036-raw2src-20260402-r9/input/source-input.md
- frozen_input_sha256: 107e661734a3beefdc071126fc2ce565333dcc96f3609734d00339c9f90ffbea
- captured_at: 2026-04-02T05:19:41Z
- original_source_path: E:\ai\LEE-Lite-skill-first\.local\raw-to-src-inputs\adr036-impl-spec-test-src.md
- embedded_title: ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线
- embedded_input_type: adr
- lineage_refs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- embedded_sections: 问题陈述, 目标用户, 触发场景, 业务动因, 用户入口与控制面, 运行时对象与状态, 目标能力对象, 成功结果, 验收影响, 治理变更摘要, 关键约束, 范围边界, 下游派生要求, 桥接摘要, 非目标
- embedded_body_excerpt: # ADR 输入：ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 ## 问题陈述 当前主链已经具备 `ADR -> SRC -> EPIC -> FEAT -> ARCH / TECH / API / UI / TESTSET -> IMPL` 的上游对象，但 `IMPL` 进入 implementation start 之前仍缺一层独立、完整、可继承的正式需求源，专门回答“这份 IMPL 能不能安全交给 AI coder 开工”。 - `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 之间的隐性冲突，经常要到编码或联调阶段才暴露。 - 单文档看似成立，但功能链、用户旅程、状态机、数据模型和 API 契约拼接后可能断裂。 - happy path 往往先被描述，失败
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## 文档语义层级

- None.

## Frozen Contracts

- None.

## 结构化对象契约

- None.

## 枚举冻结

- None.

## 语义清单

- Actors: Dev workflow / orchestration 设计者; `ll-dev-tech-to-impl` 作者; `ll-qa-impl-spec-test` 作者; human gate / reviewer; AI coder / tester / implementation consumer
- Product surfaces: `qa.impl-spec-test`; `ll-qa-impl-spec-test`; implementation-readiness verdict; deep-mode trigger rules; score-to-verdict binding rules; repair-target routing rules; counterexample coverage rules; reviewer 可在不回读原始 ADR 的前提下判断 implementation start 是否允许继续。; coder / tester 可理解主测试对象、联动 authority、修复责任与阻断条件。; downstream implementation consumer 不再把 implementation readiness 错当成“文档是否写完”。; implementation spec testing 不再因为越权补 truth、只看 happy path 或 score 不驱动 verdict 而漂移。
- Operator surfaces: runner observability surface
- Entry points: None
- Commands: None
- Runtime objects: impl_readiness_testing; cross_artifact_conflict_detection; counterexample_simulation; score_to_verdict_decision_support; repair_target_routing
- States: readiness states：`ready`、`partial`、`not_ready`
- Observability surfaces: runner observability surface

## 标准化决策

- source_projection: 将原始输入统一映射为主链兼容的标准字段。 (loss_risk=low)
- bridge_projection: 为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。 (loss_risk=medium)
- semantic_lock_freeze: 避免下游 workflow 继续从 generic bridge prose 推断主导语义。 (loss_risk=low)
- operator_surface_preservation: 避免 CLI/operator/control surface 在 SRC 层被静默压缩。 (loss_risk=low)

## 压缩与省略说明

- Compressed: problem_statement | why=正文会被整理为适合下游消费的规范化问题陈述。 | risk=low
- Compressed: bridge_context | why=bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。 | risk=medium
- Summary: SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。

## Operator Surface Inventory

- monitor_surface: runner observability surface | phase=monitor | actor=workflow / orchestration operator

## 用户入口与控制面

- 运行监控面: runner observability surface
- 用户交互边界: 用户通过 Claude/Codex CLI 显式调用 skill 入口或控制命令启动、恢复、观察运行时。

## 冲突与未决点

- No explicit contradictions detected during normalization.

## 目标能力对象

- `qa.impl-spec-test`
- `ll-qa-impl-spec-test`
- implementation-readiness verdict
- deep-mode trigger rules
- score-to-verdict binding rules
- repair-target routing rules
- counterexample coverage rules

## 成功结果

- reviewer 可在不回读原始 ADR 的前提下判断 implementation start 是否允许继续。
- coder / tester 可理解主测试对象、联动 authority、修复责任与阻断条件。
- downstream implementation consumer 不再把 implementation readiness 错当成“文档是否写完”。
- implementation spec testing 不再因为越权补 truth、只看 happy path 或 score 不驱动 verdict 而漂移。

## 治理变更摘要

- 治理对象：ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界
- 统一原则：正式文件读写统一纳入围绕 ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界 的治理边界，不再依赖分散约定。
- 下游必须继承的约束：下游需求链必须将 ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。

## Semantic Lock

- domain_type: implementation_readiness_rule
- one_sentence_truth: 仅在 IMPL 进入 implementation start 前，对 IMPL 及其联动 authority 做实施前文档压力测试，并输出 implementation-readiness verdict；该 workflow 只升级冲突，不重写上游 truth。
- primary_object: qa.impl-spec-test
- lifecycle_stage: pre_implementation_gate
- allowed_capabilities: impl_readiness_testing; cross_artifact_conflict_detection; counterexample_simulation; score_to_verdict_decision_support; repair_target_routing
- forbidden_capabilities: new_business_truth_authoring; new_design_truth_authoring; external_gate_replacement; code_quality_execution_testing; second_layer_tech_design
- inheritance_rule: IMPL is the main tested object; upstream authority remains authoritative when conflicts exist.

## 下游派生要求

- 下游 `src-to-epic` 以及后续 `FEAT / TECH / IMPL / TESTSET` 链路必须继承 implementation spec testing 是 implementation start 前的正式治理边界。
- 后续实现必须把 `pass / pass_with_revisions / block`、`quick_preflight / deep_spec_testing`、`repair_target_artifact` 与 authority non-override 做成正式 contract，而不是 prose 约定。
- 后续实现必须让 reviewer 和 implementation consumer 在不回读原始 ADR 的前提下理解什么时候强制跑 deep、什么时候必须 block、以及修复责任落点在哪里。

## 关键约束

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

## 范围边界

- In scope: 定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。
- In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。
- Out of scope: 不把 `qa.impl-spec-test` 定义为 external gate 的替代。
- Out of scope: 不要求该 workflow 直接运行代码或替代执行测试。
- Out of scope: 不允许该 workflow 越权补出新的 FEAT / TECH / API / UI truth。
- Out of scope: 不把该 workflow 降级为纯文档 lint 或格式检查器。

## 来源追溯

- Source refs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- Input type: adr
- SSOT policy: src candidate must remain reviewable even if the original external requirement file is later removed.

## 桥接摘要

- ADR-036 不是新增第二层技术设计，而是为 `IMPL -> implementation start` 之间补上一层正式、可继承的 implementation-readiness testing 边界。
- 它解决的是“AI 是否会因文档歧义实现出另一套系统”的问题，而不是单纯检查文档是否写完。
- 它要求把冲突检测、失败路径推演、score-to-verdict 与 repair target 路由标准化，但不允许 workflow 自己成为新的 truth source。

## Bridge Context

- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。
- governed_by_adrs: ADR-036, ADR-014, ADR-033, ADR-034, ADR-035
- change_scope: 将《ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线》涉及的ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界收敛为统一主链继承边界，明确 loop、handoff、gate 与 formal materialization 的协作责任。
- governance_objects: ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界
- current_failure_modes: 当前主链已经具备 `ADR -> SRC -> EPIC -> FEAT -> ARCH / TECH / API / UI / TESTSET -> IMPL` 的上游对象，但 `IMPL` 进入 implementation start 之前仍缺一层独立、完整、可继承的正式需求源，专门回答“这份 IMPL 能不能安全交给 AI coder 开工”。 - `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 之间的隐性冲突，经常要到编码或联调阶段才暴露。 - 单文档看似成立，但功能链、用户旅程、状态机、数据模型和 API 契约拼接后可能断裂。 - happy path 往往先被描述，失败路径、恢复动作、兼容迁移与 partial failure 容易漏掉。 - AI coder / tester / reviewer 可能从同一组文档中读出不同理解，最终实现出另一套系统。 因此需要在 implementation start 前新增一条专门的 implementation spec testing workflow，把 `IMPL` 作为纸面系统原型做实施前文档压力测试，而不是继续依赖零散 review 习惯。
- downstream_inheritance_requirements: 下游需求链必须将 ADR-036 IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线 涉及的治理边界 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。
- expected_downstream_objects: EPIC, FEAT, TASK
- acceptance_impact: 下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。; 下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。; 审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。
- non_goals: 不把 `qa.impl-spec-test` 定义为 external gate 的替代。; 不要求该 workflow 直接运行代码或替代执行测试。; 不允许该 workflow 越权补出新的 FEAT / TECH / API / UI truth。; 不把该 workflow 降级为纯文档 lint 或格式检查器。
