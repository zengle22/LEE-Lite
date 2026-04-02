# ADR-037：Skill 质量控制采用双环治理与失败资产化工程流程

* 状态：Draft
* 日期：2026-04-02
* 决策者：Le Zeng
* 适用范围：全部以文档/半结构化对象为主要输出的 governed skill，以及其对应的 gate、review、qualification、regression 治理链
* 相关 ADR：ADR-004、ADR-008、ADR-015、ADR-020、ADR-033、ADR-036

---

# 1. 背景

随着 `RAW -> SRC -> EPIC -> FEAT -> TECH / UI / TESTSET / IMPL` 主链与派生链逐步冻结，仓库已经为 skill 运行期质量建立了若干局部能力：

* skill contract 与 lifecycle 基线；
* structural validation / semantic review；
* external gate 前的 `Document Test` 验证层；
* `IMPL` 实施前的 `Implementation Spec Testing` 压力测试层；
* evidence / review report / gate decision 的对象化落盘。

这些能力已经能回答一类问题：

> **某一次 skill 运行出来的对象，在进入 external gate 前，是否足够可读、可测、可下游消费。**

但近期反复出现的质量问题表明，系统仍缺一层更慢、更高位的质量治理机制。

当前最常见的退化路径是：

* 某次运行暴露问题；
* 人工或 AI 立刻热修产物；
* 当前交付继续推进；
* 但失败现场没有冻结；
* 没有形成结构化 failure case；
* 没有统一归因；
* 没有回流到 skill 定义、review checklist、schema、testset 或 baseline。

结果就是：

* 相同错误会跨 run、跨 SKU、跨 skill 反复出现；
* review 有时能拦住，有时完全漏检；
* prompt 调整和局部 patch 很多，但系统自由度没有收缩；
* 团队知道“哪里经常出错”，却没有正式、可执行、可回归的治理流程。

因此，需要一份新的 ADR，正式冻结：

## **Skill 质量控制不再只依赖单次运行期验证，而采用“运行闭环 + 治理闭环”的双环治理模型。**

该模型的目标不是覆盖所有生成路径，而是把每一次失败都转化为正式治理资产，通过持续归因、集中治理与回归验证，逐步把 skill 从开放生成收敛为受控生产。

---

# 2. 问题陈述

当前真正需要回答的，不是“怎么再补一条 review 提示词”，而是以下几个更结构性的质量控制问题。

## 2.1 单次运行验证不等于系统级质量控制

`Document Test`、`supervisor review`、`external gate` 主要回答的是：

* 这一次输出是否合格；
* 这一次是否应该返修；
* 这一次能否进入下游。

它们并不自动回答：

* 这类错误是否正在高频重复；
* 它到底来自定义层、输入层、生成层还是检测层；
* 应该修 prompt、修 schema、修 checklist、修 skill 分步，还是修上游输入；
* 修完以后是否真的降低了问题密度。

如果缺少独立质量治理层，运行期验证再多，也只能得到：

* 当前 case 被处理了；
* 但系统没有变得更稳。

## 2.2 热修交付与系统修复必须分离

当前很多失败一旦出现，最自然的动作就是立刻：

* 改文档；
* 局部重跑；
* patch 某个字段；
* 让人工直接兜底。

这对保交付是必要的，但它并不等于系统已修复。

如果不把二者显式分离，就会长期陷入：

* case 一直能救火；
* skill 质量却始终靠人工经验维持；
* 同类问题持续复发。

## 2.3 未冻结失败现场，就无法可靠归因

一旦先修后记，系统会快速丢失最关键的诊断信息：

* 上游输入是什么；
* 错误产物长什么样；
* 哪一步第一次暴露问题；
* 修复到底改了什么；
* 是生成错了，还是检测没拦住。

没有冻结现场，后续“归因”就只能依赖印象，而不是证据。

## 2.4 没有失败资产化，就无法集中治理

如果失败只以聊天记录、临时口头说明或一次性 patch 存在，系统就无法稳定完成：

* 失败聚类；
* 根因分布统计；
* 高频模式识别；
* 跨 SKU 共性问题治理；
* 历史 case 回归。

结果就是治理只能凭感觉推进，而不能成为工程系统的一部分。

## 2.5 质量收敛必须依赖回归，而不是依赖记忆

