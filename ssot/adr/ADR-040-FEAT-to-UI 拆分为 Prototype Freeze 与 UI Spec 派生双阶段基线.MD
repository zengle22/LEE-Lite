# ADR-040：FEAT-to-UI 拆分为 Prototype Freeze 与 UI Spec 派生双阶段基线

* 状态：Draft
* 日期：2026-04-03
* 决策者：Le Zeng
* 适用范围：`ll-dev-feat-to-ui`、拟新增 `ll-dev-feat-to-proto` / `ll-dev-proto-to-ui`、`dev.feat-to-proto` / `dev.proto-to-ui` workflow、`prototype_package`、`ui_spec_package`、界面型 FEAT 的实施前治理链
* 相关 ADR：ADR-008、ADR-015、ADR-021、ADR-034、ADR-036、ADR-038、ADR-039

---

# 1. 背景

当前仓库已经通过 ADR-021 冻结了：

* `ll-dev-feat-to-ui`
* `dev.feat-to-ui`
* `ui_spec_package`

也就是说，系统已经承认：

## **界面层需要一个正式对象，而不是把 UI 理解散落在 FEAT、TECH、口头说明和零散草图之间。**

这一步是对的。

但随着 `IMPL`、`impl-spec-test`、`review contract` 等链路继续收敛，`FEAT -> UI` 的单段式路线开始暴露出新的混层问题：

* 当前 `feat-to-ui` 同时在承担“体验定型”和“实现契约定型”；
* UI Spec 一边要描述用户旅程、页面结构和 CTA 主次，一边又要描述字段、状态、校验、API 绑定；
* 人类真正擅长拍板的交互体验判断，被过早压平到了结构化文档里；
* AI 则被迫从 FEAT 直接跳到 UI Spec，常在没有体验锚点的情况下自行补完页面语义；
* 最终下游虽然拿到了 `UI Spec`，但这个 `UI Spec` 里仍混入大量“还没被人真正体验过”的假定。

仓库近期已经形成一个更清晰的认识：

## **很多高返工成本的问题，本质上不是实现问题，而是表达问题、旅程问题和交互问题。**

例如：

* 页面到底是引导页、状态页、列表页还是表单页；
* 一个动作到底是主 CTA、次 CTA，还是只是辅助入口；
* 信息应该一次性展开，还是分阶段暴露；
* 错误提示应该是字段级、模块级还是流程级；
* 一个流程应该一步完成、分两步完成，还是允许跳过后补。

这些问题如果只写 prose，经常“看起来都对”。

但只要做成可以点、可以跳、可以切状态的 HTML prototype，很多问题会立刻暴露：

* 用户点完下一步不知道去哪；
* 页面主语跳变；
* 非阻塞流程被做成阻塞；
* 首页展示了建议，但用户不知道为什么是这个建议；
* 补充资料与开始使用之间的优先级冲突没有被体验层发现。

这说明当前主链里缺少的，不只是“更强的 UI Spec”，而是：

## **位于 FEAT 与 UI Spec 之间的正式 Prototype Layer。**

这层不是视觉附属物，也不是实现前端的提前预演，而是：

* 冻结信息架构；
* 冻结用户旅程；
* 冻结主次动作；
* 冻结关键状态体验；
* 让人类在低成本阶段做交互判断；
* 再把已经确认的体验锚点转译为 AI 更稳定消费的 UI Spec 契约。

因此，需要一份新的 ADR，把原先单段式的 `FEAT -> UI` workflow 正式拆成两段，并把人类 prototype 审核写成硬门禁，而不是最佳实践建议。

---

# 2. 问题陈述

当前真正要解决的，不是“要不要多一份文档”，而是以下结构性问题。

## 2.1 单段式 `FEAT -> UI` 把两类完全不同的问题压成了一层

当前 `feat-to-ui` 同时试图回答两组问题：

### A. 体验定型问题

* 页面长什么样；
* 用户怎么走；
* 哪些信息先出现；
* 哪个按钮是主动作；
* 错误时用户看到什么；
* 页面之间如何回退、跳过、重试。

### B. 实现契约问题

* 页面与路由清单是什么；
* 组件层级与可见条件是什么；
* 字段的数据来源、校验规则、错误 copy 是什么；
* 状态枚举和事件定义是什么；
* API 请求、响应和异常映射是什么；
* 哪些行为是真实接线，哪些只是演示态。

