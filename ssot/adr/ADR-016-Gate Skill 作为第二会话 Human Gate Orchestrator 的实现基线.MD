# ADR-016：Gate Skill 作为第二会话 Human Gate Orchestrator 的实现基线

* 状态：Draft
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：第二会话 `Human Gate Loop`、待审批 gate queue、`gate brief`、人类决策回交链路
* 相关 ADR：ADR-001、ADR-003、ADR-006、ADR-009、ADR-015

---

# 1. 背景

ADR-001 已经正式冻结：LL v0.x 采用双会话双队列闭环架构。

其中：

* 会话 A 负责 execution loop；
* 会话 B 负责 human gate loop；
* gate 必须外置；
* human gate 不允许由 skill 内部等待，也不允许由 LLM 自判通过。

但到目前为止，第二会话仍只被定义为一个职责位，而没有被进一步冻结成一个明确可实现的 skill 形态。

这带来一个实际空缺：

> 第一会话已经可以产出待审批 gate request / waiting-human job，但第二会话究竟应该如何把这些对象组织成人类可快速判断、可批量处理、可审计回交的处理单，尚未被正式定义。

同时，ADR-015 已经冻结：

## **Machine SSOT + Human Review Projection**

其核心含义是：

* `Machine SSOT` 继续作为唯一权威源；
* gate 阶段允许使用面向人类的派生投影视图；
* Projection 只能解释、重组、压缩已有 SSOT；
* Projection 必须模板化；
* 所有审核意见最终都要回写 `Machine SSOT`。

这意味着，第二会话的人类交互表达，也不能重新走向自由发挥的 prose，而应建立在 ADR-015 的投影视图原则之上。

另一方面，ADR-009 已经冻结：

## **Gate Runtime 采用 CLI-first + file-based runtime 承载**

因此，第二会话的 gate skill 也不应被理解为一个必须依赖页面或服务端平台才能工作的组件，而应首先是一个：

* 消费文件化 gate job；
* 生成标准 human brief；
* 接收人类决定；
* 通过 gate CLI 写回结构化 decision

的最小治理技能。

当前最大的风险在于，如果把第二会话实现成一个“顺序读队列、逐个提醒人类”的简单通知器，系统会很快退化为：

* 重复提醒；
* 提示噪音过高；
* 高优先级 gate 被淹没；
* 人类回复格式漂移；
* 第一会话无法稳定消费结果。

因此，需要一份新的 ADR，把第二会话中的 gate skill 正式定义为：

## **Human Gate Orchestrator / Decision Preparation Skill**

而不是一个普通提醒器。

---

# 2. 问题陈述

当前需要回答的，不是“第二会话要不要提醒人类”，而是下面几个更结构性的问题。

## 2.1 Gate skill 的本质角色到底是什么

如果把它定义成普通 review skill，那么它会滑向：

* 读文档；
* 给意见；
* 输出 findings。

如果把它定义成 gate CLI，那么它又会滑向：

* 改状态；
* 写文件；
* 迁移队列；
* 落盘 decision。

这两种定义都不准确。

第二会话真正缺的，是一个介于“文件化 gate runtime”与“人类最终裁决”之间的中间层，用来：

* 准备决策材料；
* 压缩判断问题；
* 编排处理顺序；
* 收回结构化结果。

## 2.2 为什么“逐个播报 job”不够

如果第二会话只是：

1. 读到一个 waiting-human job；
2. 提醒一次人类；
3. 等回复；
4. 写回结果；
5. 再处理下一个；

那么很快会出现：

* 同一对象族的 gate 被拆散处理；
* 相同类型 gate 被多次重复打断；
* 高优先级 gate 不能被优先暴露；
* 同一轮审批无法形成批量上下文；
* 人类处理成本持续升高。

因此，“顺序消费”可以是 v0 的执行方式，但不能成为产品定义本身。

## 2.3 为什么人类表达不能自由生成

如果每次都临时自由写一套提醒话术，会出现：

* 不同 gate 的表达风格漂移；
* 审核人不知道每次该看什么；
* 人类回复结构不稳定；
* 第一会话无法可靠消费 decision result。

因此，第二会话必须继承 ADR-015 的原则，采用：

## **固定骨架 + 动态填充**

的人类决策表达模型。

## 2.4 为什么必须区分 skill 与 gate CLI

如果 skill 本身直接承接：

* 状态流转；
* 正式 decision 落盘；
* queue move；
* formal materialization；

