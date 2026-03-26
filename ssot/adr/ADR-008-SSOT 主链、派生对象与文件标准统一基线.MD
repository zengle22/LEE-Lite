# ADR-008：SSOT 主链、派生对象与文件标准统一基线

* 状态：Accepted
* 日期：2026-03-24
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x SSOT 对象模型、命名规则与文件标准
* 相关 ADR：ADR-001、ADR-002、ADR-003、ADR-004、ADR-005、ADR-006、ADR-007

---

# 1. 背景

随着 `raw-to-src`、`src-to-epic`、`epic-to-feat`、外部 gate、QA test execution 等链路逐步收敛，LL 已经具备较完整的对象化治理基础。

但当前仓库与讨论中，SSOT 对象模型仍存在几类持续漂移：

* 有时把 `SRC` 当作需求容器，有时把它当版本包；
* 有时把 `FEAT` 当最小功能单元，有时又继续往下串成 `TASK` 主链；
* 有时把 `TECH` 当设计真相，有时又把 `DEVPLAN` 当新的正式对象；
* 有时把 `TESTSET` 当正式测试对象，有时又额外生成 `TESTPLAN` 作为并列真相；
* 有时把 `RELEASE` 当规划包，有时又把它当发布后的事实记录；
* `TASK` 一词又天然容易滑向 Jira 待办、人力分工项、临时执行项。

这会直接导致：

* 对象边界不稳定；
* 上下游消费口径不一致；
* Agent 容易重复产文档；
* 同一事实被多份对象表达；
* 文件命名、目录分层、引用关系不断漂移。

因此，需要一份独立 ADR，正式冻结：

## **LL 的 SSOT 主链对象、FEAT 派生对象、发布对象，以及后续版本统一遵循的文件标准。**

---

# 2. 问题陈述

LL 需要解决的，不是“再补一份对象命名建议”，而是以下几个硬问题：

* 哪些对象构成正式主链；
* 哪些对象属于 FEAT 的派生对象，而不是新的主链节点；
* 哪些对象是正式 SSOT，哪些只是编排视图或输入池；
* 后续文件命名、字段最小集、目录归属应如何统一；
* 历史 `TASK / DEVPLAN / TESTPLAN / RELEASE` 应如何解释与兼容。

如果这层不先冻结，后续版本会持续出现以下问题：

## 2.1 主链过长

如果把 `TASK` 继续放在 `SRC -> EPIC -> FEAT -> TASK` 的主链里，那么：

* 功能真相与工程执行项会混层；
* 需求治理链会滑向项目管理链；
* 下游会把人员拆分、脚本拆分、一次性待办都误写成正式 SSOT。

## 2.2 派生对象伪主链化

如果写成：

```text
FEAT -> TECH -> IMPL -> TESTSET
```

就会误导下游认为：

* `IMPL` 依附于 `TECH` 而不是 `FEAT`；
* `TESTSET` 依附于 `IMPL` 而不是 `FEAT`；
* 设计、实现、测试三个对象被串成先后真相关系，而不是围绕同一 FEAT 的派生真相。

## 2.3 编排视图 SSOT 化

如果继续保留 `DEVPLAN`、`TESTPLAN` 作为正式 SSOT，对象会重复表达：

* `DEVPLAN` 往往只是 `SRC + FEAT + TECH + IMPL` 的编排视图；
* `TESTPLAN` 往往只是 `SRC + FEAT + TECH + TESTSET` 的编排视图。

这类对象一旦被当成新的真相层，就会产生重复维护与文档漂移。

## 2.4 发布对象语义不清

如果用 `RELEASE` 同时表达“规划范围”和“发布事实”，就很难明确：

* 哪个对象记录真实交付；
* 哪个对象记录已知风险与证据；
* 哪个对象可以被审计为“已经发布的事实记录”。

因此，需要把发布后事实记录单独收敛为明确对象。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用以下 SSOT 对象模型作为统一基线：