这两类问题虽然相关，但不适合在同一个首次派生动作里同时冻结。

如果把它们压在一个 skill 里，最常见的退化就是：

* UI Spec 既不像体验原型，也不像实现契约；
* 人类 review 不知道自己在审“体验是否顺”还是“字段映射是否闭合”；
* AI 为了补齐结构化字段，偷偷发明了还没被体验过的页面逻辑。

## 2.2 纯文档式 UI 派生无法稳定暴露旅程断裂

当前即使 UI Spec 写得完整，也很难仅靠阅读稳定发现：

* 页面之间语义是否连续；
* 失败路径是否真的可恢复；
* 渐进式信息展示是否自然；
* CTA 主次是否造成错导；
* 默认路径与非阻塞路径是否互相打架。

这些问题往往只有在“能体验的纸面系统”里才容易被人和 AI 同时看见。

## 2.3 人类最擅长的判断，当前被放到了太后面

人类在 UI/UX 层面最擅长的，往往不是补字段表，而是判断：

* 信息密度是否合适；
* 用户心理预期是否顺；
* 页面主语是否对；
* 交互阻力是否过大；
* 当前流程究竟是在帮助用户，还是在阻挡用户。

如果没有先做 prototype 并强制人类体验，系统就会把这些高价值判断后移到：

* 编码阶段；
* 联调阶段；
* 甚至上线前验收阶段。

那时返工代价已经最高。

## 2.4 HTML Prototype 可以做体验锚点，但不能直接替代 UI Spec

另一侧也必须明确：

## **本 ADR 不支持把 HTML prototype 直接当正式前端实现契约。**

因为 prototype 擅长表达：

* 页面布局与信息层级；
* 页面之间流转；
* 表单和按钮的基本行为；
* 一部分默认态与异常态体验。

但它不能天然完整承载：

* 组件语义边界；
* 字段级 canonical source；
* 完整状态机与 UI 映射规则；
* 哪些是假数据，哪些必须真实接后端；
* 响应式规则、可访问性要求、埋点要求；
* API request / response / error mapping。

所以真正稳定的路线必须是：

## **Prototype 负责体验定型，UI Spec 负责实现定型。**

## 2.5 必须阻断“未经人类确认就从 Prototype 自动滑进 UI Spec”

如果系统只是在 FEAT 前面多插一个 prototype 生成器，但仍允许：

* AI 生成 prototype；
* 没有人类体验；
* 没有人工确认；
* 直接自动派生 `proto-to-ui`；

那么系统只是把旧问题换了个载体，实质上仍然是在让 AI 连续两次猜。

因此本 ADR 必须把以下规则写死：

## **未经过人工体验、人工修改或人工确认的 prototype，不得进入 `proto-to-ui`。**

这不是推荐项，而是 workflow 级硬门禁。

## 2.6 如果所有界面型 FEAT 都强制走完整 prototype 链，会形成新的隐性低效

当前 ADR-040 的方向是对的，但如果把它误执行为：

* 只要 FEAT 有 UI surface
* 就必须先做完整 prototype
* 然后人工 review
* 再进入 UI Spec

那么系统会出现另一类退化：

* 简单页面改动也要走重链路；
* 低风险 FEAT 被高治理成本拖慢；
* 团队为了赶进度开始私下绕过；
* 最终不是“治理更强”，而是“治理形同虚设”。

因此，Prototype Layer 必须是：

## **一个正式可治理层，但不是所有 FEAT 一刀切的强制重流程。**

系统还需要一条显式的：

## **`FEAT -> UI route triage`**

用来判断：

* 哪些 FEAT 必须走 prototype；
* 哪些 FEAT 可以跳过 prototype；
* 哪些 FEAT 处于中间带，需要显式记录 bypass rationale。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **把原 `FEAT -> UI` 单段式 workflow 拆分为 `FEAT -> PROTOTYPE -> UI` 的双阶段派生链。**

正式链路调整为：

```text
ADR -> SRC -> EPIC -> FEAT
                    ├─> TECH
                    ├─> TESTSET
                    ├─> PROTOTYPE
                    │     └─> Human Prototype Review / Revision / Approval
                    └─> UI

PROTOTYPE(frozen, human-approved) -> UI
UI -> IMPL
```

