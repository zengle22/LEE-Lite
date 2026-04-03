# ADR-013：FEAT-to-TECH Lite-Native Skill 设计派生冻结基线（边界补强与集成上下文冻结修订）

* 状态：Accepted
* 日期：2026-04-03
* 决策者：Le Zeng
* 适用范围：`ll-dev-feat-to-tech` skill、`dev.feat-to-tech` lite-native runtime、`tech_design_package`、`workflow.dev.tech_to_impl`
* 相关 ADR：ADR-008、ADR-009、ADR-011、ADR-012、ADR-014、ADR-034、ADR-038

---

# 1. 背景

LL 当前主链已经明确了上游派生路径：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT` 是产品语义层的直接冻结对象
* `TECH`、`TASK`、`TESTSET` 在 ADR-008 中已经被定义为 FEAT 的直接派生对象

在 FEAT 到设计层对象的这一段，仓库已经落地了一条可运行的 lite-native governed skill：

* canonical skill：`skills/ll-dev-feat-to-tech/`
* runtime entry：`skills/ll-dev-feat-to-tech/scripts/feat_to_tech.py`
* workflow key：`dev.feat-to-tech`

ADR-013 的既有主张继续成立：

* 一次运行只针对单个 `FEAT`
* 输出仍为一个 `tech_design_package`
* `TECH` 是唯一正式技术设计对象
* `ARCH`、`API` 仍为条件派生对象
* 三者仍由同一个 workflow 统一派生
* freeze 前仍必须执行一致性检查
* 下游 handoff 仍指向 `workflow.dev.tech_to_impl`
* `IMPL` 不得承担第二层技术设计

本次修订不推翻这条主链，只补足它目前还不够硬的部分：让 `TECH` 真正成为足以交付给下游实施的 governed truth，而不是一份仍然需要 `IMPL` 在实施期补设计的半成品说明文。

---

# 2. 问题陈述

当前需要补强的，不是主链方向，而是正式设计边界还存在以下四类缺口。

## 2.1 对象责任已定义，但还没有完全变成强结构约束

ADR-013 已说明：

* `ARCH` 负责模块边界、职责分配、关键拓扑、数据/控制流放置
* `TECH` 负责实现方向、实现单元映射、挂接点、异常与补偿、非功能要求等
* `API` 负责 request/response/event/handoff 契约与 schema surface

但这些仍主要是说明性责任边界，还没有完全升级为：

* 强模板约束
* 强 gate 约束
* 强 handoff 约束

因此运行时产物层仍容易出现：

* `ARCH` 偏空泛
* `TECH` 混入过多架构或 API 重复内容
* `API` 退化成接口清单或补充说明

## 2.2 只从 FEAT 派生设计对象，信息边界不足

当前正式输入边界是：

* `feat_freeze_package`
* `feat_ref`

这足以支持“从单 FEAT 派生一个设计对象”，但不足以支持“面向现有系统落地的正式技术设计”。

正式技术设计除了回答“新能力怎么做”，还必须回答：

* 如何接入现有 workflow / loop / skill / CLI
* 旧模块如何扩展、替换或旁路
* 哪些旧字段、旧状态、旧接口需要兼容
* 新旧 canonical owner 如何划分
* migration / fallback / shadow mode 如何处理

这些事实并不天然完整存在于 FEAT 本体。

## 2.3 若关键技术事实不前置冻结，`IMPL` 会被迫影子化 `TECH`

ADR-013 已经要求 `TECH` 至少冻结六块内容：

* 实现单元映射
* 接口契约
* 主时序 / 调用序列
* 异常与补偿策略
* 与现有系统的挂接点
* 最小代码骨架 / 伪代码

但从实际落地看，还存在若干高风险事实没有被提升为正式 SSOT：

* 内部状态机 / 生命周期设计
* 关键算法 / 判定逻辑
* 输入输出矩阵 / side effects
* 技术名词表 / canonical ownership
* 兼容与迁移约束

如果这些继续缺失，则 `IMPL` 虽然名义上不是第二层技术设计，实际上仍会在实施时临场补设计。

## 2.4 仅有 `design_consistency_check`，不足以阻止集成语义上的猜测冻结

当前强制 gate 是 `design_consistency_check`。它能检查：

* `ARCH`、`TECH`、`API` 是否一致
* optional artifact 是否与 assessment 一致
* 设计对象之间是否存在重叠或遗漏

但它还不能回答：

* 现有输入是否足够支撑面向当前系统的正式技术设计
* 是否已有足够的 legacy boundary / ownership / migration 信息
* 是否还在用猜测补系统挂接方案

因此需要在 consistency 之外，再补一层集成充分性检查。

---

# 3. 决策

## 3.1 决策摘要

LL 继续采用：

## **一个单 FEAT、lite-native、TECH-first 的 `ll-dev-feat-to-tech` governed skill**

作为 FEAT 到设计层对象的标准派生路径。

本次修订在不改变主框架的前提下，正式补强四点：

1. 将 `ARCH / TECH / API` 的边界从说明性责任边界升级为可校验的结构性边界。
2. 将 `feat-to-tech` 的正式输入从 `feat_freeze_package + feat_ref` 升级为 `feat_freeze_package + feat_ref + integration_context`。
3. 将正式 `TECH` 的最小强制结构从六块升级为十块。
4. 将集成充分性、状态机显式性、兼容迁移约束和 canonical ownership 纳入正式 gate 与 handoff。

以下既有原则保持不变：

1. 一次运行只允许选择一个 `feat_ref`。
2. 输出仍固定为一个 `tech_design_package`。
3. `TECH` 仍是每次运行的必选主产物。
4. `ARCH`、`API` 仍是条件派生对象。
5. `ARCH`、`TECH`、`API` 仍由同一个 workflow 统一生成。
6. freeze 前仍必须执行 `design_consistency_check`。
7. 下游正式 handoff 仍固定为 `workflow.dev.tech_to_impl`。
8. `IMPL` 仍不得承担第二层技术设计。

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

当前本地真正可运行、可验证、可 freeze 的 authority 由以下文件共同构成：

* `skills/ll-dev-feat-to-tech/SKILL.md`
* `skills/ll-dev-feat-to-tech/ll.contract.yaml`
* `skills/ll-dev-feat-to-tech/input/contract.yaml`
* `skills/ll-dev-feat-to-tech/output/contract.yaml`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_common.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_cli_integration.py`