### 主链对象

| 对象 | 定位 | 作用 | 是否 SSOT |
| --- | --- | --- | --- |
| `RAW` | 原始输入 | 承接未经治理的需求、想法、问题、反馈 | 否 |
| `SRC` | 已治理需求单元 | 可独立治理、独立推进、独立验收、独立发布 | 是 |
| `EPIC` | 能力块 | 将一个 `SRC` 拆成若干较大能力域 | 是 |
| `FEAT` | 功能单元 | 可实现、可验证、可测试的最小功能真相单元 | 是 |

### FEAT 派生对象

| 对象 | 定位 | 作用 | 是否 SSOT |
| --- | --- | --- | --- |
| `ARCH` | 架构对象 | 定义系统边界、职责分配、架构决策 | 可选 |
| `TECH` | 技术设计对象 | 定义实现方案、技术边界、内部集成约束 | 是 |
| `API` | 契约对象 | 定义接口协议、数据契约、事件契约、兼容性边界 | 条件必选 |
| `IMPL` | 实现对象 | FEAT 的最小实现单元，供开发直接执行 | 是 |
| `TESTSET` | 测试对象 | FEAT 的测试覆盖单元，供 QA 直接执行 | 是 |
| `UI` | 可选设计对象 | 交互稿、页面流、组件约束等 | 可选 |

### 发布对象

| 对象 | 定位 | 作用 | 是否 SSOT |
| --- | --- | --- | --- |
| `RELEASE_NOTE` | 发布记录 | 记录一次实际交付的内容、影响、风险、证据 | 是 |

---

## 3.2 正式流程

正式主链为：

```text
RAW -> SRC -> EPIC -> FEAT
```

FEAT 的派生对象为：

```text
FEAT
 ├─> ARCH?
 ├─> TECH
 ├─> API?
 ├─> IMPL
 ├─> TESTSET
 └─> UI?
```

发布完成后形成：

```text
实际发布完成后 -> RELEASE_NOTE
```

因此，完整推荐理解为：

```text
RAW -> SRC -> EPIC -> FEAT
                    ├─> ARCH?
                    ├─> TECH
                    ├─> API?
                    ├─> IMPL
                    ├─> TESTSET
                    └─> UI?

实际发布完成后 -> RELEASE_NOTE
```

---

## 3.3 对象关系

### 主链关系

* `RAW -> SRC`
* `SRC -> EPIC`
* `EPIC -> FEAT`

### FEAT 派生关系

* `FEAT -> ARCH`
* `FEAT -> TECH`
* `FEAT -> API`
* `FEAT -> IMPL`
* `FEAT -> TESTSET`
* `FEAT -> UI`（可选）

### 发布关系

* `RELEASE_NOTE -> SRC / FEAT / IMPL / BUG / EVIDENCE` 的引用集合

---

## 3.4 正式定义

### `RAW`

`RAW` 不是正式真相对象，只是输入池。

典型来源包括：

* 用户原话
* 群聊记录
* 临时想法
* bug 现象
* 竞品观察
* 会议纪要

### `SRC`

`SRC` 正式定义为：

> **可独立治理、可独立推进、可独立验收、可独立发布的需求单元。**

因此，后续发布可以围绕 `SRC` 组织，而不要求总是围绕更大的版本包组织。

### `EPIC`

`EPIC` 用于组织较大的能力块，是主链中的能力分组层。

正式约束：

* `EPIC` 用于把一个 `SRC` 切成若干能力域；
* `EPIC` 不是为了无限细拆；
* 当 `SRC` 很小且边界清楚时，允许直接 `SRC -> FEAT`，不强制必须经过 `EPIC`。

### `FEAT`

`FEAT` 正式定义为：

> **最小功能真相单元。**

它必须满足：

* 能说清楚做什么；
* 能被实现；
* 能被测试；
* 能被验收。

### `ARCH`

`ARCH` 是架构真相对象，负责定义：

