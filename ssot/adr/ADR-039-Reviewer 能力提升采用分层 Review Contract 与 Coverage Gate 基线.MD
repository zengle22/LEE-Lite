# ADR-039：Reviewer 能力提升采用分层 Review Contract 与 Coverage Gate 基线

* 状态：Draft
* 日期：2026-04-02
* 决策者：Le Zeng
* 适用范围：全部依赖 review / test / gate judgement 的 governed workflow，尤其适用于 `gate review`、`supervisor review`、`document test`、`impl-spec-test` 与其它文档型审查链路
* 相关 ADR：ADR-006、ADR-015、ADR-033、ADR-036、ADR-037、ADR-038

---

# 1. 背景

仓库已经逐步冻结了几层与 review 相关的能力：

* ADR-015 冻结了 `Machine SSOT + Human Review Projection` 双层表达模型；
* ADR-033 冻结了 external gate 前的 `Document Test` 验证层；
* ADR-036 冻结了 `IMPL` 实施前的 `Implementation Spec Testing` 压力测试层；
* ADR-037 开始把质量问题沉淀为 `failure_case / diagnosis / remediation / regression` 等治理对象；
* 多条主链与派生链已经有 `review report`、`gate decision`、`evidence`、`projection`、`readiness verdict` 等正式产物。

这些能力解决了一个重要问题：

> **review 已经存在，而且 review 不再只靠口头流转。**

但近期多轮运行仍持续暴露出 reviewer 的第二层问题：

> **reviewer 到底是在按什么标准审。**

现在系统里最常见的退化，不是“完全没人 review”，而是：

* review 通过了，但人复盘时才发现关键维度根本没被检查；
* reviewer 能发现显眼错误，却抓不住静默偏航；
* 同一个问题在不同 skill / 不同 artifact 上忽而算 blocker、忽而只算 warning；
* review report 输出了 findings，但没有说明哪些维度审过、哪些维度没审；
* 为了补漏，最自然的冲动是“再加一个 reviewer”或“再加一条 prompt”，但判题标准仍未显式建模。

这说明当前缺失的，不是 reviewer 数量，而是：

## **review 的判题标准、覆盖范围与升级规则还没有被正式对象化。**

换句话说，ADR-015 解决的是：

* reviewer 看什么更容易理解。

但当前系统仍未正式回答：

* reviewer 应该按什么规则判断；
* 什么问题在当前阶段算 blocker；
* 哪些维度必须被覆盖；
* 哪些风险允许留到后续阶段；
* 不同 artifact family 应该套哪一组审查重点。

因此，需要一份新的 ADR，把 reviewer 能力提升正式从“更会看文档”升级为“按显式 contract 执行判断”的治理基线。

---

# 2. 问题陈述

当前真正需要回答的，不是“reviewer 提示词还要不要更强”，而是以下结构性问题。

## 2.1 没有显式判题标准，review 会退化为感觉审阅

如果系统没有正式定义：

* 需要检查什么；
* blocker / warning / info 的升级规则；
* 哪些问题必须在这个阶段暴露；
* 哪些问题可以安全后移；

那么 reviewer 最终只能按：

* 看起来顺不顺；
* 语义像不像对；
* 有没有明显缺字漏项；

这类自然语言直觉来判断。

这种 review 最多擅长发现：

* 显眼错误；
* 表面不通顺；
* 明显缺段。

它最容易漏掉的，恰恰是高返工成本的问题：

* 范围悄悄变了；
* 默认假设变了；
* 状态机少了边；
* 契约没有真的落到实现；
* 输出形式像对的，但核心口径已经漂移。

## 2.2 blocker 没有统一升级原则，就无法稳定门禁

如果 blocker 完全靠 reviewer 当场自由发挥，就会出现：

* 同类问题在不同 review run 中分级不一致；
* 某个 reviewer 把“高返工风险问题”降成 warning；
* 某个 reviewer 把“可延后优化项”误判成 blocker；
* gate 无法理解 findings 背后的真正风险边界。

系统真正缺的是一条全局可复用的升级原则，而不是越来越多的局部经验。

## 2.3 没有 coverage 声明，漏审会静默发生

当前许多 review report 只输出：

* findings
* verdict
* 建议动作

但不输出：

* 这次到底审了哪些维度；
* 哪些维度只做了部分检查；
* 哪些 required checks 根本没审。

