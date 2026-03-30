# ADR-021：FEAT-to-UI Lite-Native Skill UI Spec 冻结基线

* 状态：Accepted
* 日期：2026-03-30
* 决策者：Le Zeng
* 适用范围：`ll-dev-feat-to-ui` skill、`dev.feat-to-ui` lite-native runtime、`ui_spec_package`
* 相关 ADR：ADR-008、ADR-012、ADR-013、ADR-020

---

# 1. 背景

当前 LL 主链已经明确了两条 FEAT 直接派生路径：

* `FEAT -> TECH`
* `FEAT -> TESTSET`

但仍然缺少一个正式对象，去冻结：

## **用户如何在界面里完成这个 FEAT。**

结果是：

* 前端实现需要从 FEAT 反推页面目标、主路径和状态模型；
* `TECH` 经常被迫承接本应属于界面层的路径、字段、反馈和页面结构；
* 团队在“原型图”“口头说明”“零散 TODO”之间反复切换，没有稳定的界面层 SSOT。

因此，本 ADR 在 SSOT 中补上一层正式对象：

## **UI Spec**

它不是视觉设计稿，也不是页面代码，而是把 FEAT 稳定转成可驱动 UI / TECH 开发的界面契约。

---

# 2. 问题陈述

当前需要冻结的是以下几个漂移边界。

## 2.1 FEAT 到页面之间缺少正式契约层

如果直接让 UI 或 TECH 从 FEAT 猜页面，会出现：

* 页面目标靠猜；
* 用户主路径只存在于实现者脑内；
* 关键分支、失败态、恢复态在编码阶段才首次出现；
* 字段和接口触点直到开发时才被显式化。

## 2.2 原型图与文档说明长期并行

如果只产出草图或零散说明：

* 页面结构与用户路径没有统一载体；
* ASCII / 轻原型经常缺失；
* 评审、开发、测试都要二次猜测。

## 2.3 状态模型后置

如果 UI Spec 只写正常态，不写：

* 校验失败态
* 提交中态
* 提交失败态
* 中断 / 恢复态

则界面层无法真正形成 SSOT。

## 2.4 UI 与 TECH 的边界没有落到字段与动作

如果不冻结：

* input / display / required / derived 字段
* user actions / system actions
* data dependencies / api touchpoints
* frontend validation / backend assumptions

则 UI 和 TECH 无法真正并行。

## 2.5 不是所有 FEAT 都应该被强制派生 UI

有些 FEAT 是纯后端能力或内部治理能力，不应机械生成 UI Spec。

因此 `feat-to-ui` 不能简单等价为“所有 FEAT 自动派生 UI”。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个单 FEAT 选择、lite-native、以 UI Spec 为主对象的 `ll-dev-feat-to-ui` governed skill**

作为 FEAT 到界面契约层的标准派生路径。

本 ADR 冻结以下原则：

1. 输入固定为：
   * 一个 `feat_freeze_package`
   * 一个显式 `feat_ref`
2. 输出固定为：
   * 一个 `ui_spec_package`
3. `UI Spec` 是主对象，不是视觉稿，不是代码设计，不是测试计划。
4. 每个 `UI Spec` 必须至少冻结：
   * 页面目标
   * 用户路径
   * UX 主流程说明
   * ASCII 结构原型
   * 关键状态
   * 技术边界
5. 一个 FEAT 可以生成一个或多个 `UI Spec`。
6. 本 workflow 的唯一内建 gate 固定为：
   * `UI Spec Completeness Check`
7. gate 结果词表固定为：
   * `pass`
   * `conditional_pass`
   * `fail`
8. Phase 1 只落 skill 与 manual / opt-in runtime，不默认把 `feat-to-ui` 加进 FEAT 自动 dispatch。

---

## 3.2 命名与定位

本 ADR 固定：

* skill 名称：`ll-dev-feat-to-ui`
* workflow key：`dev.feat-to-ui`

原因是 UI Spec 在本仓库里属于：

## **工程交付导向的界面契约 workflow**

而不是视觉设计 workflow。

---

## 3.3 正式输入边界

`ll-dev-feat-to-ui` 只接受：

* 一个 freeze-ready 的 `feat_freeze_package`
* 一个显式 `feat_ref`

最小运行时输入文件集固定为：

* `package-manifest.json`
* `feat-freeze-bundle.md`
* `feat-freeze-bundle.json`
* `feat-review-report.json`
* `feat-acceptance-report.json`
* `feat-defect-list.json`
* `feat-freeze-gate.json`
* `handoff-to-feat-downstreams.json`
* `execution-evidence.json`
* `supervision-evidence.json`