面向界面型 FEAT 的推荐理解收敛为：

```text
FEAT -> HTML Prototype -> Human Prototype Review -> UI Spec -> IMPL -> Coding
```

本 ADR 冻结以下原则：

1. `dev.feat-to-ui` 不再作为**全部界面型 FEAT 的单一默认 authoring path**。
2. 新的两段式 workflow 固定为：
   * `dev.feat-to-proto`
   * `dev.proto-to-ui`
3. 新的两个 skill 固定为：
   * `ll-dev-feat-to-proto`
   * `ll-dev-proto-to-ui`
4. `feat-to-proto` 的目标是产出可体验、可批注、可修改的 HTML prototype package。
5. `proto-to-ui` 的目标是把**已人工确认并冻结**的 prototype 转译为正式 `ui_spec_package`。
6. Prototype Review 是 mandatory human gate，不得被 skill 内部自动化 judgement 替代。
7. `proto-to-ui` 必须拒绝消费未通过人工确认的 prototype package。
8. `proto-to-ui` 生成的 `UI Spec` 必须显式标记语义来源，不得把 AI 推断静默伪装成上游 authority。
9. `IMPL` 不得再承担 UI 定义职责；界面语义必须在 `PROTOTYPE / UI Spec` 层先被冻结。
10. 是否必须走 prototype，不再靠口头习惯判断，而由显式 `UI Derivation Routing Check` 决定。

## 3.3 FEAT 路由与三档三分流

并不是所有 FEAT 都应该进入 prototype 层。

本 ADR 冻结一个显式的 FEAT triage 结果：

## **`ui_route_tier`**

该结果必须在 FEAT 冻结时确定，并记录到 FEAT 的 package manifest 或等价路由记录中，再向下游派生对象透传。

### 3.3.1 路由输入信号

`ui_route_tier` 的判定至少应综合以下信号：

* `ui_required`
* `ui_surface_kind`
* `journey_delta`
* `state_delta`
* `copy_only_change`
* `surface_reuse_stability`
* `risk_sensitivity`

### 3.3.2 路由档位

| 路由档位 | 含义 | 默认路径 | 说明 |
| --- | --- | --- | --- |
| `none` | 不涉及用户可见界面 | 跳过 prototype 与 UI Spec | 只进入 TECH / TESTSET 等非 UI 派生链 |
| `direct_spec` | 稳定存量界面上的局部、低歧义修改 | 直接进入 UI Spec 路径，不要求 prototype | 适用于 copy、label、轻量校验、单表单字段级调整等有限变化 |
| `prototype_required` | 新旅程、强交互或高歧义界面变化 | `feat-to-proto -> human review -> proto-to-ui` | 任何会改变页面主路径、状态结构或恢复语义的 FEAT 都落此档 |

### 3.3.3 路由规则

以下情形默认进入 `prototype_required`：

* 新增页面、弹窗、抽屉或多步骤流程；
* 引入新的主 CTA、次 CTA 关系；
* 改变页面主语、信息层级或用户决策顺序；
* 引入非阻塞、恢复、重试、分支或部分成功语义；
* 改变跨页面流转或状态机形状；
* 单靠 prose 无法稳定表达的交互变化。

以下情形默认进入 `direct_spec`：

* 仅做文案、标签、提示词或单点 copy 修订；
* 在稳定既有页面上做单字段、单校验、单展示块的局部调整；
* 不改变主路径、不引入新状态边界、不引入新页面结构；
* 人类 reviewer 可以在不做 prototype 体验的情况下稳定判断完成态。

以下情形进入 `none`：

* 纯后端能力；
* 纯治理能力；
* 对用户不可见的内部机制；
* 不形成用户界面的任何可见变化。

### 3.3.4 路由约束

* `prototype_required` 是体验定型的强制路径，不能被 AI 自行降级。
* `direct_spec` 不能被误用为绕过 review 的快捷方式，仍需满足相应 review 与 gate。
* `none` 不得被升级成 UI 路径，只因为实现侧顺手想产出 UI 文档。
* 路由档位改变时，必须显式记录变化原因，不得静默漂移。

## 3.2 与 ADR-021 的关系

