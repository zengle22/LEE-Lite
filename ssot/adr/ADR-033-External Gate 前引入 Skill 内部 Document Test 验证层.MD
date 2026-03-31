# ADR-033：External Gate 前引入 Skill 内部 Document Test 验证层

* 状态：Draft
* 日期：2026-03-31
* 决策者：Le Zeng
* 适用范围：`product.raw-to-src`、`product.src-to-epic`、`product.epic-to-feat`、`dev.feat-to-ui`、`dev.feat-to-tech`、`qa.feat-to-testset`、`dev.tech-to-impl`
* 相关 ADR：ADR-002、ADR-006、ADR-009、ADR-010、ADR-011、ADR-012、ADR-013、ADR-014、ADR-021

---

# 1. 背景

当前仓库已经在主链与下游文档链上冻结了几类 lite-native governed workflow：

* `RAW -> SRC`
* `SRC -> EPIC`
* `EPIC -> FEAT`
* `FEAT -> UI`
* `FEAT -> TECH`
* `FEAT -> TESTSET`
* `TECH -> IMPL`

同时，系统已经明确了两条基础原则：

1. **审核与裁决必须分离**
2. **External Gate 负责 authoritative verdict**

其中：

* skill 内可以做 executor / supervisor 两角色审核；
* skill 内可以做 structural / semantic validation；
* skill 内可以做有限返修；
* 但最终的 `approve / revise / retry / reject / handoff` 不应由业务 skill 自己裁决。

这一点已经由 ADR-006、ADR-009 以及现有 gate runtime 共同冻结。

但在当前实现里，skill 内部的“验证”仍然偏碎片化：

* 有的 skill 只有 structural validation + semantic review；
* 有的 skill 直接 rebuild 后交 supervisor；
* `raw-to-src` 有较强的 auto-fix loop，但也主要围绕 intake / structure / semantic patch；
* 还没有一层被正式命名、正式建模、正式落盘的：

## **Document Test / 文档测试验证层**

这带来一个实际缺口：

> 在 external gate 看到文档包之前，系统缺少一套统一、完整、面向“文档是否真的可作为下游真相源继续工作”的内部测试层。

结果就是：

* 一些问题只有到了 external gate 才暴露；
* 不同 skill 对“文档可用性”的判断标准不一致；
* defect 虽然能被发现，但缺少固定测试分类与证据结构；
* auto-fix / rebuild / human judgement 的分流规则不统一；
* downstream readiness 经常被隐含在 prose 判断里，而不是被测试化、证据化。

因此，需要一份新 ADR，把：

* Document Test 的角色
* 与 structural / semantic review 的关系
* 与 auto-fix / rebuild 的接缝
* 与 supervisor / external gate 的职责边界
* 应输出哪些报告
* 适用于哪些 skill、以什么深度适用

统一冻结成正式基线。

---

# 2. 问题陈述

当前真正需要回答的，不是“要不要多做一次 review”，而是以下几个更结构性的问题。

## 2.1 skill 内验证到底缺的是什么

当前 skill 内已经有一些验证步骤，但这些步骤大多只回答局部问题：

* schema 是否通过
* 必填字段是否齐全
* 语义是否明显漂移
* 是否存在某些 defect

它们还没有形成一个统一的问题：

## **这份文档包在进入 external gate 前，是否已经被完整验证为“可下游消费、逻辑一致、边界清楚、返修可追溯”的对象？**

如果这个问题不被正式建模，skill 内验证就会持续漂移为：

* 一组脚本
* 一组 review report
* 一些 defect list
* 一些各 skill 自己理解的 readiness 规则

而不是一个正式 phase。

## 2.2 为什么仅靠 supervisor review 不够

如果把所有“完整检查”都留给 supervisor，那么 supervisor 会同时承担：

* review
* test
* classification
* rerun decision preparation
* gate-ready 整理

这会带来两个问题：

1. supervisor 角色变得过重，越来越像 skill 内部第二个 gate
2. 可测试的验证逻辑无法被明确沉淀成稳定报告，而是混进 review prose

因此，Document Test 需要被显式分离出来，作为：

* 介于 semantic review 与 supervisor review 之间的完整验证层
* 用结构化报告表达问题
* 为 auto-fix / rebuild / gate-ready 提供可分流证据

