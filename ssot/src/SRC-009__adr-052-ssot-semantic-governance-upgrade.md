---
id: SRC-009
ssot_type: SRC
title: 测试体系轴化 — SSOT需求轴与实施轴治理架构
status: frozen
version: v1.1
schema_version: 1.0.0
src_root_id: src-root-src-009
workflow_key: product.raw-to-src
workflow_run_id: SRC-009-adr052
source_kind: adr
source_refs:
- ADR-052
- ADR-047
- ADR-050
- ADR-051
candidate_package_ref: artifacts/raw-to-src/SRC-009-adr052
gate_decision_ref: ssot/gates/GATE-FRZ-SRC-009.json
frozen_at: '2026-04-22T00:00:00+08:00'
---

# 测试体系轴化 — SSOT需求轴与实施轴治理架构

## 问题陈述

当前测试体系存在治理层和执行层两类核心问题：

**治理层问题：**
1. `test_environment_ref` 没有来源——代码强校验但无技能生成，环境文件不在任何技能职责范围内
2. TESTSET（策略声明）和执行产物（环境、报告、Bug）混在同一治理域，未区分"需求"和"实施"两类资产
3. 用户需手动创建 environment.yaml 但不知道格式规范

**执行层问题（E2E 验收失效）：**
1. 环境不一致——"它跑过了，为什么我这里不行？"——无统一 Run Manifest 绑定版本/环境/数据
2. 断言过弱——页面有 toast 就算成功，但业务实体未落库——无业务状态断言层
3. AI 执行不可审计——AI 可能跳步、API 直调、误判——无状态机执行约束和违规检测
4. 数据/前置不可控——同账号第二次跑失败、脏状态残留——无标准化测试数据供给和清理
5. 失败排障困难——排查靠人工回放猜——无标准化事故包自动生成

**根因排序：** 断言口径不对 > 环境与数据不一致 > 异步流程未正确等待 > AI 执行绕路 > 真实产品 bug

## 目标用户

- AI 实施代理（Execution Loop Runner）——执行测试的核心消费者
- QA 技能（qa.test-plan / qa.test-run）——用户意图入口
- QA 工程师——审查测试报告、Gate 结论和事故包
- 架构/QA 治理——维护测试体系架构标准

## 触发场景

- FEAT 需求变更——触发变更影响分析，从受影响点重新编译/执行需求轴+实施轴
- TESTSET 变更——从 TESTSET 之后的需求轴模块重新编译 + 实施轴重新执行
- 目标环境变更（base_url 等）——仅 environment-provision + 实施轴重新执行，需求轴不变
- 已有执行结果需重新评估 Gate——仅 gate-evaluate 重新执行
- verifier 策略变更——仅 independent-verifier 重新执行
- 重跑/仅失败用例——仅失败 case + 关联 Scenario Spec 重新执行

## 业务动因

- E2E 测试从"脚本能跑"升级为"结果可信"，消除 AI 执行回报大量成功但手工验收仍不通的治理失效
- 通过需求轴/实施轴分离，实现声明性资产（可重新编译）与证据性资产（只追加）的独立治理
- 为 AI 执行提供状态机约束、独立验证和 8 类故障分类，形成从需求到验收的完整闭环
- 定义 GoldenPath schema 和验证标准，用于固化产品侧定义的核心用户旅程验证要求

## 冻结输入与需求源快照

- source_snapshot_mode: embedded
- frozen_input_dir: artifacts/raw-to-src/SRC-009-adr052/input/
- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界
- lineage_refs: [FRZ-001, ADR-052, ADR-047, ADR-050, ADR-051]
- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。

## Facet Bundle Selection

- facet_inference:
  - test-governance: ADR-052 定义 TESTSET/环境/Gate 的治理规则——SSOT 管理需求轴，Artifact 管理实施轴
  - test-execution-framework: 状态机执行、三层断言、8 类故障分类、L0-L3 分层执行模型
  - audit-and-verification: independent-verifier 独立认证上下文、bypass-detector 违规检测、事故包标准化
  - skill-orchestration: 2 个用户入口 Skill 编排 17+ 内部模块
- facet_bundle_recommendation: test-governance + test-execution-framework + audit-and-verification —— ADR-052 同时覆盖治理、执行、审计三层
- selected_facets: [test-governance, test-execution-framework, audit-and-verification, skill-orchestration]
- projector_selection: 全量 facet bundle 选中，4 个 facet 均需投影到下游 Epic/Feature 层

## 文档语义层级