本次修订进一步明确：

## **当前 runtime 仍是现状 authority，但在 `integration_context`、扩展 need assessment、`integration_sufficiency_check`、十块 `TECH` 结构和 handoff 扩展字段这些新增点上，以本 ADR 为升级目标真相。**

也就是说：

* 已实现部分继续以本地 runtime 为第一真相
* 本修订新增的治理要求，成为下一轮实现必须收敛到的正式 SSOT

---

## 3.3 正式输入边界

`ll-dev-feat-to-tech` 的正式输入升级为：

* 一个 freeze-ready 的 `feat_freeze_package`
* 一个显式 `feat_ref`
* 一个正式 `integration_context`

正式输入最小集至少应覆盖：

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
* `integration_context` 的结构化输入或其可追踪引用

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

### 3.3.1 `integration_context` 的正式定位

`integration_context` 是 FEAT 派生设计层时必须显式消费的上下文对象，用于冻结“该能力如何挂接到现有系统”的技术事实。

它不是可选背景材料，而是正式设计输入的一部分。

### 3.3.2 `integration_context` 至少应包含

* 现有相关 workflow / loop / skill / CLI 清单
* 现有模块与目录边界
* 相关旧字段 / 旧状态 / 旧接口定义
* canonical ownership 现状
* 兼容约束与历史行为约束
* 迁移模式假设：`replace / extend / shadow / bridge`
* 不允许改动的 legacy invariants
* 需要沿用的 gate / audit / repair / evidence 语义
* 相关 `source_refs / arch_refs / tech_refs / api_refs`

### 3.3.3 正式含义

`feat-to-tech` 不再是：

## **“从单个 FEAT 文本推出一份技术方案”。**

而是：

## **“从已冻结 FEAT + 明确集成上下文，派生一个可接入现有系统的正式设计包”。**

---

## 3.4 单 FEAT 选择原则

一次运行只允许选择一个 FEAT。

正式规则保持不变：