* 该 FEAT 在系统中放哪；
* 模块边界如何划分；
* 职责归属如何分配；
* 数据流与调用链如何组织；
* 哪些能力复用、哪些能力新增；
* 关键架构决策与系统级约束。

它关注的是：

> **系统层怎么组织。**

### `TECH`

`TECH` 是技术设计真相对象，负责定义：

* 采用什么技术方案；
* 关键实现约束是什么；
* 内部数据结构、存储、任务机制、缓存策略；
* 集成点、失败处理、幂等等工程实现策略；
* 与 `IMPL`、`TESTSET` 直接相关的技术约束。

它关注的是：

> **工程上怎么落地。**

正式收敛规则：

* `ARCH` 允许作为更高层、跨多个 FEAT 的架构设计对象存在；
* 当 FEAT 本身复杂度不足以支撑独立架构对象时，可以只保留 `TECH`；
* `ARCH` 不替代 `TECH` 的实现约束表达；
* `TECH` 不替代 `ARCH` 的系统边界与职责分配表达。

### `API`

`API` 是契约真相对象，负责定义：

* 暴露哪些接口、事件、回调或边界契约；
* 入参、出参、错误码、状态码；
* 字段语义；
* 兼容性约束与版本策略；
* 调用方假设；
* 示例请求响应或示例消息。

它关注的是：

> **模块之间怎么对接。**

本 ADR 正式规定：

* `API` 不只是代码附属物，而是正式 SSOT 对象；
* `API` 是契约源，代码是实现落点；
* 测试、联调、mock、兼容性校验、发布审计都可以直接引用 `API` 对象，而不需要从代码反推契约。

## 3.5 正式命名规则

为避免对象编号只表达“类型”而不表达“属于哪条 `SRC` 链”，LL 对 `ADR` 与 `SRC` 之外的 active SSOT 正式采用 lineage-first 命名。

### 总规则

* `ADR` 继续使用 `ADR-xxx`
* `SRC` 继续使用 `SRC-xxx`
* 其余 active SSOT 对象必须显式带上 `SRC` 编号

标准文件名前缀写法：

```text
EPIC-SRC-001-001__...
FEAT-SRC-001-001__...
ARCH-SRC-001-001__...
TECH-SRC-001-001__...
API-SRC-001-001__...
IMPL-SRC-001-001__...
TESTSET-SRC-001-001__...
UI-SRC-001-001__...
```

### 语义解释

* 第一段是对象类型前缀
* `SRC-001` 表达该对象属于哪条主链需求
* 最后一段三位序号表达该对象在该 `SRC` 链内的稳定槽位

### 派生对象对齐规则

围绕同一 `FEAT` 的派生对象，应与该 `FEAT` 共享同一个 `SRC` lineage 槽位，而不是再额外引入 `FEAT` 前缀串联。

例如：

```text
FEAT-SRC-001-004
TECH-SRC-001-004
ARCH-SRC-001-004
API-SRC-001-004
IMPL-SRC-001-004
TESTSET-SRC-001-004
UI-SRC-001-004
```

禁止继续扩张为以下旧风格作为 active baseline：

```text
EPIC-001
TECH-FEAT-SRC-001-004
IMPL-FEAT-SRC-001-004
TESTSET-FEAT-SRC-001-004
```

这些旧风格仅可作为历史兼容对象保留，不得作为后续 skill、formalization、SSOT 示例或新物化产物的默认命名。

### `IMPL`

`IMPL` 正式定义为：

> **面向工程实现的最小执行单元。**

它回答的是：

* 这个功能具体怎么落地实现；
* 开发需要消费哪些输入；
* 完成后要交出哪些输出与证据。

LL 正式采用 `IMPL`，不再把 `TASK` 作为未来标准对象名。

### `TESTSET`

`TESTSET` 正式定义为：

> **面向 FEAT 的最小测试覆盖单元。**

它回答的是：