- source_layer: ADR-052 内容 —— governed_by_adrs, change_scope, governance_objects, current_failure_modes, downstream_inheritance_requirements, key_constraints, phases, golden_paths, skills, modules, assertion_model, failure_model
- bridge_layer: 下游投影包括 qa.feat-to-testset 需求轴模块输出、qa.e2e-spec-gen 实施轴 Spec 生成、product.src-to-epic Epic 拆分
- meta_layer: lineage_refs (FRZ-001, ADR-047, ADR-050, ADR-051), source_snapshot_mode=embedded, source_kind=adr, governance_kind=REFINEMENT
- precedence_order: [source_layer, bridge_layer, meta_layer]
- override_rule: bridge/meta 不得覆盖 source_layer；需求轴声明可覆盖，实施轴证据只追加

## Frozen Contracts

- FC-001: Skill 仅用户入口，内部模块不注册为 Skill——2 个用户 Skill (qa.test-plan, qa.test-run) 编排 17+ 内部模块
- FC-002: 需求轴资产声明性可覆盖，实施轴资产证据性只追加——两类资产独立生命周期治理
- FC-003: 黄金路径 C 层断言 100% 覆盖前 gate 不得返回 pass——断言质量是 Gate 通过的必要条件
- FC-004: verifier=fail → Gate 必须=fail，不可被 settlement 覆盖——独立验证具有一票否决权
- FC-005: Phase 1 Gate 结论上限为 provisional_pass——C 层未验证时仅用于技术验证，不作为质量决策依据
- FC-006: TESTSET 中不得嵌入 test_case_pack 或 script_pack——用例扩展是运行时行为，不写入 SSOT
- FC-007: verifier 必须使用独立认证上下文——不同 API token、不同浏览器 context、不同账号、不同数据快照

## 结构化对象契约

- object: Skill
  purpose: 用户意图入口，编排内部模块
  required_fields: [skill_id, purpose, orchestrates]
  optional_fields: [modes, interaction_options]
  forbidden_fields: [internal_module_registration, direct_implementation]
  completion_effect: 触发编排模块链执行，输出 TESTSET/测试报告/Gate 结论

- object: Module
  purpose: 内部能力单元，由 Skill 编排调用
  required_fields: [module_id, axis, input, output]
  optional_fields: [phase, priority, states, code_location]
  forbidden_fields: [skill_registration]
  completion_effect: 产出结构化数据供下游模块消费

- object: AssertionLayer
  purpose: 三层断言模型（交互/页面结果/业务状态）
  required_fields: [layer_id, name, description, verification_method]
  optional_fields: [phase_requirement, verification_path]
  forbidden_fields: [optional_for_golden_paths]
  completion_effect: A/B 层必须定义；C 层按阶段要求执行，缺失影响 Gate 判定

- object: FailureClass
  purpose: 8 类标准化故障分类模型
  required_fields: [class_id, name, description, common_manifestations]
  optional_fields: [post_classification_action, confidence_threshold]
  forbidden_fields: [ad_hoc_classification]
  completion_effect: 触发对应后处理流程（PRODUCT→回归用例、SCRIPT/ORACLE→Spec 更新、FLAKY→重跑确认）

- object: GoldenPath
  purpose: 黄金路径验证对象 schema，由产品侧定义具体路径内容
  required_fields: [path_id, priority, description, dependencies]
  optional_fields: [acceptance_criteria, evidence_template]
  forbidden_fields: [undefined_environment, undefined_data]
  completion_effect: 验证对象必须满足验证标准（固定环境/数据/步骤/证据/验收），全部达标后才扩展更多验证对象
  semantic_note: 具体黄金路径（如 G1-G6）由产品侧定义，测试框架仅定义 schema 和验证标准

- object: Gate
  purpose: 测试验收 Gate 评价
  required_fields: [verdict, case_pass_rate, assertion_coverage, bypass_violations, verifier_verdict, product_bugs, env_consistency]
  optional_fields: [phase, provisional_notice]
  forbidden_fields: [hidden_verifier_failure]
  completion_effect: 决定测试是否通过/条件通过/失败，Phase 1 上限为 provisional_pass

- object: StateMachine
  purpose: 有限状态执行器，约束 AI 执行路径
  required_fields: [states, transitions, on_fail_behavior]
  optional_fields: [skip_states, phase_variant]
  forbidden_fields: [free_form_execution]
  completion_effect: 逐节点执行，产出结构化证据；任一节点失败→记录状态→跳出→生成事故包
  phase_variant_note: Phase 1 简化版（5状态）失败时全部进入 COLLECT 收集证据以便调试框架；Phase 3 完整版（9状态）前置阶段失败直接 HALT，验证阶段失败才进入 COLLECT

