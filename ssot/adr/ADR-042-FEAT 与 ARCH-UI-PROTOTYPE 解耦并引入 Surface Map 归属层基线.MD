# ADR-042：FEAT 与 ARCH-UI-PROTOTYPE 解耦并引入 Surface Map 归属层基线

* 状态：Accepted
* 日期：2026-04-06
* 决策者：Le Zeng
* 适用范围：`ll-product-epic-to-feat`、`feat_freeze_package`、未来 `surface_map_package` / `surface_map_bundle`、`ll-dev-feat-to-tech`、`ll-dev-feat-to-proto`、`ll-dev-proto-to-ui`、`ui_spec_package`、`prototype_package`、`architecture` / `api` / `ui` / `prototype` / `state-model` 类共享设计资产、`impl_candidate_package`
* 相关 ADR：ADR-008、ADR-011、ADR-021、ADR-034、ADR-038、ADR-040、ADR-041

---

# 1. 背景

仓库当前已经逐步冻结出一条产品主链：

```text
ADR -> SRC -> EPIC -> FEAT
```

并且已经补上若干 FEAT 的下游派生能力：

* ADR-021 冻结了 `FEAT -> UI Spec`
* ADR-040 将界面派生拆成 `FEAT -> PROTOTYPE -> UI`
* ADR-041 又在 prototype 前补上 `journey-ux-ascii.md` 与固定 `UI Shell Source`
* ADR-034 明确 `IMPL` 应消费上游冻结语义，而不是临时发明实现口径

这些决策本身是对的，但随着 FEAT 拆分粒度变细，系统开始暴露出另一类更基础的问题：

## **下游设计产物的归属粒度，正在被上游 FEAT 的拆分粒度错误继承。**

也就是说，当前实践里很容易默认形成以下隐含模型：

```text
1 FEAT = 1 TECH + 1 ARCH + 1 UI + 1 PROTOTYPE
```

这在真实工程里通常并不成立。

因为不同产物回答的是不同维度的问题：

* `FEAT` 更像功能责任单元，回答“这次要交付什么用户价值”
* `ARCH` 更像模块 / 子系统 / 领域边界责任单元
* `API` 更像服务域 / 契约族责任单元
* `UI` 更像页面骨架 / 信息架构 / 组件体系责任单元
* `PROTOTYPE` 更像主流程、交互流和状态体验骨架责任单元
* `TECH` 更像实现方案包或 touch-set 责任单元

这些对象天然不是同一条切分轴。

一旦 FEAT 被拆得较细，而设计资产仍被按 FEAT 一对一派生，系统就会出现以下退化：

* 多个 FEAT 共用同一份架构，却各自再写一份相似 `ARCH`
* 多个 FEAT 落在同一条 UI / Prototype 主流程里，却被拆成多份平行原型
* 一个 FEAT 只是修改已有系统资产的一小段 delta，却被误判为应该新建全套下游文档
* `IMPL` 阶段拿到多份边界重叠的设计文档，不知道哪一份才是 authority
* AI 在派生时默认走“为每个 FEAT 新建一套下游对象”的路径，导致数量膨胀和口径漂移

因此，当前真正需要修复的，不是“FEAT 要不要继续细拆”，而是：

## **必须把“功能拆分粒度”与“设计资产归属粒度”从制度上解耦。**

---

# 2. 问题陈述

本 ADR 要解决的不是文档数量表面上变多或变少，而是以下结构性问题。

## 2.1 FEAT 与设计资产当前被错误地绑定成同一条生产轴

如果系统隐含认为：

```text
pick -> FEAT -> TECH / ARCH / API / UI / PROTOTYPE
```

就等于默认：

* FEAT 拆多细，下游资产就拆多细
* FEAT 拥有设计资产，而不是引用设计资产
* 每次 FEAT 进入下游时，都优先 `create`，而不是先判断应归属到哪个已有资产

这会让本来应按长期责任边界维护的资产，被功能粒度切碎。

## 2.2 Shared Design Assets 的生命周期与 FEAT 根本不同

FEAT 更像执行单元：

* 面向交付
* 面向验收
* 可细粒度
* 生命周期相对短

而 `ARCH / API / UI / PROTOTYPE / STATE MODEL` 更像共享真相源：

* 面向系统长期定义
* 面向复用与约束
* 默认应持续演进
* 生命周期长

