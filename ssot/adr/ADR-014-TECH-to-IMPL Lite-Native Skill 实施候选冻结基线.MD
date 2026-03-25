# ADR-014：TECH-to-IMPL Lite-Native Skill 研发实施单冻结基线

* 状态：Draft
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：`ll-dev-tech-to-impl` skill、`dev.tech-to-impl` lite-native runtime、`feature_impl_candidate_package`
* 相关 ADR：ADR-008、ADR-009、ADR-013

---

# 1. 背景

当前仓库已经完成或冻结了几段相邻主链：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT -> TECH`
* `FEAT -> TESTSET`

同时，`ADR-013` 已经进一步冻结：

* `TECH` 是唯一正式技术设计
* `ARCH/API` 是按需附带的设计同簇对象
* `IMPL` 不应再承担第二层技术设计

因此，当前真正缺的不是再补一层“实施设计”，而是补一层清晰、可治理、可落盘的研发实施任务边界：

* 直接从 `FEAT` 去跑代码，会让 `TECH` 被绕过；
* 让 `IMPL` 再去重写模块职责、契约边界、失败策略，会把 `TECH` 降级成无效上游；
* 直接把 `feature_delivery_l2` 当作 repo 执行器调用，又会把实施步骤、blocked 项、交付物和验收点藏进运行时里。

因此，需要一份独立 ADR，把：

* `feat2impl` 的 authority
* 输入边界
* 研发实施单结构
* workstream 适用性判断
* 对 `template.dev.feature_delivery_l2` 的 handoff

先冻结成一条 lite-native governed 基线。

---

# 2. 问题陈述

当前真正需要回答的不是“怎么再补一版技术方案”，而是下面几个更前置的问题：

## 2.1 `feat2impl` 的主输入到底是谁

如果不冻结输入边界，就会在以下对象之间漂移：

* `feat_freeze_package`
* `tech_design_package`
* product delivery prep 产物
* 临时 task list
* repo context / prompt

而当前主链已经明确：

* `FEAT` 是能力边界真相源
* `TECH` 是正式技术设计真相源
* repo、env、path 只属于执行上下文，不替代业务真相源

## 2.2 `feat2impl` 的主输出到底是什么

如果直接宣称输出是：

* 代码 diff
* FE/BE 完工引用
* evidence pack

就会过早把“实施候选”与“实施完成”混成一件事。

但如果完全不落一个中间对象，`feature_delivery_l2` 的 phase chain 又没有一个被显式固定下来的执行入口。

## 2.3 Frontend / Backend 是否总是平级必出

某些 FEAT 明显不存在 UI surface，某些 FEAT 也可能没有独立 backend workstream。

如果每次都机械输出 FE/BE 两份实施计划：

* 会产生空洞 workstream
* 会把 surface applicability 判断藏进执行细节

## 2.4 `IMPL` 是否可以继续承担第二层技术设计

不能。

如果 `IMPL` 继续回答下面这些问题：

* 组件职责重新怎么拆
* 对象模型重新怎么定
* fail-closed / fail-open 策略要不要改
* 哪个 boundary 是否合理
* Gateway / Registry / Auditor 谁负责什么

那么 `TECH` 就会在实施阶段被影子化。

因此 `feat2impl` 必须冻结为：

## **研发实施任务文档，而不是第二层技术设计文档。**

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个单 FEAT、lite-native、task-first 的 `ll-dev-tech-to-impl` governed skill**

作为已冻结设计进入 Dev 实施主链之前的正式研发实施单派生路径。

名称不是本 ADR 的核心约束。

无论 runtime 后续采用：

* `tech-to-impl`
* `tech-to-impl`

只要其语义对象仍然是 `IMPL` 研发实施任务文档，而不是第二层技术设计，本 ADR 视为一致实现。

本 ADR 冻结以下原则：

1. 输入权威固定为：
   * 一个 freeze-ready 的 `tech_design_package`
   * 一个强制选择的 `feat_ref`
   * 一个强制选择的 `tech_ref`
2. `FEAT` lineage 必须在输入中可追溯，`ARCH/API` 如存在必须可引用。
3. 上游 planning context 可以参考：
   * `workflow.product.task.feat_to_delivery_prep`
4. 输出固定为：
   * 一个 `feature_impl_candidate_package`
5. `IMPL` 的主对象是研发实施任务文档，不是新的技术设计文档。
6. `frontend` 与 `backend` workstream 不是无条件平级必出，而必须先做 applicability assessment。
7. `integration-plan.md`、`dev-evidence-plan.json`、`smoke-gate-subject.json` 必须保留，以保证 downstream execution 不再重新解释实施边界。
8. 该 candidate package 的正式 handoff 目标固定为：
   * `template.dev.feature_delivery_l2`
9. 当前 skill 冻结的是 **研发实施单边界**，不是 repo 代码已经完成的最终证明。

同时，本 ADR 直接冻结以下硬定义：

## **IMPL 是基于已冻结 ADR / TECH / API 的研发实施任务文档，用于组织代码实现、集成接线、迁移切换与交付验收；IMPL 不得新增或改写上游技术决策与实现边界。**

---

## 3.2 Canonical Authority

本 skill 的 authority 分为三层：

### Dev authority

* `E:\ai\LEE\spec\adr\ADR-008__dev-department-ssot-alignment-and-workflow-reframe.md`
* `E:\ai\LEE\spec-global\departments\dev\workflows\templates\feature-delivery-l2-template.yaml`

### Product planning context

* `E:\ai\LEE\spec-global\departments\product\workflows\templates\feat-to-delivery-prep\v1\workflow.yaml`

它不是 `feat2impl` 的主 authority，但它可以提供：

* TASK / delivery plan 的上游交接语义
* surface applicability 的参考边界

### Local implementation authority

* `skills/ll-dev-tech-to-impl/`

也就是说：

## **`feat2impl` 的第一真相，是本地 lite-native runtime + contract + impl candidate package 结构；但其设计 authority 仍来自上游已冻结的 `TECH/ARCH/API`。**

---

# 4. 输入边界

`ll-dev-tech-to-impl` 的正式主输入不再是裸 `feat_freeze_package`，而是：

* 一个 freeze-ready 的 `tech_design_package`
* 一个显式 `feat_ref`
* 一个显式 `tech_ref`

并额外要求：

* `artifact_type = tech_design_package`
* `workflow_key = dev.feat-to-tech`
* `status ∈ {accepted, frozen}`
* `tech-freeze-gate.json.freeze_ready = true`
* selected `feat_ref` 与 selected `tech_ref` 必须真实存在
* 若 package 含 `ARCH/API`，其引用必须可解析
* upstream handoff 中必须保留到 `FEAT` 的 lineage

planning companion 可选参考：

* `workflow.product.task.feat_to_delivery_prep` 的交接结果
* repo context / existing code layout
* execution environment / migration constraints

这意味着：

## **`feat2impl` 不是从任意 FEAT markdown 起草实现计划，而是从已冻结 `TECH` 派生一个可执行的 Dev 实施入口。**

---

# 5. 输出边界

本 ADR 正式冻结 `feature_impl_candidate_package` 的最小产物集：

* `package-manifest.json`
* `impl-bundle.md`
* `impl-bundle.json`
* `impl-task.md`
* `upstream-design-refs.json`
* `integration-plan.md`
* `dev-evidence-plan.json`
* `smoke-gate-subject.json`
* `impl-review-report.json`
* `impl-acceptance-report.json`
* `impl-defect-list.json`
* `handoff-to-feature-delivery.json`
* `execution-evidence.json`
* `supervision-evidence.json`

条件存在：

* `frontend-workstream.md`
* `backend-workstream.md`
* `migration-cutover-plan.md`

这里的正式主对象不是单个 markdown，而是：

## **一个带上游设计引用、实施任务分解、workstream 适用性、Evidence Entry 和 Smoke Subject 的研发实施包。**

---

# 6. IMPL 正式边界

## 6.1 IMPL 应该回答什么

`IMPL` 应该回答：

* 这次研发任务做什么
* 依赖哪些已冻结 `ADR / TECH / API`
* 改哪些模块 / 文件范围
* 实施顺序与分步
* 每步完成条件
* 风险与 blocked 项
* 交付物清单
* 验收检查点

## 6.2 IMPL 不应该回答什么

`IMPL` 不应该回答：

* 组件职责重新怎么拆
* 对象模型重新怎么定
* fail-closed / fail-open 策略要不要改
* 哪个 boundary 是否合理
* Gateway / Registry / Auditor 谁负责什么

这些问题一旦需要变更，应回到：

* `ADR`
* `TECH`
* `API`

而不是在 `IMPL` 里偷偷改写。

## 6.3 IMPL 的七块最小结构

`impl-task.md` 至少必须包含以下七块：

### 1. 目标

本次研发实施覆盖什么，不覆盖什么。

### 2. 上游依赖

引用哪些 `ADR / TECH / API`，以及哪些 frozen decision 需要被原样继承。

### 3. 实施范围

改哪些模块 / 工程区域 / skill / CLI / schema / tests。

### 4. 实施步骤

按 `step 1 / step 2 / step 3 ...` 组织执行顺序，并写明每步完成条件。

### 5. 风险与阻塞

哪些前置未满足就不能继续，哪些风险需要升级处理。

### 6. 交付物

代码、脚本、迁移文件、测试结果、evidence、handoff 对象等。

### 7. 验收检查点

什么叫本次 `IMPL` 完成，哪些检查通过后才允许进入下游 phase。

因此：

## **IMPL 模板应保持轻量，避免长成另一份 `TECH`。**

---

# 7. Workstream 规则

## 7.1 必出对象

每次运行都必须输出：

* `impl-task.md`
* `upstream-design-refs.json`
* `integration-plan.md`
* `dev-evidence-plan.json`
* `smoke-gate-subject.json`

## 7.2 条件对象

`frontend-workstream.md` 仅在存在明确 UI / page / interaction / component implementation surface 时生成。

`backend-workstream.md` 仅在存在 runtime / service / storage / workflow / gate / contract implementation surface 时生成。

`migration-cutover-plan.md` 仅在存在迁移、切换、回滚、兼容模式切换时生成。

如果所有 workstream 都不适用，则：

* package 必须判定失败
* 不能产生一个没有执行面的 implementation candidate

---

# 8. Handoff 语义

`handoff-to-feature-delivery.json` 是正式路由对象，不是普通说明文件。

它至少必须保留：

* `target_template_id = template.dev.feature_delivery_l2`
* `feat_ref`
* `impl_ref`
* `tech_ref`
* supporting `arch_ref / api_ref`（如存在）
* phase inputs
* primary artifact ref

正式解释为：

## **下游 Feature Delivery L2 不再自己从 FEAT 或 TECH 重新拼 phase 输入，而是直接消费 IMPL 已冻结好的执行入口。**

---

# 9. 明确拒绝的方案

以下方案被本 ADR 明确拒绝：

1. 直接从 `FEAT` prompt 化地产出实现 TODO，绕过已冻结 `TECH`
2. 在 `IMPL` 中重新定义模块职责、对象模型、边界所有权或失败策略
3. 直接宣称输出是已完成 FE/BE 工件，而没有 candidate package
4. 无条件机械输出 FE/BE 两个 workstream plan
5. 让 `feat2impl` 退化成 release plan、QA strategy 或新的 shadow design doc
6. 不保留 `TECH/API/ADR` 引用，导致 Dev 再次猜测设计语义

---

# 10. 结论

LL 现在正式拥有一条实现前实施单主链：

```text
tech_design_package + feat_ref + tech_ref
  -> workstream applicability assessment
  -> impl-task
  -> optional FE / BE workstream plans
  -> optional migration / cutover plan
  -> Integration Plan
  -> Dev Evidence Plan
  -> Smoke Gate Subject
  -> feature_impl_candidate_package
  -> template.dev.feature_delivery_l2
```

本 ADR 冻结其核心语义：

## **`feat2impl` 的正确收敛方式，不是把 `IMPL` 继续做成第二层技术设计，而是让它成为基于已冻结 `ADR / TECH / API` 的研发实施任务文档，用于组织实现、接线、迁移与验收，但不得改写上游技术决策。**