如果每次修完只觉得“这次应该好了”，而没有：

* regression case；
* 历史 failure case 反跑；
* baseline update；
* 指标化对比；

那么系统很快会再次漂移，或者用一个新问题替换旧问题。

因此，本 ADR 需要正式定义：

## **Skill 质量控制的标准工程流程必须同时覆盖：失败冻结、结构化归因、集中治理、回归验证与基线更新。**

---

# 3. 决策

## 3.1 决策摘要

LEE Lite 在现有 skill-first 架构之上，正式采用：

## **Skill 质量控制双环治理模型**

即：

* **运行闭环（Run Loop）**
  负责保证单次交付不中断，执行 `生成 -> 校验 -> 发现问题 -> 冻结 -> 热修 -> 继续运行`。
* **治理闭环（Governance Loop）**
  负责把失败转化为治理资产，执行 `采集 -> 分类 -> 归因 -> 聚类 -> 排序 -> 系统修复 -> 回归 -> 基线更新`。

两条闭环的正式关系是：

1. 运行闭环负责保交付，不追求一次性消灭所有根因。
2. 治理闭环负责系统收敛，不直接替代当前交付所需的热修动作。
3. 每一次 P0 / P1 级重要失败都必须先被冻结为正式 failure case，再允许进入热修或重跑；P2 可先进入轻量 issue log，达到频次阈值后再升级。
4. 治理动作必须最终落回到 skill contract、schema、checklist、validation、testset 或对象基线，而不能停留在口头结论。

一句话定义：

> **运行闭环保证不中断，治理闭环保证不白错。**

---

## 3.2 系统目标

本 ADR 下的质量控制目标，不是通过预先覆盖全部生成路径来保证正确性，而是通过：

* 失败采集；
* 结构化归因；
* 动作类型化治理；
* 回归验证；
* baseline 更新；

持续收缩系统自由度。

因此，本 ADR 的成功标准不是“再也没有错误”，而是：

* 错误越来越可分类；
* 高频错误越来越少；
* review 漏检率下降；
* 同类问题更早暴露；
* 修复开始从个案 patch 转向系统治理。

---

### 3.2.1 重要失败分级

本 ADR 中，“重要失败”按 triage 规则分为三类：

* `P0 / Critical`
  * 阻断 external gate；
  * 导致下游消费错误；
  * 关系错绑；
  * 主链对象语义失真；
  * 会把错误带入正式下游事实源。
* `P1 / Major`
  * review 漏检的中高风险问题；
  * 重复出现的问题；
  * 明显跨 SKU 的共性问题；
  * 虽未必立即阻断 gate，但会持续侵蚀质量边界。
* `P2 / Minor`
  * 格式类问题；
  * 低风险问题；
  * 局部可热修且无复发迹象的问题。

进入条件如下：

* `P0` / `P1` 必须生成 `failure_case`；
* `P2` 可先进入轻量 `issue_log`；
* `P2` 若在同一 skill / SKU / failure pattern 上达到频次阈值，则必须升级为 `failure_case`；
* 轻量 `issue_log` 仅用于短期观测，不得替代正式失败资产化。

建议频次阈值：

* 同类 `P2` 问题在一个治理窗口内累计 `3` 次以上，升级为 `failure_case`；
* 同一 `expected_detector` 连续漏检 `2` 次以上，升级为 `P1` 级治理项；
* 同一 remediation 动作连续出现 `3` 次以上，视为系统设计问题，不再按个案处理。

### 3.2.2 Freeze 主粒度

Freeze 的主粒度显式定义为：

* `run_id`
* `artifact_id`
* `failure_scope`

其中 `failure_scope` 只能取以下值：

* `run`
* `artifact`
* `field_cluster`

默认主粒度为 `artifact-level`。

规则如下：

* 默认按 `artifact-level` 冻结单个错误对象；
* `field_cluster` 仅用于同一 artifact 内多个字段级错误可归并时；
* 只有跨多个 artifact 的系统性异常，才允许提升为 `run-level`；
* `run-level` freeze 必须说明为什么不能拆分成更小的 artifact-level failure。

---

## 3.3 运行闭环（Run Loop）正式流程

运行闭环是快环，面向单次交付。

### Step 1：Generate

skill 按其既有 contract 生成候选产物。

产物可以是：