* `feat_ref` 是强制输入，不允许默认选第一个
* 每次 run 只允许输出一个主 `TECH`
* 每次 run 至多输出该 FEAT 对应的一个 `ARCH` 和一个 `API`
* 不允许一个 run 内同时为多个 FEAT 混写设计对象

如需为多个 FEAT 派生设计，应通过多个独立 run 完成。

这是为了保证：

* design package 与 FEAT 边界一一对应
* review、evidence、handoff 都挂在单一能力面上
* 下游 `tech_to_impl` 不必再拆 package

---

## 3.5 正式输出边界

该 skill 的唯一正式输出仍为：

## **一个 `tech_design_package`**

最小运行时 package 继续包含：

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

推荐输出目录保持：

* `artifacts/feat-to-tech/<run_id>--<feat_ref>/`

本次修订新增要求：

* `integration_context` 必须在 package 内以结构化字段或受治理 supporting artifact 的方式被保留并可引用
* 下游 handoff 必须能引用该集成上下文冻结结果
* `tech-design-bundle.json` 必须携带扩展后的 need assessment、gate 结果和引用字段

因此，正式主对象仍不是散文件集合，而是：

## **一个带 need assessment、integration sufficiency、traceability、consistency check、handoff 的受治理 design package。**

---

## 3.6 设计对象责任边界升级为强模板约束

本 ADR 正式冻结：

## **`ARCH / TECH / API` 的边界不仅是说明性责任边界，也是必须通过模板与 gate 校验落实的结构性边界。**

在此之前，先冻结一个前提：

## **FEAT 是能力定义与验收边界对象，不是代码落地对象。**

FEAT 只负责冻结：

* 要解决什么能力问题
* 边界是什么
* 约束是什么
* 验收标准是什么
* 该能力从哪些上游事实派生而来
* 业务名词表、业务态和完成态语义

FEAT 不负责直接给出：

* package / module / file 落点
* 详细接口字段结构
* 主调用序列
* 异常补偿细节
* 旧系统挂接步骤
* 伪代码级实现骨架
* 内部状态机与技术 canonical ownership

### 3.6.1 `ARCH`

`ARCH` 只能回答：

* 模块边界如何划分
* 职责如何分配
* 关键调用拓扑如何组织
* 数据 / 控制流放在哪里
* 哪些边界需要调整或保持
* 哪些系统级取舍是本设计必须冻结的

`ARCH` 不得退化为：

* 详细实现步骤
* API 字段级 schema 文档
* task 排期或工单拆分
* 伪代码说明文

### 3.6.2 `TECH`

`TECH` 只能回答：

* 能力如何在当前 runtime / codebase / workflow 中落地
* 内部实现单元如何映射
* 主调用序列是什么
* 关键失败模式如何处理
* 与现有系统具体怎么挂接
* 哪些技术事实是下游实施必须继承的

`TECH` 不得退化为：

* 只讲抽象意图，不给实现落点
* 只给 TODO / checklist / task order
* 把关键状态机、关键算法、关键 side effects 推给 `IMPL` 再决定

### 3.6.3 `API`

`API` 只能回答：

* 请求 / 响应 / 事件 / 消息 / handoff 的 schema 是什么
* 错误结构与 verdict 契约是什么
* consumer / provider 的行为约束是什么
* 幂等、兼容、版本语义是什么

`API` 不得退化为：

* 解释整套系统架构
* 解释内部实现路径
* 复写 `TECH` 中的内部调用组织

因此：

## **三者是同簇派生对象，但不是同内容的三份重写文档。**

---

## 3.7 `TECH` 是唯一正式技术设计，且强制结构由六块升级为十块

本 ADR 继续正式冻结：

## **在 FEAT 派生链上，`TECH` 是唯一正式技术设计对象；`IMPL` 不是第二层技术设计。**

本次修订将正式 `TECH` 的最小结构从六块升级为十块。凡是足以 handoff 到下游实施的正式 `TECH`，必须至少补齐以下内容。

### 1. 实现单元映射

必须写清：

* `package / module / file` 落点
* 新建 / 扩展 / 替换 / 包装 哪一种方式
* 关键能力分别落到哪些实现单元

### 2. 内部接口契约

必须写清：

* 输入结构
* 输出结构
* 错误结构
* 幂等性
* 前置条件
* 关键字段与语义约束

### 3. 主时序 / 调用序列

