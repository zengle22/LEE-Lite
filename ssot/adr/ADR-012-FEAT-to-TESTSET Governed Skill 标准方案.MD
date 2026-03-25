# ADR-012：FEAT-to-TESTSET Governed Skill 标准方案

* 状态：Draft
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：`ll-qa-feat-to-testset` skill、`qa.feat-to-testset` lite-native runtime、`test_set_candidate_package`、`test_set_freeze_package`
* 相关 ADR：ADR-006、ADR-007、ADR-008、ADR-009、ADR-011

---

# 1. 背景

当前 LL 已经在主链上具备较明确的产品与研发派生路径：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT -> TECH`
* `FEAT -> TESTSET` 在 ADR-008 中已被正式定义为 FEAT 的直接派生对象，而不是 `TECH` 或 `TASK` 的下游附属物

同时，QA 侧已经有两块相邻但尚未打通的基线：

* ADR-007 已冻结 `TestSet -> 执行 -> TSE` 的 governed skill 边界；
* `E:\ai\LEE\spec-global\departments\qa\workflows\templates\test-set-production-l3-template.md` 已定义从需求分析到 Test Set 审评的 4 阶段生产流程。

但当前仓库里仍缺少一个正式 ADR，来回答下面这个更具体的问题：

> 如何把一个已经冻结的 `feat_freeze_package` 中的单个 FEAT，先稳定派生成一个可审评的 `test_set_candidate_package`，再在 blocking approval 通过后物化为可冻结、可下传给测试执行链的 `test_set_freeze_package`？

如果这层不先冻结，后续实现很容易出现几类持续漂移：

* 有人把 Test Set 生产理解成读取任意 `requirement_doc` 的文档生成器，而不是 FEAT 派生 workflow；
* 有人把 `analysis.md`、`strategy-draft.yaml` 升级成新的 SSOT 对象，重新引入历史上的 `TESTPLAN` 漂移；
* 有人直接输出一个裸 `ts-*.yaml`，却没有 governed package、evidence、review、freeze gate 与 downstream handoff；
* 有人把 QA 模板中的 3 个人工门禁重新内嵌回 skill 内部，违反 ADR-006 与 ADR-009 已冻结的 external gate / CLI-first runtime 原则；
* 有人让 `TECH` 或 `delivery_prep_bundle` 反客为主，覆盖 FEAT 本身的 acceptance boundary。

因此，需要一份独立 ADR，把：

* FEAT 到 TESTSET 的输入权威
* 中间产物边界
* 输出 package 结构
* human gate 外置方式
* 与 ADR-007 测试执行链的接缝

一次性冻结为统一基线。

---

# 2. 问题陈述

LL 当前需要解决的，不是“再写一个 QA YAML 生成器”，而是以下几个硬问题：

## 2.1 权威输入到底是谁

QA 模板中允许出现：

* `feat_freeze`
* `requirement_doc`
* `tech_design`
* `delivery_prep_bundle`
* `ui_specs`

但在 LL skill-first 体系里，如果不先冻结优先级，就会出现：

* FEAT 明明已经冻结，却又被兼容输入反向改写；
* requirement_doc 变成事实上的主输入；
* 同一个 TESTSET 在不同实现里由不同输入组合主导。

## 2.2 输出到底是对象还是文件碎片

如果只要求产出：

* `analysis.md`
* `strategy-draft.yaml`
* `ts-*.yaml`

却不要求一个 governed package，那么：

* freeze 无法表达；
* evidence 无法挂接；
* 审评结论无法归档；
* downstream handoff 无法标准化；
* test execution 无法稳定消费。

## 2.3 Analysis / Strategy 是不是新的 SSOT

如果把 QA 生产流程中的阶段性文档直接升级成平行对象，就会重新发明：

* `TESTPLAN`
* `QA_STRATEGY`
* `ANALYSIS_DOC`

这与 ADR-008 已经收敛的“编排视图不再作为正式 SSOT 扩张”相冲突。

## 2.4 人工门禁如何映射到 lite-native skill

QA 模板显式要求：

* `analysis_review`
* `strategy_review`
* `test_set_approval`

但 LL 已经通过 ADR-006、ADR-009 冻结：

* gate 必须外置；
* human review 不应由业务 skill 自己裁决；
* runtime 采用 CLI-first + file-based 形态。

因此必须回答：

* skill 如何产出 gate subject；
* external gate 如何物化 human-review / approval job；
* 哪个 gate 是 advisory，哪个 gate 是 blocking。

## 2.5 与下游 Test Execution 的接缝是什么

ADR-007 的测试执行 skill 消费的是策略级 `TestSet`，而不是一堆零散 QA 草稿。因此 FEAT-to-TESTSET skill 必须明确：

* 输出中的哪个对象是正式 `TESTSET`；
* 哪些只是 package 内部伴随产物；
* 下游 handoff 应引用什么，而不是再去重新解释 analysis / strategy。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个窄边界、单 FEAT 选择、lite-native 的 `ll-qa-feat-to-testset` governed skill**

作为 FEAT 到 TESTSET 的标准派生路径。

本 ADR 冻结以下原则：

1. 输入权威固定为：
   * 一个 `feat_freeze_package`
   * 一个必选 `feat_ref`
2. 运行时输出权威固定为：
   * 一个 `test_set_candidate_package`
   * 其中包含一个正式 `TESTSET` 草案对象和若干 package 内伴随产物
3. blocking approval 通过后，external gate 才允许把 candidate package 物化为：
   * 一个 `test_set_freeze_package`
4. `analysis.md` 与 `strategy-draft.yaml` 是 package companion artifact，不是新的 SSOT 类型。
5. `requirement_doc`、`tech_design_package`、`delivery_prep_bundle`、`ui_specs` 只能作为补强上下文，不能替代 FEAT 的权威边界。
6. QA 模板中的 3 个人工门禁继续保留，但必须通过 external gate / human-review job 外置承载。
7. `analysis_review` 与 `strategy_review` 属于 review gate，允许提出 revise_request，但不得直接冻结 package。
8. `test_set_approval` 属于 blocking approval gate，不通过则不得物化为正式可执行 `test_set_freeze_package`。
9. 输出 package 必须显式对接 ADR-007 的测试执行链，优先服务于 `TestSet` 消费，而不是重新引入 plan 文档链。

---

## 3.2 正式定义

### 3.2.1 Skill 名称与 workflow key

正式 skill 名称：

* `ll-qa-feat-to-testset`

正式 workflow key：

* `qa.feat-to-testset`

其权威上游模板为：

* `E:\ai\LEE\spec-global\departments\qa\workflows\templates\test-set-production-l3-template.md`

如对应 YAML 模板存在，则以其 YAML 结构为结构化 authority，以该 Markdown 说明为语义 authority。

### 3.2.2 Skill 边界

`ll-qa-feat-to-testset` 的职责固定为：

* 从 `feat_freeze_package` 中选定一个 FEAT；
* 解析其 acceptance、scope、constraints 与 traceability；
* 结合可选补强输入形成测试上下文；
* 产出 requirement analysis；
* 产出 test strategy draft；
* 产出标准化 `TESTSET` YAML；
* 形成 review / acceptance / freeze 所需 evidence；
* 生成面向下游 test execution 的正式 handoff。

其不负责：

* 执行测试；
* 生成 `TestCasePack`、`ScriptPack` 或 `TSE`；
* 把 strategy draft 升格为独立 SSOT；
* 绕过 FEAT 直接从原始需求起草 TESTSET；
* 在 skill 内自行完成最终 human approval。

### 3.2.3 单 FEAT 选择原则

一个 `feat_freeze_package` 可能包含多个 FEAT，因此：

* `feat_ref` 必须是强制输入；
* 每次运行只允许选择一个 FEAT；
* 每次运行只允许输出一个主 `TESTSET`；
* 如需为多个 FEAT 生成 TESTSET，应以多个独立 run 完成，而不是一次包内批量混写。

这与 `ll-dev-feat-to-tech` 的单 FEAT 派生方式保持一致。

---

# 4. 输入模型

## 4.1 正式输入

该 skill 的正式输入固定为：

* `feat_freeze_package`
* `feat_ref`

可选补强输入包括：

* `tech_design_package_ref`
* `delivery_prep_bundle_ref`
* `ui_spec_refs`
* `governing_adrs`
* `decision_refs`
* `decision_constraints`
* `architecture_constraints`
* `process_constraints`
* `requirement_doc_ref`（仅兼容）

## 4.2 输入优先级

输入优先级正式冻结为：

1. 选定 FEAT 本体
2. FEAT 继承的 `source_refs`
3. 显式传入的 ADR / constraint refs
4. 可选补强输入（TECH / delivery prep / UI）
5. 兼容输入 `requirement_doc_ref`

一旦兼容输入与 FEAT 冲突，必须：

* 以 FEAT 为准；
* 在 analysis / review 中显式记录冲突；
* 不得静默用兼容输入覆盖 FEAT acceptance boundary。

## 4.3 `derived_slug` 的语义

QA 模板中的 `module` 字段在 skill 化后应收敛为：

* `derived_slug`

其语义仅保留为：

* 派生显示名
* 文件 slug
* 包内目录定位辅助字段

若为兼容历史模板仍需接受 `module`，则：

* `module` 只能作为 legacy alias 读入；
* 进入 candidate / freeze package 时应统一归一到 `derived_slug`；
* 不得把 `module` 继续保留为主边界字段。

`derived_slug` 不能覆盖：

* `feat_ref`
* `feat title`
* `src_root_id`

正式原则是：

## **`derived_slug` 必须由 selected FEAT 派生，而不是由调用方任意指定为另一套边界。**

---

# 5. 输出模型

## 5.1 运行时输出对象与最终冻结对象

该 skill 的运行时直接输出对象为：

* `test_set_candidate_package`

只有在 blocking approval 通过后，external gate 才允许把它物化为：

* `test_set_freeze_package`

其中主对象始终是：

* 一个正式 `TESTSET`

区别在于：

* candidate package 中的 `TESTSET` 仍处于可修订状态；
* freeze package 中的 `TESTSET` 已进入冻结态，不得再做语义层静默修改。

包内伴随产物至少包括：

* `analysis.md`
* `strategy-draft.yaml`
* review / acceptance / defect / freeze gate / handoff artifacts

## 5.2 `TESTSET` 的对象定位

根据 ADR-008，`TESTSET` 是 FEAT 的直接派生 SSOT，对应：

> 面向 FEAT 的最小测试覆盖单元

因此该 skill 输出的正式真相是：

* `TESTSET`

而不是：

* `strategy-draft`
* `analysis report`
* `test plan`

这些文件只作为 package 内的支持性证据和评审材料存在。

## 5.3 推荐 artifact 清单

`test_set_candidate_package` / `test_set_freeze_package` 的最小 artifact 集应包含：

* `package-manifest.json`
* `test-set-bundle.md`
* `test-set-bundle.json`
* `test-set.yaml`
* `analysis.md`
* `strategy-draft.yaml`
* `test-set-review-report.json`
* `test-set-acceptance-report.json`
* `test-set-defect-list.json`
* `test-set-freeze-gate.json`
* `handoff-to-test-execution.json`
* `execution-evidence.json`
* `supervision-evidence.json`

如后续实现需要为 3 个外置 human gate 补充单独 subject / proposal 文件，可在不改变主对象边界的前提下追加，但不得替代上述主 package 结构。

两类 bundle 文件的职责边界正式定义为：

* `test-set-bundle.json`
  * 机器消费的 bundle 索引、对象引用清单与 artifact 绑定入口；
  * 不替代 `package-manifest.json`，也不替代主对象 `test-set.yaml`。
* `test-set-bundle.md`
  * 人类审阅入口文档，用于汇总 candidate / freeze package 的阅读顺序与关键结论；
  * 不是正式主对象，也不是 machine-readable decision source。

## 5.4 正式输出目录

推荐输出目录为：

* `artifacts/feat-to-testset/<run_id>--<feat_ref>/`

该目录是 candidate package 的运行时目录，不等同于最终 freeze package 的 formal artifact identity 或最终 SSOT 存放目录。

## 5.5 Artifact 分层

为防止实现层把所有文件都误当成冻结对象，本 ADR 将 artifacts 明确分为三层：

### A. 主冻结对象

* `test-set.yaml`
* `package-manifest.json`
* `test-set-bundle.json`

### B. 必备伴随证据

* `analysis.md`
* `strategy-draft.yaml`
* `test-set-review-report.json`
* `test-set-acceptance-report.json`
* `test-set-freeze-gate.json`
* `handoff-to-test-execution.json`

### C. 运行时证据

* `execution-evidence.json`
* `supervision-evidence.json`
* `test-set-defect-list.json`

正式规则是：

* freeze package 必须完整保留 A + B；
* C 按 evidence policy 保留原文、裁剪版或摘要，但必须保证审计可追溯。

无论 package 内存在多少 companion artifact，本 ADR 继续冻结：

## **只有 `test-set.yaml` 是正式主对象；其余文件都围绕它服务，不与它并列竞争解释权。**

## 5.6 Candidate 与 Freeze 的边界

本 ADR 正式采用：

## **方案 B：先产出 `test_set_candidate_package`，通过 blocking approval 后再物化为 `test_set_freeze_package`。**

这意味着：

* skill executor / supervisor 运行期间，不得把运行中 package 命名为 freeze-ready 正式对象；
* candidate package 可以经历 analysis、strategy、review、revise 等阶段演进；
* 只有在 `test_set_approval` passed 且 freeze gate 全部满足时，external gate 才能物化 freeze package；
* freeze package 一旦形成，即不应再回退为 draft 或 review 状态。

## 5.7 状态模型

为避免 package 状态、主对象状态与 gate 状态漂移，本 ADR 先冻结如下最小状态表：

| 对象 | 允许状态 | 权威说明 |
| --- | --- | --- |
| `test-set.yaml` | `draft` / `review_ready` / `approved` / `frozen` | 主对象状态，表达 `TESTSET` 自身成熟度 |
| `package-manifest.json` | `in_progress` / `review_pending` / `approval_pending` / `frozen` / `rejected` | package 运行状态，表达 candidate/freeze 生命周期 |
| `test-set-freeze-gate.json` | `pending` / `passed` / `failed` | freeze gate 结论 |

补充纪律如下：

* `test-set.yaml.status` 是主对象权威状态；
* `package-manifest.json.status` 是 package 生命周期权威状态；
* `test-set-freeze-gate.json.status` 只表达 freeze 结论，不替代对象状态或 package 状态。
* `test-set.yaml.status=approved` 仅表示主对象已满足进入 freeze materialization 的内容前置条件；它不单独代表 freeze 已成立，也不替代 `test_set_approval` 的外置结论。

允许的典型组合：

* `test-set.yaml=review_ready` + `package-manifest=review_pending`
* `test-set.yaml=approved` + `package-manifest=approval_pending`
* `review report passed` + `approval not yet passed`

明确禁止：

* `package-manifest=frozen` 但 `test-set.yaml` 不是 `frozen`
* `test-set-freeze-gate=passed` 但 `package-manifest` 仍停留在 `in_progress`
* freeze 后主对象回写为 `draft` 或 `review_ready`

最终冻结判定正式定义为：

## **以 `test-set.yaml.status=frozen` 与 `package-manifest.json.status=frozen` 的一致性，且 `test-set-freeze-gate.json.status=passed`，作为最终冻结成立条件。**

---

# 6. `TESTSET` 最小字段

本 ADR 为 `test-set.yaml` 先冻结以下最小字段基线：

```yaml
id:
ssot_type:
feat_ref:
epic_ref:
src_ref:
title:
coverage_scope:
risk_focus:
preconditions:
environment_assumptions:
test_layers:
test_units:
coverage_exclusions:
pass_criteria:
evidence_required:
acceptance_traceability:
source_refs:
governing_adrs:
status:
```

补充约束如下：

* `feat_ref` 必须等于本次运行选定的 FEAT；
* `test_units` 表达最小测试覆盖单元，不得混写成策略段落、执行脚本或大篮子式 `test_items`；
* `acceptance_traceability` 必须覆盖 FEAT 的 acceptance checks，而不是只写模糊测试目标；
* `environment_assumptions` 用于表达环境前提、依赖系统、数据前提和基础执行约束；
* `coverage_exclusions` 用于显式表达本 TESTSET 不覆盖或延后覆盖的区域；
* `source_refs` 必须至少保留 `FEAT-*`、`EPIC-*`、`SRC-*` 与上游 workflow run ref；
* `status` 在最终 freeze 前不得标记为 `accepted` 或 `frozen`。

如后续 QA contract 需要细化 priority、negative coverage、test data assumptions 或 environment matrix，应在不破坏上述最小集的前提下扩展。

---

# 7. 阶段模型

## 7.1 保留 QA 模板的 4 阶段语义

该 skill 必须保留 QA 模板的 4 阶段语义：

1. `requirement_analysis`
2. `strategy_design`
3. `test_set_generation`
4. `test_set_review`

这 4 个阶段是语义 authority，不得在 skill 化时被删成“只剩一个 YAML 生成步骤”。

## 7.2 Lite-native 运行时映射

在 lite-native skill 中，允许将 4 阶段收敛为同一个 governed package 的阶段性产物，但必须满足：

* analysis 有独立产物；
* strategy 有独立产物；
* TESTSET 有独立主对象；
* review 有独立结论；
* 每个阶段都可被 external gate / human review 精准指向。

也就是说：

## **skill 可以把 4 个阶段装进一个 package，但不能把 4 个阶段压扁成一个无痕步骤。**

## 7.3 各阶段职责

### Stage 1：Requirement Analysis

职责：

* 从 selected FEAT 提取测试边界、非目标、关键 acceptance、风险输入；
* 判断可选输入是否改变风险面；
* 输出 `analysis.md`。

### Stage 2：Strategy Design

职责：

* 将 FEAT acceptance 转换为测试策略、优先级、测试层分配与覆盖重点；
* 形成 `strategy-draft.yaml`；
* 识别需要额外 environment / data / UI / integration context 的区域。

### Stage 3：Test Set Generation

职责：

* 从 analysis + strategy 产出正式 `test-set.yaml`；
* 形成 acceptance coverage trace；
* 确保主 `TESTSET` 可被下游执行链消费。

### Stage 4：Test Set Review

职责：

* 由 supervisor 对完整性、可执行性、traceability 与 FEAT 对齐性进行语义审评；
* 形成 `test-set-review-report.json` 与 `test-set-acceptance-report.json`；
* 为最终 approval gate 提供可审计结论。

---

# 8. Gate 模型

## 8.1 三类 gate 继续保留

该 skill 必须保留 QA 模板中的 3 类 gate：

* `analysis_review`
* `strategy_review`
* `test_set_approval`

但它们的承载方式正式冻结为：

## **由 external gate / human-review job 外置承载，而不是由 skill 自己做最终裁决。**

## 8.2 `analysis_review`

类型：

* `human_review`

语义：

* 审核 selected FEAT 的测试边界提取是否正确；
* 可提出 revise；
* 原则上不直接 formalize 任何正式对象。

它的作用是：

* 防止 analysis 一开始就偏离 FEAT scope；
* 让后续 strategy 不建立在错误边界之上。

## 8.3 `strategy_review`

类型：

* `human_review`

语义：

* 审核测试重点、风险区、层次划分与覆盖深度；
* 可提出 revise；
* 仍不直接 formalize 正式对象。

它的作用是：

* 防止生成出的 TESTSET 只是把 FEAT acceptance 机械改写；
* 保证测试策略与 QA 风险判断一致。

## 8.4 `test_set_approval`

类型：

* `human_approval`

语义：

* 对最终 `TESTSET` 与其审评结果做 blocking approval；
* 未通过前，不得让 package 进入最终 `accepted / frozen` 状态；
* 通过后，才允许物化为下游正式可消费的 `test_set_freeze_package`。

## 8.5 advisory 与 blocking 的边界

本 ADR 正式规定：

* `analysis_review` 与 `strategy_review` 是 advisory review gate；
* `test_set_approval` 是 blocking approval gate。

这意味着：

* analysis / strategy 的 review 可触发 revise，但不单独定义 package 最终状态；
* 最终 freeze readiness 由 `test_set_approval`、结构校验、语义审评和 evidence 一起决定。

## 8.6 revise_request 纪律

advisory review gate 可触发：

* `revise_request`

但其处理纪律必须冻结为：

* revise 只能回退到当前 candidate package 内对应阶段重产物；
* 不得静默修改已通过阶段的正式结论；
* 所有 revise 必须留下 `revision note` 与 `delta evidence`；
* 被 revise 影响的阶段必须重新进入对应 review；
* 如 strategy revise 影响 `test-set.yaml`，则主 `TESTSET` 与 review report 必须一起重算，不能只补一处文本。

## 8.7 外置 gate 的最小对象化约束

即使本 ADR 暂不完全展开 gate object schema，仍必须先冻结以下最小约束：

* 每个外置 gate 必须有稳定的 subject identity；
* `analysis_review`、`strategy_review`、`test_set_approval` 都必须能 machine-readably 关联到：
  * `selected feat_ref`
  * `test_set_candidate_package`
  * 对应阶段产物或主对象版本
* review / approval 决策必须落为 machine-readable decision artifact；
* decision artifact 必须支持从 decision 反向追溯到 candidate package、selected FEAT 与 gate type。

换句话说：

* gate 不能只读自然语言说明；
* approval 不能只存在于一段人类评论；
* candidate package 与 FEAT 绑定关系不能靠目录名猜测。

---

# 9. 结构校验与语义校验

## 9.1 结构校验必须覆盖

至少需要覆盖：

* 输入 package 类型正确
* `feat_ref` 存在且唯一匹配
* required runtime artifacts presence
* `test-set.yaml` schema
* `analysis.md` 与 `strategy-draft.yaml` presence
* FEAT / EPIC / SRC traceability completeness
* downstream handoff presence
* execution / supervision evidence presence

## 9.2 语义校验必须覆盖

至少需要覆盖：

* TESTSET 是否真正覆盖 selected FEAT 的 acceptance checks
* strategy 是否体现风险优先级，而不是文档摘要
* analysis 是否准确表达 scope / non-goals / dependencies
* 可选输入是否只做补强，而没有篡改 FEAT 边界
* TESTSET 是否可被下游 ADR-007 测试执行链消费
* review 结论与主对象内容是否一致

## 9.3 freeze 前置条件

`test_set_candidate_package` 物化为 `test_set_freeze_package` 前必须同时满足：

* input_structural_pass
* input_semantic_pass
* output_structural_pass
* output_semantic_pass
* execution_evidence_present
* supervision_evidence_present
* `test_set_approval` passed

---

# 10. 与 ADR-007 的接缝

## 10.1 下游 handoff 对象

该 skill 输出的 `handoff-to-test-execution.json` 至少应保留：

* `test_set_ref`
* `feat_ref`
* `epic_ref`
* `src_ref`
* `source_refs`
* `governing_adrs`
* `acceptance_traceability_summary`
* `required_environment_inputs`

其中：

* `required_environment_inputs` 必须覆盖环境前提、测试数据前提、依赖服务、访问权限、账号或密钥引用、功能开关配置、UI 或 integration context 等执行前提；
* 不得只写成泛化描述，例如“准备测试环境”或“确保依赖可用”。

## 10.2 下游消费原则

ADR-007 的测试执行链消费的是：

* 正式 `TESTSET`
* 以及运行时需要的环境契约

而不是：

* `analysis.md`
* `strategy-draft.yaml`

因此这些伴随产物只能作为：

* review evidence
* debugging context
* rerun / investigate context

不能反客为主，成为下游执行链的正式主输入。

---

# 11. 明确拒绝的方案

## 11.1 方案 A：直接从 requirement_doc 生成 TESTSET

不采纳。

原因：

* 违背 FEAT 派生对象模型；
* 绕开 `feat_freeze_package` 的治理边界；
* 会让 TESTSET 与主链真相脱节。

## 11.2 方案 B：只输出裸 `test-set.yaml`

不采纳。

原因：

* 无法表达 governed package；
* 无法承载 review / acceptance / evidence / freeze / handoff；
* 无法稳定对接 ADR-007。

## 11.3 方案 C：把 analysis / strategy 升格为新 SSOT 对象

不采纳。

原因：

* 会重新发明 `TESTPLAN` 类对象；
* 与 ADR-008 的对象收敛原则冲突；
* 会造成 package 内 companion artifact 与正式对象边界再次混层。

## 11.4 方案 D：把 3 个 human gate 重新内嵌进 skill

不采纳。

原因：

* 违反 ADR-006 的 gate 外置原则；
* 违反 ADR-009 的 CLI-first runtime 承载原则；
* 会让 skill 重新承担最终治理裁决职责。

## 11.5 方案 E：强制依赖 TECH 先存在

不采纳。

原因：

* `TESTSET` 是 FEAT 的直接派生对象，不是 `TECH` 的子对象；
* TECH 可以补强，但不能成为 TESTSET 存在的前置合法性来源；
* 否则会把 FEAT 派生链错误串成伪主链。

---

# 12. 结果与影响

采用本 ADR 后，LL 将获得：

* 一个明确的 `feat_freeze_package -> test_set_freeze_package` 派生边界；
* 单 FEAT、单 TESTSET 的稳定运行模型；
* 与 ADR-007 测试执行链可直接对接的正式主对象；
* analysis / strategy 作为 companion artifact 的清晰定位；
* QA 模板中 3 个 human gate 的外置承载方式；
* 与 ADR-008 一致的 FEAT 派生对象边界；
* 与 ADR-006、ADR-009 一致的 gate / runtime 纪律。

代价是：

* package 结构会比单个 YAML 更重；
* human gate 外置后，需要 gate runtime 补足 materialization；
* analysis / strategy / review / freeze 的工件数量增加。

但这些复杂度属于：

## **为了让 TESTSET 成为正式可治理对象所必须显式化的成本，而不是可以继续省略的文档包装。**

---

# 13. 后续行动

本 ADR 通过后，后续实施应按以下顺序推进：

1. 使用 `ll-meta-skill-creator` 脚手架生成 `skills/ll-qa-feat-to-testset/`
2. 冻结 `ll.contract.yaml`
3. 冻结 `input/contract.yaml` 与 `output/contract.yaml`
4. 冻结 `test-set.yaml` 主对象 schema
5. 冻结 `test_set_candidate_package` / `test_set_freeze_package` schema
6. 冻结外置 gate decision artifact 与 gate subject 的最小 schema
7. 实现 `feat_to_testset.py` lite-native runtime
8. 明确 analysis / strategy / review / approval 对应的 gate subject 与 external materialization 接缝
9. 对接 ADR-007 所需的 `handoff-to-test-execution.json`

这里的实施优先级故意把 schema 放在 runtime 之前，原因是：

* 本 ADR 最重要的是对象边界，不是脚本入口；
* 边界应由 schema 与 validator 固化，而不应由 runtime 反向塑形。

在这些文件与验证脚本落地前，不应宣称 FEAT-to-TESTSET governed skill 已完成正式冻结实现。
