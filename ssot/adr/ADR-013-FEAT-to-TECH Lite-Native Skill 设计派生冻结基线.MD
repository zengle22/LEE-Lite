# ADR-013：FEAT-to-TECH Lite-Native Skill 设计派生冻结基线

* 状态：Accepted
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：`ll-dev-feat-to-tech` skill、`dev.feat-to-tech` lite-native runtime、`tech_design_package`
* 相关 ADR：ADR-008、ADR-009、ADR-011、ADR-012

---

# 1. 背景

LL 当前主链已经明确了上游派生路径：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT` 是产品语义层的直接冻结对象
* `TECH`、`TASK`、`TESTSET` 在 ADR-008 中已经被定义为 FEAT 的直接派生对象

但在 FEAT 到设计层对象的这一段，过去一直存在三个常见漂移：

* 有人把 `TECH` 当成唯一设计对象，导致 `ARCH` 和 `API` 只能以零散文档或临时说明附会进去；
* 有人想把 `ARCH`、`TECH`、`API` 拆成三个独立 workflow，结果上下文被切断、三份设计互相打架；
* 有人又把三者全部一股脑生成，最后文档边界重叠，出现“每份都讲了一遍系统、实现、接口”的混层。

同时还存在第四类漂移：

* 有人把 FEAT 直接写成实现蓝图，或者把 `TECH` 直接当成开发开工文档，结果能力边界、治理规则、实现落点、挂接策略全部混在一层，导致 FEAT 失去产品语义定位，TECH 也失去类型边界。

为了解决这个问题，当前仓库已经实现了一个可运行的 lite-native governed skill：

* canonical skill：`skills/ll-dev-feat-to-tech/`
* runtime entry：`skills/ll-dev-feat-to-tech/scripts/feat_to_tech.py`
* workflow key：`dev.feat-to-tech`

该 skill 已经把 FEAT 向设计层派生收敛为：

## **单 FEAT 选择、`TECH` 必出、`ARCH/API` 条件派生、最终统一 freeze 的一条治理链。**

本 ADR 的作用，是把这条已经落地的实现冻结为正式 SSOT。

---

# 2. 问题陈述

当前需要冻结的，不是“理论上 design workflow 应该怎样”，而是以下几个已被实现的问题边界：

## 2.1 输入到底是整个 FEAT 包，还是单个 FEAT

`feat_freeze_package` 往往包含多个 FEAT。

如果不要求显式 `feat_ref`：

* runtime 不知道该为哪一个 FEAT 出设计；
* 一次 run 会混写多个设计对象；
* 下游 `tech-impl` 无法把 handoff 精确挂到单个能力边界上。

## 2.2 `ARCH`、`TECH`、`API` 是不是平级必出

如果三者都强制生成：

* 中小 FEAT 会产生大量空洞设计；
* `ARCH`/`API` 容易沦为无意义模板文；
* review 成本上升，真正需要的判断被噪音淹没。

如果只保留 `TECH`：

* 系统边界决策会被塞回 TECH；
* 对外契约会被塞回 TECH；
* 下游实现与协作界面失去独立对象。

## 2.3 三个设计对象的边界如何不重叠

如果不冻结对象责任：

* `ARCH` 会讲一遍实现方案；
* `TECH` 会讲一遍系统分层；
* `API` 又会重复一遍边界与 contract 语义；
* 最终任何一个对象改动都会牵扯全部文档。

## 2.4 下游 handoff 应该交给谁

设计层 workflow 不是终点，真正的下游是实现层。

因此需要明确：

* 输出 package 的正式主对象是谁；
* handoff 到哪个 workflow；
* 下游是否还需要重新判断是否存在 `ARCH/API`。

## 2.5 FEAT、TECH、IMPL 是否被混成同一层

如果 FEAT 与技术文档不分层：

* FEAT 会被写成代码拆分说明，失去能力与验收边界的冻结价值；
* `TECH` 如果不承担正式技术设计，就会被不断下沉到 `IMPL` 中，最后失去 SSOT 地位；
* `IMPL` 如果继续承担第二层技术设计，就会在实施阶段偷偷改写上游边界；
* 开发无法判断什么是冻结设计，什么只是实施安排；
* review 也无法判断当前阶段到底该审“技术决策”，还是该审“执行计划”。

因此需要在本 ADR 中补上：

* FEAT 的正式定位；
* `TECH` 与 `IMPL` 的正式边界；
* 哪些技术设计内容必须留在 `TECH`；
* 哪些执行组织内容只能进入 `IMPL`。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个单 FEAT、lite-native、TECH-first 的 `ll-dev-feat-to-tech` governed skill**

作为 FEAT 到设计层对象的标准派生路径。

并冻结以下原则：

1. 输入固定为：
   * 一个 `feat_freeze_package`
   * 一个强制选择的 `feat_ref`
2. 输出固定为：
   * 一个 `tech_design_package`
3. `TECH` 是每次运行的必选主产物。
4. `ARCH` 仅在 FEAT 具有 architecture-impacting 特征时生成。
5. `API` 仅在 FEAT 存在明确跨边界契约面时生成。
6. `ARCH`、`TECH`、`API` 由同一个 workflow 统一生成，而不是拆成三个独立 workflow。
7. freeze 前必须有一个显式 `design_consistency_check`，用于检查三者是否一致且不重叠。
8. 下游正式 handoff 固定为：
   * `workflow.dev.tech_to_impl`

---

## 3.2 Canonical Authority

本 skill 的 authority 分为两层：

### 上游模板 authority

* `E:\ai\LEE\spec-global\departments\dev\workflows\templates\tech-design-l3-template.yaml`

它提供：

* L3 tech design 的阶段语义
* dev 侧 workflow 定位
* TECH 设计链的 canonical 背景

### 本仓库 implementation authority

本地真正可运行、可验证、可 freeze 的 authority 由以下文件共同构成：

* `skills/ll-dev-feat-to-tech/SKILL.md`
* `skills/ll-dev-feat-to-tech/ll.contract.yaml`
* `skills/ll-dev-feat-to-tech/input/contract.yaml`
* `skills/ll-dev-feat-to-tech/output/contract.yaml`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_common.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_cli_integration.py`