## 2.3 为什么不能把 Document Test 做成 skill 内部第二个 gate

这是本 ADR 的核心边界。

如果 Document Test 被定义成：

* 内部判通过
* 内部判不通过
* 内部决定 freeze-ready
* 内部替代 gate decision

那么它会直接违反已冻结的 gate 分权原则。

因此，Document Test 必须只做：

* 发现问题
* 生成证据
* 分类问题
* 判断 fixability
* 为 supervisor 和 external gate 提供输入

而不能做：

* 最终 approve
* 最终 reject
* 最终 dispatch
* formal materialization

## 2.4 为什么不是所有 skill 都适合 full auto-fix

`raw-to-src` 已经证明：对于高噪声上游归一化链路，skill 内 auto-fix loop 是有价值的。

但越往下游，文档对象的耦合越高：

* `src-to-epic` 的局部补丁可能破坏 EPIC capability slicing
* `epic-to-feat` 的局部补丁可能破坏 downstream derivation
* `feat-to-tech` / `tech-to-impl` 的局部补丁可能引入跨文档不一致

所以，Document Test 不应自动推导出“所有 skill 都要 full auto-fix loop”。

它更合理的职责是：

* 统一测试层
* 统一 defect 分类
* 统一 fixability 报告

至于后续动作：

* `raw-to-src` 可以走 local auto-fix
* 其它 skill 多数应走 rebuild 或 handoff to gate

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **在 external gate 前，为文档型 governed skill 引入一层显式的 Skill Internal Document Test 验证层**

其定位是：

* skill 内完整文档验证 phase
* 结构化 defect / readiness / drift / fixability 证据生成层
* auto-fix / rebuild / supervisor review 的分流输入层

而不是：

* 内部第二个 gate
* 内部最终裁决器
* 对 external gate 的替代

## 3.2 标准 phase 顺序

对于文档型 governed workflow，标准主顺序调整为：

1. `drafted`
2. `structurally_validated`
3. `semantically_reviewed`
4. `document_tested`
5. `revised`（如允许且有必要）
6. `supervisor_reviewed`
7. `gate_ready`
8. `accepted / frozen / rejected` 仍由 external gate 或 formal materialization 链决定

这里：

* `document_tested` 是 skill 内生命周期状态
* `document_tested` 仅表示：Document Test 已执行完成、主报告已落盘、defect 已分类、`recommended_next_action` 与 `recommended_actor` 已产生
* `document_tested` 不表示内容已通过、不表示 ready、不表示可冻结、不表示可 approve
* `gate_ready` 只是“证据与提交形态满足进入 external gate”的包状态
* `gate_ready` 不等于 authoritative `approve`

## 3.3 Document Test 的正式职责

Document Test 负责测试以下 6 类问题：

### 3.3.1 Structural Completeness

验证：

* package artifact 是否齐全
* manifest / bundle / report / evidence 是否相互一致
* 必填字段是否完整
* ref 是否可解析

### 3.3.2 Traceability Integrity

验证：

* `source_refs`
* upstream object refs
* handoff refs
* `revision_request_ref`
* `revision_context`
* evidence refs

是否形成完整闭环。

### 3.3.3 Boundary Correctness

验证文档是否越层。

例如：

* `SRC -> EPIC` 是否混入 FEAT / TASK / UI / implementation 细节
* `FEAT -> UI` 是否越权改写产品 acceptance
* `FEAT -> TECH` 是否混入 delivery orchestration
* `TECH -> IMPL` 是否反向承担第二层技术设计

### 3.3.4 Logic Consistency

验证文档内部逻辑是否自洽。

例如：

* goal 与 acceptance 是否冲突
* in_scope / out_of_scope 是否冲突
* 用户路径与状态机是否冲突
* API 假设与字段边界是否冲突
* rollout / fallback / readiness 语义是否冲突

### 3.3.5 Downstream Readiness

验证：

## **下游 skill 是否可以只依赖当前文档包继续工作，而不需要重新发明上游定义**

这不是风格检查，而是消费性检查。

### 3.3.5.1 Downstream Consumption Contract

`downstream readiness` 不允许只停留在 prose judgment。