如果用 FEAT 粒度去驱动这类资产的创建频率，资产本身就不再稳定。

## 2.3 ADR-040 / ADR-041 的 Prototype 路线仍可能被 FEAT 粒度切碎

ADR-040 与 ADR-041 已经明确：

* `PROTOTYPE` 是体验冻结层
* `UI` 是实现契约层
* prototype 之前还要有 Journey Structural Spec 和固定 UI Shell Source

但如果系统仍把 prototype 视为“每个 FEAT 必须各自产出一份的附属文档”，那么：

* 主流程骨架会被切成多个局部原型
* 同一产品族的 page / sheet / modal / CTA 规则会再次发散
* `PROTO` 和 `UI` 虽然存在，但仍然没有变成真正的共享资产

因此，本 ADR 必须进一步规定：

## **Prototype / UI 是 shared design assets，不是 FEAT 的私有附属物。**

## 2.4 IMPL 阶段需要的是“resolved authority”，不是一组并行候选文档

ADR-034 已经要求：

* `IMPL` 应消费上游冻结对象
* `IMPL` 不应在实施阶段重新发明设计口径

但如果 FEAT 下游没有一个正式的归属步骤，`IMPL` 仍然会遇到：

* 到底该引用哪份 `ARCH`
* 到底该更新哪条 `PROTO`
* 当前 `UI Spec` 是新资产还是旧资产的 delta
* 本次代码 touch-set 到底落在哪个 shared asset 的 authority 下

这说明 FEAT 与设计资产之间缺少一层正式对象，用来先解决：

* 影响哪些设计面
* 这些设计面由谁承接
* 本次是 `update` 还是 `create`
* 修改范围是什么

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **将 FEAT 与 Shared Design Assets 解耦，并在两者之间引入强制的 `surface-map` 归属层。**

主链理解调整为：

```text
ADR -> SRC -> EPIC -> FEAT -> SURFACE-MAP -> SHARED DESIGN ASSETS -> IMPL
```

其中：

* `FEAT` 继续作为功能责任单元存在
* `SURFACE-MAP` 作为 FEAT 进入设计层的唯一归属入口
* `ARCH / API / UI / PROTOTYPE / STATE MODEL / GLOSSARY / TECH PACKAGE` 被统一视为 shared design assets
* `IMPL` 只能消费已经完成归属解析的 shared assets

本 ADR 冻结以下原则：

1. `FEAT` 默认不再一对一拥有 `ARCH / API / UI / PROTOTYPE`
2. 若 `design_impact_required = true`，则必须在 `feat_freeze_package` 之后、任何 design 派生之前先产出并冻结 `surface-map`
3. 设计层默认 `update existing`，只有引入新的长期责任边界时才允许 `create new`
4. `PROTOTYPE` 与 `UI` 在 ADR-040 / ADR-041 的双阶段链路继续成立，但不再按 FEAT 机械碎裂
5. `IMPL` 只能基于已归属的 shared assets 编写，不得在实现阶段临时补发明新设计口径

---

## 3.2 采用双层生产模型

本 ADR 正式把当前体系分成两层。

### A. 功能层产物

用于回答：

* 这次交付什么价值
* 成功条件是什么
* 验收边界是什么
* 哪些能力可以独立推进

主要包括：

* `SRC`
* `EPIC`
* `FEAT`
* `TESTSET`
* `acceptance`
* `impl-task`

它们可以细，可以多，可以直接贴近执行节奏。

### B. 设计层产物

用于回答：

* 系统长期如何定义
* 模块与服务边界归谁维护
* 页面骨架与主流程归谁维护
* 哪些状态与契约属于共享真相源

主要包括：

* `ARCH`
* `API`
* `UI`
* `PROTOTYPE`
* `STATE MODEL`
* `DOMAIN GLOSSARY`
* `TECH PACKAGE`

这些对象默认复用、默认更新，不应跟着 FEAT 粒度被重复新建。

---

## 3.3 新增 `surface-map` 作为强制归属层

`surface-map` 是 FEAT 进入设计层前的正式对象。

它回答的不是“写哪份文档”，而是：

* 这个 FEAT 影响哪些设计面
* 每个设计面由哪个 owner asset 承接
* 本次是 `update` 还是 `create`
* 本次修改的 delta / scope 是什么

本 ADR 预留并命名新的正式对象：