同时必须满足：

* `artifact_type = feat_freeze_package`
* `workflow_key = product.epic-to-feat`
* `status ∈ {accepted, frozen}`
* `feat-freeze-gate.json.freeze_ready = true`
* 选定 `feat_ref` 在包中真实存在

选定 FEAT 的最小字段固定为：

* `feat_ref`
* `title`
* `goal`
* `scope`
* `constraints`
* `acceptance_checks`
* `source_refs`

可选 UI enrichments 包括：

* `ui_units`
* `ui_input_fields`
* `ui_display_fields`
* `ui_api_touchpoints`
* `platform`
* `trigger_scenario`

但这些 enrichments 只能补强 UI Spec，不得覆盖 FEAT 主边界。

---

## 3.4 并非所有 FEAT 自动派生 UI

本 ADR 明确：

## **UI Spec 是“涉及用户界面的 FEAT”的默认必选产物，不是“所有 FEAT”的默认直接下游。**

原因是当前 FEAT contract 尚未稳定携带统一的：

* `ui_required`
* `ui_surface_kind`
* `ui_unit_list`

如果现在把 `workflow.dev.feat_to_ui` 直接并入 FEAT 自动 dispatch，就会把纯后端 FEAT 也机械派发到 UI skill。

因此 Phase 1 固定如下：

1. `ll-dev-feat-to-ui` 正式入库并可运行；
2. 支持 manual invocation 和 future opt-in job invocation；
3. 不默认改写 FEAT 主链自动 dispatch；
4. 待 FEAT contract 增加稳定 `ui_required` 信号后，再评估是否进入自动派发主链。

### 3.4.1 Phase 1 派生准则

在 Phase 1 中，人工或系统满足任一条件时，建议派生 UI Spec：

* FEAT 涉及新增页面 / 弹窗 / 抽屉 / 流程步骤
* FEAT 改变用户可见字段、状态或反馈
* FEAT 改变用户主路径或关键分支
* FEAT 需要前端新增或调整交互入口

满足以下情况时，默认不派生 UI Spec：

* 纯后端能力
* 纯数据治理
* 对用户不可见的内部机制
* 仅 TECH 实现细节调整且不改变 UI surface

如果 Phase 1 缺少稳定结构化信号，则 manual invocation 必须显式记录派生 rationale，而不是凭习惯触发。

---

## 3.5 正式输出边界

该 skill 的唯一正式输出为：

## **一个 `ui_spec_package`**

最小运行时 package 包含：

* `package-manifest.json`
* `ui-spec-bundle.md`
* `ui-spec-bundle.json`
* `ui-flow-map.md`
* `ui-spec-completeness-report.json`
* `ui-spec-review-report.json`
* `ui-spec-defect-list.json`
* `ui-spec-freeze-gate.json`
* `execution-evidence.json`
* `supervision-evidence.json`
* 一个或多个 `[UI-<FEAT_REF>-<page_slug>]__ui_spec.md`

推荐输出目录：

* `artifacts/feat-to-ui/<run_id>--<feat_ref>/`

当一个 FEAT 产生多个 UI Spec 时，package 还必须提供一个包级总览索引，至少回答：

* 所有 UI Spec 列表
* 顺序 / 上下游关系
* 哪些是主页面，哪些是分支页面
* package-level entry / exit

本 ADR 在 Phase 1 里将该对象固定为轻量 `ui-flow-map.md`。

---

## 3.6 UI Spec 的正式责任

UI Spec 负责回答：

* 这个 FEAT 对应哪些界面任务
* 用户在页面里怎么走
* 页面结构大概长什么样
* 页面有哪些关键状态
* UI 和 TECH 的边界在哪里

每个 UI Spec 必须显式包含：

* `Page Goal`
* `Scope`
* `Entry & Exit`
* `Main Path`
* `Branch Paths`
* `UX Flow Notes`
* `Layout Structure`
* `ASCII Wireframe`
* `States`
* `Fields`
* `Actions`
* `Validation Rules`
* `Technical Boundary`
* `Feedback Rules`
* `Open Questions`
* `Completeness Checklist`

UI Spec 与 TECH 的交叉区进一步冻结为：