必须写清：

* happy path
* 主处理顺序
* 关键副作用发生点
* 返回与回执路径

### 4. 异常与补偿策略

必须写清：

* 关键失败点
* 中止 / 降级 / 重试 / partial success 规则
* 补偿与恢复语义
* evidence / audit / retention 行为

### 5. 与现有系统的挂接点

必须写清：

* 谁调用该能力
* 在哪条旧链路中接入
* 哪些旧模块保留、扩展或旁路
* compatibility / bridge / fallback 在哪里发生

### 6. 最小代码骨架 / 伪代码

必须写清：

* 模块清单
* 核心接口样例
* 至少一条 happy path
* 至少一条 failure path

### 7. 内部状态机 / 生命周期设计

必须写清：

* 核心状态
* 合法迁移
* 关键守卫条件
* 中间态 / 异常态
* 状态与字段之间的映射关系

### 8. 关键算法 / 判定逻辑

必须写清：

* 关键 decision rule
* 排序 / 聚合 / 归一化 / eligibility / 选择逻辑
* 是否 deterministic
* 允许的近似范围或策略约束

### 9. 输入输出矩阵 / Side Effects 表

必须写清：

* 每个核心动作的输入
* 输出
* 写入对象
* 外部副作用
* evidence materialization 点
* 幂等 / 重入语义

### 10. 技术名词表 / Canonical Ownership 表

必须写清：

* 核心技术名词
* 名词与业务名词的映射
* 字段 / 状态 / 对象 / event 的 canonical owner
* 禁止双真相源的约束

### 3.7.1 修订后的正式含义

只有同时满足以上十块内容的 `TECH`，才可被视为：

## **足以 handoff 到下游实施的正式技术设计对象。**

---

## 3.8 状态机、关键算法、I/O、名词表进入正式 SSOT 管理

以下内容不再允许作为临时说明、review 意见或 `IMPL` 实施期补充存在，而必须成为正式 SSOT 组成部分：

* 状态机 / 生命周期定义
* 关键算法 / 判定逻辑
* 输入输出结构与副作用表
* 技术名词表
* canonical ownership 定义
* 非功能约束
* 兼容与迁移规则

这些内容并非全部归入同一文档，而应按对象边界冻结：

### FEAT

* 业务目标
* 业务验收标准
* 业务名词表
* 业务态 / 完成态语义
* 范围与约束

### ARCH

* 模块边界
* 职责边界
* 系统级状态跨边界关系
* 关键流向和结构取舍

### API

* 外部输入输出结构
* 跨边界 schema
* consumer / provider 契约
* error / event / version 语义

### TECH

* 内部状态机实现映射
* 关键算法
* side effects
* canonical ownership
* NFR 落点
* 集成挂接规则

---

## 3.9 `TECH` 必出，`ARCH/API` 条件生成，Need Assessment 扩展为四项判断

本 ADR 继续规定：

* `TECH` 必须在每次运行中生成
* `ARCH` 是否生成，取决于 architecture-impacting assessment
* `API` 是否生成，取决于 boundary-contract assessment

在此基础上，need assessment 从两项扩展为四项正式判断：

* `arch_required`
* `api_required`
* `integration_context_sufficient`
* `stateful_design_present`

### 3.9.1 含义

* `integration_context_sufficient = false`
  表示当前输入不足以产出可落地的正式技术设计

* `stateful_design_present = false`
  表示当前设计尚未把关键状态机 / 生命周期事实显式冻结

### 3.9.2 正式要求

package 必须记录：

* 四项判断本身
* 每项判断的 rationale
* optional artifact 与这些判断之间的对应关系

这意味着：

## **`ARCH/API` 的存在性、集成上下文是否充分、状态设计是否显式，都是需要被 freeze、review 和 handoff 的治理决策。**

---

## 3.10 Gate 语义补强：新增 `integration_sufficiency_check`

本 workflow 仍必须在 freeze 前执行：

## **`design_consistency_check`**

它至少要回答：

* `TECH` 是否存在并可下游实现
* 当 `ARCH` 存在时，它是否真的覆盖系统边界问题
* 当 `API` 存在时，它是否真的覆盖契约问题
* `ARCH`、`TECH`、`API` 是否互相引用一致
* 是否出现边界重叠或遗漏