结果就是：

* reviewer 以为自己审过了；
* gate 以为 review 已经覆盖了关键风险；
* 人复盘时才发现 failure handling、migration impact、state closure 之类的维度根本没有进入审查面。

这是一种比“发现问题”更危险的失败形式：

## **系统误以为自己已经审过。**

## 2.4 reviewer 没有 oracle，就只能看文本表面

reviewer 之所以经常抓不到静默偏航，不只是因为 checklist 不够，还因为它没有稳定参照系。

当前常见缺口是：

* 没把上游 SSOT 当成 source oracle；
* 没把对象 / 状态 / 约束结构当成 structural oracle；
* 没把给定输入下的预期行为当成 behavioral oracle；
* 没把“绝对不允许发生什么”当成 negative oracle。

没有 oracle，reviewer 就容易只看文档表面，而不是判断：

* 是否冲突；
* 是否缺失；
* 是否歧义；
* 是否违背禁止项。

## 2.5 不能把解法退化成“一 Skill 一套 review contract”

如果为了补上显式标准，而把系统设计成：

* `Skill A -> Contract A`
* `Skill B -> Contract B`
* `Skill C -> Contract C`

那么很快就会走向：

* 维护爆炸；
* 合同过期；
* 没人真的更新；
* 规则越来越多但现场问题仍抓不住。

因此，本 ADR 必须同时解决两个问题：

1. review 标准必须显式化；
2. review 标准又不能碎成每个 skill 一份私有宪法。

## 2.6 本 ADR 不解决什么

本 ADR 明确不试图解决以下问题：

* 不试图让 reviewer 一次性替代 domain expert；
* 不试图把所有 review 经验编码成完整规则库；
* 不试图在第一阶段统一所有 governed workflow；
* 不要求所有 findings 都结构化到同一粒度；
* 不把 `Review Contract` 当作新的业务 SSOT；
* 不把 `coverage` 当作正确性证明。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **面向 reviewer 的分层 Review Framework**

这是系统的长期收敛模型，不是 phase 1 的完整交付清单。

该框架由以下三层组成：

1. `Global Review Escalation Policy`
   定义全平台通用 blocker 原则与最低质量门槛。
2. `Artifact Family Rules`
   按 `SRC / EPIC / FEAT`、`TECH / ARCH / API / UI`、`IMPL`、`TESTSET` 等 artifact family 定义必审维度。
3. `Risk Profiles`
   只为少量高风险场景追加更严格的检查重点；第一阶段仅冻结 `default`、`contract_sensitive`、`workflow_sensitive` 三类 profile。

同时正式冻结：

## **每次 review 都必须基于派生得到的 Review Contract 执行，并且必须输出 Coverage Declaration，而不允许只输出 findings。**

这里的“基于 Review Contract 执行”在 phase 1 可以由硬编码 routing、固定 reviewer 模板或轻量 gate adapter 承载，不要求一开始就有完整独立的 contract runtime。

一句话定义：

> **Projection 解决“看什么”，Review Contract 解决“按什么判”，Coverage 解决“到底审到哪里”。**

## 3.1.1 Phase 1 的唯一强制项

第一阶段只强制两件事：

* review 必须输出 `Coverage Declaration`；
* gate 必须识别 `not_checked` 和 `blocker_count > 0` 并阻断推进。

其余能力在 phase 1 只能作为 `recommended but not mandatory`：

* 完整的 oracle 分类；
* 完整的 contract assembly；
* 完整的 challenge loop；
* profile 扩展；
* exception rule 常驻化；
* 任何超出最小覆盖词表的自定义扩展。

---

## 3.2 全局 blocker 原则

本 ADR 正式冻结 reviewer 的全局 blocker 升级原则为：

## **凡是会让下游在“看起来合理”的前提下继续做错的，都是 blocker。**

这条原则用于统一不同 reviewer、不同 stage、不同 skill 的风险边界。

它至少覆盖以下情况：

* 与上游 SSOT 冲突；
* 缺少关键对象、关键状态、关键约束或关键输入输出定义；
* 存在足以导向两种不同实现的关键歧义；
* 改变了关键口径，但没有显式声明为 intentional change；
* 验收标准不可验证；
* 缺少必要失败路径；
* 引用了不存在的依赖、契约、接口或 artifact；
* 会让后续阶段低成本通过、高成本返工。

