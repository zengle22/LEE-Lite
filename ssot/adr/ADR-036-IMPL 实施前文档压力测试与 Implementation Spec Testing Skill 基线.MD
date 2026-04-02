# ADR-036：IMPL 实施前文档压力测试与 Implementation Spec Testing Skill 基线

* 状态：Draft
* 日期：2026-04-01
* 决策者：Le Zeng
* 适用范围：`qa.impl-spec-test` workflow、`ll-qa-impl-spec-test`、`feature_impl_candidate_package`、`impl_spec_test_report_package`、implementation start 前 gate
* 相关 ADR：ADR-014、ADR-033、ADR-034、ADR-035

---

# 1. 背景

当前仓库已经基本串起并冻结了从上游需求到实施前输入准备的主链：

* `ADR -> SRC -> EPIC -> FEAT`
* `FEAT -> ARCH / TECH / API / UI / TESTSET`
* `TECH -> IMPL`

其中：

* ADR-014 已冻结 `TECH -> IMPL` 的 task-first 派生边界；
* ADR-033 已冻结 external gate 前的 skill internal document test 验证层；
* ADR-034 已进一步冻结 `IMPL` 是 execution-time single entrypoint，而不是新的设计真相源；
* ADR-035 已把 `TESTSET` 的职责收敛到需求覆盖与 traceability contract。

但主链补齐以后，真正最危险的一步开始前移到了：

## **`IMPL` 已经生成，看起来引用也齐全，但它是否真的足够清晰、足够自包含、足够一致，能安全交给 AI coder 直接开工。**

目前仓库还缺一层专门面向这个问题的正式 skill。

如果没有这层，系统会继续暴露出一类非常典型的实施前风险：

* `IMPL` 虽然完整，但与 `FEAT / TECH / API / UI / TESTSET` 之间仍有隐性冲突；
* 页面、状态机、API、数据模型分别都“看起来合理”，但拼起来以后链路断裂；
* happy path 说得很顺，但失败态、恢复态、兼容迁移态没有闭环；
* 文档表面上能读懂，但 coder 一旦进入具体编码，会在模块边界、字段真相源、状态更新时机、前后端契约来源上各自做出不同理解；
* tester 无法从 `IMPL` 和上游对象稳定派生出验收与失败路径测试；
* 最终实现并不是“文档没写完”，而是“AI 基于歧义实现了另一套系统”。

因此，需要一份新的 ADR，把：

* `IMPL` 实施前文档压力测试层的角色；
* 与 ADR-033 Document Test 的关系；
* 与 ADR-034 `IMPL` 自包含执行包语义的接缝；
* 测试维度、输出 contract、gate verdict 与阻断规则；
* 该层在主链中的插位

统一冻结为正式基线。

---

# 2. 问题陈述

当前真正需要回答的，不是“文档是不是写完了”，而是下面几个更结构性的实施前问题。

## 2.1 完整性检查不等于可实施性检查

如果只检查：

* 有没有 API
* 有没有 UI
* 有没有状态机
* 有没有 acceptance

那么最多只能说明文档“元素齐了”，不能说明：

* 这些元素能不能被 AI 稳定拼成同一套系统；
* 下游是否会在实现中途暴雷；
* coder / tester / reviewer 是否会读取出一致的实施主语。

## 2.2 单文档检查无法发现跨文档冲突

`IMPL` 的真实风险很多不在单点，而在链路：

* `FEAT` 的产品行为主语与 `IMPL` 的执行主语漂移；
* `TECH` 的 canonical field / state model 与 `API` contract 使用方式冲突；
* `UI` 声称 non-blocking，但 `API / state / journey` 实际仍阻塞；
* `TESTSET` 验的对象与 `IMPL` 定义的完成态不是同一个东西。

如果不把 `IMPL` 与 `FEAT / TECH / ARCH / API / UI / TESTSET` 联动检查，很多问题直到编码或联调时才会出现。

## 2.3 失败路径缺失比 happy path 漏写更危险

当前很多实施文档的默认倾向仍是：

* 先把成功链讲顺；
* 失败态、部分失败、重试、回退、兼容旧系统等以后补。

但对于 AI 实施来说，真正容易导致返工的，往往不是 happy path，而是：