在此之外，新增一个强制前置检查：

## **`integration_sufficiency_check`**

它至少要回答：

* 当前输入是否已足够支撑“面向现有系统的正式技术设计”
* 是否已有足够的旧系统边界信息
* 是否已有足够的 canonical ownership 信息
* 是否已有足够的兼容 / migration 信息
* 是否存在关键 legacy dependency 未显式冻结

### 3.10.1 未通过时

若 `integration_sufficiency_check` 未通过：

* 不得进入 freeze-ready
* 不得用猜测补足挂接设计
* 必须补齐 `integration_context` 后重新派生

因此本次修订的正式 gate 语义是：

## **先判断“是否足够了解现有系统”，再判断“设计对象之间是否一致且不重叠”。**

---

## 3.11 review / acceptance / freeze 语义

该 skill 继续采用与其他 governed workflow 一致的双角色模型：

### executor

负责：

* 解析 selected FEAT
* 解析并消费 `integration_context`
* 进行四项 need assessment
* 生成 `TECH`
* 视情况生成 `ARCH` / `API`
* 执行 `integration_sufficiency_check`
* 执行 `design_consistency_check`
* 生成 review / acceptance / handoff 所需初始产物
* 记录 execution evidence

### supervisor

负责：

* 审核设计对象是否保持正确层级
* 审核 optional artifact 是否与 need assessment 一致
* 审核 `integration_context` 是否足够支撑现有系统挂接设计
* 审核 `stateful_design_present` 是否可信
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
* `integration_sufficiency_check.passed = true`
* `design_consistency_check.passed = true`
* downstream handoff present

因此：

## **`feat-to-tech` 不是 executor 写完 `tech-spec.md` 就结束，而是一条带 integration gate、supervisor 和 freeze gate 的正式治理链。**

---

## 3.12 下游 handoff 的正式定义

`handoff-to-tech-impl.json` 是正式路由对象，不是普通说明文件。

它继续至少必须保留：

* `feat_ref`
* `tech_ref`
* `arch_ref`（如存在）
* `api_ref`（如存在）
* `target_workflow`
* `primary_artifact_ref`
* `supporting_artifact_refs`

本次修订新增以下字段：

* `integration_context_ref`
* `canonical_owner_refs`
* `state_machine_ref`
* `nfr_constraints_ref`
* `migration_constraints_ref`
* `algorithm_constraint_refs`

下游继续固定为：

* `workflow.dev.tech_to_impl`

正式解释为：

## **`tech_to_impl` 不需要再重新判断该 FEAT 是否需要 `ARCH/API`，也不需要再补一版第二层技术设计，而应直接消费 design package 中已经冻结的技术真相包。**

`tech_to_impl` 的正式责任仍是：

* 组织研发实施步骤
* 编排代码改动顺序
* 管理 blocked / risk / delivery / acceptance
* 将 `ARCH/API/TECH` 的既有结论转化为执行任务

`tech_to_impl` 不得：

* 重新定义核心状态机
* 重新发明关键算法
* 重新解释系统挂接语义
* 改写 canonical owner
* 把 compatibility / migration / shadow mode 留到实施期临时决定

---

## 3.13 不允许的退化

以下做法被本 ADR 明确禁止：

1. 不传 `feat_ref`，直接拿整个 FEAT 包跑设计。
2. 把 `TECH`、`ARCH`、`API` 拆成三个互相独立的 workflow。
3. 每次都机械生成三份对象，不做 need assessment。
4. 让 `ARCH`、`TECH`、`API` 大量重复同样内容。
5. 让 `TECH` 退化成 TASK 排序、实现 TODO 或工单拆分。
6. 让 `API` 在没有契约面的 FEAT 上作为空模板输出。
7. 让 `ARCH` 在没有边界变化的 FEAT 上作为空模板输出。
8. 跳过 supervisor、`integration_sufficiency_check` 或 `design_consistency_check`，直接宣称 design freeze 完成。
9. 把 FEAT 直接写成 package / file / 伪代码级实现说明。
10. 让 `IMPL` 继续承担第二层技术设计，在实施阶段偷偷改写 `TECH` 的边界、职责或失败策略。
11. 把本应冻结在 `TECH` 中的实现单元映射、接口契约、主时序、补偿策略、挂接点、伪代码，推迟到 `IMPL` 再决定。
12. 仅凭 FEAT 文本和通用上下文，推测旧系统挂接方案并直接 freeze。
13. 未显式给出 canonical ownership，就让多个模块隐式共享状态 / 字段真相源。
14. 未显式定义关键状态机，就在 `TECH` 中只写“完成后进入某状态”之类自然语言描述。
15. 未显式定义关键算法 / 判定逻辑，就把关键 decision 留给 `IMPL` 或 coder agent 自行发挥。
16. 把兼容 / migration / bridge / shadow mode 留到实施阶段临时决定。
17. 把领域或技术名词表只保留在 prose 中，而不进入正式设计对象。
18. `TECH` 只给抽象方案，不给输入输出矩阵与副作用表。
19. `handoff-to-tech-impl.json` 不携带 `integration_context` 与关键约束引用，导致下游重新猜测系统接入方式。