本 ADR 对 ADR-021 的处理不是“完全推翻”，而是“对象保留、链路拆层”。

继续保留的内容：

* `UI Spec` 仍然是正式对象；
* `ui_spec_package` 仍然是前端实施和后续测试的重要契约层；
* UI 不等于视觉稿，也不等于实现代码，这一点仍有效。

被本 ADR 正式 supersede 的内容：

* `FEAT -> UI` 作为 direct canonical derivation path；
* `ll-dev-feat-to-ui` 作为单 skill 同时承担体验定型与实现定型的模式；
* “ASCII 结构原型”作为 UI Spec 的核心表达锚点。

新的收敛关系是：

## **ADR-021 里关于 UI Spec 对象的有效部分继续保留；但其 runtime 路径、skill 切分和前置条件以 ADR-040 为准。**

## 3.3 Routing / Triage 基线

本 ADR 进一步冻结：

## **不是所有界面型 FEAT 都必须进入完整的 `FEAT -> PROTOTYPE -> UI` 重链路。**

系统必须先执行：

* `UI Derivation Routing Check`

该检查至少输出：

* `ui_complexity_level ∈ {low, medium, high}`
* `route_decision ∈ {direct_ui_allowed, prototype_optional, prototype_required}`
* `routing_rationale`
* `evaluated_dimensions`

### 3.3.1 复杂度等级

`ui_complexity_level` 的正式词表固定为：

* `low`
* `medium`
* `high`

### 3.3.2 最小评估维度

Routing Check 至少评估：

* 是否存在多页面或多步骤流转
* 是否存在非阻塞流程、恢复流程或分支流程
* 是否存在显著状态机或异步反馈
* 是否存在用户决策敏感点
* 是否存在高返工成本的 CTA / 信息层级判断

### 3.3.3 路由规则

* `low`
  * 默认 `direct_ui_allowed`
  * 可直接进入 UI Spec authoring fast path
* `medium`
  * 默认 `prototype_optional`
  * 可以走 prototype，也可以在显式记录 `prototype_bypass_rationale` 后直达 UI Spec
* `high`
  * 固定 `prototype_required`
  * 不得绕过 prototype review

### 3.3.4 重要解释

这不推翻 Prototype Layer 的正式地位。

它只是明确：

## **Prototype Layer 是正式能力层，但是否实例化为独立 package，要看 FEAT 的复杂度与返工风险。**

---

# 4. 正式对象与职责边界

## 4.1 `PROTOTYPE` 成为新的正式派生对象

本 ADR 正式把 `PROTOTYPE` 增补为 FEAT 的界面型派生对象。

其定位是：

## **面向体验定型的人机共创锚点对象。**

它负责冻结：

* 页面结构；
* 用户旅程；
* 关键信息层级；
* CTA 主次关系；
* 默认态、空态、错误态、成功态等主要体验；
* 返回、跳过、重试等流程级行为；
* 必要的演示态与假数据展示。

它明确不负责：

* 正式组件语义契约；
* 完整字段级数据模型；
* API mapping 与真实接线方案；
* 工程级状态管理设计；
* 生产级代码质量与实现抽象。

## 4.2 `UI Spec` 的职责收敛

在本 ADR 生效后，`UI Spec` 的职责收敛为：

## **把已确认的体验锚点转成可供实现、测试和 IMPL 消费的结构化界面契约。**

它至少负责冻结：

* 页面与路由清单；
* 页面目标与进入/退出条件；
* 组件结构与可见条件；
* 字段、校验、错误文案、canonical source；
* 状态矩阵；
* 用户事件与系统事件；
* API / state / UI mapping；
* 非阻塞与阻塞规则；
* 响应式、可访问性、埋点等实施层约束。

它不再承担：

* 首次决定页面体验应该长什么样；
* 首次决定用户主路径应该怎么走；
* 首次决定 CTA 主次与旅程节奏。

这些事情应在 Prototype Review 前完成。

## 4.3 `Prototype Review` 的正式身份

本 ADR 明确：

## **`Prototype Review` 是 mandatory human gate，不是新的业务 SSOT 对象。**

它属于：

* review / approval / freeze 证据层；
* gate 语义层；
* 派生对象推进条件。

它不是：

* 新的并列设计对象；
* 可替代 prototype 本体的 truth source；
* 可替代 UI Spec 的实现契约。