相对地，`warning` 的统一口径是：

* 当前不改也能继续；
* 不会造成口径漂移；
* 不会诱导下游实现错误；
* 主要影响质量，不直接影响方向。

---

## 3.3 分层规则模型

### 3.3.1 Global Review Escalation Policy

平台级规则只维护少量稳定原子，不随单个 skill 漂移。

第一阶段建议控制在 `10` 条以内，并至少包含：

* `conflicts_with_upstream_ssot`
* `missing_required_object`
* `missing_required_state_or_transition`
* `ambiguous_contract`
* `unverifiable_acceptance`
* `silent_scope_expansion`
* `missing_required_failure_path`
* `reference_to_nonexistent_dependency`

这层回答的是：

> **什么情况下，无论 reviewer 是谁、artifact 是什么，都不允许静默推进。**

### 3.3.2 Artifact Family Rules

review 的大部分差异，不来自 skill 名字，而来自 artifact family。

因此，系统不按 skill 分裂规则，而按 artifact family 复用规则。

第一阶段冻结以下 4 类模板：

* `src_or_feat`
  * 重点检查目标清晰度、范围闭合、核心对象定义、验收可测性、上游一致性。
* `tech_or_ui`
  * 重点检查状态机闭合、契约完整性、边界条件、错误路径、跨对象一致性。
* `impl`
  * 重点检查实施契约是否落地、是否静默扩 scope、关键保护逻辑是否缺失、证据链是否完整。
* `testset`
  * 重点检查关键路径覆盖、失败路径覆盖、测试与契约绑定、测试能否真正证明达成。

### 3.3.3 Risk Profiles

profile 只针对高风险场景叠加，不重写整套规则。

第一阶段仅正式支持：

* `default`
  * 普通 review 路由。
* `contract_sensitive`
  * 对接口、schema、状态机、canonical field、authority binding 更严格。
* `workflow_sensitive`
  * 对多步流转、handoff、状态推进、失败恢复、更换主语等更严格。

新增 profile 的门槛如下：

* 必须证明现有 profile 不能通过复用、组合或少量 exception rule 表达该差异；
* 必须由该 governed workflow 的 owner 与 ADR 决策者共同确认；
* 必须记录为什么不能优先复用旧 profile；
* 必须明确该 profile 相对现有 profile 增加了什么判定差异。

profile 的组织约束如下：

* phase 1 冻结的正式 profile 总数不超过当前已列出的 `3` 个；
* 默认优先复用旧 profile，而不是新建 profile；
* 新增 profile 必须是例外，不是常态；
* 任何新增 profile 都应先尝试回收到 `artifact family rule` 或 `exception rule`；
* 如果一个新 profile 只服务单个 skill 且不能复用到其他 artifact family，默认视为设计失败信号。

本 ADR 明确禁止：

## **为每个 skill 维护一整套独立 review 宪法。**

skill 最多只允许：

* 声明自己的 `artifact_type`；
* 选择 0 到 2 个 `risk profile`；
* 在极少数情况下追加 `1-3` 条 exception rule。

### 3.3.4 Exception Rules

exception rule 是允许存在的，但它们必须满足以下条件：

* 只能是临时性的补丁，而不是长期常驻私法；
* 必须可审计，能够追溯是谁加的、为什么加、什么时候复核；
* 必须优先回流到 `Global Review Escalation Policy`、`Artifact Family Rules` 或 `Risk Profiles`；
* 必须带有明确的复核点或失效点；
* 不得无限累积，不得通过堆 exception 规避规则收敛。

---

## 3.4 人、AI 与机器的职责分层

本 ADR 正式冻结 reviewer 能力建设中的职责边界。

### 人定义

人负责定义：

* 风险边界；
* blocker 升级规则；
* 各类 artifact 的 minimum bar；
* 不可违反的 negative constraints；
* 哪些问题允许留到后续阶段。

### AI 实例化

AI reviewer 负责基于当前 review context 实例化：

* 当前任务下的具体检查项；
* 当前任务的重点疑点列表；
* 当前任务的 coverage blind spots；
* 当前任务下 blocker / warning 的具体 findings。

### 机器执行

机器负责执行固定格式与 gate 规则，例如：