* 保存成功但 completion 未更新；
* 风险门槛未通过但 UI 没有恢复动作；
* 网络失败后状态半写入；
* 设备连接失败后主链是否继续；
* 新旧字段或新旧状态并存时谁优先。

## 2.4 `IMPL` 需要一份可执行的 readiness verdict，而不是抽象建议

如果最后只输出：

* 有风险
* 建议优化
* 需要补充

这种结果很难进入主链治理。

真正需要的是：

* 问题分级
* 影响范围
* 修复动作
* 是否阻断实施
* 最终 gate verdict

否则 external gate、execution runner 和 human reviewer 都无法稳定消费。

## 2.5 需要一层专门保护产品行为主语的实施前测试

`IMPL` 非常容易从产品行为主语，滑回：

* 治理主语
* 流程主语
* 实现主语

一旦发生这种漂移，下游 coder 虽然能写出代码，但写出来的不一定是产品想要的行为链。

因此，这层 skill 必须显式检查：

## **`IMPL` 是否仍然忠于产品行为主语，而不是仅仅忠于实施便利性。**

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一套位于 `IMPL -> implementation start` 之间的 `Implementation Spec Testing` governed skill 基线**

其正式 workflow key 为：

* `qa.impl-spec-test`

其建议 skill 名称为：

* `ll-qa-impl-spec-test`

该 skill 的核心目标不是文档 lint，也不是再做一轮泛化 review，而是：

## **在编码前，把 `IMPL` 当成待上线系统的纸面原型，做一次多维度文档级预演与找茬，并给出是否允许进入实施的 gate verdict。**

## 3.2 定位

本 ADR 正式冻结该 skill 的定位为：

## **面向 `IMPL` 的实施前文档压力测试层**

它负责回答的核心问题固定为：

## **这份 `IMPL` 能不能安全交给 AI coder 开工，且大概率不会在实施中途因为文档歧义、链路断裂或失败路径缺失而暴雷。**

因此它：

* 是 ADR-033 Document Test 的一个专业化、IMPL 定向化子类；
* 直接服务于 ADR-034 所定义的 `IMPL` 自包含执行包；
* 以 `FEAT / TECH / ARCH / API / UI / TESTSET` 的联动一致性为主要测试面；
* 以 implementation readiness 为结果导向。

它不是：

* 文档 lint 工具；
* 第二层技术设计；
* repo 代码层静态分析器；
* external gate 的替代；
* 实际运行代码后的执行测试。

## 3.2A 主测试对象优先级与越权边界

`qa.impl-spec-test` 的主测试对象优先级固定为：