* 该 FEAT 的覆盖范围是什么；
* 主要风险点是什么；
* QA 需要执行哪些测试项；
* 达到什么标准才算通过。

### `UI`

`UI` 是可选对象，仅在存在用户界面、交互流、视觉组件约束时使用。

不是所有 FEAT 都必须有 `UI`。

### `RELEASE_NOTE`

`RELEASE_NOTE` 正式定义为：

> **发布后的事实记录对象。**

它不是规划视图，不是待发布范围猜测，而是一次实际交付的记录，负责沉淀：

* 交付了什么；
* 用户可见变化是什么；
* 相关技术变化是什么；
* 已知风险是什么；
* 证据引用是什么；
* 何时发布。

---

# 4. 明确拒绝的对象关系

## 4.1 不再采用 `TASK` 作为未来标准对象

`TASK` 太容易退化为：

* 人工分工项；
* 临时待办；
* Jira ticket；
* 无稳定边界的实现碎片。

因此本 ADR 正式规定：

* 新标准对象统一使用 `IMPL`；
* `TASK` 仅作为历史兼容名理解；
* 后续版本不再把 `TASK` 作为规范中的正式对象类型。

## 4.2 不再把 `DEVPLAN / TESTPLAN` 视为正式 SSOT

本 ADR 正式规定：

* `DEVPLAN` 不是新的真相对象；
* `TESTPLAN` 不是新的真相对象；
* 它们最多只是执行编排视图或消费视图。

开发侧直接消费：

* `SRC`
* `FEAT`
* `TECH`
* `IMPL`

QA 侧直接消费：

* `SRC`
* `FEAT`
* `TECH`
* `TESTSET`

## 4.3 不把 FEAT 派生对象串成伪主链

正式禁止写成：

```text
FEAT -> TECH -> IMPL -> TESTSET
```

更准确的关系永远是：

```text
FEAT
 ├─> TECH
 ├─> API?
 ├─> IMPL
 └─> TESTSET
```

其中：

* `IMPL` 可以引用 `TECH`；
* `IMPL` 可以引用 `API`；
* `TESTSET` 可以引用 `TECH`；
* `TESTSET` 可以引用 `API`；
* 但 `TECH`、`API`、`IMPL` 与 `TESTSET` 仍然是 `FEAT` 的派生对象，而不是新的顺序主链。

## 4.4 不把 `ARCH / TECH / API` 混成一个对象

本 ADR 进一步规定三者边界必须写清：

* `ARCH`：模块边界、职责分配、系统级决策
* `TECH`：实现方案、内部约束、工程落地策略
* `API`：外部或跨模块契约

正式禁止以下漂移：

* 在 `ARCH` 里重写大段实现细节；
* 在 `TECH` 里重复一份完整接口协议；
* 在 `API` 里重新承载架构分层与实现方案全文。

---

# 5. 文件标准

## 5.1 统一原则

后续版本的 SSOT 文件标准必须以本 ADR 为准，并遵守以下统一原则：

1. 以 `ssot_type` 作为对象类型真相，不以目录名猜对象语义。
2. 以显式引用字段表达对象关系，不以路径邻接猜依赖。
3. 一份文件只承载一个正式对象，不把多个对象混写成大包文档。
4. 编排视图、执行计划、分析草稿不得升级成新的 SSOT 类型。
5. 发布后事实使用 `RELEASE_NOTE`，不再用规划对象替代。

## 5.2 推荐目录

本 ADR 推荐后续版本使用如下目录拓扑：

* `ssot/src/`
* `ssot/epic/`
* `ssot/feat/`
* `ssot/tech/`
* `ssot/api/`
* `ssot/impl/`
* `ssot/testset/`
* `ssot/ui/`
* `ssot/release_note/`
* `ssot/adr/`

注意：

* 这是未来标准目录；
* 本 ADR 不要求立即对历史目录做批量迁移；
* 历史兼容目录可以暂时保留，但新标准应以此为目标。

