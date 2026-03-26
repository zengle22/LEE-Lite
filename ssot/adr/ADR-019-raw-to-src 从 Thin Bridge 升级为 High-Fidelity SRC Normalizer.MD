# ADR-019：raw-to-src 从 Thin Bridge 升级为 High-Fidelity SRC Normalizer

* 状态：Draft
* 日期：2026-03-26
* 决策者：Le Zeng
* 适用范围：`product.raw-to-src`、`product.src-to-epic`、ADR 类输入的主链继承语义、SRC 上游真相保真策略
* 相关 ADR：ADR-001、ADR-002、ADR-003、ADR-005、ADR-008、ADR-010、ADR-018

---

# 1. 背景

当前仓库中的 `raw-to-src` 已经成功承担了以下职责：

* 接住未经治理的原始输入；
* 把输入统一转换为一个可被主链消费的 `SRC candidate`；
* 在 skill 内执行最小结构修补、review、evidence 落盘；
* 通过正式 gate 接缝把结果送入第二会话 pending queue；
* 让 `src-to-epic`、`epic-to-feat` 等下游能够消费稳定字段，而不是直接读取原始文本。

这一设计在 ADR-002 中是合理的，因为当时的首要目标是：

## **尽快跑通主链，而不是先把 SRC 做成最大语义保真载体。**

因此，`raw-to-src` 被刻意设计为：

* 单一输入归一化节点；
* 双环修复节点；
* gate-ready producer；
* thin bridge SRC producer。

其重点是：

* 单题归一化；
* 稳定 schema；
* 外挂 gate；
* 下游可路由；
* 避免在最上游就滑入 EPIC / FEAT / TECH / IMPL 设计展开。

这套设计解决了主链启动问题，但也带来了新的问题：

## **对于复杂 ADR，尤其是同时包含 runtime、operator control surface、CLI 入口、监控面和恢复策略的输入，thin bridge 容易把关键信息压缩掉。**

ADR-018 就暴露了这个问题：

* ADR 原文中存在 `workflow 入口`、`CLI-first control surface`、`观测与监控面` 等语义；
* 但当前 `raw-to-src` 产出的 `SRC` 更像治理摘要；
* 进入 `src-to-epic` 后，下游继续继承的是被压缩后的字段，而不是原始需求语义全貌。

因此，需要对 `raw-to-src` 的职责模型进行一次正式升级。

---

# 2. 问题陈述

当前需要解决的核心问题，不是“`raw-to-src` 能不能继续工作”，而是：

* `raw-to-src` 产出的 `SRC` 是否仍然是主链的上游真相，还是已经退化为一份便于路由的摘要；
* 对复杂 ADR 而言，`SRC` 是否只保留了治理摘要，而丢失了 operator-facing 入口、运行控制面、观测面等重要产品语义；
* `src-to-epic` 下游当前消费的字段，是否让上游被迫提前压缩，而不是允许下游从完整 `SRC` 中选择性投影；
* `review` 当前是否只检查“bridge 是否够薄、够像桥接摘要”，却没有检查“关键语义是否已被不当压缩或遗漏”；
* 系统是否需要把 `SRC` 从 thin bridge 升级为高保真 normalization layer，同时继续保留现有 bridge 字段兼容下游。

如果不调整，系统会继续出现以下结构性问题。

## 2.1 `SRC` 从“上游真相”退化为“可路由摘要”

`raw-to-src` 当前对 ADR 输入的首要行为是生成 `governance_bridge_src`。

这让 `SRC` 更像一份主链治理摘要，而不是 raw source 的高保真 normalized source。

## 2.2 复杂 operator / control surface 语义容易在 SRC 层被压缩掉

对于 ADR-018 这类输入，用户真正要构建的并不只是“后台自动推进 runtime”，还包括：

* 单独的 operator-facing skill 入口；
* 通过 Claude / Codex CLI 触发的启动入口；
* 初始化、resume、repair、monitor 等控制面；
* backlog / running / failed / deadletter 等观测面。

这些内容如果在 SRC 层就丢失，下游很难再稳定恢复。

## 2.3 下游派生被迫围绕压缩字段工作

当前 `src-to-epic` 主要消费：