* `SRC / EPIC / FEAT / TECH / UI / TESTSET / IMPL`
* report package
* review package
* 其它文档型/半结构化 governed object

### Step 2：Validate / Review / Gate Prep

进入已有验证链：

* schema validation
* relation validation
* semantic review
* document test
* supervisor review
* gate-ready packaging

本 ADR 不替代 ADR-033 / ADR-036 定义的运行前验证层，而是在其之上补充失败治理。

### Step 3：Detect

问题可由以下任一来源触发发现：

* rule validator
* review skill
* document test / implementation spec testing
* external gate
* 下游执行器
* 人工终审
* 用户反馈

### Step 4：Freeze

一旦检测到需要诊断或后续治理的问题，必须先冻结现场。

最小冻结内容包括：

* `run_id`；
* `artifact_id`；
* `failure_scope`（`run / artifact / field_cluster`）；
* 上游输入与关键 context；
* 错误产物；
* 当前 skill / SKU / revision；
* 触发阶段与触发者；
* 如已尝试修复，则记录修复 diff；
* 必要的日志、validator 输出、review evidence。

冻结完成前，不得把该问题直接视为“已被系统修复”。

### Step 5：Capture Failure Case

失败必须对象化记录为标准 `failure_case`。

最小字段示例：

```yaml
failure_id: FC-20260402-001
skill_id: dev.tech-to-impl
sku: impl_spec_builder
run_id: RUN-20260402-018
artifact_id: IMPL-SRC-023-004
failure_scope: artifact
triage_level: P1
detected_stage: post_review
detected_by: human
severity: high
symptom_summary: "implements 关系绑定错误，导致下游引用错位"
evidence_refs:
  - upstream_context
  - failed_output
  - validator_report
  - patch_diff
status: open
```

### Step 6：Hotfix

冻结后，允许运行闭环执行热修，以保证交付继续：

* 人工直接修；
* 人工指挥 AI 修；
* 局部 patch；
* 局部重跑；
* 限定范围 rebuild。

但热修的正式语义仅是：

> **恢复当前交付。**

它不自动等于：

> **系统根因已经解决。**

### Step 7：Continue

若问题已被当前交付可接受地隔离或修复，流程继续推进：

* 进入下一个验证节点；
* 进入 external gate；
* 或继续派发下游 job。

运行闭环的原则是：

* 不因为单个失败无限阻塞整条链；
* 但也不能跳过 failure capture 直接假装无事发生。

---

## 3.4 治理闭环（Governance Loop）正式流程

治理闭环是慢环，面向系统收敛。

### Step 8：Classify

每个 failure case 必须结构化分类。

标准问题类型至少包括：

* `structure_error`
* `relation_error`
* `semantic_drift`
* `granularity_error`
* `detection_miss`
* `repair_side_effect`

可按 skill 域补充更细分类，但不得缺少顶层标准分类。

### Step 9：Diagnose

每个 case 必须输出正式根因归因，且主根因仅允许落在以下五层之一：

* `definition_weakness`
* `input_contamination`
* `generation_freedom`
* `detection_weakness`
* `repair_fault`

允许有 `primary` 与 `secondary` 两级根因，例如：

```yaml
root_cause_primary: detection_weakness
root_cause_secondary: generation_freedom
```

这样做的目的，是强制治理回到可动作的层级，而不是停留在“模型不稳定”“质量一般”这类无效描述。

判定规则如下：

* `definition_weakness`：当规则边界本身不清，且不同合理执行者会得出不同结果时优先判到这一层；
* `input_contamination`：当上游输入存在旧口径、缺失、冲突或未声明隐含前提时优先判到这一层；
* `generation_freedom`：当输入与定义足够清楚，但产物仍发生自由补全、语义漂移或越界推断时优先判到这一层；
* `detection_weakness`：当问题本可在现有阶段被发现，但未被 validator / review / test 拦住时优先判到这一层；
* `repair_fault`：当修复动作引入新错、越界修改或形成循环补丁时优先判到这一层。

### Step 10：Detection Gap Analysis

每个 case 必须回答：

> **为什么没有在更早阶段被发现？**

标准缺口类型至少包括：

* `rule_possible_but_missing`
* `comparison_possible_but_missing`
* `semantic_check_needed_but_missing`
* `check_phase_not_triggered`