换句话说：

* Prototype 是体验锚点对象；
* Prototype Review 是该对象能否推进的人工裁决层；
* UI Spec 是已确认体验的实施契约层。

---

# 5. 新 workflow 基线

## 5.0 `UI Derivation Routing Check`

### 5.0.1 定位

Routing Check 是位于 authoring 前的 route decision layer。

它回答的不是：

* 这个 FEAT 有没有 UI

而是：

* 这个 FEAT 的 UI 风险和体验复杂度，是否值得进入 prototype 重链路。

### 5.0.2 最小输出 contract

Routing Check 的最小结构化输出应至少包含：

```yaml
ui_derivation_route:
  ui_complexity_level: low | medium | high
  route_decision: direct_ui_allowed | prototype_optional | prototype_required
  routing_rationale: string
  evaluated_dimensions:
    multi_step_flow: boolean
    workflow_branching: boolean
    async_or_stateful_behavior: boolean
    user_decision_sensitivity: boolean
    cta_or_information_hierarchy_risk: boolean
  prototype_bypass_rationale: string | null
```

### 5.0.3 路由后果

* `direct_ui_allowed`
  * 可以直接进入 UI Spec fast path
  * 但仍需保留 route decision 证据
* `prototype_optional`
  * 默认建议走 prototype
  * 如绕过 prototype，必须显式记录 bypass rationale
* `prototype_required`
  * 必须进入 `feat-to-proto`
  * 不得直接进入 UI Spec authoring

### 5.0.4 与本 ADR 的关系

因此，本 ADR 拒绝的不是“任何 direct UI route”。

本 ADR 真正拒绝的是：

## **把单段式 `FEAT -> UI` 作为全部界面型 FEAT 的统一默认路线。**

## 5.1 `ll-dev-feat-to-proto`

### 5.1.1 命名与定位

* skill 名称：`ll-dev-feat-to-proto`
* workflow key：`dev.feat-to-proto`

定位：

## **把一个 frozen FEAT 转成 review-ready 的 HTML prototype package。**

### 5.1.2 正式输入边界

`ll-dev-feat-to-proto` 只接受：

* 一个 `feat_freeze_package`
* 一个显式 `feat_ref`

与 ADR-021 原有 `feat-to-ui` 相同，prototype 只能补强 FEAT 语义，不得覆盖 FEAT 主边界。

### 5.1.3 正式输出边界

该 skill 的正式输出固定为：

## **一个 `prototype_package`**

最小运行时 package 应至少包含：

* `package-manifest.json`
* `prototype-bundle.md`
* `prototype-bundle.json`
* `prototype-flow-map.md`
* `prototype-review-guide.md`
* 一个可直接本地体验的 HTML prototype 目录或入口文件
* `prototype-completeness-report.json`
* `prototype-review-report.json`
* `prototype-defect-list.json`
* `prototype-freeze-gate.json`
* `execution-evidence.json`
* `supervision-evidence.json`

建议输出目录：

* `artifacts/feat-to-proto/<run_id>--<feat_ref>/`

### 5.1.4 Prototype 的硬约束

`feat-to-proto` 输出必须满足：

1. Prototype 必须是可体验产物，优先为 HTML prototype，而不是只有 ASCII 草图或 prose。
2. Prototype 可以使用假数据、静态页面和演示态切换。
3. Prototype 必须覆盖至少：
   * 主页面/主视图
   * happy path
   * 至少 2 类关键失败或异常路径
   * 默认态与关键状态提示
4. Prototype 必须显式说明哪些行为是 demo behavior，哪些未来需要真实接线。
5. Prototype 不得冒充 production frontend，不得直接承诺工程代码结构。

### 5.1.5 内建 gate

该 skill 的唯一内建 gate 固定为：

* `Prototype Experience Completeness Check`

其 verdict 固定为：

* `pass`
* `conditional_pass`
* `fail`

但这里的 `pass` 或 `conditional_pass` 只表示：

* 该 prototype 已达到 review-ready；
* 不表示可直接进入 `proto-to-ui`。

## 5.2 Human Prototype Review

### 5.2.1 硬门禁原则

本 ADR 固定：

## **`prototype_package` 在没有人工确认之前，只能处于 `review_required` 或 `revise_required` 语义，不得直接视为 freeze-ready。**

