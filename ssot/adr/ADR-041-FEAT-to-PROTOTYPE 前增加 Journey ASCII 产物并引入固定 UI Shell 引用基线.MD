# ADR-041：FEAT-to-PROTOTYPE 前增加 Journey Structural Spec 产物并引入固定 UI Shell Source 基线

* 状态：Draft
* 日期：2026-04-06
* 决策者：Le Zeng
* 适用范围：`ll-dev-feat-to-proto`、`ll-dev-proto-to-ui`、`dev.feat-to-proto` / `dev.proto-to-ui` workflow、`prototype_package`、界面型 FEAT 的体验冻结链、`ui_spec_package` 的上游语义来源治理
* 相关 ADR：ADR-015、ADR-021、ADR-039、ADR-040

---

# 1. 背景

ADR-040 已经把原先单段式的 `FEAT -> UI` 拆成：

```text
FEAT -> PROTOTYPE -> UI
```

这一步解决了一个关键问题：

## **UI 不能直接从 FEAT 跳到实现契约，中间必须先有体验冻结层。**

但在最近的 prototype authoring 实践里，又出现了两个新的漂移点。

## 1.1 体验层仍然缺少一个“原型前”的结构冻结对象

现在的 `feat-to-proto` 已经能产出静态 HTML prototype，但它仍然容易把以下问题混在一起：

* 用户旅程是否真的走得通；
* 页面之间到底是什么关系；
* 一个交互应该是 page、sheet、modal 还是 inline section；
* 主 CTA 与次 CTA 的优先级是否稳定；
* 哪些失败路径是阻断，哪些失败路径是可降级继续。

这些问题如果直接在 HTML prototype 里首次出现，仍然会有两个退化：

* 交互结构与视觉骨架纠缠在一起，review 时不容易只审结构；
* 人和 AI 都更容易被页面表象带偏，而不是先冻结 journey 和 container 边界。

因此，prototype 之前还需要一个更轻、更硬的冻结层，用来先把：

* 旅程
* 页面映射
* CTA 层级
* 容器类型
* 关键分支与错误态

压成一个可直接审阅的结构对象。

本 ADR 把这个对象统一命名为：

## **Journey Structural Spec (`journey-ux-ascii.md`)**

## 1.2 Prototype 每次都从零发明 App Frame，会导致页面漂移

当前 `feat-to-proto` 在生成 prototype 时，虽然能产出页面和跳转，但没有一个固定的 UI Shell / App Frame 作为约束来源。

结果就是：

* 每个 FEAT 都可能重新发明页面头部、返回机制、CTA 位置和状态反馈容器；
* 同一产品里，不同 prototype 的 page / modal / sheet 边界容易漂移；
* `proto-to-ui` 在转译时缺少一个明确的壳层 authority，只能从 prototype 表象反推结构。

这会带来一个很典型的问题：

## **页面单看成立，但产品不像一个产品。**

所以当前缺失的，不是再加一份视觉稿，而是：

* 一个原型前的 Journey Structural Spec；
* 一个固定引用、可重复消费的 UI Shell Source。

---

# 2. 问题陈述

本 ADR 要解决的，不是“文档够不够多”，而是以下结构性问题。

## 2.1 没有 Journey Structural Spec，prototype 仍可能先画再想

如果 `feat-to-proto` 直接从 FEAT 进入 HTML prototype，那么即使最后有 prototype 可点，也不代表以下东西在原型前被真正冻结：

* page map
* decision points
* container choice
* error / degraded / retry path
* CTA hierarchy

这会让 prototype review 退化为“看页面顺不顺”，而不是先确认：

* 整条链路是否合理；
* 页面边界是否一致；
* 产品行为是否在视觉之前被锁定。

## 2.2 没有固定 UI Shell Source，prototype 会把壳层和业务层混写

如果每个 FEAT 在 `feat-to-proto` 里都重新发明 UI 框架，则：

* header / nav / footer / sticky CTA 位置不稳定；
* page / modal / bottom sheet / inline banner 的判定会漂移；
* 业务页面会不知不觉承担本该属于 app frame 的职责；
* `proto-to-ui` 只能从页面表现反推壳层，不再有一个显式 authority。

这会直接削弱下游 `ui_spec_package` 的一致性。