同时必须记录 `expected_detector`，用于说明理论上本应由谁发现该问题：

* `schema_validator`
* `relation_validator`
* `semantic_review`
* `document_test`
* `impl_spec_testing`
* `human_final_review`

### Step 11：Remediation Plan

治理建议必须写成动作类型，而不是泛化 prose。

Remediation Plan 必须显式分为两栏：

* `Immediate Remediation`
  * 本次 case 要如何止血；
  * 例如 patch artifact、rerun step、manual override。
* `System Remediation`
  * 系统以后如何少犯；
  * 例如 add_relation_check、tighten_definition_boundary、split_skill_steps。

标准动作类型至少包括：

* `add_schema_validation`
* `add_relation_check`
* `add_upstream_diff_check`
* `restrict_freeform_generation`
* `add_review_checklist_item`
* `split_skill_steps`
* `enforce_unknown_output`
* `tighten_definition_boundary`
* `limit_patch_scope`

动作可以组合，但必须显式指定：

* 作用层级；
* 目标对象；
* 预期降低的错误类型；
* 需要的回归方式。

### Step 12：Archive Governance Assets

每个完成诊断的 case 至少应沉淀为：

* `failure_case`
* `diagnosis_report`
* `remediation_plan`
* `regression_case`（如适用）
* `issue_log`（如适用）

这些对象必须可引用、可审阅、可回归，而不能只存在于一次性对话中。

### Step 13：Aggregate

治理周期内，应对 failure case 做聚类统计，至少观察：

* 错误类型分布；
* 根因分布；
* detection gap 分布；
* skill / SKU 维度问题密度；
* 高频失败模式。

治理窗口与触发阈值如下：

* 固定每周一次 `weekly review`；
* 每累计 `10` 个 active failure case，触发一次专项 review；
* `P0` / `P1` 失败可立即触发专项治理，不等待周会；
* 同类错误在一个治理窗口内累计 `3` 次以上，提升为高优先级；
* 同一 `expected_detector` 连续漏检 `2` 次以上，优先治理检测层；
* 同一 remediation 在一个治理窗口内连续出现 `3` 次以上，优先治理系统定义或流程层。

### Step 14：Prioritize

治理优先级按以下顺序处理：

1. 高频问题
2. 高严重度问题
3. review / test 漏检问题
4. 跨 skill / 跨 SKU 共性问题

### Step 15：Fix System

治理动作修的是系统，而不是单个产物。

允许的系统级动作包括：

* 收紧对象定义边界；
* 增加 schema / relation / diff 校验；
* 调整 review checklist；
* 增加 failure-oriented examples / anti-examples；
* 拆 skill phase；
* 引入中间结构态；
* 限制 repair 可改范围；
* 明确 unknown / unresolved 的合法输出形态。

### Step 16：Regression

所有系统级治理必须经过回归验证。

最小回归方法包括：

* 用原 failure case 反跑；
* 用同类历史 case 回归；
* 用 testset / qualification case 验证；
* 检查是否引入新类型副作用。

### Step 17：Baseline Update

治理完成后，必须更新至少一项正式基线：

* skill prompt / contract
* schema
* validation rule
* checklist
* testset
* object definition
* governance playbook

Baseline update 之后，必须保留回链关系，用于追踪治理效果：

* `baseline_change -> addresses -> failure_pattern`
* `remediation_plan -> implemented_by -> baseline_change`

没有 baseline update，则本 ADR 下不视为治理完成。

---

## 3.5 正式对象与落盘边界

为避免污染 ADR-008 已冻结的业务主链 SSOT，本 ADR 不把失败治理对象直接并入业务主链 `SRC / EPIC / FEAT / TECH / IMPL / TESTSET / UI`。

本 ADR 正式引入一组：

## **governance-side formal objects**

它们是受治理、可审计、可追溯的正式对象，但不等于业务真相主链对象。

最小对象集合包括：

* `FAILURE_CASE`
* `DIAGNOSIS_REPORT`
* `REMEDIATION_PLAN`
* `REGRESSION_CASE`
* `ISSUE_LOG`

推荐关系包括：

* `failure_case -> relates_to -> artifact`
* `failure_case -> caused_by -> skill_or_sku`
* `diagnosis_report -> analyzes -> failure_case`
* `remediation_plan -> remediates -> failure_pattern`
* `regression_case -> verifies -> remediation_plan`
* `issue_log -> escalates_to -> failure_case`

