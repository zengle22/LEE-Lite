# ADR-034：IMPL 作为派生执行契约与自包含实施包收敛层

* 状态：Draft
* 日期：2026-03-31
* 决策者：Le Zeng
* 适用范围：`dev.tech-to-impl`、`ssot/impl`、`feature_impl_candidate_package`、`template.dev.feature_delivery_l2`、coder/tester 下游执行入口
* 相关 ADR：ADR-008、ADR-013、ADR-014、ADR-021、ADR-033

---

# 1. 背景

当前仓库已经基本冻结并串起了从决策到执行前输入准备的主链与派生链：

* `ADR -> SRC -> EPIC -> FEAT`
* `FEAT -> ARCH / TECH / API / UI / TESTSET`
* `TECH -> IMPL`

其中：

* `ADR / SRC / EPIC / FEAT` 逐层冻结为什么做、做什么、能力怎么拆；
* `ARCH / TECH / API / UI / TESTSET` 分别冻结系统边界、技术方案、契约边界、交互约束与验证口径；
* `IMPL` 已经被 ADR-014 冻结为“研发实施任务文档，而不是第二层技术设计”。

但随着链路逐步完整，`IMPL` 的职责又出现了新的收敛需求：

* 执行 Agent 不应在运行期继续沿整条链四处回捞上下文；
* coder 与 tester 需要共享同一份冻结后的执行输入，而不是各自重新理解上游；
* UI / TECH / TESTSET 的关键约束需要在交付前被合并成一次可消费的任务闭包；
* `IMPL` 需要更明确地区分哪些内容是必须遵守的执行契约，哪些只是帮助理解的背景说明。

同时，现有口径还存在一处容易误解的张力：

* ADR-008 把 `IMPL` 列为正式对象，并描述为“面向工程实现的最小执行单元”；
* ADR-014 已经进一步指出 `IMPL` 不是新的技术设计，不得改写上游决策；
* 但系统还没有明确冻结：**`IMPL` 到底是不是新的事实源，还是一次执行的派生收敛视图。**

因此，需要一份新的 ADR，把 `IMPL` 的最终定位再往前推进一步：

## **`IMPL` 不是新的需求/设计真相源，而是从上游 SSOT 派生出来、面向执行的自包含实现契约与实施任务包。**

---

# 2. 问题陈述

当前真正需要回答的，不是“要不要把 IMPL 写得更长”，而是以下几个更结构性的边界问题。

## 2.1 `IMPL` 当前仍然容易被误解成新的事实源

如果只说：

* `IMPL` 是开发直接执行的对象；
* `IMPL` 是最小实现单元；
* `IMPL` 是正式对象；

那么执行侧很容易进一步误解为：

* `IMPL` 可以自己补需求；
* `IMPL` 可以自己改技术边界；
* `IMPL` 可以自己选择忽略 UI / TESTSET；
* `IMPL` 与上游冲突时，可以以 `IMPL` 为准。

这会把 `IMPL` 从“派生执行视图”滑向“新的最终真相层”。

## 2.2 运行期沿链检索不稳定

如果 coder / tester 在执行时继续临时检索上游链路，每次都可能出现：

* 多看一个文档；
* 漏看一个文档；
* 看错 revision；
* 把历史约束误带进当前任务；
* 把 informative 背景错当 normative 约束。

结果就是同一任务的执行输入并不稳定。

## 2.3 coder 与 tester 容易消费到不同版本的“任务理解”

当前链路里：

* coder 更偏向看 `TECH / API / IMPL`；
* tester 更偏向看 `TESTSET / FEAT / IMPL`；
* UI 约束又可能独立落在 `UI`；
* 业务边界又来自 `FEAT / EPIC / SRC / ADR`。

如果没有一份最终的执行收敛包：

* coder 做的是一版理解；
* tester 验的是另一版理解；
* gate 审的是第三版口径；
* 最后虽都“引用了上游”，但并不消费同一份冻结输入。

## 2.4 `IMPL` 缺少显式的规范性分层

现有 `IMPL` 已经强调“不做第二层技术设计”，但仍缺少更细的显式约束：

* 哪些内容是 `MUST`；
* 哪些内容只是背景说明；
* 哪些执行步骤是 required；
* 哪些只是 suggested；
* 哪些边界一旦变化必须回到上游重冻。

如果这层不冻结，执行 Agent 仍然容易把“建议写法”和“硬约束”混在一起。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **把 `IMPL` 定义为从上游 SSOT 派生而来的 `Implementation Contract / Execution Bundle`。**

它的职责不是成为新的需求、设计或测试事实源，而是：