## 2.3 如果把 UI Shell 也当成每次运行新生成的文本，固定性仍然不存在

本 ADR 明确反对：

* 每次 `feat-to-proto` 临时写一份新的 UI Shell 说明；
* 然后把这份新写的壳层说明再当上游 authority。

因为这只是把“每次重新发明”的问题换了个载体。

真正需要的是：

## **一个固定可引用的 UI Shell Source。**

`feat-to-proto` 可以把它快照进输出包，但不应该把壳层定义本身做成每次重新生成的自由文本。输出包内的快照文件统一命名为 `ui-shell-spec.md`，它只是本次运行的 shell snapshot，不是 source 本体。

## 2.4 `proto-to-ui` 若不显式消费 Journey Structural Spec 与 UI Shell snapshot，会丢失上游结构语义

即使 `feat-to-proto` 产出了更好的中间对象，如果 `proto-to-ui` 仍然只读取：

* `prototype/index.html`
* `prototype/mock-data.json`
* review / gate 文件

而不强制读取：

* `journey-ux-ascii.md`
* `ui-shell-spec.md`

那么 Journey 与 Shell 仍然只是“存在过”，没有真正进入 UI 契约链。

---

# 3. 决策

## 3.1 决策摘要

LL 正式在 ADR-040 定义的双阶段链路上再补一层固定结构约束：

```text
FEAT
  -> Journey Structural Spec
  -> UI Shell Source Snapshot
  -> HTML Prototype
  -> Human Prototype Review / Freeze
  -> UI Spec
```

并冻结以下原则：

1. `feat-to-proto` 必须新增一个 FEAT 局部产物：
   * `journey-ux-ascii.md`
2. `feat-to-proto` 必须固定消费一个 UI Shell Source authority，并在输出包中快照为：
   * `ui-shell-spec.md`
3. `ui-shell-spec.md` 的上游定义不是本次运行临时发明，而是固定引用的 canonical UI Shell Source。
4. `prototype_package` 必须显式记录：
   * `journey_ascii_ref`
   * `ui_shell_ref`
   * `ui_shell_source_ref`
   * `ui_shell_version`
   * `ui_shell_snapshot_hash`
   * `shell_change_policy`
5. `proto-to-ui` 必须把 `journey-ux-ascii.md` 与 `ui-shell-spec.md` 视为输入契约的一部分，而不是可有可无的附属文档。
6. `ui-semantic-source-ledger` 必须把 journey 结构语义与 shell 框架语义分别入账。
7. Journey Structural Spec 是 FEAT 级局部冻结对象；UI Shell Source 是跨 FEAT 复用的固定框架 authority。

## 3.2 `journey-ux-ascii.md` 的最小契约

`journey-ux-ascii.md` 的正式名称是：

## **Journey Structural Spec**

它负责冻结：

* journey 主链
* page map
* decision points
* primary CTA / secondary CTA
* 关键状态
* 关键分支
* container hint
* open questions / frozen assumptions

它不负责：

* 视觉样式
* 字体、颜色、圆角
* 像素级布局
* 工程实现细节

它的定位是：

## **交互结构冻结层，不是视觉设计层。**

### Journey Structural Spec 最小模板

`journey-ux-ascii.md` 至少应包含以下 section：

1. `Journey main chain`
2. `Page map`
3. `Decision points`
4. `CTA hierarchy`
5. `Container hints`
6. `Error / degraded / retry paths`
7. `Open questions / frozen assumptions`

## 3.3 UI Shell Source 与 `ui-shell-spec.md` 的区分

`ui-shell-spec.md` 是：

## **UI Shell Source 的运行时快照**

它负责冻结：

* 顶层导航方式
* 页面头部与返回行为
* CTA 放置原则
* page / modal / bottom sheet / inline banner 的使用规则
* 统一状态反馈模式
* 一组跨页面通用组件与容器约束

它不是每个 FEAT 自由生成的文档，而应来自一个稳定的 canonical UI Shell Source。`ui-shell-spec.md` 只能表达快照结果，不能反向成为 shell source 本体。

### UI Shell Source 最小治理字段

`prototype_package` 至少应携带以下 shell 治理字段：

* `ui_shell_source_ref`
* `ui_shell_version`
* `ui_shell_snapshot_hash`
* `shell_change_policy`