* `Review Contract` 的结构化生成；
* `Coverage Declaration` 的必填校验；
* required checks 未覆盖时阻断推进；
* blocker 数量非零时阻断推进；
* review artifact 的落盘与 traceability。

正式原则：

## **人定义判定框架，AI展开当前任务检查项，机器负责强制执行输出与门禁。**

---

## 3.5 Review Contract 作为派生治理对象

本 ADR 新增一类正式治理对象：

## **Review Contract**

它不是新的业务真相源，也不是新的 skill 私有文档。
它不得承载新的领域语义，只能组合既有规则并实例化本次 review。

它的定位是：

* 一次 review run 的治理判题合同；
* 由 `Global Review Escalation Policy + Artifact Family Rules + Risk Profiles + current metadata` 派生生成；
* 用于约束 reviewer 的判断面、coverage 输出与 gate 行为。

对首阶段实现者需要明确：

* `Review Contract` 是目标治理对象；
* phase 1 可以先把它落成 reviewer 模板内嵌配置、gate 侧硬编码映射或轻量 JSON/YAML 片段；
* phase 1 不要求先做出完整独立的 contract assembly runtime，再开始落地 coverage gate。

在完整形态下，它至少应表达：

* `derived_from`
* `artifact_type`
* `review_profiles`
* `required_checks`
* `blocker_if`
* `warning_if`
* `required_oracles`
* `must_report_coverage`
* `must_run_stages`

最小结构可收敛为：

```yaml
derived_from:
  global_review_escalation_policy: global_review_escalation_policy_v1
  artifact_family_rule_set: impl_v1
  risk_profiles:
    - default
    - workflow_sensitive

artifact_type: impl
review_profiles:
  - default
  - workflow_sensitive

required_checks:
  - ssot_alignment
  - object_completeness
  - contract_completeness
  - state_transition_closure
  - failure_path
  - testability

blocker_if:
  - conflicts_with_upstream_ssot
  - missing_required_object
  - ambiguous_contract
  - silent_scope_expansion
  - unverifiable_acceptance

warning_if:
  - naming_inconsistency
  - weak_rationale
  - optional_edge_case_missing

required_oracles:
  - source
  - structural
  - negative

must_report_coverage: true
must_run_stages:
  - extract
  - coverage
  - judge
  - challenge
```

phase 1 如果暂时不显式落单独 contract 文件，至少也应保证以下信息在 reviewer carrier 或 gate carrier 中可追溯：

* `artifact_type`
* `derived_from`
* `required_checks`
* `blocker_if`
* `must_report_coverage`

---

## 3.6 Review Oracle 正式分类

本 ADR 正式冻结 review 中可复用的 `oracle` 分类。

但对首阶段团队需要再强调一次：

* `oracle` 分类是推荐采用的统一抽象；
* phase 1 不要求把四类 oracle 全部产品化为独立对象；
* phase 1 只要求 reviewer 能说明自己依赖了哪些参照系，以及这些参照系如何支撑 findings。

### A. Source Oracle

上游 SSOT、冻结对象、正式 contract、authority artifact。

用于判断：

* 是否冲突；
* 是否遗漏；
* 是否漂移；
* 是否把 projection / commentary 冒充 authority。

### B. Structural Oracle

对象、状态、约束、输入输出 schema、required fields、state transition。

用于判断：

* 结构是否闭合；
* 是否缺关键节点；
* 是否缺关键边；
* 是否存在结构级歧义。

### C. Behavioral Oracle

给定输入、上下文或前提下，系统应该如何行动。

用于判断：

* happy path 是否真的闭合；
* failure path 是否合理；
* 不同文档对同一行为的解释是否一致。

### D. Negative Oracle

系统明确禁止发生的事。

例如：

* 不得静默扩 scope；
* 不得把建议型输出冒充为已更新状态；
* 不得默认继承未明示的历史实现细节；
* 不得在 authority 冲突时自创第三真相。

本 ADR 要求：

## **高质量 review 不只检查“应该有什么”，还必须检查“绝对不应该发生什么”。**

---

## 3.7 四段式审查执行模型

reviewer 的正式执行顺序冻结为四段式。

### Step 1：Extract

先抽取结构，不做裁决。

至少提取：

* 核心对象；
* 状态与状态变化；
* 输入输出；
* 约束；
* 假设；
* 未定义项；
* 与上游 authority 的绑定点。

