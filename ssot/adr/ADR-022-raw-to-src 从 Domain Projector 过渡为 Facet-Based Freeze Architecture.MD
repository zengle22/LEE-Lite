# ADR-022：raw-to-src 从 Domain Projector 过渡为 Facet-Based Freeze Architecture

* 状态：Draft
* 日期：2026-03-30
* 决策者：Le Zeng
* 适用范围：`product.raw-to-src`、`SRC` 高保真冻结层、`src-to-epic` 及后续派生 workflow 的上游语义继承方式
* 相关 ADR：ADR-002、ADR-008、ADR-010、ADR-019、ADR-021

---

# 1. 背景

ADR-019 已经正式把 `raw-to-src` 从 thin bridge summary 升级为：

## **High-Fidelity SRC Normalizer + Bridge Projection**

这解决了一个关键问题：

* `SRC` 不应只是给下游路由的一页摘要；
* `SRC` 必须重新承担上游 normalized source 的职责；
* 复杂 raw 中的重要语义不能在 `raw-to-src` 层被静默压缩掉。

但 ADR-019 之后出现了一个新的工程问题：

## **generic shell 仍然不够表达复杂 product raw，而单纯增加 domain projector 又会把系统拖向模板膨胀。**

最近这轮 `smart-plan-generation-v2-mvp` 的候选包已经暴露了这点：

* 只用 generic shell 时，文档虽然可追溯，但会退化成“有壳无骨”的摘要；
* 误套 onboarding projector 时，骨架看起来完整，但语义会串题；
* 如果继续沿“每来一个领域补一个 projector”走下去，维护成本会线性增长，规则还会越来越隐式。

因此，需要一份新的 ADR，回答两个问题：

1. `raw-to-src` 后续到底应该继续沿“领域模板”演进，还是升级为更通用的结构化抽取系统；
2. 如果 `raw-to-src` 采用 facet 化，后续 `src-to-epic / epic-to-feat / feat-to-tech / feat-to-ui / feat-to-testset` 是否也必须按领域继续复制 projector 体系。

---

# 2. 问题陈述

当前真正要解决的问题，不是“是否允许继续增加 projector”，而是下面四个更根本的问题。

## 2.1 为什么单纯增加 domain projector 不是长期解法

按领域持续增加 projector，表面上只是增加模板，实质上是在增加一组新的隐式系统：

* 分类规则；
* 语义冻结规则；
* 字段映射规则；
* review 检查规则；
* 演进兼容逻辑。

这会导致 `raw-to-src` 很快变成一个越来越难维护的“专家规则堆”。

## 2.2 为什么真实 raw 很难保持单一领域归类

真实输入经常同时包含多种语义侧面，例如：

* object model；
* state machine；
* workflow；
* policy / decision；
* reporting / deliverable；
* provenance / audit。

因此，很多问题不是“它属于 onboarding 还是 training-plan”，而是：

> **这份 raw 同时具备哪些值得冻结的语义维度。**

如果仍然强行单选某个领域 projector，就会把混合型问题压扁。

## 2.3 为什么 projector 膨胀会侵蚀 SSOT 的单一性

如果越来越多关键结构都只写在 projector 逻辑中，那么系统最终会变成：

* 一部分规则在文档里；
* 一部分规则在 projector 里；
* 一部分规则在 review gate 里。

久而久之，真正的权威定义就不再只存在于 `SRC`，而开始分散到实现逻辑中。

## 2.4 为什么后续 workflow 不应重复复制领域分类体系

如果 `raw-to-src`、`src-to-epic`、`epic-to-feat`、`feat-to-tech`、`feat-to-ui`、`feat-to-testset` 都各自维护一套按领域分类的 projector：

* 相同语义会在多层被重复理解；
* 不同层的分类边界会逐渐漂移；
* 上游冻结过的对象与枚举会在下游被二次改写；
* 维护成本会按 workflow 数量乘上领域数量一起膨胀。

这不是主链应有的演进方式。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **generic kernel + facet inference + facet extractor registry + freeze policy registry + unified SRC composer + review/freeze gate**

作为 `raw-to-src` 的目标架构。

从 ADR-022 起：

1. `raw-to-src` 的长期扩展单位不再是“领域模板”，而是“语义 facet”。
2. domain projector 允许继续存在，但只作为过渡层和推荐 bundle，不再作为长期唯一扩展机制。
3. `SRC` 的冻结内容由：
   * generic shell
   * selected facets
   * freeze policy
   共同决定，而不是由单一 projector 硬编码决定。
4. 后续 workflow 默认不新增按领域复制的一整套 projector；优先继承 `SRC` 已冻结的 facet 结果，必要时只新增 facet-aware consumer。

一句话定义：

> **raw-to-src 的本质不是“给 raw 套领域模板”，而是“把 prose 中对下游最重要的结构显式化”。**