1. 主测试对象是 `IMPL`
2. `FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority
3. repo context 仅作为辅助上下文

同时冻结以下硬边界：

## **`qa.impl-spec-test` may detect and escalate cross-artifact conflicts, but must not establish new business truth or design truth when authoritative upstream objects disagree.**

这意味着：

* 它可以发现并升级 `API` 与 `UI` 的冲突；
* 它可以发现并升级 `TECH` 与 `IMPL` 的 canonical field 冲突；
* 它可以建议修复应回到 `FEAT / TECH / API / UI / TESTSET`；
* 但它不得在报告里偷偷补出新的 authoritative 设计结论来替代上游对象。

## 3.3 主链插位

本 skill 的正式插位固定为：

* `ADR / SRC / EPIC / FEAT`
* `FEAT -> ARCH / TECH / API / UI / TESTSET`
* `TECH -> IMPL`
* `qa.impl-spec-test`
* implementation start / `template.dev.feature_delivery_l2`

正式原则：

1. `qa.impl-spec-test` 在 `IMPL` 已生成且引用可解析后运行。
2. 未通过该层的 `IMPL` 不得自动 dispatch 进入 coder 主链。
3. 若系统存在 external gate，则 external gate 仍保持 authoritative decision；`qa.impl-spec-test` 提供的是 implementation-readiness verdict 与修复建议，而不是替代 gate 的最终裁决。

## 3.4 两种运行模式

本 ADR 冻结该 skill 至少支持两种模式：

### Mode A：`quick_preflight`

用于快速筛查。

最小输出必须包括：

* `verdict`
* `implementation_readiness`
* `blocking_issues`
* `missing_information`
* `recommended_next_action`

### Mode B：`deep_spec_testing`

用于重要功能或高风险链路。

必须完整执行：

* 8 个测试维度
* 跨文档冲突检测
* 失败路径推演
* 用户旅程模拟
* UI / API / state mapping 分析
* counterexample 场景测试

## 3.4A 模式触发规则

默认允许人工或 runtime 显式选择模式，但以下任一条件成立时，必须运行 `deep_spec_testing`：

* `migration_required = true`
* 存在 canonical field、canonical ownership 或 state boundary 敏感 FEAT
* 存在跨页面主链加后置增强链
* 本次 `IMPL` 新引入 `UI / API / state` 任一主对象
* 当前对象是 external gate 前的最后一个 implementation candidate

运行时不得因为默认快捷而在上述场景下降级为 `quick_preflight`。

---

# 4. 核心原则

## 4.1 测可实施性，不只测完整性

该 skill 不只检查“有没有写”，而要检查：

* AI 是否能据此稳定落地；
* 哪些地方会诱发实现分叉；
* 哪些信息缺失会迫使下游重新发明设计。

## 4.2 测链路，不只测单点

`IMPL` 不是单独评价对象。

正式要求：

* 必须联动检查 `FEAT`
* 必须联动检查 `TECH`
* `ARCH / API / UI / TESTSET` 存在时必须联动检查
* 问题允许判定为“单文档都对，但连起来错”

## 4.3 测失败模式，不只测 happy path

对于状态机、数据写入、用户旅程和 API 契约：

* 非法输入
* 半成功
* 局部失败
* 可恢复
* 可重试
* 回退
* 兼容旧系统

都必须进入正式测试面。

## 4.4 测产品行为主语

该 skill 必须显式检查：

* `IMPL` 是否仍然承接产品行为而不是实施便利性；
* 是否把邻近 FEAT 的职责意外吸收进来；
* 是否把治理或流程话语替代了用户行为链。

## 4.5 输出必须可执行

所有重要问题都必须至少给出：

* 问题标题
* 影响
* 证据
* 修复动作
* 优先级
* 是否阻断实施

## 4.6 最终必须给 gate verdict

该 skill 的标准结论不是摘要，而是以下之一：

* `pass`
* `pass_with_revisions`
* `block`

---

# 5. 测试维度

本 ADR 正式冻结该 skill 至少覆盖以下 8 个维度，并产出 0 到 10 的 dimension score。

## 5.1 `functional_logic`

检查：

* `IMPL` 是否完整承接 `FEAT` 的功能目标；
* 功能入口、出口、成功条件是否明确；
* 是否遗漏关键业务动作；
* 是否错误吸入相邻 FEAT 责任；
* 是否存在功能闭环不成立。

典型问题类型：

* `functional_chain_gap`
* `feature_responsibility_overreach`
* `closure_not_achieved`

## 5.2 `data_modeling`

检查：

* canonical field / entity owner 是否明确；
* 状态机是否合法、可达、可恢复；
* 状态与字段含义是否一致；
* 是否存在双写、双真相源、暗中替代状态字段；
* 是否存在未定义中间态或异常态。

典型问题类型：

* `canonical_ownership_conflict`
* `illegal_state_transition_gap`
* `completion_derivation_ambiguity`

## 5.3 `user_journey`

检查：

* 首进、首次完成、继续补全、失败恢复等主旅程是否完整；
* 页面之间的前后衔接是否成立；
* 用户在失败后是否知道下一步怎么做；
* non-blocking 声明是否在旅程中真实成立。

典型问题类型：

* `journey_dead_end`
* `recovery_path_missing`
* `next_step_ambiguity`

## 5.4 `ui_usability`

检查：

* 页面类型与交互角色是否匹配；
* CTA 优先级是否清楚；
* 错误反馈是否可理解；
* 是否存在隐性阻塞；
* UI 是否真实映射状态机和失败路径。

典型问题类型：

* `page_type_mismatch`
* `action_priority_ambiguity`
* `non_blocking_not_reflected_in_ui`

## 5.5 `api_contract`

检查：

* API 是否足够支撑功能链和失败链；
* 请求 / 响应字段来源是否清楚；
* 幂等、错误码、冲突表达是否覆盖主要失败模式；
* 契约边界是否与状态机一致；
* 前后端是否可能因字段语义不清而分叉实现。

典型问题类型：

* `field_source_ambiguity`
* `idempotency_gap`
* `failure_contract_underdefined`

## 5.6 `implementation_executability`

检查：

* `IMPL` 是否足以指导下游任务直接开工；
* touch set 是否明确；
* 执行顺序是否明确；
* 边界与交付物是否可操作；
* coder 是否仍需重新发明一轮设计。

典型问题类型：

* `touch_set_missing`
* `task_order_undefined`
* `acceptance_to_task_gap`

## 5.7 `testability`

检查：

* 是否能从 `IMPL / TECH / API / UI / TESTSET` 派生真实测试；
* 完成态是否可观测；
* 关键失败态是否可观测；
* `TESTSET` 是否在测正确对象；
* evidence points 是否足够。

典型问题类型：

* `acceptance_not_observable`
* `critical_failure_not_testable`
* `testset_subject_drift`

## 5.8 `migration_compatibility`

检查：

* 是否存在旧页面、旧字段、旧状态、旧投影兼容问题；
* 新旧并存时谁优先是否明确；
* 双写期 / alias 期 / fallback 规则是否明确；
* 兼容失败时是否 fail-closed 或 fail-safe 有定义。

典型问题类型：

* `legacy_writeback_risk`
* `state_priority_undefined`
* `migration_fallback_missing`

---

# 6. 执行协议

本 ADR 正式冻结 `qa.impl-spec-test` 的最小执行协议为 7 步。

## Step 1：读取与建模输入

必须提取：

* 目标功能
* 核心对象
* 状态机
* API 契约
* UI surface
* 完成态
* 关键不变量
* 兼容 / 迁移约束

## Step 2：生成系统视图

必须把输入重组为至少以下 4 类系统视图：

* 功能链
* 用户旅程图
* 状态 / 数据关系图
* UI / API / state mapping 表

## Step 3：逐维度测试

必须对第 5 节定义的 8 个维度逐项执行规则检查，并记录：

* score
* findings
* coverage confidence

## Step 4：跨文档冲突检测

至少检测以下耦合面：

* `FEAT vs IMPL`
* `TECH vs IMPL`
* `TECH / ARCH / API` 内部一致性与 `IMPL` 的接缝
* `API vs UI`
* `UI vs user_journey`
* `TESTSET vs implementation acceptance`

## Step 5：失败路径推演

深度模式下至少要模拟以下 counterexample 家族：

* canonical field 缺失
* 非法输入
* patch 保存成功但 completion 未更新
* 状态写入失败
* 网络失败
* risk gate fail
* device auth / finalize fail
* compatibility conflict blocked

正式原则：

## **如果文档无法解释这些反例场景中的恢复或阻断策略，就不能判定为实施就绪。**

深度模式下还必须满足：

## **每个被识别为高风险的维度，至少命中 1 个反例场景；否则不得宣称 counterexample coverage 充分。**

## Step 6：实施就绪性判定

必须明确回答两个问题：

1. 这份 `IMPL` 能不能直接交给 AI coder 编码。
2. 还缺哪些最关键的信息，否则 AI 实施会显著漂移。

同时必须按所选执行模式判定：

* `strong_self_contained`
* `upstream_follow_allowed`

也就是说：

## **`self_contained_readiness = sufficient` 必须始终相对于所选 execution mode 解释，不能脱离模式单独成立。**

## Step 7：输出 gate 报告

最终必须输出：

* `verdict`
* readiness summary
* dimension scores
* issue list
* missing information
* repair plan

深度模式下建议附带：

* `repair_patch_suggestions`

其职责不是偷偷改写上游 truth，而是明确指出：

* 哪一段文档缺什么
* 应补哪个字段、状态、异常流或恢复动作
* 哪些问题应修 `IMPL`
* 哪些问题应回到上游对象重冻

---

# 7. 输入与输出 contract

## 7.1 输入边界

`qa.impl-spec-test` 的正式主输入固定为：

* 一个 `feature_impl_candidate_package`
* 一个显式 `impl_ref`
* 可解析的 `feat_ref`
* 可解析的 `tech_ref`

并按需带入：

* `arch_ref`
* `api_ref`
* `ui_ref` 或 `ui_refs`
* `testset_ref` 或 `testset_refs`
* `source_refs`
* `repo_context`
* migration / existing system notes

正式输入原则：

1. `IMPL` 是主测试对象。
2. `FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority，不可只把它们当背景。
3. repo context 仅作为实施接线与 touch set 辅助，不得替代上游真相源。