因此，本 ADR 明确：

## **本地 runtime + contract + role split 是 `dev.feat-to-tech` 的第一真相。**

---

## 3.3 正式输入边界

`ll-dev-feat-to-tech` 只接受：

* 一个 freeze-ready 的 `feat_freeze_package`
* 一个显式 `feat_ref`

正式输入最小集为：

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
* 选定的 `feat_ref` 在 package 中真实存在
* 选定 FEAT 至少具备：
  * `feat_ref`
  * `title`
  * `goal`
  * `scope`
  * `constraints`
  * `acceptance_checks`
  * `source_refs`

这意味着：

## **`feat-to-tech` 不是“从任意 FEAT markdown 写技术方案”，而是“只消费已治理、已冻结的 FEAT 包中的一个正式 FEAT”。**

---

## 3.4 单 FEAT 选择原则

一次运行只允许选择一个 FEAT。

正式规则：

* `feat_ref` 是强制输入，不允许默认选第一个
* 每次 run 只允许输出一个主 `TECH`
* 每次 run 至多输出该 FEAT 对应的一个 `ARCH` 和一个 `API`
* 不允许一个 run 内同时为多个 FEAT 混写设计对象

如需为多个 FEAT 派生设计，应通过多个独立 run 完成。

这是为了保证：

* design package 与 FEAT 边界一一对应
* review、evidence、handoff 都挂在单一能力面上
* 下游 `tech-impl` 不必再拆 package

---

## 3.5 正式输出边界

该 skill 的唯一正式输出为：

## **一个 `tech_design_package`**

最小运行时 package 包含：

* `package-manifest.json`
* `tech-design-bundle.md`
* `tech-design-bundle.json`
* `tech-spec.md`
* `tech-review-report.json`
* `tech-acceptance-report.json`
* `tech-defect-list.json`
* `tech-freeze-gate.json`
* `handoff-to-tech-impl.json`
* `execution-evidence.json`
* `supervision-evidence.json`

条件存在：

* `arch-design.md`
* `api-contract.md`

推荐输出目录：

* `artifacts/feat-to-tech/<run_id>--<feat_ref>/`

其中正式主对象不是散文件集合，而是：

## **一个带 need assessment、traceability、consistency check、handoff 的受治理 design package。**

---

## 3.6 设计对象责任边界

本 ADR 正式冻结三类对象的责任：

在此之前，先冻结一个前提：

## **FEAT 是能力定义与验收边界对象，不是代码落地对象。**

FEAT 只负责冻结：