## **`surface_map_package`**

Phase 1 可先以单 FEAT 为粒度，固定一个 `feat_ref`。

### `surface-map` 的产出时机

本 ADR 明确规定：

## **`surface_map_package` 必须在 `feat_freeze_package` 之后、任何 design 派生之前生成并冻结。**

也就是说，`surface-map` 不是：

* `feat draft` 阶段的随手说明
* 某个 design skill 在运行中临时补写的附属备注
* `IMPL` 阶段回填的归属解释

它是正式主链中的前置门禁对象。

### `surface-map` 的 gate 条件

若 FEAT 或 FEAT cluster 标记：

* `design_impact_required = true`

则没有有效的 `surface_map_package`，不得进入以下链路：

* `feat-to-tech`
* `feat-to-prototype`
* `proto-to-ui`
* `impl_candidate_package`

如果 `design_impact_required = false`，则允许跳过 `surface-map`，但必须在 FEAT 或上游 gate 中留存 bypass rationale。

### `surface-map` 的校验责任

本 ADR 明确采用三层校验：

* `package schema validation` 负责校验 `surface_map_package` 的字段完整性、词表合法性与引用格式
* `workflow gate` 负责校验需要设计归属的 FEAT 是否在 design 派生前已经持有有效 `surface_map_package`
* `impl-spec-test` 或同类 cross-doc validation 负责校验 `surface-map` 与下游 shared asset / impl 引用是否一致

三者缺一不可。

### Phase 2：支持 multi-FEAT 归属

Phase 1 先固定单 FEAT 粒度的 `surface_map_package`。

Phase 2 允许扩展为：

* `surface_map_package` for one feat
* `surface_map_bundle` for a feat cluster

适用场景包括：

* 同一 EPIC 下多个 FEAT 共同更新一个主流程 prototype
* 多个 FEAT 一起才值得对同一 UI / ARCH owner 做一次结构更新

但无论单 FEAT 还是 FEAT cluster，归属对象都必须显式、可审计，不得退回口头约定。

### `surface-map` 最小语义字段

```yaml
feat_ref: FEAT-XXX
title: string

design_surfaces:
  architecture:
    - owner: ARCH-XXX
      action: update | create
      scope:
        - string
      reason: string

  api:
    - owner: API-XXX
      action: update | create
      scope:
        - string
      reason: string

  ui:
    - owner: UI-XXX
      action: update | create
      scope:
        - string
      reason: string

  prototype:
    - owner: PROTO-XXX
      action: update | create
      scope:
        - string
      reason: string

  tech:
    - owner: TECH-XXX
      action: update | create
      scope:
        - string
      reason: string
```

其中：

* `owner` 指向既有 shared asset，或在 `create` 时预留新 owner id
* `action` 只允许 `update` 或 `create`
* `scope` 记录本次改动的局部边界
* `reason` 用于解释为什么归属到该资产，或为什么必须新建
* `design_impact_required` 用于表达该 FEAT 是否必须经过 design 归属门禁

建议的扩展元数据包括：

```yaml
design_impact_required: true
related_feat_refs:
  - FEAT-XXX
surface_map_generated_from: feat_freeze_package
```

---

## 3.4 Shared Design Assets 必须具备 owner identity

从本 ADR 生效起，以下设计资产必须具备稳定 owner id：

* `ARCH-*`
* `API-*`
* `UI-*`
* `PROTO-*`
* `TECH-*`
* 以及后续纳入该层的 `STATE-*` / `GLOSSARY-*`

没有 owner id 的设计资产，不得作为长期 authority 被持续引用。

原因是：

* 没有 owner id，就无法表达“多个 FEAT 更新同一资产”
* 没有 owner id，就无法表达“默认 update existing”
* 没有 owner id，AI 仍会回到“生成一份新的平行文档”路径

### owner id 的身份规则

本 ADR 进一步明确：

* `owner id` 是 shared design asset 的长期逻辑身份
* 文档标题可以调整，承载文件可以迁移，但 `owner id` 不得在普通 FEAT 派生中随意改写
* `owner id` 的变更、合并或废弃，必须视为结构调整，而不是普通内容更新

### owner id 与文件实例、版本的区分

shared design asset 至少要区分三层：

* `owner id`：逻辑身份，例如 `UI-COACH-CONVERSATION-SHELL`
* `artifact file`：当前承载文件或 package 的路径
* `version / revision`：该 owner 当前被更新到的版本或修订号