- object: RunManifest
  purpose: 绑定执行时的世界快照（版本/环境/账号/数据）
  required_fields: [run_id, app_commit, base_url, browser, generated_at]
  optional_fields: [frontend_build, backend_version, feature_flags, test_data_snapshot, accounts]
  forbidden_fields: [mutable_after_creation]
  completion_effect: 测试结果绑定此 manifest 实现可复现性

- object: Environment
  purpose: 测试环境定义（由 environment-provision 生成）
  required_fields: [base_url, browser, timeout, headless]
  optional_fields: [account_runner, account_verifier, managed, version]
  forbidden_fields: [embedded_in_testset]
  completion_effect: 作为 test_environment_ref 来源

- object: Accident
  purpose: 标准化失败取证包
  required_fields: [case_id, manifest, screenshots, traces, network_log, console_log, failure_classification]
  optional_fields: [videos, storage_state, dom_snapshot, entity_snapshot]
  forbidden_fields: [ad_hoc_format]
  completion_effect: 为故障分类提供标准化输入

- object: Verifier
  purpose: 独立验证层，不信任 runner 结论
  required_fields: [verdict, confidence, c_layer_verdict, detail]
  optional_fields: [query_path, account_isolation]
  forbidden_fields: [shared_context_with_runner]
  completion_effect: 输出 verdict，一票否决 Gate

## 枚举冻结

> **命名说明：**
> - **Skill ID**（用户调用标识）：使用点号分隔，如 `qa.test-plan`、`qa.test-run`
> - **skill_ref**（内部注册标识）：使用 `skill.` 前缀 + 下划线，如 `skill.qa.test_plan`
> - 两种命名风格服务于不同层面：Skill ID 用于用户意图识别，skill_ref 用于内部模块注册和编排

- field: skill_id
  semantic_axis: 用户意图入口
  allowed_values: ["qa.test-plan", "qa.test-run"]
  forbidden_semantics: 内部模块注册为 Skill
  used_for: 用户交互入口、编排根节点

- field: module_id
  semantic_axis: 内部能力单元
  allowed_values: ["feat-to-testset", "api-plan-compile", "api-manifest-compile", "api-spec-compile", "e2e-plan-compile", "e2e-manifest-compile", "e2e-spec-compile", "environment-provision", "run-manifest-gen", "scenario-spec-compile", "state-machine-executor", "bypass-detector", "independent-verifier", "accident-package", "failure-classifier", "test-data-provision", "l0-smoke-check", "test-exec-web-e2e", "test-exec-cli", "settlement", "gate-evaluation"]
  forbidden_semantics: 直接用户调用
  used_for: 模块间编排、DAG 定义

- field: assertion_layer
  semantic_axis: 断言验证深度
  allowed_values: ["A", "B", "C"]
  forbidden_semantics: 跳过 A 或 B 层直接验证 C 层
  used_for: 断言覆盖率统计、Gate 判定

- field: failure_class
  semantic_axis: 故障根因分类
  allowed_values: ["ENV", "DATA", "SCRIPT", "ORACLE", "BYPASS", "PRODUCT", "FLAKY", "TIMEOUT"]
  forbidden_semantics: 新增未定义类别、ad-hoc 分类
  used_for: 故障趋势分析、后处理路由

- field: gate_verdict
  semantic_axis: 验收结论
  allowed_values: ["pass", "conditional_pass", "fail", "provisional_pass"]
  forbidden_semantics: 自定义结论类型
  used_for: 质量决策、CI/CD 闸门

- field: phase
  semantic_axis: 实施阶段
  allowed_values: ["1a", "1b", "2", "3", "4"]
  forbidden_semantics: 跳过阶段直接上线
  used_for: 功能开关、C 层要求、编排方式

## 治理变更摘要

- ADR-052 定义测试体系的治理架构重构：从混合治理拆分为需求轴（SSOT）+ 实施轴（Artifact）双轴模型
- 当前失控点：test_environment_ref 无来源、声明/执行产物混域、AI 执行不可审计、断言过弱、数据不可控
- 新的统一原则：声明可覆盖 vs 证据只追加、Skill 仅用户入口、独立验证一票否决、黄金路径固化标准
- 下游必须继承：需求轴/实施轴分层规则、枚举冻结（skill_id/module_id/assertion_layer/failure_class/gate_verdict）、7 条关键约束
- 下游不应误展开：内部模块不应注册为 Skill、TESTSET 不应嵌入 test_case_pack、verifier 不应复用 runner 上下文

