# ADR-015：Machine SSOT + Human Review Projection 双层表达模型

* 状态：Accepted
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：LL / LEE 的 SSOT 治理、gate 审核阶段、`SRC / EPIC / FEAT / TECH / TESTSET` 表达层
* 相关 ADR：ADR-006、ADR-008、ADR-009、ADR-010、ADR-011、ADR-013、ADR-014

---

# 1. 背景

随着 `SRC -> EPIC -> FEAT -> TECH / IMPL / TESTSET` 主链与派生链逐步冻结，LL 现在已经形成了一条比较清晰的 SSOT 路线：

* 上游对象负责定义边界、输入输出、完成态与下游冻结条件；
* gate 不再内嵌在业务 skill 中，而是作为外置治理环节存在；
* 下游 workflow 应消费正式 SSOT，而不是临时 prose 或人工理解稿。

但在最近几轮 EPIC / FEAT 收敛中，一个问题越来越明显：

> 机器最适合消费的 SSOT 形态，与人类最适合审核的文档形态，并不相同。

当前已经校准出的事实是：

* 对 AI 而言，最重要的是：
  * 结构稳定
  * 字段一致
  * 边界清晰
  * 禁止项明确
  * 可继承、可验证、可冻结
* 对人类而言，最重要的是：
  * 能快速理解这是什么产品 / 这条流在干什么
  * 能把握业务主线与角色协作
  * 能识别漏项、歧义与边界错误
  * 能在 gate 阶段做判断

如果强行把 SSOT 本体写成“同时最适合 AI 与人类”的混合文档，通常会出现双输：

* 对 AI 来说，叙述太多，噪音过高；
* 对人类来说，规格过硬，阅读负担过大；
* 对治理来说，authoritative 定义与说明性文本容易混层。

因此，需要正式冻结一个分层原则：

## **SSOT 保持机器优先，gate 审核阶段使用面向人类的派生投影视图。**

---

# 2. 问题陈述

当前 LL 需要解决的，不是“把文档写得更顺一点”，而是以下几个更结构性的治理问题。

## 2.1 SSOT 是否必须同时成为最佳执行源和最佳阅读稿

如果要求同一份 SSOT 同时服务：

* AI 执行
* 下游继承
* schema 校验
* gate 人工审核

那么文档会自然滑向混合体：

* 一部分是 authoritative 约束；
* 一部分是 narrative 解释；
* 一部分是帮助理解的示例；
* 一部分是为了审核而追加的重述。

最终会导致：

* 机器提取成本升高；
* 同一语义在多个位置重复；
* 解释性段落与正式字段不一致；
* 很难再判断哪部分才是权威定义。

## 2.2 Gate 阶段的人类审核需要的不是字段堆叠，而是产品视图

AI 执行阶段更关注：

* 输入输出
* 完成态
* authoritative output
* fallback / prohibited paths
* frozen downstream boundary

但在 gate 阶段，人类更关心：

* 这东西到底在干什么；
* 用户和角色为什么需要它；
* 主流程是否闭合；
* 交付物是否像一个完整产品切片；
* 有没有明显漏项、错项、歧义。

也就是说，gate 是最需要“人类可理解产品视图”的地方。

## 2.3 如果把大量 narrative 直接塞回 SSOT，会污染 SSOT 本体

这会造成至少四类问题：

* 文档变长，AI 消费成本更高；
* 同一含义在正文和解释区重复出现；
* 修订时正文与说明容易漂移；
* gate 通过后无法清楚区分哪些内容可继承，哪些只是帮助阅读。

## 2.4 如果 Projection 不被定义为派生物，就会重新产生多真相源

最危险的退化路径是：

* 一份 SSOT；
* 一份审核稿；
* 一份人工批注稿；
* 一份下游理解稿。

如果这些对象都开始承载正式定义，系统就会重新退化为多真相源。

因此，本 ADR 要正式回答的问题是：

## **如何让 SSOT 继续保持机器优先，同时让 gate 阶段具备高质量的人类审核视图，并且不引入第二真相源。**

---

# 3. 决策

## 3.1 决策摘要

LL / LEE 正式采用：

## **Machine SSOT + Human Review Projection**

中文可解释为：

## **机器优先 SSOT + 人类审核投影视图**

正式原则如下：

1. `Machine SSOT` 是唯一权威源，继续服务 AI 执行、继承、验证、下钻与冻结。
2. `Human Review Projection` 只在 gate 审核阶段作为人类友好视图存在。
3. Projection 必须由最新 `Machine SSOT` 派生生成，而不是人工另写的并列文档。
4. 人类审核发生在 Projection 上，但最终冻结与下游继承仍以 `Machine SSOT` 为准。
5. 所有审核意见都必须回写 `Machine SSOT`，然后重新生成 Projection。