---

## 3.2 核心架构

ADR-022 将 `raw-to-src` 的职责拆成六层。

### 1. Generic Kernel

负责完全通用、与领域无关的输入整理工作：

* intake
* source snapshot
* provenance
* normalization notes
* ambiguity register
* omission / compression report

这一层不承担领域判断，也不承担业务冻结规则。

### 2. Facet Inference

负责判断这份 raw 具备哪些值得冻结的语义维度，例如：

* 是否存在核心对象体系；
* 是否存在状态流转；
* 是否存在必须冻结的枚举；
* 是否存在 hard constraints；
* 是否存在判定逻辑或 policy；
* 是否存在主输出与附属视图区分；
* 是否存在 workflow step / precondition / postcondition；
* 是否存在指标、依赖、时序或 actor/role 结构。

Facet inference 的输出不是“属于哪个领域”，而是：

## **这份 raw 需要哪些 facet。**

但 ADR-022 同时明确：

## **facet inference 不是最终真相，只是 facet selection 的候选来源。**

正式顺序应固定为：

1. facet inference 产出 candidate facets；
2. bundle recommender 产出建议组合；
3. review / gate 决定最终 `selected facets`；
4. unified composer 只消费最终 `selected facets`。

也就是说：

* inference 可以漏，也可以多；
* bundle recommender 可以给偏向性建议；
* 真正进入 `SRC` 的 facet 集合，必须经过 selection / review 决议；
* composer 不得直接把 inference 结果视为权威输入。

为了避免把“有价值的语义”误等同于“应该做 facet”，ADR-022 进一步明确：

* 不是所有重要语义都应进入 facet registry；
* 只有能稳定服务多类 raw、并且能以更低重叠度提升下游派生质量的语义，才值得抽象成 facet；
* 强领域特异、一次性、仅适合单个项目的语义，应优先保留为 raw 层文本、bundle recommender 规则或局部派生逻辑，而不是提升为 facet。

### 3. Facet Extractor Registry

`raw-to-src` 正式以 facet extractor 作为可扩展单位。

首批推荐支持的 facet 包括：

* `object_model`
* `state_machine`
* `enumeration`
* `constraint`
* `decision_policy`
* `workflow`
* `view_deliverable`
* `actor_role`
* `dependency`
* `metric`
* `provenance_normalization`

这些 facet 是跨领域可复用的结构能力，而不是领域模板。

ADR-022 进一步冻结：

## **不是“凡是重要语义都做 facet”，而是“凡是可复用、可冻结、可校验的结构能力，才允许进入 facet registry”。**

因此，一个新 facet 只有同时满足以下准入条件时，才允许进入 registry：

1. `跨领域复用`
   * 不能只服务一个非常狭窄的问题或单个业务题。
2. `对下游派生有高价值`
   * 提取后应显著降低 `SRC -> EPIC -> FEAT -> TECH/UI/TESTSET` 的继承漂移风险。
3. `可定义冻结粒度`
   * 必须能清楚说明最小冻结单元是什么，而不是只描述一个模糊概念。
4. `可做 gate 校验`
   * 必须能形成 review / freeze gate 的显式检查项，否则只是装饰性结构。
5. `与其他 facet 低重叠`
   * 必须能与现有 facet 保持相对解耦，避免 registry 只是把同一能力拆成多个高度重叠名字。

如果一个候选能力不满足以上条件，则应优先处理为：

* 某个现有 facet 的字段扩展；
* 某个 bundle recommender 的启发式规则；
* 或某层 workflow 的局部派生逻辑；

而不是直接新增 facet。

反过来说，凡是满足“高价值”但不满足“跨领域复用 / 可冻结粒度 / 可 gate 校验 / 低重叠”的语义，都不应硬塞进 facet registry。

### 4. Freeze Policy Registry

真正需要配置化的，不是“某个领域长什么样”，而是：

> **在识别到某类 facet 时，哪些内容必须冻结到什么粒度。**

例如：

* 如果检测到 `state_machine`，则必须输出：
  * states
  * transitions
  * terminal states
  * forbidden transitions
  * unresolved ambiguities
* 如果检测到 `enumeration`，则必须输出：
  * canonical values
  * aliases in raw
  * normalization decisions
  * extension policy
* 如果检测到 `view_deliverable`，则必须区分：
  * primary deliverable
  * supporting views
  * derived reports
  * non-authoritative renderings

### 5. Unified SRC Composer

`SRC` 由统一 composer 负责输出。

它的输入是：

* generic shell
* selected facets
* freeze policies

它的输出仍然是统一的 `SRC candidate` 结构，而不是不同领域各自长成不同文档。

### 6. Review / Freeze Gate

review gate 不再跟着 projector 名称走，而应按 facet 做检查。