那么第二会话的语义层与文件运行时层就会重新混在一起。

这会导致：

* skill 变胖；
* runtime contract 漂移；
* 审计链不稳定；
* 后续 UI / API 扩展无统一对象层可依赖。

因此必须补一份 ADR，明确：

## **gate CLI 是执行器，gate skill 是人类决策编排器。**

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一个运行在第二会话中的 Gate Skill，作为 Human Gate Orchestrator / Decision Preparation Skill**

用于消费待审批 gate job，并将其转化为可快速判断、可批量处理、可审计回交的人类处理单。

可参考名为：

* `ll-gate-human-orchestrator`

名称不是本 ADR 的核心约束；核心约束是其职责定位与边界。

本 ADR 冻结以下原则：

1. 该 skill 只属于 ADR-001 定义的第二会话 `Human Gate Loop`，不属于执行会话。
2. 该 skill 的主输入是 waiting-human queue 中的 gate job、相关 `Machine SSOT`、必要 evidence 与最新 gate context。
3. 该 skill 不是普通 review skill，而是人类决策准备与回交编排 skill。
4. 该 skill 的人类表达必须建立在 ADR-015 的 `Human Review Projection` 原则之上。
5. 该 skill 不直接落 formal gate 状态，不绕过 gate CLI。
6. 该 skill 至少承担：识别、压缩、编排、回交 四类职责。
7. v0 允许顺序消费 queue，但必须同时具备去重与优先级能力。
8. v1 应逐步补齐批量合并、摘要增强与标准化 decision 模板。

一句话定义：

> **Gate skill 不是提醒器，而是第二会话中的人类 gate 编排器。**

---

## 3.2 正式角色定义

该 skill 的正式角色是：

## **Human Decision Preparation Skill**

它负责：

* 从待审批队列中读取 gate job；
* 判断当前 gate 属于哪一类；
* 生成人类最小可判断处理单；
* 指导人类用稳定格式给出结果；
* 把人类决定整理成第一会话可消费的结构化对象。

它不负责：

* 直接编写业务 artifact；
* 替代人类做最终裁决；
* 在 skill 内直接 materialize 正式 gate 结果；
* 越过 decision 文件直接推进 execution queue；
* 把自己做成另一个业务审稿器。

---

## 3.3 四项核心职责

本 ADR 将 gate skill 的最小职责冻结为四项。

### 1. 识别

判断：

* 这是什么 gate；
* 来自哪个 workflow / skill；
* 关联哪个对象；
* 当前处于哪个阶段；
* 是否需要快速确认、重点阅读、方案选择或升级处理。

### 2. 压缩

把复杂的 `SSOT + gate job + evidence` 压缩成可让人快速判断的 `gate brief`。

### 3. 编排

决定：

* 现在应该提醒谁处理；
* 按什么优先级处理；
* 是否应与同类 gate 合并；
* 是否应该延后到批处理窗口。

同时，编排阶段不能只停留在行为描述，还必须沉淀为可追踪对象。

最小应形成：

* `gate-brief`
* `gate-brief-record`
* `gate-pending-human-decision`

### 4. 回交

把人类自然语言决定整理为结构化 decision，并通过正式 runtime 写回第一会话可消费的结果对象。

---

# 4. 三层实现结构

本 ADR 建议并冻结 gate skill 的三层结构。

## 4.1 第一层：Queue Consumer

这一层尽量机械，不承担复杂语义推理。

职责：

* 轮询或读取 pending gate queue；
* 识别新进入 `waiting-human/` 的 job；
* 去重；
* 锁定正在处理的项；
* 跳过已完成、已失效、已撤销对象；
* 基于优先级决定处理顺序。

最小硬约束：

* 同一 job 不应被重复提醒；
* 同一个 gate item 在任一时刻只能被一个 active claim 所持有；
* 必须保留可追溯的 claim / release 记录；
* v0 默认单消费者顺序处理，不要求并发调度。

## 4.2 第二层：Gate Triage & Brief Builder

这一层是核心语义层。

职责：

* 分类 gate 类型；
* 决定人类需要的阅读强度；
* 生成标准 `gate brief`；
* 给出最小阅读材料与建议关注点；
* 提供稳定的人类回复模板。

这一层的目标不是替人决策，而是：

## **降低人类做 gate 决策的摩擦成本。**

### 4.2.1 最小编排对象

本 ADR 明确，编排阶段至少应产出一个可追踪的 `gate-brief-record` 对象，而不是只在会话中保留瞬时消息。