## 7.2 建议输入 schema

```yaml
impl_ref: string
impl_package_ref: string
feat_ref: string
tech_ref: string
arch_ref: string | null
api_ref: string | null
ui_refs: list[string]
testset_refs: list[string]
source_refs: list[string]
repo_context:
  enabled: boolean
  touchable_paths: list[string]
  observable_paths: list[string]
  migration_notes_ref: string | null
execution_mode:
  mode: quick_preflight | deep_spec_testing
  require_strong_self_contained: boolean
  allow_upstream_follow: boolean
  simulate_counterexamples: boolean
risk_profile:
  domain: product_impl
  strictness: high
```

## 7.3 输出对象

本 ADR 正式冻结 `qa.impl-spec-test` 的输出对象为：

* 一个 `impl_spec_test_report_package`
* 一个 `implementation_readiness_gate_subject`

最小产物集建议包括：

* `package-manifest.json`
* `impl-spec-test-report.md`
* `impl-spec-test-report.json`
* `impl-spec-test-defects.json`
* `impl-spec-test-counterexamples.json`
* `impl-spec-test-gate-subject.json`
* `repair-patch-suggestions.md`
* `execution-evidence.json`
* `supervision-evidence.json`

## 7.4 建议输出 schema

```yaml
verdict: pass | pass_with_revisions | block
implementation_readiness: ready | partial | not_ready
self_contained_readiness: sufficient | insufficient
self_contained_evaluation_mode: strong_self_contained | upstream_follow_allowed
dimension_scores:
  functional_logic: number
  data_modeling: number
  user_journey: number
  ui_usability: number
  api_contract: number
  implementation_executability: number
  testability: number
  migration_compatibility: number
blocking_issues:
  - id: string
    title: string
    impact: string
    evidence: list[string]
    repair_action: string
high_priority_issues:
  - id: string
    title: string
    impact: string
    evidence: list[string]
    repair_action: string
normal_issues:
  - id: string
    title: string
    impact: string
    evidence: list[string]
    repair_action: string
missing_information:
  - string
repair_plan:
  immediate: list[string]
  before_coding: list[string]
  during_coding: list[string]
recommended_next_action: revise_impl | rederive_upstream | proceed_to_gate | proceed_to_coding
recommended_actor: impl_author | upstream_owner | human_gate | coder
repair_target_artifact: IMPL | FEAT | TECH | ARCH | API | UI | TESTSET | MULTI
```