### 5.2.2 人工评审关注点

人工 review 至少应检查：

* 信息是否拥挤或缺失；
* CTA 主次是否正确；
* 用户旅程是否顺；
* 是否存在页面语义跳变；
* 错误与回退路径是否自然；
* 非阻塞与阻塞边界是否符合产品意图；
* 页面主语是否仍忠于 FEAT。

### 5.2.3 人工 review 的正式 verdict

Prototype Review 的 verdict 词表固定为：

* `approved`
* `revise`
* `rejected`

其中：

* `approved` 表示 prototype 可以冻结并进入 `proto-to-ui`
* `revise` 表示必须回到 `feat-to-proto` 修订
* `rejected` 表示当前原型方向不成立，应回到更上游重新判断

### 5.2.4 Prototype Review 必须结构化，不得只留下自然语言批注

本 ADR 进一步冻结：

## **`prototype-review-report.json` 必须是结构化 review contract 的输出，而不是只写一段 approval prose。**

最小结构化输出应至少包含：

```yaml
prototype_review:
  verdict: approved | revise | rejected
  review_contract_ref: string
  coverage_declaration:
    required_checks:
      - journey_check
      - cta_hierarchy_check
      - flow_consistency_check
      - state_experience_check
      - feat_alignment_check
    completed_checks: list
    not_checked: list
  journey_check:
    passed: boolean
    issues: list
  cta_hierarchy_check:
    passed: boolean
    issues: list
  flow_consistency_check:
    passed: boolean
    issues: list
  state_experience_check:
    passed: boolean
    issues: list
  feat_alignment_check:
    passed: boolean
    issues: list
  blocking_points: list
  human_adjustments: list
  reviewer_identity: string
  reviewed_at: string
```

### 5.2.5 与 ADR-039 的关系

Prototype Review 必须复用 ADR-039 已冻结的：

* `Review Contract`
* `Coverage Declaration`
* blocker 升级原则

也就是说：

* review 不得只给 verdict，不给 coverage；
* `not_checked` 不得被当作通过；
* 会诱导下游继续做错的 prototype 问题必须升级为 blocker。

### 5.2.6 人工修改与确认要求

本 ADR 明确要求：

## **人工 review 不是“看过一眼”就算完成。**

它至少必须留下以下之一：

* 明确批注与修订请求；
* 对 prototype 的人工修改记录；
* 明确的批准记录与批准人标识。

若人类直接修改 prototype 文件，`prototype_package` 必须在 freeze 前重新收集：

* 当前文件清单；
* 变更摘要；
* 审批 evidence；
* 最终 verdict。

### 5.2.7 `prototype-freeze-gate.json`

`prototype_package` 只有在以下条件全部满足时才允许 freeze：

* input structural/semantic pass
* output structural/semantic pass
* `prototype-completeness-report.json` 存在
* `prototype-review-report.json` 存在
* `prototype-review-report.json.verdict = approved`
* `prototype-review-report.json.coverage_declaration.not_checked = []`
* `prototype-review-report.json.blocking_points = []`
* `prototype-review-report.json.review_contract_ref` 可解析
* human reviewer identity 与 review timestamp 可追踪
* execution/supervision evidence 完整

## 5.3 `ll-dev-proto-to-ui`

### 5.3.1 命名与定位

* skill 名称：`ll-dev-proto-to-ui`
* workflow key：`dev.proto-to-ui`

定位：

## **把一个已人工确认并冻结的 `prototype_package` 转成正式 `ui_spec_package`。**

### 5.3.2 正式输入边界

`ll-dev-proto-to-ui` 只接受：

* 一个 freeze-ready 的 `prototype_package`
* 一个显式 `prototype_ref` 或等价的页面/原型选择标识

同时必须满足：

* `prototype-freeze-gate.json.freeze_ready = true`
* `prototype-review-report.json.verdict = approved`
* package 中保留上游 `FEAT / EPIC / SRC` traceability

### 5.3.3 正式输出边界

该 skill 的正式输出仍固定为：

## **一个 `ui_spec_package`**

但其 authority 来源不再是“直接从 FEAT 首次猜页面”，而是：

* 上游 FEAT 真相
* 已确认的 Prototype 体验锚点