每条 workflow 必须定义自己的最小 `downstream consumption contract`，至少回答：

* 下游消费方最少需要哪些字段、边界、约束、handoff 与 trace
* 哪些定义必须显式给出，不能靠 agent 推断
* 哪些缺口会导致下游 skill 重新发明上游规则
* 哪些缺口属于 blocking gap，哪些只是不完整但仍可进入 gate review

当前各 workflow 的最小检查项冻结如下：

#### `product.raw-to-src`

至少检查：

* `problem_statement` 是否闭合
* `key_constraints / in_scope / out_of_scope` 是否足以支撑 `src-to-epic`
* `semantic_inventory` 与 provenance 是否足够
* revision context 与 source refs 是否可追溯

#### `product.src-to-epic`

至少检查：

* capability slicing 是否可导出
* scope / non-scope 是否可被 `epic-to-feat` 继续拆解
* acceptance semantics 是否清楚
* upstream facts 与 inherited constraints 是否显式

#### `product.epic-to-feat`

至少检查：

* feat 边界是否互斥且基本完备
* acceptance 是否可继承到 FEAT
* dependencies / rollout assumptions 是否明确
* downstream handoff 是否足以支撑 `feat-to-ui`、`feat-to-tech`、`feat-to-testset`

#### `dev.feat-to-ui`

至少检查：

* user path 与 state model 是否可直接驱动 UI 实现
* field boundary / validation rule / feedback rule 是否明确
* UI/TECH 边界是否清楚
* 是否仍需要下游重新发明页面主结构或主状态机

#### `dev.feat-to-tech`

至少检查：

* `TECH` 是否足以驱动 `tech-to-impl`
* `ARCH / API` 的存在条件与边界是否清楚
* 主设计、约束、touchpoints、risk handling 是否可消费
* 是否存在需要下游重新定义的核心技术决策

#### `qa.feat-to-testset`

至少检查：

* acceptance 到 strategy 的映射是否清楚
* test units 是否足以成为最小执行前提
* 环境、依赖、qualification 边界是否可消费
* 是否存在需要 test execution 重新定义的测试目标或策略边界

#### `dev.tech-to-impl`

至少检查：

* implementation task 是否可直接进入执行链
* upstream frozen design refs 是否完整
* integration / evidence / smoke gate 输入是否明确
* 是否仍需下游重新发明实施边界或工作流分工

### 3.3.6 Revision Regression

当本轮输入来自 `revise / retry` 时，Document Test 必须额外验证：

* 是否真实吸收了 revision request
* 是否引入新的 semantic drift
* 是否把之前已通过的内容重新破坏

## 3.4 Document Test 的标准产物

P0 阶段不要求一开始就拆成 5 个物理文件。

每个接入该 phase 的文档型 skill，至少应输出一个主报告：

* `document-test-report.json`

该主报告必须内嵌以下 section：

* `structural`
* `logic_consistency`
* `downstream_readiness`
* `semantic_drift`
* `fixability`

P1 之后，允许在不改变主报告语义的前提下，把某些 section 派生为独立文件视图，例如：

* `logic-consistency-report.json`
* `downstream-readiness-report.json`
* `semantic-drift-report.json`
* `fixability-report.json`

但这些派生文件是主报告的展开视图，不得成为新的主真相源。

## 3.5 缺陷分类标准

Document Test 发现的问题必须至少分成以下四类：

* `mechanical_fixable`
* `local_semantic_fixable`
* `rebuild_required`
* `human_judgement_required`

含义如下：

### `mechanical_fixable`

问题可通过局部、机械、低语义风险修复完成。

例如：

* 缺少标准字段
* artifact 间 ref 不一致
* evidence 漏写
* manifest 漏字段

### `local_semantic_fixable`

问题可以局部修，但需要受控语义补丁。

这类问题主要适用于 `raw-to-src`，也可少量用于其它 skill 的小范围补洞。

### `rebuild_required`

问题影响文档主结构、主边界或主逻辑，需要整包重建后再审。

这是大多数下游文档 skill 的默认返修路径。

### `human_judgement_required`

问题本质上是：

* 目标冲突
* 范围冲突
* 产品策略冲突
* 技术路径冲突
* 组织性优先级冲突