* `problem_statement`
* `target_users`
* `business_drivers`
* `key_constraints`
* `in_scope`
* `out_of_scope`
* `bridge_context`
* `semantic_lock`

这意味着上游如果没有把复杂语义冻结进这些字段，下游很难再补回。

## 2.4 review 当前只检查 bridge 质量，不检查保真质量

当前 `raw-to-src` review 关注：

* same-topic fidelity；
* bridge density；
* semantic lock completeness；
* placeholder content；
* downstream actionability。

但它没有正式检查：

* 哪些 raw 语义被省略；
* 哪些语义被压缩；
* 是否遗漏 operator / control surface；
* 是否存在未显式记录的矛盾；
* `SRC` 是否仍足以独立作为上游真相。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **High-Fidelity SRC Normalizer + Bridge Projection**

作为 `raw-to-src` 的新职责模型。

其核心原则如下：

1. `raw-to-src` 继续是唯一原始输入归一化路径；
2. `raw-to-src` 不再只产出 thin bridge summary；
3. `SRC` 必须同时包含：
   * 高保真 normalized source layer；
   * 向下游兼容的 bridge projection layer；
4. 现有 `problem_statement / bridge_context / semantic_lock` 等字段继续保留，作为下游兼容投影视图；
5. 新增高保真字段用于保留 raw 语义、显式记录压缩、冲突、operator surface 和 provenance；
6. `review` 必须从“bridge density 检查”升级为“bridge density + semantic preservation 检查”；
7. `src-to-epic` 第一阶段保持兼容，不立即强依赖新增字段；
8. 后续由 `src-to-epic`、`epic-to-feat`、`feat-to-tech` 逐步开始消费高保真字段。

---

## 3.2 正式定义

从 ADR-019 起，`raw-to-src` 的正式输出模型不再是：

* `raw source -> thin bridge SRC`

而是：

* `raw source -> high-fidelity SRC`
* `high-fidelity SRC -> bridge projection`

其中：

### 1. High-Fidelity Source Layer

负责：

* 整理；
* 结构化；
* 术语统一；
* 去重；
* 矛盾显式化；
* provenance 保留；
* operator / CLI / monitoring / control surface 保真；
* 明确记录哪些信息被压缩、哪些未决。

### 2. Bridge Projection Layer

负责：

* 给下游当前 workflow 提供兼容字段；
* 将高保真 `SRC` 投影为主链可稳定消费的治理摘要与继承约束；
* 不替代 high-fidelity source layer；
* 不构成唯一上游真相。

---

# 4. 旧模型与新模型对比

## 4.1 旧模型：Thin Bridge Summarizer

旧模型的主要优点：

* 简单；
* schema 稳定；
* 易于做 gate-ready routing；
* 适合快速打通 `raw-to-src -> src-to-epic -> epic-to-feat` 主链；
* 可在最上游阻断多主题、重复真相和明显不安全输入。

旧模型的主要缺点：

* `SRC` 容易退化为治理摘要；
* 对复杂 ADR 的语义保真不足；
* operator / control surface / monitoring surface 等信息容易在 bridge synthesis 中被压缩；
* review 不具备“语义遗漏”检查能力；
* 下游容易继承压缩字段，而不是继承原始语义全貌。

## 4.2 新模型：High-Fidelity SRC Normalizer

新模型的主要优点：

* `SRC` 重新成为真正的上游 normalized source；
* 复杂 ADR 的关键语义不必在 SRC 层被提前压缩；
* operator-facing skill 入口、CLI 启动面、初始化和监控面等内容可以被显式冻结；
* 下游仍然可以继续消费 bridge projection，而不会立刻被打断；
* 之后可逐步让下游更多依赖高保真字段，而不是依赖摘要猜测。

新模型的主要成本：

* `SRC` 体积会更大；
* `review` 更复杂；
* 需要新增 schema / artifact / validation；
* 不能再只依赖 bridge density 来判断 freeze-readiness。

---

# 5. 新增的 High-Fidelity 字段与产物

从 ADR-019 起，`raw-to-src` 应在保留现有字段的同时，新增以下 high-fidelity 字段或独立 artifact。

## 5.1 `semantic_inventory`

用于列出 raw 中被冻结的关键语义对象。