最小对象族如下：

#### `gate-brief`

面向人类的处理单视图，承载：

* human-facing projection；
* decision question；
* minimum reading set；
* suggested focus；
* human decision actions。

#### `gate-brief-record`

面向 runtime 与审计的编排记录，至少承载：

* `brief_ref`
* `claim`
* `priority`
* `merge_group`
* `decision_target`
* `decision_basis_refs`
* `status`

#### `gate-pending-human-decision`

表示一个已被编排、正在等待人类返回结果的正式待处理单元。

它可以引用：

* `gate-brief`
* `gate-brief-record`
* 原始 `gate job`

这样可以避免后续实现分别退化为：

* 只靠消息历史；
* 只靠文件名约定；
* 只靠 job state 猜当前编排状态。

## 4.3 第三层：Decision Capture & Handoff Writer

这一层负责把聊天式回复变成结构化治理对象。

至少要输出：

* `decision`
* `decision_reason`
* `decision_target`
* `decision_basis_refs`
* `requested_patches`
* `patch_focus`
* `approver`
* `timestamp`
* `next_action`

其中：

* `decision_target` 用于明确本次决定作用于哪个对象、哪个版本或哪个 brief 对应的待处理单元；
* `decision_basis_refs` 用于明确本次决定基于哪一轮 `Machine SSOT`、`Human Review Projection`、`gate-brief` 与 evidence。

并通过 gate CLI / file runtime 写回：

* `gate-decision`
* `gate-result`
* `patch-instruction`
* 或升级类结果对象

这一层的核心价值是：

## **把聊天变成可审计对象。**

---

# 5. Gate 类型与分流规则

为了避免所有 gate 都以同一强度打给人类，本 ADR 先冻结五类 gate。

## 5.1 Freeze Gate

用于判断一个对象是否允许进入正式冻结态。

典型问题：

* 是否允许 freeze；
* 是否必须退回修补；
* 是否还缺少关键 evidence。

## 5.2 Quality Gate

用于判断当前质量是否允许继续下游推进。

典型问题：

* 是否允许继续拆分；
* 是否必须先补质量缺口；
* 是否需要补充 reviewer 结论。

## 5.3 Exception Gate

用于判断某个例外是否允许带条件放行。

典型问题：

* 是否接受例外；
* 例外的附加条件是什么；
* 条件未满足时应如何退回。

## 5.4 Choice Gate

用于多方案并存时的人类选路。

典型问题：

* 在 A / B / C 之间选哪条；
* 选择后应冻结哪一条为正式方向；
* 其余方案是否全部废弃或保留待查。

## 5.5 Escalation Gate

用于当前问题超出本层 skill 可裁决范围，需要升级给更高层人类处理。

典型问题：

* 是否升级；
* 升级给谁；
* 升级前必须补哪些材料。

---

## 5.6 Triage 强度分层

对每个 gate，第二会话应先做强度分流，而不是统一提醒。

最小分层如下：

### 快速确认型

只需要：

* `approve`
* `reject`

或轻量 `yes/no` 决策。

### 重点阅读型

需要人类阅读主文档、差异、风险摘要后再判断。

### 多方案比较型

需要并列呈现候选路线、差异、取舍与建议。

### 升级处理型

需要明确说明为什么当前层无法裁决，以及应升级到哪个角色。

## 5.7 默认映射规则

为了避免不同 skill 作者各自发明 gate 分类方式，v0 阶段至少冻结以下规则：

1. 每个进入 `waiting-human` 的 gate job 都应显式携带 `gate_type`。
2. 若 `gate_type` 缺失，runtime 可临时回退到：
   * `quality_gate`
   * 或 `unknown_gate`
3. 若被归为 `unknown_gate`，则必须升级处理，不允许静默套用默认模板后继续。
4. `Choice Gate` 必须显式给出候选集合，不允许只写“需要选一个方向”。
5. `Escalation Gate` 必须显式说明升级原因与升级目标。

---

# 6. 人类表达模型

## 6.1 设计来源

本 ADR 明确：

## **gate skill 的人类表达设计引用 ADR-015。**

具体含义是：

* `gate brief` 不是新的真相源；
* `gate brief` 必须从最新 `Machine SSOT` 与其对应 `Human Review Projection` 派生；
* `gate brief` 只能解释、重组、压缩已有信息；
* 所有人类意见最终仍需回写 `Machine SSOT` 或结构化 gate result。

形式化地说：

## **Gate Brief = Human Review Projection + Gate Context + Decision Template**