### Step 2：Coverage

声明这次 review 覆盖了哪些维度，哪些只做了部分检查，哪些没审。

至少使用三态：

* `checked`
* `partial`
* `not_checked`

### Step 3：Judge

基于 `Review Contract`、`oracles` 与平台 blocker 原则，输出：

* `blocker`
* `warning`
* `info`
* `verdict`

Judge 的输出必须是结构化 findings，而不是散落在 prose 里的评论。

### Step 4：Challenge

执行专门的对抗式追问，而不是重复总结。

典型 challenge 包括：

* 这里有没有偷偷扩 scope；
* 这里是不是默认继承了旧实现；
* 这里是不是把建议伪装成闭环动作；
* 这里输入缺失会怎样；
* 这里是否存在两种都讲得通的解释。

正式原则：

* `Challenge` 输出 `challenge_questions` 和 `triggered_suspicion`；
* `Challenge` 不直接改 `verdict`；
* 只有当 `Challenge` 产生新的 `finding`，才需要回到 `Judge` 重新裁决。

## **Judge 负责结构化分类问题，Challenge 负责逼出新的怀疑点。**

---

## 3.8 Coverage Declaration 成为必交对象

本 ADR 明确规定：

## **review 不再只交 findings，必须同时交 coverage。**

Coverage 是对审查范围的声明，不是对正确性的证明。

phase 1 先只允许以下最小公共维度词表：

* `ssot_alignment`
* `object_completeness`
* `contract_completeness`
* `state_transition_closure`
* `failure_path`
* `testability`

在 phase 1 中，不在这个词表内的维度名一律视为自定义扩展，默认不进入强制门禁。

最小形态如下：

```yaml
coverage:
  ssot_alignment: checked
  object_completeness: checked
  contract_completeness: partial
  state_transition_closure: checked
  failure_path: not_checked
  testability: checked
```

对应 gate 规则如下：

1. `required_checks` 中出现 `not_checked`，不得静默通过。
2. `required_checks` 中只要存在 `partial`，必须给出理由与后续动作。
3. `blocker` 非零时，不得给出可推进 verdict。
4. 未提交 coverage 的 review report 视为不完整证据，不得进入 formal gate judgement。

这条规则的目标不是让 reviewer 更繁琐，而是让“没审到”从静默失败变成显式暴露。

---

## 3.9 Review Routing 正式收敛方式

为了避免一开始就落成庞大的 knowledge engineering 项目，本 ADR 同时冻结一条工程收敛原则：

## **先做 review routing 与 contract assembly，再逐步深化规则细节。**

第一阶段只要求系统能基于：

* `artifact_type`
* 是否 `contract_sensitive`
* 是否 `workflow_sensitive`

自动选择：

* 哪套 reviewer 模板；
* 哪组 required checks；
* 哪些 finding 默认升为 blocker；
* 哪组 oracle 必须被使用。

也就是说，skill 不维护审查规则正文，skill 只挂标签。
第一阶段里，`review routing` 和 `contract assembly` 本身也属于 recommended but not mandatory 的实现项，不应被解释成必须一次性全量完成。

---

# 4. 与现有 ADR 的关系

## 4.1 与 ADR-015 的关系

ADR-015 解决的是 `Human Review Projection`。

它回答：

* reviewer 更容易看懂什么。

本 ADR 解决的是 `Review Contract` 与 `Coverage Declaration`。

它回答：

* reviewer 应该按什么标准审；
* 哪些维度必须覆盖；
* findings 如何升级。

二者关系固定为：

> **Projection 提供可读视图，Review Contract 提供判题规则。**

## 4.2 与 ADR-033 的关系

ADR-033 把 `Document Test` 定义为 skill 内完整验证 phase。

本 ADR 不替代 `Document Test`，而是约束其 reviewer / tester judgement 层：

* Document Test 可以继续产出 defect、readiness、recommended next action；
* 但其 judgement 也必须逐步迁移到显式 `Review Contract + Coverage` 模型。

## 4.3 与 ADR-036 的关系

ADR-036 定义了 `qa.impl-spec-test` 的定位与测试维度。

本 ADR 为它补上：

* 哪些测试维度属于 required checks；
* 哪些冲突默认升为 blocker；
* impl-spec review 必须如何声明 coverage；
* `IMPL` 开工前的审查不得只给建议、不交覆盖面。