本 ADR 明确反对把文件名直接等价成 owner identity。

### owner split 规则

当单一 owner 长期同时承载多个互相弱相关的主骨架，且 update scope 持续互不重叠时，允许拆分 owner。

但 owner split 必须满足：

* 不能在普通 FEAT 派生中偷偷完成
* 必须有专门的拆分决策或迁移决策记录
* 必须保留旧 owner 到新 owner 的映射关系

### shared asset 的反向追踪要求

每个 shared design asset 至少应支持以下反向追踪元数据：

```yaml
related_feats:
  - FEAT-XXX
  - FEAT-YYY
last_updated_by:
  - FEAT-YYY
open_deltas:
  - string
```

其中：

* `related_feats` 用于表达哪些 FEAT 长期影响该资产
* `last_updated_by` 用于表达最近一次或最近一组更新来源
* `open_deltas` 用于表达尚未完全沉淀或仍在演进中的局部 scope

---

## 3.5 `TECH-*` 进入 shared design assets 的边界

本 ADR 保留 `TECH-*` 进入 shared design assets 的可能性，但必须进一步限缩其适用范围。

只有以下对象，才应视为 `TECH-*` shared asset：

* 可被多个 FEAT 持续复用的实现策略包
* 长期维护的规则包、执行逻辑包或决策包
* 对上游 `ARCH / API / UI / PROTOTYPE` 形成稳定实现约束的技术 authority

以下对象不得提升为 `TECH-*` shared asset：

* 单次实施的改动顺序说明
* 只服务本次开发排期的 handler / file touch list
* 临时性的前后端联调安排
* 本次任务包内部的局部执行说明

这些内容应归入：

* `impl`
* `task`
* `execution package`

而不是被提升为长期 shared design asset。

---

## 3.6 `update` 与 `create` 的硬判定

本 ADR 固定以下默认规则：

### 默认规则

## **先查 owner asset，默认 update，例外才 create。**

只有满足“引入新的长期责任边界”时，才允许 `create`。

### 允许 `create` 的典型情形

* 新子系统或新模块边界形成
* 新服务域或新 API 契约族形成
* 新主页面骨架或独立主流程形成
* 新长期维护的状态机或领域模型形成
* 新实现方案包在长期上可被多个 FEAT 复用

### 默认应 `update` 的典型情形

* 只是现有模块内新增一段能力
* 只是现有 API 上新增 endpoint / 字段 / error mapping
* 只是现有 UI shell / page flow 上新增 card / panel / state
* 只是现有 prototype 主流程上的一个步骤扩展
* 只是对已有技术方案包追加新规则或新 touch-set

### `create` 的判定清单

为了避免“新的长期责任边界”在执行时被主观化，本 ADR 追加以下硬规则：

## **`create` 必须同时满足至少 2 条判定信号；否则一律按 `update` 处理。**

允许作为 `create` 信号的标准问题包括：

* 是否引入新的长期维护 owner
* 是否形成新的独立主流程或主页面骨架
* 是否形成新的服务域或契约族
* 是否形成新的状态机 authority
* 是否预期会被多个 FEAT 持续复用

若不足 2 条，则默认视为已有 owner 的局部更新。

---

## 3.7 Prototype 与 UI 的重新定位

ADR-040 与 ADR-041 保持有效，但在本 ADR 下它们的归属语义进一步明确为：

### `PROTOTYPE`

负责：

* 主流程骨架
* 页面 / sheet / modal / panel 之间的流转
* 关键状态体验
* Journey Structural Spec 落到可体验原型后的表现

它默认应按主流程骨架维护，而不是按单个 FEAT 切碎。

### `UI`

负责：

* 页面结构
* 信息架构
* 组件与区域关系
* UI 语义与实现契约

它默认应挂靠到稳定的 UI owner asset，而不是每个 FEAT 各自拥有一份。

因此，本 ADR 明确：

## **`FEAT -> PROTOTYPE -> UI` 是派生链，不等于 `1 FEAT -> 1 PROTOTYPE -> 1 UI`。**

一个 FEAT 更常见的情况是：

* 更新一份已有 `PROTO-*`
* 再更新一份已有 `UI-*`

而不是各自新建。

---

## 3.8 IMPL 只消费 resolved shared assets