也就是说，第二会话使用的不是自由 prose，而是 ADR-015 在 gate 场景下的特化投影。

## 6.2 正式命名

“人类表达模型”在本 ADR 中更正式地命名为：

* `Human Gate Brief Template`

也可解释为：

* `Human Decision Prompt Model`

两者指向同一个对象：一个固定骨架、动态填充的人类处理单模板。

## 6.3 固定骨架

每个 `gate brief` 至少必须包含以下七块。

### 1. 一句话摘要

说明这是什么 gate、作用于哪个对象、当前为什么进入人工处理。

### 2. 决策问题

明确告诉人类：

* 你现在只需要判断什么。

### 3. 为什么需要你处理

说明：

* 这是 freeze、quality、choice、exception 还是 escalation；
* 为什么当前不能继续自动推进。

### 4. 建议关注点

最多给出 3 到 5 个应重点查看的问题。

### 5. 最小阅读材料

只给人类必须看的最小集，例如：

* 主 SSOT；
* 最新 Projection；
* 差异摘要；
* 关键 evidence；
* 必要 findings。

### 6. 可选回复动作

最小必须支持：

* `approve`
* `reject`
* `needs_patch`
* `escalate`

如属 `Choice Gate`，则应替换为：

* `choose_a`
* `choose_b`
* `choose_c`

等互斥选项。

这里的动作语义进一步冻结为：

* 它们是 `human decision actions`；
* 它们不是 formal runtime states；
* formal gate state 仍由 gate CLI 根据结构化 decision 物化。

### 7. 回交格式

必须明确告诉人类：

* 若同意，最少要写什么；
* 若驳回，最少要写什么；
* 若要求修补，必须指出 `patch_focus`；
* 若升级，必须说明升级原因。

## 6.4 动态填充项

模板中的动态部分应来自：

* 当前对象类型；
* 当前 gate 类型；
* 变更摘要；
* 风险摘要；
* 差异点；
* 上游 lineage；
* 推荐 patch focus；
* 关键 evidence 引用。

## 6.5 硬约束

`gate brief` 必须遵守以下限制：

1. 只能解释、压缩、重组，不得新增 authoritative 语义。
2. 必须保留一个短而硬的 authoritative snapshot。
3. 不允许每次自由改写模板结构。
4. 不允许把完整 SSOT 原样倾倒给人类当处理单。
5. 不允许只给 narrative、不保留正式判断锚点。

---

# 7. 编排规则

## 7.1 优先级

第二会话最小必须支持三档优先级：

* `P0`：必须尽快处理
* `normal`：正常处理
* `batch`：可进入批处理窗口

如果没有优先级，第二会话会退化成简单通知机。

## 7.2 去重

同一 `job_id`、同一 `gate_ref`、同一对象同一版本的重复提醒必须被抑制。

## 7.3 合并

v0 阶段可以不强制实现批量合并，但 ADR 已明确该能力属于正向演进方向。

优先合并的对象类型包括：

* 同源 workflow；
* 同对象族；
* 同一批次同类型 gate。

合并后的目标表达应类似：

* “这里有 3 个同属一个 EPIC 的 FEAT freeze gate，请一次性完成判断。”

## 7.4 顺序消费的地位

本 ADR 明确：

* 顺序消费 queue 是 v0 合理实现；
* 但“顺序播报”不是 gate skill 的正式定义；
* 一旦具备批量合并能力，应优先减少人类切换成本。

---

# 8. 与 ADR-001、ADR-006、ADR-009 的边界关系

## 8.1 与 ADR-001 的关系

本 ADR 明确：

## **gate skill 的双会话设计引用 ADR-001。**

具体含义是：

* 该 skill 只属于第二会话；
* 第一会话不运行该 skill；
* 该 skill 只消费 waiting-human / gate request 相关对象；
* 它不替代 execution loop；
* 它不抢夺会话 A 的业务推进职责。

## 8.2 与 ADR-006 的关系

ADR-006 关注的是：

* final decision 与 materialization 层；
* candidate package 的 formal 晋升；
* gate consumer 与 run closure。

本 ADR 关注的是：

* 人类决策准备；
* gate brief；
* decision capture；
* 回交编排。

因此两者关系是：

* ADR-006 更偏 formal decision / materialization；
* ADR-016 更偏 human decision orchestration。

两者并不冲突，而是上下衔接。

## 8.3 与 ADR-009 的关系

ADR-009 已冻结：

* CLI-first
* file-based runtime