## 关键约束

- Skill 仅作为用户入口，内部模块不注册为 Skill
- 需求轴资产声明性可覆盖，实施轴资产证据性只追加
- 黄金路径 C 层断言 100% 覆盖前 gate 不得返回 pass
- verifier=fail → Gate 必须=fail，不可被 settlement 覆盖
- Phase 1 Gate 结论上限为 provisional_pass
- TESTSET 中不得嵌入 test_case_pack 或 script_pack
- verifier 必须使用独立认证上下文（不同 token、不同浏览器 context、不同账号、不同数据快照）

## 范围边界

- In scope: 测试体系治理架构（需求轴/实施轴拆分）、2 个用户 Skill 定义、17+ 内部模块接口契约、三层断言模型、状态机执行器、8 类故障分类、GoldenPath schema 定义、4 阶段实施计划、Gate 评价维度、存储分层与清理策略
- Out of scope: 具体实现代码编写、UI 界面设计、非测试体系的其他治理域、分布式编排器、数据库 schema 变更

## 内嵌需求源快照

- Frozen input ref: artifacts/raw-to-src/SRC-009-adr052/frz-package/
- Frozen input sha256: (computed at freeze time)
- Captured at: 2026-04-22T00:00:00+08:00
- Original source path: ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md
- Embedded source summary: ADR-052 v1.5-draft 定义测试体系按需求轴/实施轴拆分，2 个用户 Skill (qa.test-plan/qa.test-run) 编排 17+ 内部模块。需求轴 SSOT 管理"测什么"，实施轴 Artifact 管理"在哪测、怎么跑、结果是否可信"。三层断言 (A:交互/B:页面结果/C:业务状态)、状态机 9 状态 (Phase 1 简化 5 状态)、8 类故障分类、GoldenPath schema 定义、4 阶段实施计划 (1a/1b/2/3/4)。7 条关键约束包括 Skill 入口约束、需求/实施轴分离、C 层覆盖 Gate 限制、verifier 一票否决、Phase 1 Gate 上限、TESTSET 边界、verifier 独立性。具体黄金路径内容（示例 G1-G6）由产品侧定义，用于验证测试框架能力。Skill ID 使用点号分隔（qa.test-plan），skill_ref 使用下划线（skill.qa.test_plan），服务于不同层面。Phase 1 状态机简化版失败时全部进入 COLLECT 收集证据，Phase 3 完整版前置失败直接 HALT。

## 来源追溯

- Source refs: ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md
- Input type: adr
- SSOT policy: 本 SRC 已内嵌并冻结 FRZ-001 需求源快照，不依赖外部文件存活。所有语义内容已嵌入 src-candidate.md 和 src-candidate.json。外部 ADR-052 仅用于追溯，不是理解候选的前提。

## Bridge Context

- governed_by_adrs: [ADR-052, ADR-047, ADR-050, ADR-051]
- change_scope: 测试体系治理架构重构——从混合治理拆分为需求轴(SSOT)+实施轴(Artifact)双轴模型，2 个用户 Skill 替代 5 层分散技能，补齐 10 个待补内部模块，建立三层断言、状态机执行、独立验证的验收闭环
- governance_objects: [Skill(qa.test-plan, qa.test-run), Module(17+), AssertionLayer(A,B,C), FailureClass(8类), GoldenPath(schema), Gate, StateMachine, RunManifest, Environment, Accident, Verifier]
- current_failure_modes: [ENV, DATA, SCRIPT, ORACLE, BYPASS, PRODUCT, FLAKY, TIMEOUT]
- downstream_inheritance_requirements: 下游 Epic/Feature 层必须继承需求轴/实施轴分层规则、枚举冻结、7 条关键约束；TESTSET 不得嵌入执行产物；verifier 必须独立
- expected_downstream_objects: [Epic(按阶段拆分), Feature(按模块拆分), TESTSET(需求轴输出), Environment(实施轴输入), RunManifest(每次执行绑定), Gate(每次结算输出)]
- acceptance_impact: Gate 评价维度公开化（用例通过率/断言覆盖率/bypass违规/verifier verdict/PRODUCT故障/环境一致性）；verifier 一票否决；Phase 1 上限 provisional_pass 透明披露 C 层缺口
- non_goals: 具体实现代码、UI 设计、分布式编排、数据库 schema 变更、非测试体系的其他治理域