## 4.4 与 ADR-037 的关系

ADR-037 关注失败资产化与双环治理。

本 ADR 关注 reviewer 本身的判断质量。

二者结合后，系统可以进一步把 failure case 归因为：

* 生成失败；
* 检测失败；
* review routing 错误；
* coverage 缺失；
* blocker 升级错误。

## 4.5 与 ADR-038 的关系

ADR-038 冻结了 authority 与 carrier 的边界。

本 ADR 在 review 维度继续沿用同一原则：

* `Review Contract` 是治理 authority；
* reviewer prompt / template / script 只是 carrier；
* skill 名字不能反向定义 review authority。

---

# 5. 工程落地建议

## 5.1 MVP

第一阶段不追求完整 review expert system，只做最小闭环。

Phase 1 真正强制落地的只有：

* `Coverage Declaration` 必须输出；
* gate 必须识别 `not_checked` / `blocker_count > 0` 并阻断推进。

其它能力都先按 `recommended but not mandatory in phase 1` 处理。

### 5.1.1 Phase 1 最小实施清单

首落地团队只需要完成以下 3 步：

1. 统一 coverage 最小公共词表。
2. 让 reviewer 在每次 review 中输出 coverage。
3. 让 gate 对 `missing coverage`、`not_checked`、`blocker_count > 0` 做稳定阻断。

如果这 3 步尚未完成，不应继续扩展 profile、exception rule 或独立 contract runtime。

### 5.1.2 Phase 1 推荐配套交付物

以下交付物有助于稳定扩展，但不属于 phase 1 唯一强制项：

* 1 份 `Global Review Escalation Policy`
* 4 份 `Artifact Family Rules`
* 3 份首批 `profile`
* 1 个最小 `Review Contract` 组装器
* 1 份 `Coverage Declaration` 标准输出格式

### 5.1.3 第一阶段 artifact family 模板

* `src_or_feat`
* `tech_or_ui`
* `impl`
* `testset`

### 5.1.4 第一阶段 profile

* `default`
* `contract_sensitive`
* `workflow_sensitive`

### 5.1.5 第一阶段 gate 规则

* `missing coverage -> block`
* `required check = not_checked -> block`
* `blocker_count > 0 -> block`
* `coverage` 只按 phase 1 最小公共维度词表解析

### 5.1.6 第一阶段不建议做的事

* 不为每个 skill 写独立 review 宪法；
* 不一开始就维护大量 exception rules；
* 不把所有 reviewer 经验都塞成超大规则库；
* 不让 prose findings 替代结构化 coverage；
* 不把 phase 1 解释成必须完成完整 review expert system。

## 5.2 推荐推进顺序

1. 先统一全局 blocker 原则。
2. 再冻结 4 类 artifact 模板。
3. 再补 2 个高风险 profile。
4. 然后让 `Document Test` 与 `impl-spec-test` 优先接入。
5. 最后再把其它 review-heavy workflow 迁移过来。

---

# 6. 结果预期

## 阶段 1

review 从“只给意见”升级为“给意见 + 给 coverage”。

## 阶段 2

reviewer 对 blocker / warning 的分级开始稳定，漏审从静默变成显式。

## 阶段 3

failure case 可以明确归因到：

* 规则缺失；
* profile 选错；
* oracle 不足；
* coverage 未达标；
* reviewer 执行不完整。

## 阶段 4

review 开始从“发现显眼错误”进化到“提前拦截静默偏航”。

---

# 7. 明确反模式

## 7.1 把 reviewer 数量增长当成 reviewer 能力建设

多一个 reviewer，不会自动补出判题标准。

## 7.2 把 prompt 变长当成 contract 显式化

prompt 可以承载 carrier，但不能替代治理对象。

## 7.3 把 finding 列表当成 coverage

有 findings，不等于 required dimensions 已经覆盖。

## 7.4 把 skill 名字当成规则来源

skill 只能挂载 rule 组合，不能私有化 review 法律体系。

## 7.5 只检查正向期望，不检查 negative oracle

这会让 silent drift 长期逃逸。

---

# 8. 一句话结论

## **reviewer 能力提升的关键，不是再加 reviewer，而是把 review 从“自然语言读后感”升级为“基于分层 Review Contract 的覆盖式判题系统”。**