这类问题不应由 skill 内自动修补决定。

## 3.5.1 缺陷升级规则

为了避免 fixability 分类漂移，以下升级规则正式冻结：

* 触及主结构、主边界、主状态机、主 acceptance semantics：直接升级为 `rebuild_required`
* 触及跨文档一致性、继承约束、handoff contract：默认升级为 `rebuild_required`
* 触及产品目标、优先级、策略取舍、组织性依赖冲突：直接升级为 `human_judgement_required`
* 触及 formal source truth 冲突、revision request 与现状冲突、上游 authority 不明确：默认升级为 `human_judgement_required`
* 只有在 patch 不会改变主边界、主状态机、主 acceptance、主 handoff 的情况下，才允许保留为 `local_semantic_fixable`
* 只有在问题是字段缺漏、ref 漏写、manifest/evidence 漏项、低风险一致性修复时，才允许保留为 `mechanical_fixable`

## 3.6 与 auto-fix / rebuild 的关系

Document Test 不等于 auto-fix。

它与返修动作的关系是：

1. 先测试
2. 再分类
3. 再决定进入：
   * local auto-fix
   * rebuild
   * supervisor aggregation only
   * external gate judgement

其中，Document Test 主报告必须同时产出：

* `recommended_next_action`
* `recommended_actor`

`recommended_actor` 至少允许以下枚举：

* `executor_local_patch`
* `workflow_rebuild`
* `supervisor_handoff`
* `external_gate_review`
* `human_owner_decision`

其中：

* `raw-to-src` 允许在 Document Test 后进入 stronger local repair loop
* 其它大多数文档型 skill 默认进入 rebuild 或 gate-ready review

## 3.7 与 supervisor 的关系

supervisor 不再直接承担“全部测试工作”。

其职责应收敛为：

* 汇总 structural / semantic / document test 证据
* 判定是否已具备提交 external gate 所需的证据完整性与包完整性
* 整理返修建议与 defect list
* 生成 handoff / gate subject

supervisor 仍然是 skill 内最终 review 角色，但不是 Document Test 的替代。

这里进一步冻结一条边界：

* supervisor 可以判断“是否具备进入 gate 的证据完整性”
* supervisor 不可以判断“内容已经实质通过到足以 approve”

也就是说，supervisor 负责 **submission readiness**，不负责 **authoritative approval judgement**。

## 3.8 与 external gate 的关系

external gate 的职责不变。

Document Test 不改变以下事实：

* skill 不做最终 approve
* skill 不做最终 reject
* skill 不做 dispatch
* skill 不做 formal materialization

Document Test 只是提高 gate 之前的内部验证质量，降低低级问题进入 gate 的比例。

---

# 4. 适用范围与分层策略

## 4.1 全量适用对象

本 ADR 适用于当前 7 个文档型 workflow：

* `product.raw-to-src`
* `product.src-to-epic`
* `product.epic-to-feat`
* `dev.feat-to-ui`
* `dev.feat-to-tech`
* `qa.feat-to-testset`
* `dev.tech-to-impl`

## 4.2 深度分级

不是所有 skill 的 Document Test 深度都完全相同。

### A. Full Document Test + Local Repair Friendly

* `product.raw-to-src`

特点：

* 输入噪声高
* patchable 问题多
* 局部修补收益高

### B. Full Document Test + Rebuild Preferred

* `product.src-to-epic`
* `product.epic-to-feat`
* `dev.feat-to-ui`
* `dev.feat-to-tech`
* `qa.feat-to-testset`
* `dev.tech-to-impl`

特点：

* 必须完整测试
* 但内容级返修多数应通过 rebuild 完成
* 不鼓励大规模 local patch

## 4.3 不适用对象

以下 workflow 不在本 ADR 的 Document Test 适用范围内：

* `governance.gate-human-orchestrator`
* `repo.project-init`
* `skill.test-exec-cli`
* `skill.test-exec-web-e2e`
* `workflow.execution-loop-job-runner`

原因是它们不是“governed authored document package regeneration workflow”。

---

# 5. 生命周期与状态机调整

现有文档型 skill 生命周期中，应允许显式出现：

* `document_tested`

推荐迁移后的标准状态链为：