其中：

* `ui_shell_source_ref` 指向 canonical UI Shell Source
* `ui_shell_version` 表示 source 的版本号或治理代号
* `ui_shell_snapshot_hash` 表示 `ui-shell-spec.md` 的快照校验值
* `shell_change_policy` 说明 shell 是否允许在同一产品族内升级、如何升级、是否需要重新快照

Phase 1 实现允许：

* canonical UI Shell Source 先以 skill resource 形式随 `ll-dev-feat-to-proto` 固定提供；
* `feat-to-proto` 在输出包中把它快照为 `ui-shell-spec.md`；
* 同时记录 `ui_shell_source_ref`、`ui_shell_version`、`ui_shell_snapshot_hash`、`shell_change_policy`，供下游审计。

## 3.4 `feat-to-proto` 的职责调整

`dev.feat-to-proto` 不再只是：

* 产出 HTML prototype；
* 产出 review / gate 文件。

而必须固定完成以下顺序：

1. 从 FEAT / 已有 UI authority 提取页面单元与主路径。
2. 先生成 `journey-ux-ascii.md`，冻结结构语义。
3. 解析固定 `ui_shell_source_ref`，把其快照进包内 `ui-shell-spec.md`。
4. 在上述两者约束下生成 HTML prototype。
5. 进入 human review / freeze gate。

## 3.5 `proto-to-ui` 的职责调整

`dev.proto-to-ui` 不再只消费 prototype 页面表现，而必须同时消费：

* `prototype/index.html`
* `prototype/mock-data.json`
* `journey-ux-ascii.md`
* `ui-shell-spec.md`

并在 `ui-semantic-source-ledger.json` 中明确区分：

* from_prototype.layout
* from_prototype.flow
* from_journey.journey_structure
* from_shell.shell_frame
* from_feat.business_constraints
* inferred_by_ai

这样下游才能区分：

* 哪些语义来自 journey 冻结；
* 哪些来自固定 shell source snapshot；
* 哪些是 prototype 表现；
* 哪些仍是 AI 推断。

## 3.6 Journey 与 Shell 的归属优先级

当同一对象同时涉及 Journey 和 Shell 时，采用以下优先级：

1. Journey 决定局部流程、步骤顺序、决策点与状态转移语义。
2. Shell 决定跨页面壳层、导航方式、容器家族、CTA 位置原则与状态反馈模式。
3. 若一项描述既影响流程语义也影响壳层承载方式，则 Journey 负责“发生什么”，Shell 负责“放在哪里、用什么容器承载”。

## 3.7 跨 FEAT 共享旅程的例外规则

默认情况下，`journey-ux-ascii.md` 以 FEAT 局部冻结为主。

若多个 FEAT 共享同一条主旅程或同一主屏壳层，则必须满足：

1. 共享旅程由更高层对象统一冻结并显式引用。
2. 单个 FEAT 不得复制一份“几乎相同”的 journey 作为本地 authority。
3. 若 FEAT 只拥有共享旅程中的局部片段，必须在 `journey-ux-ascii.md` 中声明上游共享 authority 与本次局部切片边界。

---

# 4. 产物与契约变化

## 4.1 `prototype_package` 新增字段

`prototype_package` 必须新增：

* `journey_ascii_ref`
* `ui_shell_ref`
* `ui_shell_source_ref`
* `ui_shell_version`
* `ui_shell_snapshot_hash`
* `shell_change_policy`

其中：

* `journey_ascii_ref` 指向包内 `journey-ux-ascii.md`
* `ui_shell_ref` 指向包内 `ui-shell-spec.md`
* `ui_shell_source_ref` 指向固定 canonical UI Shell Source

## 4.2 `prototype_package` 新增运行时文件

`feat-to-proto` 输出目录新增：

* `journey-ux-ascii.md`
* `ui-shell-spec.md`

## 4.3 `proto-to-ui` 输入约束新增

`proto-to-ui` 的输入校验必须拒绝：

* 缺少 `journey_ascii_ref`
* 缺少 `ui_shell_ref`
* 缺少 `ui_shell_source_ref`
* 缺少 `ui_shell_version`
* 缺少 `ui_shell_snapshot_hash`
* `journey-ux-ascii.md` 不存在
* `ui-shell-spec.md` 不存在