* 要解决什么能力问题
* 边界是什么
* 约束是什么
* 验收标准是什么
* 该能力从哪些上游事实派生而来

FEAT 不负责直接给出：

* package / module / file 落点
* 详细接口字段结构
* 主调用序列
* 异常补偿细节
* 旧系统挂接步骤
* 伪代码级实现骨架

这些内容如果存在，应进入 FEAT 的技术派生层，而不是回写到 FEAT 本体。

### `ARCH`

只负责：

* 模块边界
* 职责分配
* 关键调用拓扑
* 数据 / 控制流放置
* 架构取舍与边界决策

不负责：

* 详细实现步骤
* 全量接口字段 schema
* task 级交付拆分

### `TECH`

只负责：

* 能力的技术定义与实现方向
* runtime carrier
* 内部约束
* 关键实现路径的原则性展开
* 实现单元映射
* 核心接口契约
* 主时序 / 调用序列
* 异常与补偿策略
* 与现有系统的挂接点
* 最小代码骨架 / 伪代码
* 非功能要求
* 下游 `tech-impl` 所必须继承的技术约束

不负责：

* 系统级边界总图
* 对外 API 全量契约细节
* task 级排期

### `API`

只负责：

* request / response / event / handoff contract
* schema surface
* 兼容性与版本策略
* error / verdict / decision 契约
* consumer / provider 约束

不负责：

* 大段架构说明
* 内部实现步骤
* 宏观系统分层设计

因此：

## **三者是同簇派生对象，但不是同内容的三份重写文档。**

---

## 3.6.1 `TECH` 是唯一正式技术设计

本 ADR 进一步正式冻结：

## **在 FEAT 派生链上，`TECH` 是唯一正式技术设计对象；`IMPL` 不是第二层技术设计。**

`TECH` 回答：

* 这个能力切面是什么
* 边界在哪里
* 哪些规则不能变
* 内部与外部对象如何协同
* 核心实现路径怎么设计
* 下游研发实施必须遵守哪些技术事实

这就是当前 `ll-dev-feat-to-tech` 的主产物定位。

换句话说：

## **当前 `feat-to-tech` 输出的 `TECH`，就是正式技术设计本体，而不是等待 `IMPL` 再补一版“第二层设计”。**

---

## 3.6.2 `TECH` 的六块强制内容

凡是足以 handoff 到下游实施的正式 `TECH` 文档，必须至少补齐以下六块内容。

这六块内容不是建议项，而是正式技术设计的最小结构基线。

### 1. 实现单元映射

必须写清：

* 对应哪个 `package / module / file`
* 是新建还是扩展已有模块
* 模块之间谁依赖谁
* 关键能力分别落到哪些实现单元

禁止只写组件名或抽象对象名，而不给代码落点。

### 2. 接口契约

每个核心组件至少写清：

* 输入结构
* 输出结构
* 错误结构
* 关键字段
* 是否幂等
* 调用前置条件

禁止只写“required outputs”“decision exists”之类概念级表述，而不给结构约束。

当存在对外或跨边界契约时：

* `API` 继续负责正式 request / response / event schema；
* `TECH` 负责说明这些契约在实现路径中的使用方式，而不是重复整份外部 schema。

### 3. 主时序 / 调用序列

必须明确主要 happy path 的调用顺序，包括但不限于：

* 请求归一化
* 前置校验
* 依赖检查
* 主处理执行
* 回执或结果构建
* staging / evidence / materialization 等副作用落点
* 返回路径

如果没有调用序列，开发只能自行猜测，设计边界会立刻发散。

### 4. 异常与补偿策略

必须明确关键失败点上的处理语义，例如：

* 前序步骤成功、后序步骤失败时如何补偿
* 是否允许 partial success
* 哪些失败可降级，哪些失败必须中止
* receipt / dispatch / retention / closure 等环节失败时如何记录与恢复

`risks`、`fallback`、`forbidden shortcuts` 不能替代可执行的失败处理策略。

### 5. 与现有系统的挂接点

必须回答：

* 谁调用该能力
* 先接入哪些旧 skill / CLI / loop
* compatibility mode 在哪里开启
* file handoff / gate / repair / audit findings 分别在哪个步骤发生
* 新能力是新 workflow、新阶段，还是现有主链中的扩展点

如果没有挂接点说明，文档就只是“新世界定义”，无法落到当前系统。

### 6. 最小代码骨架 / 伪代码