## 5.3 推荐文件命名

推荐文件命名如下：

* `SRC-xxx__slug.md`
* `EPIC-SRC-xxx-xxx__slug.md`
* `FEAT-SRC-xxx-xxx__slug.md`
* `ARCH-SRC-xxx-xxx__slug.md`
* `TECH-SRC-xxx-xxx__slug.md`
* `API-SRC-xxx-xxx__slug.yaml`
* `IMPL-SRC-xxx-xxx__slug.md`
* `TESTSET-SRC-xxx-xxx__slug.yaml`
* `UI-SRC-xxx-xxx__slug.md`
* `RELEASE_NOTE-xxx__slug.md`

说明：

* `SRC / EPIC / FEAT / TECH / IMPL / UI / RELEASE_NOTE` 建议使用 Markdown；
* `API / TESTSET` 可继续使用 YAML；
* 关键在于对象边界与字段口径统一，而不是格式本身必须绝对一致。

## 5.4 兼容映射

历史对象的兼容解释如下：

* `TASK-*`：按历史 `IMPL` 解释
* `DEVPLAN-*`：按编排视图解释，不是 SSOT
* `TESTPLAN-*`：按编排视图解释，不是 SSOT
* `REL-*` 或 `RELEASE`：若表达规划范围，可视为历史 release planning object；若表达已发布事实，后续应迁移到 `RELEASE_NOTE`

---

# 6. 各对象最小字段

以下字段为后续版本建议统一遵循的最小字段基线。

## 6.1 `SRC`

```yaml
id:
title:
goal:
problem:
scope:
non_goals:
acceptance_summary:
raw_refs:
status:
```

## 6.2 `EPIC`

```yaml
id:
src_ref:
title:
goal:
scope:
acceptance_summary:
depends_on:
status:
```

## 6.3 `FEAT`

```yaml
id:
epic_ref:
src_ref:
title:
goal:
user_value:
scope:
non_goals:
acceptance_criteria:
constraints:
depends_on:
status:
```

## 6.4 `TECH`

```yaml
id:
feat_ref:
title:
design_summary:
interfaces:
data_contracts:
integration_points:
constraints:
risks:
status:
```

## 6.5 `API`

```yaml
id:
feat_ref:
tech_ref:
title:
protocol_type:
consumer:
provider:
version:
path_or_topic:
method:
purpose:
request_schema:
response_schema:
error_codes:
compatibility:
security_constraints:
rate_limit:
examples:
change_notes:
status:
```

轻量版本可先简化为：

```yaml
id:
feat_ref:
title:
type:
endpoint:
request:
response:
errors:
compatibility:
status:
```

## 6.6 `IMPL`

```yaml
id:
feat_ref:
tech_ref:
title:
goal:
scope:
inputs:
outputs:
depends_on:
done_criteria:
evidence_required:
status:
```

## 6.7 `TESTSET`

```yaml
id:
feat_ref:
tech_ref:
title:
coverage_scope:
risk_focus:
preconditions:
test_items:
pass_criteria:
evidence_required:
status:
```

## 6.8 `RELEASE_NOTE`

```yaml
id:
src_refs:
feat_refs:
impl_refs:
api_refs:
bug_refs:
summary:
user_visible_changes:
technical_changes:
known_risks:
evidence_refs:
released_at:
```

---

# 7. 必选与可选对象规则

不是所有 FEAT 都必须拥有同样多的派生对象，但最小规则如下：

## 7.1 必选

对于进入正式开发与上线链路的 FEAT，原则上应具备：

* `TECH`
* `IMPL`
* `TESTSET`

## 7.2 可选

以下对象按需要存在：

* `ARCH`
* `API`
* `UI`

原因如下：

* 不是所有 FEAT 都需要独立架构层设计；
* 不是所有 FEAT 都存在跨边界契约；
* 不是所有功能都有 UI；
* 但只要进入开发，就应该有实现边界；
* 只要进入上线，就应该有测试覆盖。