推荐落盘方向包括但不限于：

* `artifacts/reports/validation/`
* `artifacts/reports/repair/`
* `artifacts/reports/review/`
* 后续新增的 `artifacts/reports/governance/`
* 或未来正式收敛到 `ssot/governance/`

本 ADR 的 authority 不强制立即迁移目录，但强制要求对象化与可追溯性。

---

## 3.6 三个工程不变量

### 3.6.1 冻结优先原则

> **未冻结失败现场，不允许把问题视为已进入正式修复流程。**

### 3.6.2 修复分离原则

> **产物热修不等于系统修复。**

### 3.6.3 错误资产化原则

> **每一个重要失败，都必须沉淀为可复用治理资产。**

这三个不变量，优先级高于局部实现习惯。

---

## 3.7 适用范围与非适用范围

本 ADR 特别适用于：

* 文档型 governed skill；
* 半结构化对象生成 skill；
* `SRC / EPIC / FEAT / TECH / UI / TESTSET / IMPL` 等需要 review、gate、freeze 的对象链；
* qualification / review / gate 前存在明显语义风险的工作流。

典型适用例子包括：

* `product.raw-to-src`
* `product.src-to-epic`
* `product.epic-to-feat`
* `dev.feat-to-tech`
* `dev.feat-to-ui`
* `qa.feat-to-testset`
* `dev.tech-to-impl`
* `qa.impl-spec-test`

本 ADR 不优先适用于：

* 纯 deterministic code transform；
* 单步工具调用；
* 没有可审阅中间产物的简单自动化脚本。

对这些场景，常规测试与 CI 往往比 failure governance 更直接。

---

# 4. 与现有 ADR 的关系

## 4.1 与 ADR-033 的关系

ADR-033 定义的是：

* 单次 skill 运行内部的 `Document Test` 验证层。

本 ADR 定义的是：

* 跨运行、跨 case、跨 SKU 的质量治理闭环。

因此：

* `Document Test` 负责发现问题；
* 本 ADR 负责把问题变成治理资产并推动系统收敛。

二者互补，不能互相替代。

## 4.2 与 ADR-036 的关系

ADR-036 解决的是：

* `IMPL` 实施前的高压力文档测试与 readiness verdict。

本 ADR 解决的是：

* 这些 verdict 所暴露出的失败模式，如何进入长期治理。

因此：

* `Implementation Spec Testing` 是检测层；
* 本 ADR 是失败治理层。

## 4.3 与 ADR-008 的关系

ADR-008 冻结的是业务主链与派生 SSOT。

本 ADR 新增的是治理侧正式对象，而不是替换或扩张业务主链。

如果未来要把治理对象纳入 SSOT 目录级 authority，应通过后续 ADR 或 ADR-008 修订显式完成，而不是隐式混入现有业务对象模型。

---

# 5. 工程落地建议

## 5.1 MVP

本 ADR 的最小可执行落地，不建议一开始就做成复杂自动闭环。

最稳的起步方式是：

> **出问题 -> 先跑问题采集 skill -> 再人工或人工指挥 AI 热修产物 -> 流程继续 -> 后面再集中治理。**

也就是说：

* 先把“采集”做好；
* 再把“热修”限制住；
* 最后再把“归因、治理、回归”逐步加深。

### 5.1.1 最小执行顺序

最小落地流程如下：

1. 发现问题
2. 先运行 `failure_capture_skill`
3. 再人工或人工指挥 AI 热修产物
4. 修后让主流程继续
5. 周期性汇总 `failure_case` 再做集中治理

典型触发来源包括：

* AI review 没过；
* 人工终审发现；
* 下游执行时报错；
* 人工肉眼看出不对。

这个顺序的核心原则是：

> **先采集，后热修；热修保交付，治理修系统。**

不允许默认采用以下顺序：

* 发现问题；
* 直接让 AI 自由修；
* 改完继续；
* 后面靠记忆回想问题是什么。

### 5.1.2 `failure_capture_skill` 的最小职责

第一阶段推荐先做一个最小版 `failure_capture_skill`。

其职责不是修复，而是冻结现场并输出受限修复上下文。

最小输入包括：

* 当前产物；
* 上游输入；
* 问题描述；
* 发现阶段；
* 发现者。