* 收敛当前任务所需的上游有效约束；
* 冻结一次可执行的任务输入；
* 为 coder / tester / patch / debug / gate checker 提供同一份直接可消费上下文；
* 明确交付物、验收标准、证据要求与执行边界；
* 避免执行期继续依赖不稳定的链式检索与二次解释。

因此，本 ADR 正式冻结：

1. `IMPL` 仍然保留为正式受治理对象；
2. 但 `IMPL` **不是新的事实定义源**；
3. `IMPL` 的 authority 仅限于：
   * 当前任务执行输入的冻结结果；
   * 上游约束的执行级收敛表达；
   * 交付、验收、证据、执行边界的统一入口；
4. 若 `IMPL` 与上游 `ADR / SRC / EPIC / FEAT / ARCH / TECH / API / UI / TESTSET` 冲突，以上游已冻结对象为准；
5. 发生冲突时，应回到上游修订或重新派生 `IMPL`，不得在执行期让 `IMPL` 私自改口径。

## 3.2 `IMPL` 的正式身份

本 ADR 将 `IMPL` 的身份明确为：

## **执行视图 / 派生视图 / 收敛视图，而不是源头视图。**

更具体地说：

* 对需求真相，以上游 `SRC / EPIC / FEAT` 为准；
* 对设计真相，以上游 `ARCH / TECH / API / UI` 为准；
* 对验证真相，以上游 `TESTSET` 为准；
* 对“这一次具体怎么组织执行输入、交付物、验收映射与证据提交”，以 `IMPL` 为准。

因此：

## **`IMPL` 是本次执行输入的 canonical package / execution-time single entrypoint，而不是业务事实、设计事实或测试事实的 SSOT。**

这里故意不再把 `IMPL` 直接表述为“执行输入的 SSOT”，因为这句话虽然方向上成立，但在执行侧极易被误读为：

* 既然是 SSOT，那就直接改 `IMPL`
* 上游还没冻好，也可以先在 `IMPL` 里补
* tester 只需要按 `IMPL` 验，不必再对照 `TESTSET`

本 ADR 明确拒绝这种解释。

`IMPL` 的正确定位是：

* 它是一次执行的单一入口；
* 它是上游真相在执行时刻的收敛包；
* 它让下游少回链，而不是让下游忘记上游 authority 仍然存在。

## 3.3 与 ADR-008 的关系

ADR-008 仍然有效，但对其中 `IMPL` 的语义作如下精化解释：

* `IMPL` 仍是 `FEAT` 的正式派生对象；
* `IMPL` 仍是开发直接消费的对象；
* 但 ADR-008 中“最小实现单元”的含义，正式收敛为：

> **面向一次具体实施交付的最小执行契约单元。**

它不再被理解为：

* 可以独立定义新需求的对象；
* 可以覆盖上游技术设计的对象；
* 可以替代 `TESTSET` 的测试真相对象。

## 3.4 与 ADR-014 的关系

ADR-014 仍然有效，并被本 ADR 继续向前推进：

* ADR-014 已冻结 `IMPL` 不是第二层技术设计；
* 本 ADR 进一步冻结 `IMPL` 必须是**自包含执行包**；
* ADR-014 冻结“不得改写上游设计边界”；
* 本 ADR 进一步冻结“执行期不应再要求到处回链检索”。

因此两份 ADR 的组合语义为：

## **`IMPL` 既不是第二层技术设计，也不是新的事实源；它是基于已冻结上游对象收敛得到的自包含执行契约。**

---

# 4. 权威与冲突规则

## 4.1 Upstream authority

`IMPL` 的上游 authority 固定来自以下对象中与当前任务相关的有效子集：

* `ADR`
* `SRC`
* `EPIC`
* `FEAT`
* `ARCH`（如存在）
* `TECH`
* `API`（如存在）
* `UI`（如存在）
* `TESTSET`

这些对象负责定义：

* 为什么做；
* 做什么；
* 设计边界是什么；
* 契约边界是什么；
* UI 约束是什么；
* 应该如何验收。

## 4.2 IMPL authority

`IMPL` 自身只负责定义：

* 本次任务的执行目标；
* 本次任务包含与不包含的修改范围；
* 上游约束的执行级整理与优先级重排；
* 模块触点、交付物、证据要求；
* 对 `TESTSET` 的验收映射；
* coder / tester / downstream runtime 的统一执行入口。

## 4.3 冲突处理

当 `IMPL` 与上游对象冲突时，必须按以下规则处理：