从本 ADR 生效起，`IMPL` 必须显式引用：

* `surface_map_package`
* 以及其中解析出的 owner assets

`IMPL` 可以定义：

* touch-set
* 实施顺序
* 风险与回滚边界
* 任务切分
* 验收点

但不得：

* 在未经过 `surface-map` 的前提下临时新建 `ARCH / UI / PROTOTYPE`
* 把实现阶段的临时判断反向提升为 shared design asset authority

---

## 3.9 示例：AI 教练 MVP

以一个 AI 教练 MVP 为例，若当前有以下 FEAT：

* 最小信息采集
* 训练计划生成
* 每日训练调整
* 训练后反馈再规划

旧模型很容易退化为：

```text
4 个 FEAT
-> 4 份 ARCH
-> 4 份 UI
-> 4 份 PROTOTYPE
```

本 ADR 采用的更合理表达应是：

### 共享资产

* `ARCH-COACH-MVP-CORE`
* `ARCH-TRAINING-PLAN-ENGINE`
* `API-TRAINING-PLAN`
* `UI-COACH-CONVERSATION-SHELL`
* `PROTO-MVP-COACH-MAIN`

### 单 FEAT 的 `surface-map`

```yaml
feat_ref: FEAT-COACH-DAILY-ADJUSTMENT
title: 每日训练计划调整

design_surfaces:
  architecture:
    - owner: ARCH-COACH-MVP-CORE
      action: update
      scope:
        - daily_adjustment_flow
        - plan_regeneration_trigger
      reason: 属于既有 AI 教练主流程扩展

  api:
    - owner: API-TRAINING-PLAN
      action: update
      scope:
        - get_daily_plan
        - regenerate_adjusted_plan
      reason: 属于既有训练计划服务域

  ui:
    - owner: UI-COACH-CONVERSATION-SHELL
      action: update
      scope:
        - daily_adjustment_card
        - plan_diff_display
      reason: 属于既有会话主界面扩展

  prototype:
    - owner: PROTO-MVP-COACH-MAIN
      action: update
      scope:
        - pre_run_adjustment_flow
      reason: 属于 MVP 主流程骨架的一部分

  tech:
    - owner: TECH-PLAN-ADJUSTMENT
      action: create
      scope:
        - adjustment decision rules
        - readiness evaluation
      reason: 新增一组可长期维护的实现规则包
```

这个例子体现的核心就是：

## **FEAT 影响 shared assets，但并不拥有它们。**

---

# 4. 硬规则

## Rule 1：FEAT 默认不新建 `ARCH / API / UI / PROTOTYPE`

只有引入新的长期责任边界时，才允许 `create`。

## Rule 2：Shared Design Asset 必须有 owner id

没有稳定 owner id 的资产，不得作为长期 authority 进入主链；owner id 不得在普通 FEAT 派生中随意改写。

## Rule 3：`surface-map` 是 FEAT 进入设计层的唯一入口

当 `design_impact_required = true` 时，没有有效 `surface-map`，不得直接派生设计层资产。

## Rule 4：Prototype 按主流程骨架维护，不按功能点切碎

FEAT 只是在既有 prototype 上更新 flow / state / card / panel。

## Rule 5：UI 按页面骨架与信息架构维护，不按单 FEAT 私有化

一个页面骨架或会话 shell 可以承载多个 FEAT。

## Rule 6：IMPL 只能消费已归属资产

实施阶段不得补发明新的 shared design asset 口径。

## Rule 7：TESTSET 可以贴近 FEAT，设计资产不应贴着 FEAT 频繁复制

测试是执行验证单元；设计资产是系统真相源。

## Rule 8：owner split 不得在普通 FEAT 派生中隐式完成

shared asset 的拆分、合并、重命名或迁移，必须作为显式结构调整处理。

## Rule 9：只有长期实现策略包才允许提升为 `TECH-*`

单次实施说明、排期说明和 touch-list 不得被提升为 shared design asset。

## Rule 10：shared asset 必须支持反向追踪

至少应能反查最近由哪些 FEAT、哪些 `surface-map` 更新过。

---

# 5. 对现有链路的影响

## 5.1 对 FEAT contract 的影响

FEAT 继续保留为功能责任单元，但建议补充显式信号：

* `design_impact_required: true | false`
* `candidate_design_surfaces: []`
* `surface_map_mode: single | bundle | bypass`
* `bypass_rationale: string | null`