---

# 4. 设计后果

采用本修订后，将得到以下结果。

## 4.1 `TECH` 更接近真正的唯一正式技术设计

`TECH` 不再只是实现导向说明文，而是一个真正足以冻结：

* 实现单元
* 状态机
* 关键算法
* 输入输出
* side effects
* 挂接点
* 兼容约束
* canonical ownership

的主对象。

## 4.2 `IMPL` 更难影子化 `TECH`

由于状态机、关键算法、I/O、副作用、canonical owner、挂接点都已冻结，下游实施空间会收缩到执行组织层，而不是继续补设计。

## 4.3 面向旧系统集成的设计可显式审查

“如何与现有系统集成”不再藏在 executor 的默认理解里，而是变成：

* 正式输入
* 正式判断
* 正式 gate
* 正式 review 对象

## 4.4 代价

代价是：

* `feat-to-tech` 输入会更重
* design package 的结构会更完整
* need assessment 与 gate 会更严格
* 某些以往能边实施边补的内容必须前置显式化

但这些成本属于：

## **为了让 `TECH` 真正成为 governed truth，而不是半成品设计说明所必须承担的复杂度。**

---

# 5. 事实来源与实现对齐要求

本 ADR 仍依据以下已落地文件冻结现状边界，并以此作为升级改造的第一批实现落点：

* `skills/ll-dev-feat-to-tech/SKILL.md`
* `skills/ll-dev-feat-to-tech/ll.contract.yaml`
* `skills/ll-dev-feat-to-tech/input/contract.yaml`
* `skills/ll-dev-feat-to-tech/input/schema.json`
* `skills/ll-dev-feat-to-tech/output/contract.yaml`
* `skills/ll-dev-feat-to-tech/output/schema.json`
* `skills/ll-dev-feat-to-tech/output/template.md`
* `skills/ll-dev-feat-to-tech/agents/executor.md`
* `skills/ll-dev-feat-to-tech/agents/supervisor.md`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_common.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_documents.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_builder.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py`
* `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_cli_integration.py`
* `skills/ll-dev-tech-to-impl/input/contract.yaml`
* `skills/ll-dev-tech-to-impl/input/schema.json`
* `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_validation.py`

它不再只是：

## **implementation-derived SSOT**

也是：

## **下一轮 `feat-to-tech` / `tech-to-impl` runtime 对齐到新治理边界的升级基线。**

---

# 6. 结论

LL 现在正式拥有一条补强后的设计层派生主链：

```text
feat_freeze_package + feat_ref + integration_context
  -> need assessment
  -> integration_sufficiency_check
  -> TECH mandatory
  -> ARCH optional
  -> API optional
  -> design_consistency_check
  -> freeze-ready tech_design_package
  -> handoff-to-tech-impl with integration/state/owner/algorithm refs
  -> workflow.dev.tech_to_impl
  -> IMPL task package
```

本 ADR 冻结其核心语义：

## **FEAT 到设计层的正确收敛方式，不是把 `ARCH / TECH / API` 拆碎，也不是把 `IMPL` 变成第二层技术设计，而是在单 FEAT 边界内先用 `FEAT + integration_context` 冻结唯一正式 `TECH`（按需附带 `ARCH/API`），再由下游 `IMPL` 仅负责研发实施组织与交付。**