1. `ADR / SRC / EPIC / FEAT / ARCH / TECH / API / UI / TESTSET` 优先于 `IMPL`
2. `IMPL` 不得通过 prose、task list、workstream notes、brief summary 等任何形式覆盖上游边界
3. 若执行发现上游不完整或互相冲突，应产生 revision request 或回到上游重冻
4. 不允许以“为了交付方便”为由，由 `IMPL` 在本地补出新的需求、技术决策或测试口径

---

# 5. 输入边界

`dev.tech-to-impl` 派生 `IMPL` 时，必须输入并冻结：

* 一个已 accepted / frozen 的 `TECH`
* 一个显式 `feat_ref`
* 一个显式 `tech_ref`
* 与当前任务相关的上游有效引用集合

这里的“相关上游有效引用集合”至少包括：

* 决策来源：相关 `ADR`
* 需求来源：`SRC / EPIC / FEAT`
* 设计来源：`ARCH / TECH / API`
* 体验来源：`UI`（如存在）
* 验收来源：`TESTSET`

正式约束如下：

1. `IMPL` 必须显式列出 `derived_from` / `selected_upstream_refs`
2. 每个被收敛进 `IMPL` 的上游对象必须可追溯到具体 ref 与版本状态
3. 只允许收敛 accepted / frozen / freeze-ready 的上游对象
4. 运行期辅助上下文可以引用 repo、现有代码、环境前提与迁移约束
5. 但 repo / env / code layout 只能作为 execution context，不能替代业务或设计真相源

## 5.1 受控例外机制

本 ADR 承认真实执行中可能存在上游未完全冻结的情况，例如：

* `UI` 尚未完全冻结
* `TESTSET` 只冻结了部分覆盖
* `API` 只有部分契约已定
* `TECH` 已 accepted，但 repo 现实存在历史债或兼容包袱

因此，系统允许 `IMPL` 在受控条件下带入 **provisional inputs**，但必须同时满足以下约束：

1. 必须显式标记 `provisional_ref` / `provisional_source`
2. 必须写清未冻结部分影响哪些模块、哪些验收项、哪些风险边界
3. 必须明确声明 provisional 内容不得被下游当作最终 domain truth / design truth / test truth
4. 必须生成对应的 follow-up freeze task、revision request 或上游补冻动作
5. 不得把 provisional 内容静默写成 `Normative / MUST`

换言之：

## **可以带着受控未冻输入执行，但不能把“未冻”伪装成“已定”。**

---

# 6. 输出边界与文档结构

## 6.1 Canonical output

`feature_impl_candidate_package` 的正式主对象仍然是 `IMPL`，但其人类可读主文档必须被视为：

## **自包含 Implementation Contract / Execution Bundle**

现有命名如：

* `impl-bundle.md`
* `impl-task.md`
* `IMPL-SRC-...-implementation-task-package.md`

都可以继续保留。

但自本 ADR 起，这些文档的语义必须统一收敛到“执行契约与任务包”，而不是“自由发挥的实现计划”。

## 6.2 `IMPL` 主文档必须包含的最小骨架

`IMPL` 主文档至少必须包含以下 11 类内容：

### 1. 任务标识

至少包括：

* `impl_ref`
* `title`
* `status`
* `version/schema_version`
* `workflow_key`
* `derived_from`

### 2. 本次目标

明确：

* 这次要完成什么
* 何谓完成
* 哪些结果会被视为任务完成

### 3. 范围与非目标

必须同时写清：

* in-scope
* out-of-scope
* 本次明确不做什么

### 4. 上游收敛结果

必须列出并冻结：

* `adr_refs`
* `src_ref`
* `epic_ref`
* `feat_ref`
* `arch_ref`（如存在）
* `tech_ref`
* `api_ref`（如存在）
* `ui_ref`（如存在）
* `testset_ref`

同时需要给出每类对象对执行的具体影响摘要，而不是只留下裸引用。

### 5. 规范性约束

必须显式标记为：

## **Normative / MUST**

这里至少要收敛：

* 必须遵守的接口或 schema 事实
* 必须满足的数据结构或状态机约束
* 必须满足的错误处理与兼容性要求
* 必须满足的 UI 规则
* 必须通过的测试口径与验收条件

### 6. 背景说明

必须显式标记为：

## **Informative / Context Only**

这里用于解释：

* 为什么这样设计
* 哪些历史决策影响了当前实现
* 哪些背景可帮助理解但不是执行硬约束

### 7. 实施要求

至少包括：

* 允许修改哪些模块
* 明确 touch set / module plan
* 允许的实现方式
* 禁止的实现方式
* 是否允许新增依赖、改 schema、改 UI、改 API

### 8. 交付物要求

至少包括：

* 代码产物
* 测试产物
* 文档产物
* 证据产物
* handoff 产物