## 7.3 `API` 的条件必选规则

`API` 不是所有 FEAT 必选，但只要存在“跨边界契约”，`API` 就应该进入 SSOT。

### 必须有 `API` 的情况

* 前后端接口
* 服务间 RPC / HTTP / gRPC
* 消息事件
* webhook
* 对第三方暴露的回调
* 明确的模块边界契约
* 需要 mock 或 contract test 的对接点

### 可以没有独立 `API` 对象的情况

* 纯前端本地交互逻辑
* 纯算法内部实现
* 单模块内部私有函数调用
* 非边界型小改动

---

# 8. 执行流视图

## 8.1 产品治理

```text
RAW -> SRC -> EPIC -> FEAT
```

## 8.2 研发执行

```text
FEAT -> TECH -> IMPL -> 开发实施 -> 证据
```

这里是执行视图，不是主链重定义。

## 8.3 测试执行

```text
FEAT -> TESTSET -> 测试执行 -> 证据
```

这里同样是执行视图，不是新的主链。

## 8.4 发布记录

```text
交付完成 -> RELEASE_NOTE
```

---

# 9. 迁移与兼容策略

本 ADR 通过后，后续版本应按以下方式推进：

## 9.1 立即生效

从本 ADR 起，新建或新版本化的 SSOT 对象应优先遵循：

* `RAW -> SRC -> EPIC -> FEAT`
* `FEAT -> ARCH / TECH / API / IMPL / TESTSET / UI`
* `RELEASE_NOTE` 作为发布事实记录

## 9.2 历史对象不强制立即批量改名

本 ADR 不要求立刻对历史仓库执行全量重命名。

也就是说：

* 历史 `TASK-*` 文件可以继续存在；
* 历史 `DEVPLAN-*`、`TESTPLAN-*` 文件可以继续存在；
* 历史 `REL-*` 文件可以继续存在。

但解释口径必须改变：

* `TASK` 视为历史 `IMPL`；
* `DEVPLAN / TESTPLAN` 视为编排视图；
* `REL / RELEASE` 视为历史 release planning 或历史发布对象；
* 新标准不再继续扩张这些对象族。

## 9.3 后续模板与生成器

后续所有 SSOT 模板、生成器、workflow 输出模板，在升级版本时应以本 ADR 为基线：

* 不再新增 `TASK` 作为正式对象名；
* 不再把 `DEVPLAN / TESTPLAN` 生成为主 SSOT；
* 发布后记录优先落 `RELEASE_NOTE`；
* `TECH / API / IMPL / TESTSET` 应直接围绕 `FEAT` 建模。

---

# 10. 结果与影响

采用本 ADR 后，LL 将获得：

* 明确的主链长度；
* 稳定的 FEAT 派生对象边界；
* `API` 作为正式契约对象进入 SSOT；
* `IMPL` 替代 `TASK` 的工程语义统一；
* `DEVPLAN / TESTPLAN` 去 SSOT 化；
* `RELEASE_NOTE` 作为发布事实记录的单独定位；
* 更稳定的命名、目录与字段基线。

代价是：

* 历史对象与新标准会短期并存；
* 模板、脚本、生成器后续需要逐步迁移；
* 某些现有 `RELEASE / TASK / TESTPLAN` 口径需要重新解释。

但这些代价属于必要收敛成本，而不是可以继续拖延的命名细节。

---

# 11. 最终结论

ADR-008 正式规定：

> **SRC 是最小可交付需求单元，FEAT 是最小功能真相单元，API 是最小跨边界契约单元，IMPL 是最小实现单元，TESTSET 是最小测试覆盖单元，RELEASE_NOTE 是发布后的事实记录。**

并且：

> **后续版本的 SSOT 文件标准必须以本 ADR 为准，不再把 TASK、DEVPLAN、TESTPLAN 继续扩张为新的正式 SSOT 主对象。**