这不是让 FEAT 自己决定 owner，而是让 FEAT 显式声明：

* 是否需要进入 `surface-map`
* 可能影响哪些设计面

## 5.2 对 Prototype / UI 链路的影响

ADR-040 / ADR-041 不被废止，而是被上移到归属层之后：

```text
FEAT
  -> SURFACE-MAP
  -> resolve prototype owner / ui owner
  -> FEAT-to-PROTOTYPE delta
  -> PROTOTYPE-to-UI delta
```

也就是说，未来 `feat-to-proto` 与 `proto-to-ui` 的输入，不应只知道“我是哪个 FEAT”，还应知道：

* 我在更新哪个 `PROTO-*`
* 我在更新哪个 `UI-*`
* 本次 scope 是什么

## 5.3 对 Architecture / API / TECH 的影响

虽然当前仓库还没有全部设计层派生都收敛成正式 workflow，但从本 ADR 生效起，语义上统一采用同一规则：

* `ARCH` 以模块 / 子系统边界为 owner
* `API` 以服务域 / 契约族为 owner
* `TECH` 只在其为长期实现策略包时才以 owner asset 形式存在

后续是否单独新增 `feat-to-arch`、`feat-to-api` 或其他派生 skill，应以本 ADR 的 owner / surface-map 语义为前提，不再允许直接按 FEAT 粒度机械复制。

---

# 6. 落地建议

## Phase 1：先止血

1. 停止把“1 FEAT 自动派生 1 套 design docs”当默认模式
2. 为已有 `ARCH / API / UI / PROTOTYPE / TECH` 补 owner id
3. 新增 `surface_map_package` 模板
4. 在 `IMPL` 前增加 “resolved shared assets” 检查
5. 为 design 派生链加上 `design_impact_required` 与 `surface-map` gate

## Phase 2：整理存量

1. 合并同主题、同边界、同 owner 的平行设计文档
2. 把零散 prototype 收敛为主流程骨架资产
3. 为已有 FEAT 补齐它们影响的 design surface 引用关系
4. 为 shared assets 补齐 `related_feats` / `last_updated_by` 等反向追踪元数据
5. 视需要引入 `surface_map_bundle` 支持 FEAT cluster 归属

## Phase 3：固化到 workflow / skill

1. `epic-to-feat` 输出增加 design impact signal
2. 新增 `surface-map` 生产或校验步骤
3. 下游 design skill 默认读取 owner + action + scope
4. `create` 新设计资产时强制输出 justification

---

# 7. 收益、代价与风险

## 7.1 预期收益

* 设计资产数量下降，不再被 FEAT 粒度机械放大
* shared design assets 成为更稳定的长期真相源
* AI 默认从 `update existing` 思维出发，而不是默认新建
* `IMPL` 拿到更清晰的 authority，减少边界冲突
* `PROTOTYPE` 与 `UI` 回到骨架资产定位，而不是碎片化功能图

## 7.2 代价

* 主链中新增一层 `surface-map`
* 需要给存量设计资产补 owner id
* 需要调整现有 skill / runner 的默认派生心智

## 7.3 风险

* 如果 owner 划分本身不清，混乱会被推迟到 `surface-map`
* 如果 `update` / `create` 判定过松，系统仍会回退到文档爆炸
* 如果 `surface-map` 只是附属说明而不是硬门禁，AI 仍会跳过归属层直接新建文档

因此，本 ADR 的关键不是只增加一个对象名，而是：

## **把 `surface-map`、owner id、默认 update 三件事一起作为硬约束执行。**

---

# 8. 最终决议

从本 ADR 生效起：

1. **FEAT 不再默认一对一派生 `ARCH / API / UI / PROTOTYPE`**
2. **新增 `surface-map` 作为 FEAT 进入设计层的强制归属步骤**
3. **`ARCH / API / UI / PROTOTYPE / TECH` 统一视为 shared design assets**
4. **设计层默认 `update existing`，只有跨新边界才允许 `create new`**
5. **`IMPL` 只能基于已归属的 shared assets 编写**

一句话总结：

> **功能可以细拆，设计资产不能跟着细碎。**
> **FEAT 是交付单元；ARCH / API / UI / PROTOTYPE 是共享真相源；两者之间必须通过 `surface-map` 解耦。**