例如：

* 有 `enumeration` facet，则检查枚举是否冻结完整；
* 有 `state_machine` facet，则检查状态迁移是否闭合；
* 有 `constraint` facet，则检查 hard / soft 约束是否分层；
* 有 `view_deliverable` facet，则检查 primary output 是否被显式声明。

---

## 3.3 Domain Projector 的新地位

ADR-022 不要求立刻删除所有 projector。

相反，本 ADR 正式允许保留 projector 外壳，但重新定义其角色：

## **projector 不再是“领域模板”，而是 facet bundle recommender。**

例如：

* onboarding projector
  * 推荐 `actor_role + workflow + decision_policy + view_deliverable`
* training-plan projector
  * 推荐 `object_model + state_machine + enumeration + constraint + view_deliverable`
* governance-bridge projector
  * 推荐 `object_model + workflow + decision_policy + provenance_normalization + constraint`

也就是说，projector 在过渡期可以存在，但内部必须退化为：

* facet 推荐器；
* facet 配置器；
* optional hint provider。

它不再是长期持有业务真相的地方。

---

## 3.4 Facet 中间表示

ADR-022 明确要求，facet 抽取优先产出结构化 IR，而不是直接写 prose。

推荐的最小中间表示如下：

```yaml
facets:
  object_model:
    confidence: high
    entities: ...
  state_machine:
    confidence: medium
    states: ...
    transitions: ...
  enumeration:
    confidence: high
    fields: ...
  constraint:
    confidence: high
    hard_rules: ...
    soft_rules: ...
  view_deliverable:
    confidence: medium
    primary_output: ...
    supporting_views: ...
```

这样可以把“抽取”和“成文”解耦，避免每次都重新把规则写死在文档模板中。

---

# 4. 可行性判断

本 ADR 判断该方案：

## **可行，而且比继续堆 domain projector 更可持续。**

理由如下。

## 4.1 它兼容 ADR-019，不要求推翻现有 high-fidelity SRC 方向

ADR-019 已经确立：

* `SRC` 必须成为 high-fidelity normalized source；
* 现有 bridge 字段继续作为兼容投影层。

ADR-022 只是把“高保真内容如何生成”从 projector 规则堆，进一步升级成 facet 系统。

因此两者不是冲突关系，而是递进关系。

## 4.2 它允许分阶段迁移，不要求一次性重写全部 workflow

ADR-022 允许先在 `raw-to-src` 落地：

* facet inference
* facet extractor registry
* freeze policy

下游 workflow 第一阶段只需要继续消费 `SRC` 现有结构，不必立刻重构。

## 4.3 它更适合混合型 raw

很多输入天然同时包含多个语义维度。

facet 化之后，系统不必强迫它们进入某个单一领域，而是可以组合抽取，显著降低“分类先行导致语义压扁”的风险。

## 4.4 它让 gate 规则更稳定

按 facet 校验，比按 projector 名称校验更规则化、更容易维护，也更适合后续把审查标准沉淀为统一治理能力。

---

# 5. 对后续 workflow 的要求

## 5.1 不要求每个后续 workflow 都新增领域 projector

ADR-022 明确：

## **后续 `src-to-epic / epic-to-feat / feat-to-tech / feat-to-ui / feat-to-testset` 不应默认各自新增一套按领域复制的 projector。**

更合理的原则是：

1. `raw-to-src` 负责首次把高风险语义冻结为 facet 结果；
2. 下游 workflow 优先消费和继承这些冻结结果；
3. 只有当某一层存在新的、该层专有的语义压缩风险时，才允许新增该层的 facet-aware derivation logic；
4. 即使新增，也应优先复用 facet 体系，而不是重新发明领域模板。

## 5.2 下游 workflow 的 facet 继承协议

ADR-022 明确，下游 workflow 默认不重新解释上游已冻结 facet，而应按以下三种协议消费：

### 1. `inherit-as-authoritative`

含义：

* 直接继承；
* 不允许改写定义；
* 只允许引用，不允许在下游重命名后重新定义语义。

适用示例：

* object model 中的 canonical entities
* canonical enumeration values
* state machine 中的 canonical state names
* hard constraints

### 2. `inherit-and-project`

含义：

* 上游定义不改；
* 允许在本层按本层视角重新组织、切片或投影；
* 但不得改变权威含义。

适用示例：

* workflow
* deliverable / view
* dependency

### 3. `derive-with-justification`

含义：

* 允许本层基于上游 frozen facets 产生新的解释、映射或拆分；
* 但必须显式说明 `derived_from` 与 `rationale`；
* 不得伪装成新的上游权威定义。

适用示例：

* tech 分解
* UI 表现映射
* testset 覆盖映射

一句话原则：