因此本 ADR 进一步明确：

* gate skill 不直接取代 gate CLI；
* gate CLI 负责状态流转与正式写回；
* gate skill 负责阅读、压缩、提示、采集、结构化整理。

正式边界如下：

### gate CLI 负责

* gate 文件状态流转；
* queue 操作；
* formal decision 落盘；
* job 创建与回写；
* materialization 所需的正式写操作。

### gate skill 负责

* 读取待处理 gate job；
* 分类与 triage；
* 构建 `gate brief`；
* 组织人类回复；
* 标准化 decision object；
* 调 gate CLI 写回结果。

一句话边界：

> **gate CLI 是执行器，gate skill 是人类决策编排器。**

---

# 9. v0 实现基线

如果当前目标是先把闭环跑通，v0 只要求以下最小链路：

1. 从 gate queue 中取一个 pending job；
2. 识别 gate type；
3. 生成标准 `gate brief`；
4. 提示人类处理；
5. 接收人类结果；
6. 标准化为 decision object；
7. 调 gate CLI 写回；
8. 继续处理下一个 job。

v0 阶段强制补齐的能力只有两项：

* 去重
* 优先级

本 ADR 明确：

* v0 不要求复杂调度器；
* v0 不要求完整 UI；
* v0 不要求多消费者并发；
* v0 允许顺序处理；
* 但 v0 不能退化为纯提醒器。

---

# 10. v1 正向演进方向

当 v0 跑稳后，最优先补以下三项：

## 10.1 批量合并提醒

把同类 gate 合并成人类可一次处理的 brief。

## 10.2 Gate Brief 摘要增强

自动补出：

* 变更摘要；
* 风险摘要；
* 推荐关注点；
* 差异亮点。

## 10.3 标准化 Decision 模板

把人类回复进一步收敛为有限动作集，而不是自由发挥 prose。

最小动作集为：

* `approve`
* `reject`
* `needs_patch`
* `escalate`

## 10.4 Brief / Merge Record 增强

在批量合并与标准化 decision 模板稳定后，应继续补齐：

* `brief record`
* `merge-group record`
* `decision basis record`

---

# 11. 明确拒绝的方案

以下方案被本 ADR 明确拒绝。

## 11.1 把 gate skill 定义成单纯通知器

只做“读一个 job，提醒一次人类”不构成正式 gate orchestration。

## 11.2 把 gate skill 做成第二个业务评审 skill

它不负责产出新的业务 findings 体系，也不重做上游业务语义审查。

## 11.3 让人类表达每次自由生成

这会导致 brief 漂移、回复漂移、回交流程不可治理。

## 11.4 让 skill 直接改 formal gate 状态

这样会把语义层和 runtime 执行层重新混在一起。

## 11.5 所有 gate 一律同强度提醒

这会制造人类通知风暴，并淹没真正高优先级的决策项。

---

# 12. 验收标准

本 ADR 生效后，一个合格的 gate skill 至少应满足以下标准。

## 12.1 对人类

* 审核人能在最小阅读材料下快速理解当前 gate；
* 审核人知道自己只需要判断什么；
* 审核人知道应该按什么格式回复；
* 同类 gate 不会无限制造切换成本。

## 12.2 对第一会话

* 第一会话能稳定消费结构化 decision；
* 不依赖自然语言猜测通过 / 驳回 / 修补 / 升级语义；
* decision、patch、next action 可直接进入后续 runtime。

## 12.3 对 queue / runtime

* 重复 job 不会重复打扰人类；
* 失效 gate 不会继续生成 `gate brief`；
* claim / release 状态有结构化记录；
* decision 回交后 queue 中可见状态能够收敛到单一结果。

## 12.4 对治理

* 不新增第二真相源；
* 不绕过 gate CLI 与正式文件对象；
* 每次人类决策都可追溯到对象、理由、时间与 approver；
* gate 审核意见最终仍能回写 `Machine SSOT`。

---

# 13. 结论

LL 在第二会话的 gate 实现上，正式采用：

## **Human Gate Orchestrator / Decision Preparation Skill**

其正式含义是：

> **第二会话中的 gate skill 不应只是顺序读队列并提醒人类，而应负责待审批 gate 的分流、摘要、提示、决策收集与结构化回交；它的人类表达必须引用 ADR-015 的投影视图原则，它的会话边界必须服从 ADR-001 的双会话设计，它与 gate CLI 的关系应保持为“skill 负责编排，CLI 负责执行”。**