并且 package 必须新增一份：

* `ui-semantic-source-ledger.json`

用于冻结：

* 哪些语义来自 FEAT
* 哪些语义来自 prototype
* 哪些语义来自其它 authority object
* 哪些语义是 AI inference

### 5.3.3A `ui-semantic-source-ledger.json`

本 ADR 明确：

## **`HTML Prototype -> UI Spec` 是语义压缩与补全，不是等价映射。**

因此 `proto-to-ui` 不能只输出“最终正确答案”，还必须输出：

## **语义来源账本。**

最小结构化格式应至少支持：

```yaml
ui_spec_semantic_sources:
  from_prototype:
    - semantic_area: layout
      refs: list
    - semantic_area: flow
      refs: list
    - semantic_area: cta_hierarchy
      refs: list
  from_feat:
    - semantic_area: business_constraints
      refs: list
    - semantic_area: completion_criteria
      refs: list
  from_other_authority:
    - authority_type: TECH | API | ARCH | TESTSET
      semantic_area: string
      refs: list
  inferred_by_ai:
    - semantic_area: string
      rationale: string
      confidence: low | medium | high
      requires_explicit_review: boolean
      approved_by: string | null
```

### 5.3.3B 推断语义的硬规则

所有 `inferred_by_ai` 条目都必须显式标记，不得静默埋进 UI Spec。

尤其以下推断属于高风险域：

* canonical data source
* state semantics
* API / error mapping
* completion semantics
* blocker / non-blocker behavior

这些内容如果不是直接来自上游 authority，就必须满足以下之一：

* 回写上游对象并获得 authority
* 在 review 中被显式批准
* 保持为 open question，不得伪装成已冻结真相

### 5.3.4 `proto-to-ui` 的硬约束

`proto-to-ui` 必须遵守：

1. 不得绕过 frozen prototype 重新发明主路径。
2. 不得在没有 upstream authority 支持时，从 prototype 私自扩展新需求。
3. 必须把 prototype 中已经确认的体验要点转译为结构化实现契约。
4. 必须补齐 prototype 无法稳定承载的实施语义：
   * 数据来源
   * 字段规则
   * 状态矩阵
    * API mapping
    * 事件定义
    * 边界态
    * 可访问性和响应式要求
5. 任何被 `inferred_by_ai` 补齐的语义，都必须进入 `ui-semantic-source-ledger.json`。
6. 若 prototype 与 FEAT 冲突，以 FEAT 与人工 review 结论为 authority，必要时阻断并回退，而不是在 UI Spec 内私自调和。

### 5.3.5 内建 gate

`ll-dev-proto-to-ui` 的唯一内建 gate 固定为：

* `UI Spec Implementation Readiness Check`

其 verdict 固定为：

* `pass`
* `conditional_pass`
* `fail`

这里的核心不是体验是否顺，而是：

## **下游前端、测试和 IMPL 是否已经拿到足够稳定的实施契约。**

同时，以下情况默认不得判定为 `pass`：

* 存在未声明来源的关键语义
* 存在未标记的 AI inference
* 关键高风险推断没有显式 review 决议
* `ui-semantic-source-ledger.json` 缺失或不可追踪

---

# 6. 链路责任重划

## 6.1 FEAT

`FEAT` 负责定义：

* 用户目标；
* 功能边界；
* 核心约束；
* 完成态；
* 不做什么。

`FEAT` 不负责像素级或页面级体验定型。

## 6.2 PROTOTYPE

`PROTOTYPE` 负责定义：

* 页面结构；
* 用户旅程；
* 主要信息层级；
* 主要交互逻辑；
* CTA 主次；
* 关键状态体验。

`PROTOTYPE` 不负责工程实现细节。

## 6.3 UI Spec

`UI Spec` 负责定义：

* 页面/组件清单；
* 字段和 props 契约；
* 状态枚举；
* 交互事件；
* 表单规则；
* API 绑定；
* 文案规范；
* 埋点与实施边界。

`UI Spec` 不再负责首次发明体验。

## 6.4 IMPL

`IMPL` 负责定义：

* 前后端 touch set；
* 实施顺序；
* 文件落点；
* 依赖关系；
* 联调路径；
* 验收映射；
* 风险点与交付策略。

`IMPL` 不再承担 UI 定义职责。