即使 prototype 已通过人工 review，也不得跳过这两个对象。

## 4.4 质量 gate

本 ADR 不接受“只要文件存在就算合格”的门禁。

`journey-ux-ascii.md` 至少要通过以下 gate：

* 主链完整
* 页面映射明确
* 关键决策点列出
* CTA 层级明确
* 关键错误 / degraded / retry 路径明确
* container hint 明确

`ui-shell-spec.md` 至少要通过以下 gate：

* 导航规则明确
* CTA placement 原则明确
* state feedback mode 明确
* container family 规则明确
* shell source / snapshot 关系明确

若任一 gate 不通过，`proto-to-ui` 必须把该 package 视为不可进入 UI Spec 派生链。

## 4.5 Prototype SSOT 正式目录与文件名规范（Journey 格式）

为避免 `ssot/prototype` 的路径与文件名随标题漂移，本 ADR 要求 prototype 正式发布采用固定文件名 + id-only 目录。

### 4.5.1 归属键（id-only）

* 正式 SSOT 目录以 `prototype_owner_ref` 作为唯一定位键（不在路径中拼接 title / slug）。
* `prototype_owner_ref` 的语义是“journey owner id”（允许多个 FEAT 归属到同一 owner，并进行 owner 级合并发布）。

### 4.5.2 推荐目录结构（固定文件名）

```text
ssot/prototype/
  SRC-003/
    PROTO-SRC-003-001/
      index.html
      app.js
      styles.css
      runtime-smoke-dom.html
      mock-data.json
      mock-data.js
      journey-model.json
      journey-model.js
      journey-ux-ascii.md
      ui-shell-spec.md
      owner-publication-manifest.json
      prototype-bundle.snapshot.json
      package-manifest.snapshot.json
```

其中：

* `index.html` 是可运行视图入口（便于 review / 点验）。
* `journey-ux-ascii.md` 与 `journey-model.json` 是结构真相源（可审计、可被下游消费）。
* `ui-shell-spec.md` 是壳层 authority 的运行时快照（必须保留用于审计）。
* `prototype-bundle.snapshot.json` / `package-manifest.snapshot.json` 固定保留候选包快照，便于追溯本次发布输入。

---

# 5. 设计约束

## 5.1 Journey Structural Spec 不得膨胀成第二份 PRD

它必须短、硬、可验证。

优先保留：

* chain
* page map
* CTA
* branch
* error / degraded
* container hint

不鼓励写成长篇解释性 prose。

## 5.2 UI Shell Source 必须是固定 authority，而不是每次重写

如果 shell 自身每次运行都可以被自由改写，那么它就不再是壳层 authority。

所以本 ADR 强制：

## **运行时可以快照 shell，但不可以在没有显式治理动作的前提下重新发明 shell。**

## 5.3 Shell 是交互骨架，不只是视觉壳

Shell 至少要约束：

* 导航
* container type
* CTA placement
* state feedback mode
* common structural components

如果它只是 header/footer 外观描述，则不满足本 ADR 的目标。

---

# 6. 实施落点

## 6.1 Phase 1

在当前仓库内先落以下最小闭环：

1. 新增 ADR-041。
2. 在 `ll-dev-feat-to-proto` 中新增：
   * `journey-ux-ascii.md`
   * 固定 `ui-shell-spec.md` 快照
3. 在 `ll-dev-proto-to-ui` 中强制读取并验证上述两个对象。
4. 在 `ui-semantic-source-ledger.json` 中纳入 journey / shell 两类来源。

## 6.2 后续可选演进

后续可以再把 UI Shell Source 从 skill resource 上升为仓库内正式可版本化对象，但这不是本 ADR 的 Phase 1 前置条件。

---

# 7. 结果

本 ADR 生效后，`FEAT -> PROTOTYPE -> UI` 不再只是：

* 先画页面
* 再审页面
* 再写 UI Spec

而是变成：

* 先冻结 journey 结构
* 再套用固定 shell source snapshot
* 再做 prototype
* 再冻结为 UI contract

最终目标是：

## **减少 prototype 与实现阶段对页面容器、导航方式、CTA 优先级和状态表达的重复发明。**