* UI Spec 可以声明接口触点、字段边界、前端校验和反馈规则
* UI Spec 冻结“界面侧需要什么”
* TECH 冻结“系统如何实现它”
* UI Spec 不定义后端内部数据模型、服务拆分、持久化策略、状态机实现细节
* TECH 必须消费 UI Spec 中冻结的页面路径、状态和触点，不得在无回写的情况下擅自改写

UI Spec 明确不负责：

* 最终视觉稿
* 像素级样式
* 实际代码结构
* 测试用例细节
* 上线策略
* 后续体验优化决策

---

## 3.7 多 UI Spec 拆分规则

### 生成 1 个 UI Spec

适用于：

* 单页面功能
* 单弹窗
* 单步骤表单

### 生成多个 UI Spec

适用于：

* 多步骤流程
* 明显不同页面职责
* 页面结构差异大
* 一个 FEAT 含多个独立用户任务

推荐拆分维度固定为：

* 按页面拆
* 按步骤拆
* 按用户任务拆

不建议按组件过细拆分。

`ui_units` 在 Phase 1 中是优先输入信号，但不是唯一拆分依据：

* 如果 FEAT 显式提供 `ui_units`，skill 应优先按其拆分
* 如果 `ui_units` 缺失，skill 可以基于 FEAT 内容推断，但必须记录 inference rationale 与 open questions

对于复杂页面，ASCII Wireframe 至少要表达主结构态；如存在高风险失败态或提交态，建议补一份对应状态的 ASCII。

---

## 3.8 Completeness Gate

本 workflow 的唯一 gate 固定命名为：

## **UI Spec Completeness Check**

它不评审“美不美”，只评审：

## **够不够完整，能不能作为后续 UI / TECH 开发输入。**

最小检查域固定为：

### A. 目标完整性

* 页面目标是否明确
* 用户任务是否明确
* 完成定义是否明确

### B. 路径完整性

* 是否有主路径
* 是否至少有两条关键分支
* 是否定义进入与退出条件

### C. 结构完整性

* 是否有页面区块
* 是否有 ASCII 原型
* 是否体现关键信息顺序

### D. 状态完整性

* 是否覆盖至少五个关键状态
* 是否有失败态
* 是否有提交中态

推荐最小状态命名集为：

* `initial`
* `ready`
* `validation_error`
* `submitting`
* `submit_error`
* `submit_success`

### E. 技术边界完整性

* 是否有字段边界
* 是否有关键动作
* 是否有数据依赖 / 接口触点
* 是否有前端校验规则

通过标准冻结为：

* `pass`: 可以直接进入后续 UI / TECH 开发
* `conditional_pass`: 可以进入，但必须带着 open questions
* `fail`: 缺关键路径、状态或技术边界，不允许视为 ready

`conditional_pass` 的语义进一步收紧为：

### 允许存在的 open questions

* 文案措辞未定
* 次级说明区是否折叠
* 某些非关键 display 字段是否展示

### 不允许以 open questions 形式漏过去的关键项

* 主路径是否这样走
* 关键状态是否存在
* 提交后跳转到哪里
* 哪些字段必填
* 哪些接口触点被调用
* 失败反馈怎么做

也就是说：

## **主路径、关键状态、关键字段、关键动作、关键触点、关键失败反馈，不允许以 open questions 形式带入后续流程。**

---

# 4. 实现冻结

本仓库对 `dev.feat-to-ui` 的第一真相固定为：

* `skills/ll-dev-feat-to-ui/SKILL.md`
* `skills/ll-dev-feat-to-ui/ll.contract.yaml`
* `skills/ll-dev-feat-to-ui/input/contract.yaml`
* `skills/ll-dev-feat-to-ui/output/contract.yaml`
* `skills/ll-dev-feat-to-ui/scripts/feat_to_ui.py`

runtime 必须做到：

1. 解析 selected FEAT
2. 支持显式 `ui_units` 驱动多 UI Spec 输出
3. 在缺少 `ui_units` 时允许推断拆分，但必须显式记录 rationale
4. 输出 package-level `ui-flow-map.md`
5. 生成 `UI Spec Completeness Check`
6. 只有 `pass` 或满足收紧语义的 `conditional_pass` 才视为 readiness 通过

---

# 5. 一句话定义

> **FEAT → UI Spec** 的目标，是把业务功能定义转成一个可驱动开发的界面契约；该契约必须包含页面目标、用户路径、UX 主流程、ASCII 结构原型、关键状态以及技术边界，并通过 `UI Spec Completeness Check` 后，作为后续 UI / TECH 开发的输入。