一句话定义：

> **执行靠 SSOT，审核看 Projection，冻结仍回到 SSOT。**

---

## 3.2 双层表达模型的正式定义

### A. Machine SSOT

`Machine SSOT` 是正式 SSOT 本体。它的第一优先级是：

* 对 AI 清晰；
* 对 schema / validator 友好；
* 对下游派生稳定；
* 对 freeze boundary 明确。

它负责冻结：

* 边界
* 输入输出
* completed state
* authoritative output
* 约束
* 禁止项
* downstream frozen boundary
* open technical decisions

### B. Human Review Projection

`Human Review Projection` 是 gate 阶段的人类审核视图。它的第一优先级是：

* 帮助人类快速理解产品；
* 提高审核效率；
* 暴露歧义、遗漏与边界风险；
* 聚焦真正需要人类判断的问题。

它是一个：

* 由 SSOT 派生的 review artifact；
* 只读的理解与审核视图；
* 不可直接继承的辅助对象。

---

## 3.3 真相源原则

本 ADR 明确冻结：

## **Machine SSOT 是唯一权威源。**

因此：

* Projection 不是权威源；
* Projection 不能替代 SSOT；
* Projection 不能直接作为下游 `TECH / TASK / TESTSET / IMPL` 的输入；
* Projection 上的人类批注，只有在回写 SSOT 后才算正式修订。

正式口径如下：

> **Projection 可读，不可继承；SSOT 可继承，可冻结。**

---

# 4. 目标与适用范围

## 4.1 目标

本规则同时满足两件事：

1. 保证 SSOT 对 AI 足够稳定、结构化、可继承。
2. 保证 gate 阶段的人类能快速理解产品、发现问题、做判断。

## 4.2 适用范围

该规则适用于以下 SSOT 层级：

* `SRC`
* `EPIC`
* `FEAT`
* `TECH`
* `TESTSET`

当前优先适用层级为：

* `EPIC`
* `FEAT`

原因是这两层最容易出现“AI 可消费，但人类不易快速理解”的张力。

---

# 5. 角色定位

## 5.1 Machine SSOT 的职责

Machine SSOT 的职责是冻结正式业务与治理边界，而不是成为最佳阅读稿。

它必须继续保持：

* 结构化
* 字段稳定
* 术语一致
* 约束显式
* 对 AI 友好

采用本 ADR 后，Machine SSOT 不要求为了人类阅读体验而过度 narrative 化。

## 5.2 Human Review Projection 的职责

Human Review Projection 的职责是把 SSOT 翻译成更适合人类理解与判断的审核视图。

它应重点呈现：

* 这是什么产品 / 这条流是什么；
* 谁在使用，为什么使用；
* 主业务流如何闭合；
* 关键交付物是什么；
* 审核人最应该盯什么；
* 当前风险与歧义点在哪里。

Projection 的重点是解释、重组、强调，而不是新增正式语义。

---

# 6. 使用流程

标准流程正式冻结如下：

## Step 1

产出或修订 `Machine SSOT`

## Step 2

基于最新 `Machine SSOT` 自动生成 `Human Review Projection`

## Step 3

人类基于 Projection 做 gate 审核

## Step 4

审核意见回写到 `Machine SSOT`

## Step 5

SSOT 更新后重新生成 Projection

## Step 6

以更新后的 `Machine SSOT` 作为冻结结果进入下游

这里的关键约束是：

## **gate 决策可以参考 Projection，但 freeze result 必须锚定 SSOT。**

---

# 7. Human Review Projection 的标准模板

Projection 不允许自由发挥，必须模板化生成，以避免同一 SSOT 每次渲染出不同关注点。

## 7.1 EPIC Projection 最小模板

对 `EPIC`，Projection 至少包含：

### 1. Product Summary

说明这是什么产品能力块，它解决什么问题。

### 2. Product Line Summary

说明整条主线由哪些产品流组成，当前 EPIC 位于哪里。

### 3. Roles and User Stories

汇总核心角色与诉求，转写成人类可快速理解的形式。

### 4. Epic Scope / Non-goals

明确这轮做什么、不做什么。

### 5. Review Focus

指出本轮 gate 最值得人工检查的问题。

### 6. Risks / Ambiguities

列出当前存在的歧义、遗漏、边界风险。

## 7.2 FEAT Projection 最小模板

对 `FEAT`，Projection 至少包含：