---

# 7. 迁移与兼容策略

## 7.1 `ll-dev-feat-to-ui` 的状态

本 ADR 生效后：

* `ll-dev-feat-to-ui` 不再作为全部界面型 FEAT 的统一默认 authoring path；
* 历史产物继续有效；
* 历史 `ui_spec_package` 不因本 ADR 失效。

在过渡期内，它可以只承担以下两类角色之一：

* 低复杂度 FEAT 的 direct UI fast path carrier
* 新 routing shell 的兼容入口

但它不得继续承载：

* 把所有 FEAT 一律 direct 到 UI Spec
* 跳过 `prototype_required` 的硬门禁

## 7.2 新旧链路兼容原则

Phase 1 固定如下：

1. 新增 `ll-dev-feat-to-proto`
2. 新增 `ll-dev-proto-to-ui`
3. 引入 `UI Derivation Routing Check`
4. `dev.feat-to-ui` 不再接受“直接从 FEAT 生成 UI Spec”的新默认入口，而是转为 route-aware 入口
5. 当 route 为 `prototype_required` 时，兼容壳只能作为 orchestration alias：
   * 先运行 `feat-to-proto`
   * 停在人工 review
   * 人工批准后再运行 `proto-to-ui`
6. 当 route 为 `direct_ui_allowed` 或带显式 bypass 的 `prototype_optional` 时，才允许 direct UI fast path
7. 兼容壳不得绕过人工 review 直接连跑到 UI Spec

## 7.3 自动派发策略

与 ADR-021 类似，本 ADR Phase 1 仍不建议直接纳入强制自动派发主链。

原因不是这条链不重要，而是：

* 何时需要 prototype 仍依赖稳定的 `ui_required` 信号；
* 何时必须走 prototype 还依赖稳定的 routing / complexity 信号；
* human review gate 需要明确 owner；
* prototype 文件编辑、批准和 freeze evidence 需要先稳定 runtime contract。

因此，Phase 1 建议：

* skill 正式入库；
* 支持 manual invocation；
* 支持 future opt-in job invocation；
* 待 approval evidence 与 human ownership contract 稳定后，再评估自动推进。

---

# 8. 后果

## 8.1 收益

采用本 ADR 后，系统获得以下收益：

* 体验错误在更低成本阶段暴露；
* 人类与 AI 的分工更清楚；
* UI Spec 不再同时扮演原型和契约两种角色；
* `IMPL` 与 coder 不必再在实现阶段重新发明页面语义；
* `impl-spec-test` 和后续 review 可以围绕更稳定的 UI authority 工作。

## 8.2 成本

本 ADR 也明确引入以下成本：

* 新增一个正式派生对象族；
* 新增一个强制 human gate；
* 新增 prototype package 的运行时 contract 与 evidence 管理；
* 旧 `feat-to-ui` 相关脚本和 skill 需要拆分、迁移或兼容包装。

这些成本是有意承担的。

因为它们换来的是：

## **把最贵的返工，从编码后、联调后，前移到 prototype review 前。**

## 8.3 明确拒绝的路线

本 ADR 明确拒绝两条路线：

### 路线 A：把单段式 `FEAT -> UI` 继续当成全部界面型 FEAT 的统一默认路线

拒绝原因：

* 体验定型与实现定型混层；
* 人类 review 关注点持续漂移；
* AI 更容易在 UI Spec 里发明未经体验确认的语义。

### 路线 B：`Prototype -> 直接实现`

拒绝原因：

* prototype 不是完整实现契约；
* 会把组件语义、状态映射、数据契约等关键问题再次留给编码阶段猜。

因此本 ADR 的最终立场固定为：

## **Prototype 负责体验定型，UI Spec 负责实现定型，IMPL 负责工程落地。**

---

# 9. 一句总结

本 ADR 不是在主链里“多加一道文书工序”，而是在代码之前正式增加一层：

## **低成本、高反馈、必须有人类拍板的体验定型层。**

该层的正式形态就是：

## **`FEAT -> Prototype -> Human Review -> UI Spec`**

从此以后：

* 没有 prototype，不进入 UI Spec authoring；
* prototype 未经人工确认，不进入 `proto-to-ui`；
* 没有 UI Spec，不允许把 prototype 直接当正式前端实现契约。