至少提供：

* 模块清单
* 核心接口样例
* 一条 happy path 伪代码
* 一条 failure path 伪代码

没有这一层，开发仍然需要重新发明实现组织方式。

因此，本 ADR 正式规定：

## **这六块内容属于正式 `TECH` 的强制结构，不强行塞回 FEAT，也不允许继续下沉到 `IMPL` 中重写一版。**

---

## 3.7 `TECH` 必出，`ARCH/API` 条件生成

本 ADR 正式规定：

* `TECH` 必须在每次运行中生成
* `ARCH` 是否生成，取决于 architecture-impacting need assessment
* `API` 是否生成，取决于 boundary-contract need assessment

### `ARCH` 触发条件

至少包括以下类型：

* FEAT 涉及模块边界变化
* FEAT 涉及职责重分配
* FEAT 涉及跨模块调用拓扑调整
* FEAT 涉及 IO/path/topology/registry/gate placement 等系统放置问题
* FEAT source refs 已显式引用 `ARCH-*`

### `API` 触发条件

至少包括以下类型：

* FEAT 显式包含 contract / proposal / decision / handoff / queue 等边界对象
* FEAT 需要 consumer/provider 协作约束
* FEAT 需要 request/response/event/message 语义
* FEAT 的输出本身就是对外或跨边界 exchange object

如果不满足，则必须显式输出：

* `arch_required = false`
* `api_required = false`

而不是生成空洞对象。

---

## 3.8 Need Assessment 的正式地位

need assessment 不是实现细节，而是正式 package 内容的一部分。

正式要求：

* package 必须记录 `arch_required`
* package 必须记录 `api_required`
* package 必须记录每个判断的 rationale
* optional artifact 的存在与否必须与该判断一致

这意味着：

## **`ARCH/API` 的存在性本身，就是一个需要被 freeze、review 和 handoff 的治理决策。**

---

## 3.9 一致性检查是强制 gate

本 workflow 必须在 freeze 前执行：

## **`design_consistency_check`**

它至少要回答：

* `TECH` 是否存在并可下游实现
* 当 `ARCH` 存在时，它是否真的覆盖了系统边界问题
* 当 `API` 存在时，它是否真的覆盖了契约问题
* `ARCH`、`TECH`、`API` 是否互相引用一致
* 是否出现边界重叠或遗漏

如果 consistency check 未通过，则：

* package 不得 freeze-ready
* 必须进入 revise

---

## 3.10 review / acceptance / freeze 语义

该 skill 采用与其他 governed workflow 一致的双角色模型：

### executor

负责：

* 解析 selected FEAT
* 进行 need assessment
* 生成 `TECH`
* 视情况生成 `ARCH` / `API`
* 生成 review / acceptance / handoff 所需初始产物
* 记录 execution evidence

### supervisor

负责：

* 审核设计对象是否保持正确层级
* 审核 optional artifact 是否与 need assessment 一致
* 审核 consistency check 是否可信
* 形成 supervision evidence
* 决定 `pass / revise / reject`

freeze-ready 至少要求：

* input_structural_pass
* input_semantic_pass
* output_structural_pass
* output_semantic_pass
* execution_evidence_present
* supervision_evidence_present
* `TECH` present
* optional outputs match assessment
* cross-artifact consistency passed
* downstream handoff present

因此：

## **`feat-to-tech` 不是 executor 写完 `tech-spec.md` 就结束，而是一条带 supervisor 和 freeze gate 的正式治理链。**

---

## 3.11 下游 handoff 的正式定义

`handoff-to-tech-impl.json` 是正式路由对象，不是普通说明文件。

它至少必须保留：

* `feat_ref`
* `tech_ref`
* `arch_ref`（如存在）
* `api_ref`（如存在）
* `target_workflow`
* `primary_artifact_ref`
* `supporting_artifact_refs`

下游固定为：

* `workflow.dev.tech_to_impl`

正式解释为：

## **`tech-impl` 不需要再重新判断该 FEAT 是否需要 `ARCH/API`，也不需要再补一版第二层技术设计，而应直接消费 design package 中已经冻结的技术结论。**

当前下游 runtime 名称即使暂时保留 `tech_to_impl`，其语义也必须被解释为：

## **`IMPL` 研发实施任务 workflow，而不是继续生产新一层 `TECH` 的 workflow。**

`tech-impl` 的正式责任应是：