至少应覆盖：

* actors
* product surfaces
* operator surfaces
* entry points
* commands
* runtime objects
* states
* observability surfaces
* constraints
* non-goals

## 5.2 `source_provenance_map`

用于把 `SRC` 中的关键字段追溯回原始输入片段。

至少应能回答：

* 哪个字段来自 raw 的哪一段；
* 是原样保留、标准化还是摘要化；
* 若进行了压缩，压缩发生在哪里。

## 5.3 `contradiction_register`

用于显式记录 raw 中存在的冲突、歧义和未决点。

不得让系统在未记录的情况下静默吞掉矛盾。

## 5.4 `normalization_decisions`

用于记录 normalization 过程中做出的结构化决定。

例如：

* 哪些术语被统一；
* 哪些列表被去重；
* 哪些表述被折叠为 canonical term；
* 哪些字段因不完整而被保守表达。

## 5.5 `omission_and_compression_report`

用于显式说明：

* 哪些信息被省略；
* 哪些信息被压缩；
* 为什么这样处理；
* 对下游理解是否存在风险。

## 5.6 `operator_surface_inventory`

这是 ADR-019 的关键新增项。

用于冻结：

* 单独的 operator-facing skill 入口；
* CLI control surface；
* initialization / resume / repair / monitor 等操作面；
* 相关 user actor；
* 相关输入输出；
* 相关状态和观测接口。

对于 ADR-018 这类输入，如果 `operator_surface_inventory` 缺失，则不得视为高质量 freeze-ready `SRC`。

---

# 6. review 与 freeze-readiness 新规则

从 ADR-019 起，`raw-to-src` review 不再只做 bridge density 检查，还必须新增以下检查维度：

1. `semantic_preservation`
   * 关键 raw 语义是否仍然保留在 `SRC`

2. `operator_surface_preserved`
   * 若 raw 存在 operator / CLI / monitor surface，`SRC` 是否已显式冻结

3. `contradictions_explicit`
   * 所有可识别冲突是否进入 `contradiction_register`

4. `compression_risk_acceptable`
   * 所有压缩与省略是否已记录，且风险可接受

5. `bridge_projection_consistent_with_source_layer`
   * 兼容字段是否正确反映了 high-fidelity source layer，而不是另起一套摘要真相

因此，从 ADR-019 起，`raw-to-src` 的 freeze-readiness 不再由“bridge 看起来够像 bridge”单独决定，而必须同时满足：

* bridge 可消费；
* high-fidelity source 足够完整；
* 关键语义未被静默压掉。

---

# 7. 与既有 ADR 的关系

## 7.1 与 ADR-002 的关系

ADR-002 冻结了：

* `raw-to-src` 是唯一原始输入归一化路径；
* 双环修复；
* 外挂 gate；
* candidate / evidence / proposal 的职责边界。

ADR-019 不推翻这些边界。

ADR-019 只修正一件事：

## **`raw-to-src` 的 candidate 不应只是 thin bridge summary，而应升级为 high-fidelity normalized source + bridge projection 的双层输出。**

## 7.2 与 ADR-003 的关系

ADR-003 冻结了：

* 文件化 handoff runtime；
* artifact / job / handoff / gate / evidence 对象分层。

ADR-019 不改变这些流转对象，只增强 `SRC candidate` 本身的内容密度和可继承性。

## 7.3 与 ADR-008 的关系