### 9. 验收标准与 `TESTSET` 映射

必须把：

* 功能验收
* UI 验收
* 回归要求
* smoke / qualification / evidence 要求

统一映射到：

* `TESTSET` 中的 case / unit / acceptance traceability

这部分可以是摘要视图，但不得与 `TESTSET` 真相冲突。

### 10. 执行顺序建议

这里可以存在建议步骤，但必须显式区分：

* `Required`
* `Suggested`

不允许把建议顺序伪装成硬约束。

### 11. 风险与注意事项

至少包括：

* 易误解点
* 高风险改动点
* 不能自由发挥的区域
* 发现上游冲突时的回退与升级路径

## 6.3 自包含的边界

本 ADR 进一步明确：

## **自包含并不等于全文复制；`IMPL` 应收敛执行所需最小充分信息，而不是镜像上游全文。**

因此，`IMPL` 的收敛边界应遵循以下规则：

### 应展开进入 `IMPL` 的内容

* 本次执行必须遵守的规则事实
* 本次验收直接依赖的 acceptance / testset 映射
* 关键接口、关键数据结构、关键状态边界
* 当前任务 touch set、交付物、证据要求
* coder / tester 不展开就无法稳定执行的前提

### 默认只保留摘要 + ref 的内容

* 长篇历史论证
* 完整 ADR 背景
* 完整 TECH 设计细节
* 完整 UI 说明全文
* 完整 TESTSET 全量正文

### 明确禁止的内容

* 把 `ADR / TECH / UI / TESTSET` 大段全文镜像进 `IMPL`
* 为了“自包含”而复制整份上游文档
* 复制后又不维护同步关系，导致 `IMPL` 与上游一起漂移

因此：

## **`IMPL` 必须是 self-contained，而不是 copy-contained。**

## 6.4 可选双视图

如果后续实现希望降低单文档阅读负担，可以允许：

* `impl-brief`：给人类 reviewer / orchestrator 的摘要视图
* `impl-contract`：给 coder / tester / executor 的完整自包含视图

但无论是否拆分：

## **完整执行契约视图必须存在，且必须能够单独支撑一次稳定执行。**

---

# 7. 强制语义规则

自本 ADR 起，`IMPL` 必须满足以下硬规则：

1. **不得发明新需求**
2. **不得改写上游技术边界**
3. **不得替代 `TESTSET` 成为测试真相源**
4. **不得把 UI / API / compatibility 约束静默降级为可选建议**
5. **不得只给 ref 而不收敛执行所需关键信息**
6. **必须显式区分 Normative 与 Informative**
7. **必须显式区分 Required 与 Suggested**
8. **必须能被 coder 与 tester 作为同一份执行入口消费**
9. **必须在文档内体现当前任务的交付闭环，而不是只给一个模糊 TODO 列表**
10. **若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准**

## 7.1 Repo discrepancy handling

真实执行中最常见的偏移，不是文档冲突，而是：

* 上游冻结对象说的是一套
* repo 当前代码长的是另一套

此时必须触发 **discrepancy handling**，而不能默认采用“代码现状优先”。

正式规则如下：

1. repo 现状只能作为差异信号，不得自动升格为 truth source
2. 若代码现状与已冻结 `FEAT / TECH / API / UI / TESTSET` 冲突，必须显式记录 discrepancy
3. 必须决定是：
   * 修代码以对齐上游
   * 还是回上游发起修订 / 重冻
4. 在 discrepancy 未被显式处理前，不得把“当前代码如此”当成新的隐式 authority

---

# 8. Freshness 与重派生

`IMPL` 既然是冻结后的执行输入，就不能写完后长期悬空使用。

因此，本 ADR 正式增加 freshness / re-derive 规则：

## 8.1 以下情况必须触发 re-derive 或 revision review

* 任一 selected upstream ref 的版本或状态发生变化
* `TESTSET` 的 acceptance / coverage / strategy 发生变化
* `API` 或 `UI` 契约发生变化
* `TECH` 的 boundary、touch set、接口或失败策略发生变化
* 实际实现触点超出 `IMPL` 原先声明的 touch set
* 交付物要求或验收口径发生变化
* provisional input 被正式冻结或被否决

## 8.2 以下情况至少需要 freshness check

* 长时间未执行的 `IMPL` 重新被拿出来继续推进
* coder 与 tester 消费的 `IMPL` 版本不一致
* handoff 目标、evidence 结构或 gate 要求发生变化

这意味着：

## **`IMPL` 不是“写完就放着不管”的说明书，而是带 freshness 条件的冻结执行包。**

---