---

# 8. 问题分级与 gate 规则

## 8.1 问题分级

该 skill 的问题分为 4 类：

### Blocking Issues

不修不得开工。

### High Priority Issues

建议在开工前修复，否则高概率导致实现漂移或返工。

### Normal Issues

可边实施边修，但必须可控且不影响主链。

### Missing Information

不是显式错误，但缺失后会让 AI 在实施时自行补设计。

## 8.2 硬规则

本 ADR 正式冻结以下硬规则：

### Rule 1

如果 `IMPL` 不能独立回答“改哪些模块、先后顺序、哪些接口 / 状态 / UI 必须实现”，直接判为：

* `implementation_readiness = not_ready`
* `verdict = block`

### Rule 2

如果 canonical field、state、capability flag、UI flow、API 契约存在任意两处冲突，直接标为：

* `high_risk_design_conflict`

且至少进入 `high_priority_issues`；若冲突会直接诱发实现分叉，则进入 `blocking_issues`。

### Rule 3

如果关键失败路径没有恢复动作，不得只报 warning，必须报：

* `blocking_issue`

### Rule 4

如果 `TESTSET` 无法覆盖完成态与关键失败态，必须判为：

* `testability insufficient`

严重时不得进入实施。

### Rule 5

如果 `UI` 声称 non-blocking，但 `API / state / journey` 实际仍阻塞，必须判为：

* `severe_design_conflict`

默认至少 `pass_with_revisions`，严重时 `block`。

## 8.3 评分与 verdict 绑定规则

dimension scores 不是展示字段，必须参与 verdict 计算。

至少冻结以下绑定规则：