ADR-008 统一了主链与派生对象：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT -> TECH / IMPL / TESTSET / UI?`

ADR-019 的目标之一，正是确保 `SRC` 真正承担起作为主链上游真相的职责，而不是提前退化为摘要。

## 7.4 与 ADR-010 的关系

ADR-010 冻结了 `src-to-epic` 的具体实现。

ADR-019 规定：

* `src-to-epic` 第一阶段继续兼容现有 bridge 字段；
* 但后续允许逐步消费 high-fidelity `SRC` 字段；
* `src-to-epic` 不得继续假设 `SRC` 只有 bridge summary 一层。

## 7.5 与 ADR-018 的关系

ADR-018 原文包含：

* runner 自动推进语义；
* workflow 入口；
* CLI-first control surface；
* 观测与监控面。

ADR-019 规定：

## **这类 operator / CLI / monitor 语义不得在 raw-to-src 的 bridge synthesis 中被静默压缩。**

---

# 8. 对下游的兼容与影响

## 8.1 对 `src-to-epic` 的第一阶段影响

第一阶段要求：

* 不删除任何现有 bridge 字段；
* 不取消 `source_kind = governance_bridge_src`；
* 不取消 `bridge_context`；
* 不取消 `semantic_lock`；
* 不改变现有 `problem_statement / target_users / business_drivers / key_constraints / in_scope / out_of_scope` 的可读性。

因此，在第一阶段：

## **`src-to-epic` 不需要立即修改，就应当仍能继续运行。**

## 8.2 对 `src-to-epic` 的后续影响

后续允许 `src-to-epic` 逐步增加对 high-fidelity 字段的消费，例如：

* `operator_surface_inventory`
* `semantic_inventory`
* `contradiction_register`
* `omission_and_compression_report`

这样 `src-to-epic` 在复杂输入上不再只能依赖压缩字段。

## 8.3 对 `epic-to-feat` 与更下游的影响

在第一阶段，不要求它们立即消费新增字段。

但 ADR-019 为后续修复提供了基础：

* `epic-to-feat` 可以显式拆出 operator entry / control surface FEAT；
* `feat-to-tech` 可以为 operator-facing skill 入口产出 TECH / API / optional UI 设计；
* `TESTSET` 可基于 `operator_surface_inventory` 生成启动、监控、恢复相关测试集。

---

# 9. 迁移策略

ADR-019 正式采用三阶段迁移。

## 9.1 Phase 1：兼容增强

目标：

* `raw-to-src` 新增 high-fidelity 字段与 artifact；
* 保留现有 bridge 字段；
* 不要求 `src-to-epic` 修改。

输出特征：

* `SRC` 同时具有 high-fidelity source layer 与 bridge projection layer；
* 当前下游仍可按老字段消费。

## 9.2 Phase 2：review 升级

目标：

* `raw-to-src` review 新增 semantic preservation 检查；
* `ADR-018` 这类包含 operator surface 的输入，若未保留对应字段则必须 `revise`。

## 9.3 Phase 3：下游渐进消费

目标：

* `src-to-epic` 开始消费 `operator_surface_inventory` 等高保真字段；
* `epic-to-feat` 开始拆出 operator/control surface FEAT；
* `feat-to-tech` 为这些 FEAT 产出具体技术设计。

---

# 10. 明确不选的方案

## 10.1 方案 A：继续保持 thin bridge 不变

不选原因：

* 已经证明会在复杂 ADR 上压掉重要语义；
* `SRC` 继续会退化为路由摘要；
* 无法稳定支撑 `ADR-018` 这类含 operator surface 的需求。

## 10.2 方案 B：直接推翻现有 bridge contract

不选原因：

* 会立即打断 `src-to-epic`；
* 风险过高；
* 不符合 skill-first 主链渐进演进策略。

## 10.3 方案 C：把高保真保留责任完全推给 `src-to-epic`

不选原因：

* `src-to-epic` 只能消费 `SRC` 已经保留的语义；
* 如果 `SRC` 层已压缩，下游无法可靠恢复；
* 上游真相层职责会继续悬空。

---

# 11. 后果

采用 ADR-019 后，系统将出现以下变化：

1. `raw-to-src` 的职责会变重，但边界仍然清晰：
   * 它负责 high-fidelity normalization；
   * 不负责下游设计展开；
   * 不负责最终 gate decision。

2. `SRC` 重新成为真正的上游 normalized source，而不只是桥接摘要。

3. `src-to-epic` 第一阶段仍保持兼容，不必立即重写。

4. review 成本会上升，但系统对复杂 ADR 的保真度会显著提高。

5. 对 ADR-018 这类输入，operator-facing skill 入口、CLI control surface、初始化和监控面将可以在 `SRC` 层被正式冻结并稳定继承。

---

# 12. 一句话结论

ADR-019 正式规定：

## **`raw-to-src` 不再只是 thin bridge summarizer，而应成为 high-fidelity SRC normalizer；现有 bridge 字段保留为兼容投影视图，但不得继续替代完整的上游真相层。**