> **下游 workflow 默认不重新发明上游已冻结 facet；如需新增解释，必须说明它是如何从上游派生出来的。**

为了便于 review / gate 执行，这三类协议的选择规则也一并冻结：

* `inherit-as-authoritative` 适合定义层、枚举层、状态层、硬约束层；
* `inherit-and-project` 适合本层只做切片、不改语义的 deliverable / workflow / view 层；
* `derive-with-justification` 适合必须结合本层职责重新组织的实现、界面或测试语义，但必须显式写出 `derived_from` 和 `rationale`。

示例补充：

* `plan_lifecycle` 的 canonical state names 应走 `inherit-as-authoritative`，下游不能改名后再当作新真相；
* `today_session` 在 `src-to-epic` 或 `feat-to-ui` 中通常走 `inherit-and-project`，因为它是对既有冻结结果的视图切片；
* `session_feedback` 在 `feat-to-tech` 或 `feat-to-testset` 中可走 `derive-with-justification`，因为实现和测试需要把同一冻结事实拆成接口、表单和断言，但不能把拆分后的字段反过来当作上游定义。

## 5.3 后续 workflow 的推荐演进方式

### `src-to-epic`

应逐步变成：

* facet-aware epic decomposition consumer

它关心的是：

* 哪些 facet 已被冻结；
* 哪些 facet 应投影成 EPIC 级边界；
* 哪些 facet 只是继承背景，不应在 EPIC 层重定义。

### `epic-to-feat`

应逐步变成：

* facet-preserving feature decomposition consumer

它关心的是：

* 哪些冻结对象、状态、枚举要落入 FEAT 范围；
* 哪些规则必须被显式继承；
* 哪些 FEAT 只是按产品行为切片，而不是重写 source-layer 语义。

### `feat-to-tech / feat-to-ui / feat-to-testset`

更不应按领域复制 projector。

它们应主要围绕：

* interface / implementation / UI / test concerns
* consumption of inherited frozen facets

必要时可以有自己的 facet-aware consumer，但不应再回到“重新理解 training-plan/onboarding/governance-bridge 到底是什么”的层面。

---

# 6. 迁移策略

ADR-022 采用三阶段迁移。

## 6.1 Phase 1：Projector 外壳保留，内部 facet 化

第一阶段允许继续保留：

* onboarding projector
* training-plan projector
* governance-bridge projector

但它们内部必须改为 facet bundle 推荐器，而不是继续发展成独立模板体系。

## 6.2 Phase 2：Projector Registry 降级为 Facet Bundle Registry

第二阶段中：

* “领域分类”不再是强制单选；
* projector 只提供建议 facet 组合；
* 系统可按实际 raw 增减 facet。

## 6.3 Phase 3：Gate 全面 facet-aware

第三阶段中：

* structural review
* semantic review
* acceptance review

都应按 facet completeness / freeze policy 来做，而不是按 projector 名称做分支判断。

---

# 7. 明确拒绝的方案

## 7.1 继续用一个 generic template 硬吃所有 raw

不选原因：

* 文档会退化成规范化摘要；
* 很难稳定支撑下游派生；
* 关键对象、状态、枚举、约束仍然容易漂移。

## 7.2 继续按领域无限增加 projector

不选原因：

* 维护成本高；
* 混合型问题难处理；
* 规则会分散到 projector 实现中；
* 最终侵蚀 SSOT 的单一性。

## 7.3 让后续每一层 workflow 都各自复制一套领域 projector

不选原因：

* 上游已冻结语义会被多次重复理解；
* 不同 workflow 会逐渐形成不同的领域边界；
* 主链整体复杂度会指数式上升。

---

# 8. 后果

采用 ADR-022 后，系统会出现以下变化。

## 8.1 对 `raw-to-src`

* 扩展单位从“领域模板”转向“语义 facet”；
* projectors 由权威模板降级为过渡期 facet bundle 推荐器；
* gate 可以更明确地阻断“有壳无骨”的空心候选。

## 8.2 对 `SRC`

* `SRC` 仍保持统一文档骨架；
* 但内部冻结内容由 selected facets 决定；
* `SRC` 的真相来源更多地回到显式结构，而不是实现逻辑。

## 8.3 对下游 workflow

* 不再默认要求各层新增领域 projector；
* 优先继承和消费 `raw-to-src` 已冻结的 facet 结果；
* 只在确有必要时新增 facet-aware consumer，而不是新增领域模板。

---

# 9. 一句话结论

ADR-022 正式规定：

## **`raw-to-src` 的长期方向不是“generic kernel + 越来越多的 domain projector”，而是“generic kernel + semantic facets + freeze policy + unified review gate”；projector 只保留为过渡期的 facet bundle 推荐器，而后续 workflow 默认继承 facet 结果，不再按领域重复复制 projector 体系。**