* `drafted`
* `structurally_validated`
* `semantically_reviewed`
* `document_tested`
* `revised`
* `supervisor_reviewed`
* `gate_ready`
* `accepted`
* `frozen`
* `rejected`

其中：

* `accepted / frozen / rejected` 依然属于 external authority 或 formal publish 流程结果
* skill 内部只负责走到 `gate_ready`

---

# 6. 报告结构建议

## 6.1 `document-test-report.json`

建议至少包含：

* `workflow_key`
* `run_id`
* `tested_at`
* `test_outcome`
* `defect_counts`
* `recommended_next_action`
* `recommended_actor`
* `sections`

其中：

* `test_outcome` 不得命名为 `decision`
* `test_outcome` 只表达测试结论摘要，不表达 gate verdict

推荐枚举：

* `no_blocking_defect_found`
* `blocking_defect_found`
* `inconclusive`
* `not_applicable`

## 6.2 `sections.logic_consistency`

建议至少包含：

* `checked_topics`
* `conflicts_found`
* `severity`
* `blocking`

## 6.3 `sections.downstream_readiness`

建议至少包含：

* `downstream_target`
* `consumption_contract_ref`
* `ready_for_gate_review`
* `blocking_gaps`
* `missing_contracts`
* `assumption_leaks`

## 6.4 `sections.semantic_drift`

建议至少包含：

* `revision_context_present`
* `drift_detected`
* `drift_items`
* `semantic_lock_preserved`

## 6.5 `sections.fixability`

建议至少包含：

* `mechanical_fixable`
* `local_semantic_fixable`
* `rebuild_required`
* `human_judgement_required`
* `recommended_next_action`
* `recommended_actor`

---

# 7. 迁移策略

## 7.1 P0

先把 Document Test 作为统一 phase 名称与统一证据面冻结。

这一步先要求：

* phase 存在
* 一个主报告存在
* 分类存在
* `document_tested` 状态语义被硬定义
* `test_outcome`、`recommended_next_action`、`recommended_actor` 被固定

不强制所有 skill 同时具备同等复杂度的实现。

P0 明确采用：

* 一个主报告 `document-test-report.json`
* 五个内嵌 section
* workflow-specific downstream consumption contract

而不是一开始就要求 5 个物理文件同时落地。

## 7.2 P1

优先接入：

* `raw-to-src`
* `src-to-epic`
* `epic-to-feat`

因为它们构成产品主链。

## 7.3 P2

再接入：

* `feat-to-ui`
* `feat-to-tech`
* `feat-to-testset`
* `tech-to-impl`

并对各自的 downstream readiness 测试标准做细化。

---

# 8. 非目标

本 ADR 明确不做以下事情：

* 不把 Document Test 升级成内部 gate
* 不允许业务 skill 自行做最终 approve/reject
* 不要求所有 skill 都采用 `raw-to-src` 式 full auto-fix loop
* 不要求所有 defect 都能自动修补
* 不把 execution skill、gate skill、runner skill 强行纳入文档测试模型

---

# 9. 影响

采用本 ADR 后，会带来以下变化：

* 文档型 skill 的内部验证层从“零散 review 脚本”升级为显式 phase
* defect 分类、证据结构、返修分流逻辑更统一
* external gate 会收到更成熟的 gate-ready package
* `raw-to-src` 的 auto-fix 优势可以被保留，但不会被误推广到全部 skill

同时，也会带来新的实现要求：

* lifecycle 需要增加 `document_tested`
* runtime 需要增加标准 report 落盘
* supervisor 需要消费 document test 结果
* skill contract 需要声明 document test phase 的输入输出

---

# 10. 结论

LL 正式把：

## **Document Test 作为 external gate 之前的 skill 内完整文档验证层**

冻结为文档型 governed workflow 的标准构件。

它的本质不是“多一轮 review”，而是：

* 把文档是否真正可用
* 问题是否可修
* 返修该怎么分流
* evidence 应如何结构化

这些原本散落在各 skill 中的逻辑，正式收敛成统一 phase。

从本 ADR 生效起：

* 文档型 governed skill 应逐步接入 `document_tested` phase
* 该 phase 只负责验证与证据，不负责最终裁决
* external gate 仍然保留唯一 authoritative verdict 地位