1. 任一 `blocking_issue` 存在，直接 `verdict = block`
2. 任一 `severe_design_conflict` 存在，默认 `verdict = block`
3. `implementation_executability < 6`，至少 `verdict = pass_with_revisions`
4. `testability < 6`，至少 `verdict = pass_with_revisions`
5. 两个及以上 `high_priority_issues` 且涉及不同维度，至少 `verdict = pass_with_revisions`
6. 若 `self_contained_readiness = insufficient` 且 execution mode 为 `strong_self_contained`，默认至少 `pass_with_revisions`；若因此导致 coder 无法直接开工，则 `block`

runtime 可以在此基础上增加更细的 scoring policy，但不得弱化以上最低约束。

## 8.4 Verdict 语义

`verdict = pass` 表示：

* `IMPL` 已满足进入实施的最低自包含与一致性要求；
* 允许进入 coding start 或继续进入 external gate。

`verdict = pass_with_revisions` 表示：

* `IMPL` 基本方向成立，但存在需要在编码前完成的修补项；
* 默认不允许自动 dispatch 给 coder，除非这些修补项已被落地并复核。

`verdict = block` 表示：

* 当前 `IMPL` 不具备稳定实施条件；
* 必须修 `IMPL`，或回到上游对象重新派生。

正式边界：

## **`pass / pass_with_revisions / block` 是 implementation-readiness verdict，不是 external gate 的 authoritative legal decision。**

---

# 9. 与现有 ADR 的关系

## 9.1 与 ADR-033 的关系

ADR-033 冻结的是通用 `Document Test` 验证层。

本 ADR 在其基础上进一步冻结：

* `qa.impl-spec-test` 是面向 `IMPL` 的专业化 document test；
* 它更强调链路压力测试、失败路径推演与 implementation readiness；
* 它不是泛化到所有 workflow 的统一规则替代，而是 `IMPL` 的专用深测层。

## 9.2 与 ADR-034 的关系

ADR-034 冻结 `IMPL` 是 execution bundle / self-contained contract。

本 ADR 进一步回答：

* 如何判断这个 execution bundle 是否真的足够自包含；
* 如何判断它是否会在实施时诱发另一套系统被实现出来；
* 如何用标准化 verdict 阻止不合格 `IMPL` 进入 coder 主链。

## 9.3 与 ADR-014 的关系

ADR-014 冻结 `IMPL` 不是第二层技术设计。

本 ADR 继续冻结：

* `qa.impl-spec-test` 也不得退化成第二层技术设计；
* 该 skill 负责找冲突、找空洞、找失败链缺口；
* 若发现设计 authority 缺失，应推动上游修订，而不是在测试报告里偷偷补设计真相。

## 9.4 与 ADR-035 的关系

ADR-035 强调 `TESTSET` 的需求覆盖与 traceability。

本 ADR 将这一原则前移到实施前：

* `IMPL` 若无法映射到可测试完成态和失败态，应被判为 readiness 不足；
* `TESTSET` 若与 `IMPL` 的完成态 / 失败态不一致，必须被视为正式缺陷。

---

# 10. 非目标

本 ADR 明确排除以下目标：

* 把 `qa.impl-spec-test` 做成纯文档格式 lint；
* 让该 skill 直接替代 external gate；
* 让该 skill 直接评审代码质量或运行代码；
* 让该 skill 充当新的技术设计 author；
* 让该 skill 静默修正上游 truth source；
* 让 `IMPL` 在未通过 readiness 检查时仍默认自动进入 coder 主链。

---

# 11. 最终冻结语句

LL 正式冻结：

## **`qa.impl-spec-test` 是一条位于 `IMPL -> implementation start` 之间的专业化 governed workflow。它以 `IMPL` 为主测试对象，以 `FEAT / TECH / ARCH / API / UI / TESTSET` 为联动 authority，对功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性和兼容迁移风险进行实施前文档压力测试，并输出 `pass / pass_with_revisions / block` 的 implementation-readiness verdict。**

同时正式拒绝以下退化解释：

* 只检查文档是否写完；
* 只检查 schema 是否通过；
* 只看 `IMPL` 自身而不看上游对象；
* 只看 happy path；
* 只输出摘要而不给阻断结论；
* 在 readiness 不足时仍让 AI coder 自动开工。