### 1. Flow Summary

说明这条流是什么，位于主链的哪个位置。

### 2. Usage Narrative

说明谁在什么场景下触发它，完成后谁拿到什么。

### 3. Main Business Flow

用 5 到 10 步串起主流程，不要求审核人自己拼接多个机器字段。

### 4. Key Deliverables

明确本切片最终产出什么，哪个是 business deliverable，哪个是 authoritative output。

### 5. Authoritative Snapshot

这部分必须保留，并且应尽量短，但必须明确列出：

* `completed state`
* `authoritative output`
* `frozen downstream boundary`
* `open technical decisions`

### 6. Review Focus

至少覆盖以下检查方向：

* 产品形态是否清楚；
* 流转是否闭合；
* 交付物是否唯一；
* 是否把产品定义责任偷渡给 `TECH`；
* 回流 / 拒绝 / 重试路径是否完整。

### 7. Risks / Ambiguities

列出潜在风险、歧义术语、可能缺失的异常流、可能重叠的 FEAT 边界等。

---

# 8. Projection 的生成约束

Human Review Projection 在生成时必须遵守以下硬约束：

## 8.1 只能解释、重组、压缩已有 SSOT

Projection 可以：

* 翻译机器字段为人类语言；
* 合并分散字段为主线视图；
* 强调值得审核的要点；
* 推导出需要人工关注的风险与歧义点。

Projection 不可以：

* 擅自新增 authoritative 定义；
* 擅自改写完成态；
* 擅自改写输出边界；
* 擅自引入新的冻结承诺。

## 8.2 必须保留 authoritative snapshot

Projection 不能只剩 narrative。

如果人类只看到故事而看不到正式约束，就会遗漏：

* authoritative output 是否唯一；
* admission / completion 规则是否闭合；
* fallback 是否受控；
* 下游 boundary 是否已经冻结。

因此，Projection 必须保留一个短而硬的 authoritative snapshot。

## 8.3 必须模板化

同类对象必须使用稳定模板，避免：

* 同样的 SSOT 产生不同审稿重点；
* 审核人每次看到不同结构；
* review view 自由发挥后产生语义漂移。

---

# 9. 禁止事项

以下行为被视为违反本 ADR：

## 9.1 禁止把 Projection 当成 SSOT 使用

Projection 不是正式真相源。

## 9.2 禁止只改 Projection、不改 SSOT

如果修改没有回写到 SSOT，则不构成正式修订。

## 9.3 禁止 Projection 自由发挥新增权威语义

Projection 只能解释与组织 SSOT，不能新增 authoritative 定义。

## 9.4 禁止下游直接继承 Projection

`TECH / TASK / TESTSET / IMPL` 只能继承 `Machine SSOT`。

## 9.5 禁止用 narrative 掩盖 authoritative 约束

Projection 不能把 authoritative snapshot 淹没在纯叙述文本里。

---

# 10. 验收标准

本规则生效后，以下标准同时满足时才算成立。

## 10.1 对 AI

* 下游仍只依赖 `Machine SSOT`；
* SSOT 仍可稳定下钻 `TECH / IMPL / TESTSET`；
* 字段与术语保持稳定；
* validator / freeze 逻辑不需要改读 Projection。

## 10.2 对人类

* gate 审核时无需手工拼装主线；
* 审核人能快速理解产品、功能、流转与交付物；
* 审核人能明确指出问题并将意见回写 SSOT。

## 10.3 对治理

* 不新增第二真相源；
* 不引入“审核稿漂移”；
* 审核意见最终都沉淀回 SSOT；
* freeze decision 仍可被追溯到正式 SSOT。

---

# 11. 当前执行策略

本 ADR 生效后，立即采用以下策略：

## EPIC / FEAT

* SSOT 本体继续保持机器优先；
* gate 阶段新增 `Human Review Projection`；
* Projection 采用固定模板生成；
* 审核意见必须回写 SSOT；
* 冻结结果以 SSOT 为准。

后续如要把该模型扩展到 `SRC / TECH / TESTSET`，应保持同一原则：

* **review view 是派生物，不是新的对象层。**

---

# 12. 结论

LL / LEE 在 SSOT 治理上，正式采用：

## **机器优先本体 + 人类审核投影视图**

其正式含义是：

> **SSOT 是唯一权威源，继续服务 AI 执行、继承、验证与冻结；Projection 是 gate 阶段的人类友好审核视图，只负责帮助理解与评审，不构成新的真相源。审核在 Projection 上进行，冻结与下游继承仍以 SSOT 为准。**