# 9. 下游消费语义

## 9.1 coder 的消费方式

coder 应以 `IMPL` 作为直接执行入口，但必须理解：

* `IMPL` 中的设计边界来自 `TECH / ARCH / API / UI`
* `IMPL` 中的业务边界来自 `FEAT / EPIC / SRC / ADR`
* `IMPL` 中的验收与测试映射来自 `TESTSET`

coder 不应在执行期把 `IMPL` 当成“可以继续写需求”的地方。

## 9.2 tester 的消费方式

tester 可以以 `IMPL` 作为测试执行入口与上下文闭包，但：

* `TESTSET` 仍然是测试真相源；
* `IMPL` 只负责把本次测试所需的范围、依赖、交付状态、证据要求与验收映射收敛到同一入口；
* 若 `IMPL` 与 `TESTSET` 不一致，应以 `TESTSET` 为准并触发修订。

## 9.3 gate / checker 的消费方式

gate、document test、checker 需要额外验证：

* `IMPL` 是否真的自包含；
* 是否完整收敛了相关上游对象；
* 是否越权生成了新事实；
* 是否把 informative 背景混写成 normative 约束；
* 是否与 `TESTSET`、`UI`、`TECH` 保持一致。

ADR-033 中的 Document Test 后续应把：

* self-containedness
* upstream consistency
* normative / informative separation
* acceptance / testset mapping completeness

纳入 `TECH -> IMPL` 的标准验证项。

---

# 10. 机器可判定投影

本 ADR 当前仍是语义冻结文档，但其规则已经足够接近 machine-readable contract。

因此，后续 skill / checker / gate 不应只依赖 prose 判断，而应至少为 `IMPL` 建立一层机器可判定投影或 schema，至少覆盖以下字段：

* `authority_scope`
* `selected_upstream_refs[]`
* `provisional_refs[]`
* `normative_items[]`
* `informative_items[]`
* `required_steps[]`
* `suggested_steps[]`
* `acceptance_trace[]`
* `handoff_artifacts[]`
* `conflict_policy`
* `freshness_status`
* `rederive_triggers[]`

其中：

* `Document Test` 应优先验证字段齐备性、一致性与 trace completeness
* external gate 不必重做上游业务设计，但应能据此判断 `IMPL` 是否越权、失鲜或缺少执行闭包

在 schema 尚未正式落地前，上述字段仍可先通过 markdown frontmatter、sidecar json 或 package manifest 投影实现。

---

# 11. 明确拒绝的方案

本 ADR 明确拒绝以下方案：

## 11.1 把 `IMPL` 变成新的最终事实源

拒绝原因：

* 会与 `FEAT / TECH / UI / TESTSET` 形成双真相；
* 会让执行阶段的临时收敛反客为主；
* 会让上游冻结失去意义。

## 11.2 继续要求执行 Agent 在运行期沿链检索

拒绝原因：

* 输入不稳定；
* 版本漂移；
* 难以审计；
* 难以保证 coder 与 tester 看到的是同一份任务定义。

## 11.3 把 `IMPL` 做成第二层技术设计

拒绝原因：

* ADR-014 已明确禁止；
* 会影子化 `TECH`；
* 会导致实施阶段静默改设计。

## 11.4 现在强制改名为 `IMPL_CONTRACT`

本 ADR 不强制立即改对象名。

原因是：

* 仓库现有对象类型、目录、skill 与物料都已使用 `IMPL`
* 当前真正需要冻结的是语义，而不是先做命名迁移

因此：

* canonical object type 继续保留 `IMPL`
* 但推荐在人类可读层把它解释为 `Implementation Contract / Execution Bundle`

---

# 12. 结果与影响

本 ADR 生效后，链路语义正式收敛为：

> **ADR 定方向，SRC / EPIC / FEAT 定目标与边界，ARCH / TECH / API / UI / TESTSET 定设计与验收约束，IMPL 负责把相关上游真相收敛成一次可直接执行的完整任务包。**

带来的直接影响是：

* coder / tester / checker 会消费同一份冻结执行输入；
* `IMPL` 的包体会更重，但执行期更稳；
* 上游对象的 authority 更清楚，不再被 `IMPL` 反客为主；
* `dev.tech-to-impl` 的输出将更像“执行契约包”，而不是“实现随笔”；
* `Document Test` 与 external gate 更容易检查 `IMPL` 是否真正可执行、可验收、可追溯。

本 ADR 的最终结论是：

## **赞成把最终 `IMPL` 做成自包含完整文档，但其正式身份必须是从上游 SSOT 派生出来的执行收敛层，而不是新的 SSOT 源头层。**