* 组织研发实施步骤
* 编排代码改动顺序
* 管理 blocked / risk / delivery / acceptance
* 将 `ARCH/API/TECH` 的既有结论转化为执行任务，而不是重写其边界

---

## 3.12 不允许的退化

以下做法被本 ADR 明确禁止：

1. 不传 `feat_ref`，直接拿整个 FEAT 包跑设计。
2. 把 `TECH`、`ARCH`、`API` 拆成三个互相独立的 workflow。
3. 每次都机械生成三份对象，不做 need assessment。
4. 让 `ARCH`、`TECH`、`API` 大量重复同样内容。
5. 让 `TECH` 退化成 TASK 排序、实现 TODO 或工单拆分。
6. 让 `API` 在没有契约面的 FEAT 上作为空模板输出。
7. 让 `ARCH` 在没有边界变化的 FEAT 上作为空模板输出。
8. 跳过 supervisor 和 consistency gate，直接宣称 design freeze 完成。
9. 把 FEAT 直接写成 package / file / 伪代码级实现说明。
10. 让 `IMPL` 继续承担第二层技术设计，在实施阶段偷偷改写 `TECH` 的边界、职责或失败策略。
11. 把本应冻结在 `TECH` 中的实现单元映射、接口契约、主时序、补偿策略、挂接点、伪代码，推迟到 `IMPL` 再决定。

---

# 4. 设计后果

采用本 ADR 后，将得到以下结果：

## 4.1 设计层派生对象边界更稳定

`ARCH`、`TECH`、`API` 的职责被写死，后续实现和评审不需要再靠口头解释。

## 4.2 workflow 更短，但不失治理

没有把设计层拆成过碎的 3 条链，但仍然保留了：

* need assessment
* 双角色 review
* freeze gate
* downstream handoff

## 4.3 下游 `tech-impl` 接口更清晰

`tech-impl` 只需消费一个 package，不再自己重做：

* 是否需要 architecture companion
* 是否需要 API companion
* 设计对象之间是否一致

同时，`tech-impl` 也必须清楚自己不承担的范围：

* 不再重新拆组件职责
* 不再重新定义对象模型
* 不再重新决定 fail-closed / fail-open / boundary ownership
* 不再影子化 `TECH`

## 4.4 代价

代价是：

* package 结构比单文件技术方案更重
* need assessment 与 consistency check 成为强制环节
* optional artifact 的存在性也要被纳入 review
* `TECH` 需要写到足够可实施，不能再把关键设计空洞地留给 `IMPL` 二次发明

但这些复杂度属于：

## **为了让设计层对象真正成为 governed truth 所必须显式化的成本。**

---

# 5. 事实来源

本 ADR 依据以下已落地文件逆向冻结：

* `skills/ll-dev-feat-to-tech/SKILL.md`
* `skills/ll-dev-feat-to-tech/ll.contract.yaml`
* `skills/ll-dev-feat-to-tech/input/contract.yaml`
* `skills/ll-dev-feat-to-tech/input/schema.json`
* `skills/ll-dev-feat-to-tech/output/contract.yaml`
* `skills/ll-dev-feat-to-tech/output/schema.json`
* `skills/ll-dev-feat-to-tech/output/template.md`
* `skills/ll-dev-feat-to-tech/resources/upstream-workflow-analysis.md`
* `skills/ll-dev-feat-to-tech/agents/executor.md`
* `skills/ll-dev-feat-to-tech/agents/supervisor.md`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_common.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_cli_integration.py`

它是一份：

## **implementation-derived SSOT**

而不是脱离现有实现另写的一份理想流程图。

---

# 6. 结论

LL 现在正式拥有一条稳定的设计层派生主链：

```text
feat_freeze_package + feat_ref
  -> need assessment
  -> TECH mandatory
  -> ARCH optional
  -> API optional
  -> cross-artifact consistency check
  -> freeze-ready tech_design_package
  -> workflow.dev.tech_to_impl
  -> IMPL task package
```

本 ADR 冻结其核心语义：

## **FEAT 到设计层的正确收敛方式，不是把 `ARCH` / `TECH` / `API` 拆碎，也不是把 `IMPL` 变成第二层技术设计，而是在单 FEAT 边界内先冻结唯一正式 `TECH`（按需附带 `ARCH/API`），再由下游 `IMPL` 仅负责研发实施组织与交付。**