最小输出应至少包含三类对象：

1. `failure_case`
2. `diagnosis_stub`
3. `repair_context`

其中：

#### A. `failure_case`

这是最基本的失败记录对象，至少应包含：

* `failure_id`
* `skill_id`
* `sku`
* `run_id`
* `artifact_id`
* `failure_scope`
* `detected_stage`
* `detected_by`
* `severity`
* `symptom_summary`
* `evidence_refs`

#### B. `diagnosis_stub`

第一阶段不要求做完整重归因，但至少要有轻量初判，避免后面只剩一堆“出过问题”的记录。

最小字段建议包括：

* `error_class`
* `root_cause_primary`
* `expected_detector`
* `remediation_hint`

#### C. `repair_context`

这是后续修复 agent 或人工修复使用的受限上下文包。

最小内容建议包括：

* 哪部分错了；
* 建议只改哪些范围；
* 哪些内容不能动；
* 修复目标是什么。

其目的不是替代人工判断，而是限制后续 AI 修复继续自由发挥。

### 5.1.3 热修阶段的规范

`failure_capture_skill` 跑完以后，才进入手动热修。

这里的“手动热修”允许两种形态：

* 人工亲自修改；
* 人工基于 `failure_case` 与 `repair_context` 指挥 AI 修改。

第二种虽然由 AI 执行，但正式语义仍属于：

* 人工主导修复；
* AI 受限执行。

为防止热修再次污染现场，热修阶段应遵守以下最小规则：

* 只改指定范围；
* 不允许顺手重构；
* 必须保留修复 diff；
* 修后重新过最小校验；
* 修复动作回写到 `failure_case`。

### 5.1.4 第一阶段不建议做的事

为了先把流程跑稳，第一阶段不建议上来就做：

* 采集后自动修；
* 完整自动归因；
* 所有小问题都走重治理流程。

原因如下：

* 采集尚未稳定前，自动修会让 failure case 与实际修复脱钩；
* taxonomy 尚未跑稳前，完整归因容易制造伪精确；
* 每个小问题都走重流程，会让治理系统很快过载。

因此，第一阶段应优先采用轻重分流：

* 轻问题：简版采集 + 直接热修
* 重问题：完整 `failure_case` + 纳入后续治理

### 5.1.5 第一阶段的最小交付物

最小可落地实现应至少包含：

1. 一个标准 `failure_case` 模板
2. 一个标准 `diagnosis_stub` 模板
3. 一个标准 `repair_context` 模板
4. 一个可重复调用的 `failure_capture_skill`
5. 一个固定周期的 failure review 节点

只要这五项先跑起来，系统就能开始回答：

* 哪些错误其实是同一类；
* 哪些 skill 的定义边界有问题；
* 哪些 review 规则在持续漏检；
* 哪些问题总是靠同一种 patch 在救火。

## 5.2 推荐推进顺序

建议按以下顺序落地：

1. 第一阶段：先上线 `failure_capture_skill`，只做采集、初步标签与修复上下文
2. 第二阶段：再拆成 `failure_capture`、`failure_classify`、`repair_context_builder`
3. 第三阶段：再补 `diagnosis_skill`、`weekly_governance_review`、`regression_pack_builder`
4. 运行稳定后，再把高频 remediation 动作接回 schema / checklist / prompt / skill baseline
5. 最后再补自动聚类、自动统计和更完整的治理报表

---

# 6. 结果预期

采用本 ADR 后，系统的阶段性变化应表现为：

## 阶段 1

* 问题仍然很多；
* 但失败开始可追溯；
* 团队不再靠记忆讨论问题。

## 阶段 2

* 错误开始可分类；
* 能看见高频失败模式；
* 能识别哪类问题属于 review 漏检。

## 阶段 3

* 高频大错下降；
* 运行期热修减少；
* 治理动作开始稳定沉淀为 baseline。

## 阶段 4

* 失败集中到少数低风险类型；
* 新问题更早暴露；
* skill 输出进入受控生产状态。

---

# 7. 一句话结论

> **Skill 质量不是通过覆盖所有生成路径来保证，而是通过“失败冻结 -> 失败资产化 -> 结构化归因 -> 分层治理 -> 回归验证 -> 基线更新”，持续收缩系统自由度。**
