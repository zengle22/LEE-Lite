# ADR-002：Raw-to-SRC 采用双环修复、外挂 Gate、Job 路由的标准治理方案

* 状态：Accepted
* 日期：2026-03-20
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）skill-first 产品需求主链
* 相关 ADR：ADR-001、ADR-003

---

# 1. 背景

在 ADR-001 中，LL 已正式确定采用“双会话双队列闭环模型”作为 v0.1 执行架构，并明确要求优先跑通：

* `raw-to-src`
* `src-to-epic`
* `epic-to-feat`

其中，`raw-to-src` 是产品需求主链的第一个正式治理节点。

它的职责不是写方案、拆任务或进入实现，而是：

* 接住各种未经治理的原始输入；
* 统一将其收敛为单一、可追溯、可复用的正式需求源；
* 为后续 `EPIC / FEAT / TASK` 提供唯一上游真相；
* 在最早阶段阻断重复真相、范围漂移、多主题混杂与不合规桥接。

第一版 `ADR-002` 已经基本建立了 `raw-to-src` 作为 governed skill 的输入、输出、evidence、acceptance、defect 和 freeze 机制，但仍停留在：

## **治理增强版单 skill 内闭环**

这与 ADR-001 已冻结的目标架构存在偏差。

当前必须进一步对齐到：

## **双环双队列 + Gate 外挂 + Job 驱动 + Next Skill 可路由**

因此，本次 ADR 修订的重点不是增加更多实现细节，而是重新冻结 `raw-to-src` 的架构边界，使其成为：

* 可接入双会话双队列的 skill；
* 可审计的双环修复路径；
* 可被外挂 gate 消费并继续路由的标准结果生产者；
* 可嵌入 ADR-003 所定义的文件化 handoff runtime。

---

# 2. 问题陈述

LL 需要解决的不是“如何把一段 raw 文本改写成一份文档”，而是：

* 如何接受多类 raw 输入并统一进入正式需求主链；
* 如何保证每次运行只产出 1 个与原始输入同题的 SRC candidate；
* 如何严格区分结构修复与语义修复；
* 如何为 LLM 修复建立明确 budget，而不是无限重试；
* 如何让 skill 产出 artifact、evidence、report 和 next action，而不是在 skill 内部自判所有 gate；
* 如何让 `raw-to-src` 的结果可以被外挂 decision layer 消费，并自然进入：
  * 当前 skill 重试；
  * 人工处理队列；
  * 下一个 skill 队列；
  * freeze handler。

如果不这样调整，`raw-to-src` 会继续成为一个过重的 skill：

* 既是生成器；
* 又是校验器；
* 又是修复器；
* 又是审批器；
* 又是冻结器。

这会直接冲突于 ADR-001 已冻结的双环双队列架构。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **Governed Raw-to-SRC Skill + External Gate Decision Layer**

作为原始需求归一化的唯一标准路径。

该方案的正式原则如下：

1. `raw-to-src` skill 负责消费输入 job，产出结构化结果；
2. skill 内只负责：
   * intake
   * normalization
   * structural loop
   * semantic loop
   * evidence 落盘
   * proposed next actions
3. 最终 gate、freeze、queue routing、next skill dispatch 不在 skill 内完成；
4. 这些动作由外挂 gate / decision layer 处理；
5. 所有重试必须受 budget 约束；
6. 所有失败必须产生标准 job 或 block 输出，而不是自然语言停住；
7. 任何会生成新中间状态 artifact 的步骤，都必须先校验，再决定是否进入下一步。

---

## 3.2 正式定义

`raw-to-src` 的正式定义如下：

1. **输入是 raw，而不是 SSOT**

   * 接受 `adr`
   * 接受 `raw_requirement`
   * 接受 `business_opportunity`
   * 接受 `business_opportunity_freeze`
   * 拒绝已带 `ssot_type` 且状态为 `frozen / active / deprecated` 的对象

2. **输出是单个 SRC candidate 结果包**

   * 每次运行最多处理并产出 1 个 SRC candidate
   * skill 结果可以包含 freeze-ready candidate
   * skill 本身不承担最终 freeze 决策

3. **同题归一化是硬约束**

   * 输出必须与原始输入同题
   * 禁止把 workflow、schema、实现策略写成 SRC 业务主题
   * 禁止在本流程内生成 EPIC、FEAT、TASK 或实现方案

4. **ADR 输入必须走 thin bridge SRC**

   * `source_kind = governance_bridge_src`
   * 必须显式记录 bridge context
   * 必须将 ADR 的治理意图重写为下游可继承的需求源语义，而不是只补齐字段
   * 禁止从 ADR 直接跳到下游交付设计

5. **修复必须双环分离**

   * 结构问题进入 structural loop
   * 语义问题进入 semantic loop
   * 两类 loop 的 budget 独立计算

6. **Gate 必须外挂**

   * skill 不内置最终 approval gate
   * skill 不内置最终 freeze gate
   * skill 不负责最终 queue routing
   * skill 只负责给出可消费的结果、evidence、suggested next actions 与 handoff proposal

7. **所有失败都必须结构化输出**

   * retry proposal
   * human handoff proposal
   * blocked proposal
   * next-skill proposal

不得只输出“失败了”或停留在自然语言状态。

8. **最小修补优先**

   * 修补优先采用局部 patch，而不是整体重写
   * 每轮修补必须仅针对当前 defect list 中已识别的问题
   * 未被 defect 明确指出的章节、字段、语义边界，不得顺带改写
   * 若局部 patch 已无法安全完成，则必须升级为人工 handoff 或 blocked

---

# 4. 输入标准

## 4.1 接受的输入类型

`raw-to-src` 接受四类输入：

1. `adr`
2. `raw_requirement`
3. `business_opportunity`
4. `business_opportunity_freeze`

输入文件可为：

* `.md`
* `.txt`
* `.json`
* `.yaml`
* `.yml`

---

## 4.2 输入最小字段标准

输入至少应可提取出：

* `input_type`
* `title`
* `body`
* `source_refs`

若为半结构化对象，允许从以下位置抽取：

* `requirement_overview.description`
* `requirement_overview.target_users`
* `key_designs...`
* Markdown 章节
* ADR 编号与引用

---

## 4.3 输入禁止项

以下输入必须被阻断：

1. 已经是 SSOT 对象的输入
2. `gate-materialize` 占位对象
3. 明确包含多个独立问题域的输入
4. 标题或正文短到无法安全归一化的输入

阻断原因：

* SSOT 输入应走对应下游流程；
* 占位对象不是真实业务源；
* 多主题输入破坏“一次运行一个 SRC”；
* 信息缺失会导致不安全推断。

---

# 5. 输出标准

## 5.1 Skill Result 与正式 SRC 的区分

本 ADR 明确区分两个层次：

### 1. skill result

由 `raw-to-src` skill 直接产出，用于外挂 gate 消费。

### 2. frozen SRC

由外挂 freeze gate 或 freeze handler 最终确认并落盘到 `ssot/src` 的正式对象。

换言之：

## **skill 可以产出 freeze-ready candidate，但不自带最终 freeze 权限**

---

## 5.2 Frozen SRC 标准

当外挂 gate 决定放行并执行 freeze 时，正式输出目录固定为：

* `ssot/src`

命名规则固定为：

* `SRC-<编号>__<slug>.md`

frontmatter 至少包含：

* `id`
* `ssot_type`
* `title`
* `status`
* `version`
* `schema_version`
* `src_root_id`
* `workflow_key`
* `workflow_run_id`
* `source_kind`
* `source_refs`
* `frozen_at`

正文至少包含：

1. `问题陈述`
2. `目标用户`
3. `触发场景`
4. `业务动因`
5. `关键约束`
6. `范围边界`
7. `来源追溯`

若输入为 ADR，还必须包含：

* `Bridge Context`

并且本 ADR 进一步冻结：

## **ADR 派生的 `governance_bridge_src` 不得只是“ADR 标题套进 SRC 模板”，而必须形成下游可消费的需求源密度。**

这意味着仅有：

* 正确标题
* `source_kind = governance_bridge_src`
* 形式完整的 `Bridge Context`

仍不足以视为高质量 freeze-ready candidate。

对于 ADR 输入，正文与 `Bridge Context` 至少必须能独立表达：

1. 本次治理变更作用于哪些对象
2. 当前失控点或现状问题是什么
3. 新的统一原则或约束是什么
4. 下游对象必须继承哪些硬约束
5. 明确不希望下游继续展开什么

若仅凭该 SRC 本身，仍无法让下游稳定理解“要治理什么、为什么治理、约束何在、不要误展开什么”，则不得进入高质量 freeze-ready 状态。

建议 ADR bridge SRC 在正文中增加专属治理章节，例如：

* `治理变更摘要`
* 或 `本次治理变化`

该章节用于显式描述：

* 本次 ADR 带来的治理变化
* 生效对象与边界
* 下游必须继承的约束

---

## 5.3 Skill Result 输出包标准

`raw-to-src` skill 至少应输出以下结构化结果：

* `package-manifest.json`
* `result-summary.json`
* `src-candidate.json`
* `structural-report.json`
* `acceptance-report.json`
* `defect-list.json`
* `retry-budget-report.json`
* `execution-evidence.json`
* `supervision-evidence.json`
* `proposed-next-actions.json`
* `run-state.json`

可选输出：

* `job-proposal.json`
* `handoff-proposal.json`

---

# 6. 双环修复模型

本 ADR 正式冻结：

## **raw-to-src 必须使用结构环与语义环分离的双环修复模型**

---

## 6.1 总原则：环内逐步闭环

本 ADR 明确冻结以下总原则：

## **凡是会生成新的中间状态 artifact 的步骤，必须紧跟对应校验；校验失败时优先做局部最小修补，不允许默认进入下一生成步骤。**

这意味着 `raw-to-src` 不是：

* 先连续生成多个状态
* 最后统一检查
* 再统一修复

而必须是：

* generate
* validate
* minimal patch
* revalidate
* next step

只有当前步骤的局部闭环通过，才允许进入下一步。

这条原则不仅是流程约束，也是结果包约束。至少以下产物必须能回放阶段内局部闭环：

* `package-manifest.json`
* `stage_results`
* `structural-report.json`
* `execution-evidence.json`

换言之，外部消费者必须能直接看出：

* 问题在哪个阶段被发现；
* 问题在哪个阶段被最小 patch；
* patch 只改了哪些字段或章节；
* patch 后的 revalidation 是否通过。

---

## 6.2 第一环：结构闭环

结构闭环负责解决确定性、可脚本化的问题。

结构环不是一个粗粒度的大 loop，而是由多个阶段内局部闭环组成。

正式步骤如下：

### 结构闭环 A：输入闭环

1. `input_validation`
2. `input_fix_assessment`
3. `input_minimal_patch`（可选）
4. `input_revalidation`

### 结构闭环 B：intake 闭环

5. `raw_input_intake`
6. `intake_validation`
7. `intake_minimal_patch`
8. `intake_revalidation`

### 结构闭环 C：candidate 闭环

9. `source_normalization`
10. `structural_acceptance_check`
11. `structural_fix_loop`
12. `structural_recheck`

结构环只处理：

* schema/contract 结构问题
* frontmatter 缺失
* 必需章节缺失
* 引用字段缺失
* 命名与 ID/path 规则问题
* ADR bridge 必填字段缺失

结构环明确禁止处理：

* 同题与否的语义争议
* scope 漂移
* 越层问题
* 用户/场景/业务动因是否合理的语义问题

并且本 ADR 明确要求：

* `load / parse / infer` 不得隐式等同于 patch；
* 自动补默认值必须作为显式 `minimal_patch` 事件记录；
* intake 阶段发现的问题，不得默认拖延到 candidate 阶段统一修复。

---

## 6.3 结构环进入条件

结构环从输入闭环开始，并在每个局部闭环通过后才能进入下一局部闭环。

并且本 ADR 明确冻结以下规则：

## **结构未通过，不得进入语义评审**

原因：

* 否则语义 reviewer 会在不完整对象上重复工作；
* 会把结构成本错误转移给语义环；
* 会导致 defect loop 持续膨胀。

---

## 6.4 结构环退出条件

结构环通过的标准如下：

* 输入合法
* intake 结构合法
* candidate 结构合法
* 输出 contract 合法
* frontmatter 完整
* 必需章节完整
* 文件/ID/path 规则合法
* ADR bridge 必填字段完整

若全部满足，则结构环结束并允许进入语义环。

若预算耗尽仍未通过，则结构环结束但状态为失败，并必须产出：

* `retry-budget-report.json`
* `job-proposal.json`
* 由外挂 gate 物化 `human_handoff` 或 `blocked` 结果

---

## 6.5 第二环：语义闭环

语义闭环负责解决需要 LLM 评审或人工治理判断的问题。

语义环同样不是单一 review loop，而是由多个阶段内局部闭环组成。

正式步骤如下：

### 语义闭环 A：source semantic 闭环

13. `source_semantic_review`
14. `source_semantic_patch`
15. `source_semantic_recheck`

### 语义闭环 B：acceptance semantic 闭环

16. `semantic_acceptance_review`
17. `semantic_fix_loop`
18. `semantic_recheck`
19. `freeze_readiness_assessment`

语义环只处理：

* 是否同题
* 是否越层
* 是否无授权扩 scope
* bridge 语义是否正确
* bridge 信息密度是否足够支撑下游消费
* P0/P1 语义缺陷是否清零
* 是否达到 freeze-ready 状态

并且本 ADR 明确要求：

* `source_semantic_review` 与 `semantic_acceptance_review` 不是一个大 review 的两个别名；
* 两者都必须在 `stage_results` 与 evidence 中留下独立的输入、发现、修补与复检痕迹；
* 若没有安全的局部语义 patch 路径，则必须显式升级为 `retry`、`human_handoff` 或 `blocked`，不得伪装为“自动通过”。

对于 `input_type = adr` 或 `source_kind = governance_bridge_src`，语义环必须额外检查：

1. 是否已将 ADR 抽取为“治理对象 - 现状问题 - 新原则 - 下游继承点 - 非目标”主线
2. `问题陈述` 是否只是标题复写，或缺少“现状问题 + 需要改变什么”
3. `目标用户`、`触发场景`、`业务动因` 是否仍停留在通用模板句
4. `Bridge Context.change_scope` 是否只是标题重复，而非治理摘要
5. `acceptance_impact` 是否明确表达了下游继承要求

---

## 6.6 语义环退出条件

语义环通过的标准如下：

* 与原始输入同题
* 不越层
* bridge 语义正确
* 关键约束得到保留
* 若为 ADR bridge SRC，则已达到最低治理信息密度
* P0/P1 语义缺陷清零
* supervisor 给出允许进入 freeze readiness 的判断

若语义环预算耗尽仍未通过，则：

* skill 不得自判 freeze；
* 必须产出 `job-proposal.json` 或至少给出明确的 `proposed-next-actions.json`；
* 必须在 `retry-budget-report.json` 中记录耗尽原因。

---

## 6.6.1 ADR Bridge Synthesis 要求

本 ADR 正式要求：对于 `adr` 输入，不得只复用通用 normalization 产出一个“字段齐全但正文空泛”的 bridge SRC，而必须执行专门的 `bridge synthesis`。

该 synthesis 至少应提取并重写以下五类语义：

1. `治理对象`
   * 本次 ADR 影响哪些 skill、artifact、path、治理边界或运行规则
2. `当前失控点`
   * 当前为什么需要治理变更，现状错误或漂移表现是什么
3. `新的统一原则`
   * 本次 ADR 引入了哪些新约束、新边界或统一规则
4. `下游继承要求`
   * `src-to-epic` 及后续 skill 必须保留和继承哪些约束
5. `明确非目标`
   * 本层不展开哪些 API、实现细节、技术设计或下游分解

该 synthesis 的结果必须同时进入：

* 正文关键章节
* `Bridge Context.change_scope`
* `Bridge Context.acceptance_impact`
* `Bridge Context.non_goals`

仅做字段补齐，不视为满足本条要求。

---

## 6.6.2 ADR Bridge 最低信息密度规则

对于 `governance_bridge_src`，以下内容不得停留在高泛化模板句：

* `问题陈述`
* `业务动因`
* `关键约束`
* `Bridge Context.change_scope`
* `Bridge Context.acceptance_impact`

以下类型的句子可以作为过渡提示，但不得作为最终章节主体：

* “受该问题影响的业务角色”
* “当原始问题被触发并需要正式需求源时”
* “将原始问题收敛为下游可复用的正式需求源”

若关键章节仍主要由此类通用句构成，则必须判为语义不通过，并进入 `retry`、`human_handoff` 或 `blocked` 路径。

---

## 6.6.3 标题复写与下游可消费性检查

对于所有 SRC candidate，尤其是 `governance_bridge_src`，语义环必须至少包含以下专项检查：

### `problem_statement_quality_check`

至少判断：

* `问题陈述` 不是标题复写
* 包含现状问题
* 包含为什么需要治理变更
* 包含影响对象或影响范围

### `downstream_actionability_check`

仅凭 SRC 本身，至少应能判断：

* 需要治理的对象
* 现有问题
* 核心约束
* 下游继承要求
* 非目标

若上述两项检查不通过，则不得直接进入高质量 freeze readiness。

---

## 6.7 Minimal Patch Principle

本 ADR 正式冻结：

## **修补默认采用局部最小 patch，不允许把修补过程退化为隐式整体重写。**

具体规则如下：

1. 修补必须优先针对当前 defect list 中已识别的问题；
2. 未被 defect 明确指出的章节、字段、语义边界，不得顺带改写；
3. 修补不得扩大 scope、改变主题、重构对象层级；
4. 修补不得引入新的业务信息，除非该信息已经在 source refs 或 review findings 中明确出现；
5. 若局部 patch 无法安全完成，必须升级为：
   * `human_handoff`
   * `blocked`
   * 或由外挂 gate 决定的其他人工路径。

---

# 7. Retry Budget 与 Bounded Repair Policy

本 ADR 正式冻结：

## **所有修复必须受预算约束，不允许无界重试**

---

## 7.1 预算对象

至少定义以下三类预算：

* `structural_fix_budget`
* `semantic_fix_budget`
* `total_repair_budget`

推荐默认值：

* `structural_fix_budget = 3`
* `semantic_fix_budget = 2`
* `total_repair_budget = 4`

具体数值可在实现层细调，但三类预算对象本身是架构强约束。

其中 `total_repair_budget` 在本 ADR 中被定义为：

## **全局硬上限保险丝**

也就是说：

* 每次进入 patch / retry 前，都必须同时检查局部 budget 与 total budget；
* 一旦 `total_repair_budget` 耗尽，即使局部 budget 仍有余额，也必须停止自动修补；
* 后续只能进入 `retry proposal`、`human_handoff proposal`、`blocked proposal` 或由外挂 gate 物化的等价动作。

---

## 7.2 计数规则

以下行为均计入 retry：

1. 一次基于 defect list 的 candidate 重写
2. 一次基于 review findings 的语义修订
3. 一次完整 recheck 后再次进入 fix loop
4. 一次由 skill 内部自动触发的再评审

以下行为不单独计数，但必须被 evidence 记录：

* 纯读取
* 纯解析
* 纯格式化输出

当前实现若只记录 budget 而不让 budget 参与控制流，不视为符合本 ADR。

---

## 7.3 结构环预算策略

* 结构问题优先自动修
* 结构 budget 用尽后，不再进入语义环
* 只要 total budget 已耗尽，同样必须停止结构修复
* 必须输出：
  * `retry-budget-report.json`
  * `job-proposal.json`
  * 必要时由外挂 gate 物化 `retry` / `human_handoff` / `blocked`

结构环失败后的推荐去向：

* 若问题可补信息：`input-clarification` 或 `retry`
* 若问题需人工处理：`human_handoff`
* 若问题不可继续：`blocked`

---

## 7.4 语义环预算策略

* 语义问题只允许 bounded retry
* 每次修复必须引用上轮 `semantic_findings`
* 达到 `semantic_fix_budget` 后仍失败，不得 freeze
* 只要 total budget 已耗尽，同样必须停止语义修复
* 必须输出：
  * `retry-budget-report.json`
  * `job-proposal.json` 或至少给出明确 handoff proposal

语义环失败后的推荐去向：

* 若仍可重试：`retry`
* 若需要人类裁决：`human_handoff`
* 若输入本身不适合继续：`blocked`

---

## 7.5 预算升级策略

推荐的升级策略如下：

### 第 1 轮

* 基于局部 defect 做定点修复

### 第 2 轮

* 带完整 defect context 重修

### 第 3 轮及以后

* 不再扩写修复范围
* 直接升级到人工处理或阻断

本 ADR 明确禁止：

* budget 耗尽后继续静默重试；
* 为了过关而放宽 contract；
* 用模糊自然语言替代结构化 handoff。

---

# 8. 步骤职责与实现边界

本 ADR 定义的是标准方案，不等于要求当前脚本实现已经完全重构到位。

当前实现可以是过渡态，但后续演进必须以本章职责边界为准。

---

## 8.1 Skill 内职责

`raw-to-src` skill 内只保留以下职责：

1. 输入读取
2. 原始信息 intake
3. 同题归一化
4. 阶段级结构校验
5. 阶段级最小结构修补
6. 语义评审
7. 阶段级最小语义修补
8. evidence / report 落盘
9. 提出建议动作

skill 内禁止承担：

* 最终 approval gate
* 最终 freeze gate
* 最终 queue routing
* 最终 next skill dispatch

---

## 8.2 外挂 Gate 职责

外挂 gate / decision layer 负责：

1. 判断是否允许 freeze
2. 判断是否进入 retry
3. 判断是否转人工队列
4. 判断是否生成 blocked job
5. 判断是否生成并物化 handoff
6. 判断是否投递下一个 skill 的 ready job
7. 生成正式 decision 文件

因此：

## **Gate 不属于 raw-to-src skill 内部步骤，而是 skill 输出的消费者**

---

## 8.3 Freeze Readiness 的边界

`raw-to-src` skill 可以输出：

* `freeze-ready`
* `not-freeze-ready`

但这只是 readiness assessment，不是最终 freeze decision。

若实现中仍保留类似 `freeze-guard` 的 CLI，其语义必须被限制为：

* `package readiness validator`
* `gate input guard`

而不得扩张为：

* 最终 freeze decision
* next-skill routing decision
* retry / blocked / human_handoff 裁决器

真正 freeze 时，外挂 gate / freeze handler 应消费：

* candidate
* acceptance report
* defect list
* retry budget report
* execution evidence
* supervision evidence
* handoff proposal（如存在）

然后决定：

* freeze
* materialize retry handoff + ready job
* materialize human handoff + human queue item
* block / failed / deadletter
* materialize next-skill handoff + ready job

---

# 9. Job Output、Handoff 与 Next Skill Dispatch Contract

本 ADR 正式冻结：

## **raw-to-src 必须支持 handoff + job 化输出，而不是只输出文档与报告**

---

## 9.1 Handoff 优先原则

依据 ADR-003：

## **没有 handoff，不算正式流转。**

因此，`raw-to-src` 的 next skill dispatch 不应仅描述一个 job，而必须同时描述：

* 流转到哪个目标 skill
* 哪个 candidate / artifact 作为 primary input
* 哪些 evidence / report / gate result 作为 supporting context
* 当前 decision layer 建议的下一步动作

因此，本 ADR 明确要求：

* `proposed-next-actions.json` 是最小要求
* `handoff-proposal.json` 是推荐要求
* `job-proposal.json` 只负责运行实例，不替代 handoff

---

## 9.2 Job 类型

至少定义以下 4 类 job：

### 1. `next_skill`

用于正常流转到下一个 skill。

### 2. `retry`

用于当前 skill 在 budget 内重试。

### 3. `human_handoff`

用于进入人工会话队列。

### 4. `blocked`

用于明确阻断，不再自动推进。

本 ADR 明确要求：`retry` 是正式动作类型，而不是隐式重跑。

因此：

* `proposed-next-actions.json` 必须允许 `recommended_action = retry`
* `job-proposal.json` 必须允许 `job_type = retry`
* `retry` 必须作为独立治理事件进入统计、审计与 queue routing

---

## 9.3 Job 最小字段

所有 job 至少应包含：

* `job_id`
* `job_type`
* `from_skill`
* `target_skill`
* `handoff_ref`
* `source_run_id`
* `source_artifacts`
* `gate_decision_ref`
* `reason`
* `priority`
* `status`
* `created_at`

若用于双队列路由，还应包含：

* `queue_path`
* `consumer_type`
* `retry_count`
* `retry_budget`

其中：

* `consumer_type = skill_loop | human_loop`

* `queue_path` 必须映射到 ADR-001 / ADR-003 已冻结的目录语义，而不是自造临时路径。

---

## 9.4 Handoff Proposal 最小字段

`handoff-proposal.json` 至少应包含：

* `handoff_id`
* `from_skill`
* `to_skill`
* `source_run_id`
* `primary_artifact_ref`
* `supporting_artifact_refs`
* `gate_result_ref`
* `evidence_bundle_refs`
* `required_context`
* `expected_output_type`
* `created_at`

`handoff-proposal.json` 是 skill 对下游接缝的建议表达，不等同于最终物化 handoff。

---

## 9.5 Proposed Next Actions

`raw-to-src` skill 必须至少产出：

* `proposed-next-actions.json`

该文件至少应表达：

* 当前结果状态
* 推荐下一步动作
* 推荐目标 skill
* 推荐 handoff 动作
* 推荐队列目录
* 是否建议 freeze

该文件不是最终 decision，而是外挂 gate 的输入之一。

---

## 9.6 Next Skill 规则

建议冻结以下路由规则：

### 场景 A：通过 freeze readiness，且外挂 gate 决定继续主链

* 生成 `handoff`
* `job_type = next_skill`
* `target_skill = product.src-to-epic`
* `queue_path = artifacts/jobs/ready/`

### 场景 B：结构失败但 budget 未耗尽

* 可复用当前 artifact / evidence 生成 retry handoff
* `job_type = retry`
* `target_skill = product.raw-to-src`
* `queue_path = artifacts/jobs/ready/`

### 场景 C：语义失败且 budget 耗尽

* 生成 human handoff
* `job_type = human_handoff`
* `target_skill = human.review.raw-to-src`
* `queue_path = artifacts/human-queue/waiting-human/`

### 场景 D：输入无效或不应继续

* 不生成下游业务 handoff
* `job_type = blocked`
* `queue_path = artifacts/jobs/failed/` 或 `artifacts/jobs/deadletter/`

---

# 10. Dual-Agent Supervision and Decision Separation

本 ADR 正式冻结三层角色分工：

1. executor
2. supervisor
3. external gate

三者必须分权运行，不得混层。

---

## 10.0 运行时硬分权要求

本 ADR 不接受“只有两个 evidence 文件，但仍由同一执行路径同时产出全部结论”的软分权实现。

至少需要满足以下硬约束：

1. executor 不得直接写 supervision conclusion；
2. supervisor 不得静默回写 candidate；
3. gate decision 不得由 supervisor 伪装产出；
4. 关键产物必须能追溯 `created_by_role`、`created_by_step` 与输入来源。

若某实现仅在文档层约定分权，而在 runtime / file ownership / CLI boundary 上没有限制，则不视为完全符合本 ADR。

---

## 10.1 Executor 边界

executor 负责：

* intake
* normalization
* patch application
* artifact 生成
* execution evidence 落盘

executor 不得负责：

* 最终 acceptance 决策
* 最终 freeze 决策
* 最终 queue 路由裁决
* 绕过 defect list 隐式整体重写 candidate

executor 产生的关键对象至少包括：

* candidate artifact
* structural report
* execution evidence
* patch lineage

这些对象的 ownership 必须明确为 executor。

---

## 10.2 Supervisor 边界

supervisor 负责：

* 独立检查 executor 产物
* 产生 semantic findings / acceptance findings
* 判断 freeze-readiness
* 产出 recommended action
* 落盘 supervision evidence

supervisor 不得负责：

* 静默直接改写 artifact
* 绕过 defect list 直接重写 candidate
* 直接生成最终 gate decision
* 直接物化正式 queue job

supervisor 产生的关键对象至少包括：

* semantic findings
* acceptance findings
* supervision evidence
* readiness recommendation

这些对象的 ownership 必须明确为 supervisor，且默认以只读方式消费 candidate package。

---

## 10.3 External Gate 边界

external gate 负责：

* 消费 skill result 与 supervision evidence
* 形成最终 decision
* 决定 freeze / retry / human_handoff / blocked / next_skill
* 物化最终 handoff、queue job 或 freeze action

因此：

## **supervisor 是监督者，不是第二执行器，也不是最终 gate。**

---

## 10.4 Execution Evidence

执行证据至少应记录：

* `skill_id`
* `run_id`
* `role`
* `input_path`
* `outputs`
* `stage_results`
* `commands_run`
* `structural_results`
* `key_decisions`
* `uncertainties`
* `created_artifacts`

其中 `stage_results` 至少应能表达：

* 当前阶段由哪个角色执行；
* 当前阶段读了什么；
* 当前阶段产出了什么；
* 当前阶段发现了哪些问题；
* 当前阶段应用了哪些最小 patch；
* patch 后 revalidation 的结果。

---

## 10.5 Supervision Evidence

监督证据至少应记录：

* `role`
* `reviewed_inputs`
* `reviewed_outputs`
* `acceptance_dimensions`
* `semantic_findings`
* `decision`
* `reason`
* `readiness_recommendation`
* `ownership_scope`

若被审对象为 `governance_bridge_src`，`acceptance_dimensions` 至少还应覆盖：

* `bridge_semantic_density`
* `downstream_actionability`
* `governance_constraint_clarity`
* `non_goal_explicitness`

---

## 10.6 Retry Budget Evidence

新增要求：

* 每次运行必须显式记录 retry budget 消耗情况

至少应包含：

* 结构环已消耗次数
* 语义环已消耗次数
* 总预算已消耗次数
* 每一轮修复的输入原因
* 每一轮修复后的结果
* 为什么继续
* 为什么停止

正式产物建议为：

* `retry-budget-report.json`

---

## 10.7 Skill Result 与 Gate Decision 的区分

本 ADR 明确要求区分：

### skill result

由 skill 直接产出，例如：

* `result-summary.json`
* `proposed-next-actions.json`

### gate decision

由外挂 gate 产出，例如：

* `gate-decision.json`

不得把 gate decision 混写进 skill result。

---

# 11. Queue Routing 与阶段状态机

为对齐 ADR-001 与 ADR-003，本 ADR 不再使用抽象 `queue/skill-ready/` 语义，而采用已冻结目录语义：

* `artifacts/jobs/ready/`
* `artifacts/jobs/running/`
* `artifacts/jobs/done/`
* `artifacts/jobs/failed/`
* `artifacts/jobs/deadletter/`
* `artifacts/human-queue/waiting-human/`
* `artifacts/human-queue/approved/`
* `artifacts/human-queue/rejected/`

其中：

* `artifacts/jobs/ready/` 由 execution loop 消费
* `artifacts/human-queue/waiting-human/` 由 human loop 消费
* `artifacts/jobs/failed/` 表示当前链路失败但仍可审计
* `artifacts/jobs/deadletter/` 表示终止自动推进
* `artifacts/jobs/done/` 表示当前阶段已被 gate 正式消费并结案

---

## 11.1 最小阶段状态机

为避免 queue consumer 与 gate consumer 只能靠 report 内容猜状态，本 ADR 明确要求定义独立的 `run-state.json`，并至少支持以下 run 级阶段状态：

* `input_invalid`
* `input_fixing`
* `intake_failed`
* `intake_fixing`
* `structural_fixing`
* `structural_failed`
* `semantic_reviewing`
* `semantic_fixing`
* `semantic_failed`
* `retry_recommended`
* `freeze_ready`
* `handed_off`
* `blocked`
* `completed`

这些状态用于：

* 标记当前 run 所处阶段；
* 为外部 gate 与 queue handler 提供稳定消费接口；
* 支撑后续更正式的 state machine / decision schema。

这些状态不替代 ADR-003 已冻结的 artifact 状态、job 状态与 step attempt 状态，而是 `raw-to-src` 运行视角下的派生状态。

`result-summary.json` 可以保留高层摘要，但不得替代 `run-state.json` 承担状态机职责。

---

# 12. Job Proposal 与 Materialized Job 的区分

为避免 skill 与 gate 的职责再次混层，本 ADR 明确区分：

### `proposed-next-actions.json`

由 skill 产出，表达推荐下一步动作。

### `job-proposal.json`

由 skill 可选产出，表达建议的 job 结构，但不是最终入队对象。

### `handoff-proposal.json`

由 skill 可选产出，表达建议的 handoff 结构，但不是最终物化 handoff。

### `gate-decision.json`

由 external gate 产出，表达最终裁决。

### `materialized-handoff.json`

由 gate 或 queue handler 产出，表达最终正式流转 handoff。

### `materialized-job.json`

由 gate 或 queue handler 产出，表达最终正式入队 job。

因此：

## **skill 可以提出 job / handoff proposal，但不直接等同于最终 materialized handoff 或 materialized job。**

同理：

## **skill 可以提出 retry proposal，但不得把“再次运行一次”伪装成未显式声明的隐式行为。**

---

# 13. 当前实现与目标方案的关系

本 ADR 是目标方案的正式冻结，而不是对当前脚本状态的逐行复述。

因此本 ADR 明确承认：

* 当前 `raw-to-src` 实现可能仍处于 executor 与 supervisor 共用一条执行路径的过渡态；
* 当前阶段内局部闭环可能尚未完全显式化；
* 当前 `retry` 可能尚未作为正式 action 落到 runtime control flow；
* 当前 budget 可能仍停留在记录层，而未完全成为控制流约束；
* 当前 evidence / report / retry 输出也可能尚未完全拆分；
* 这些实现状态不改变本 ADR 对正式架构边界的定义。

后续实现演进应以本 ADR 为准，逐步完成：

1. 阶段内局部闭环显式化
2. executor / supervisor 的命令边界与 ownership 分离
3. `retry` 正式进入 action 与 job contract
4. budget 进入控制流
5. gate 外挂
6. handoff proposal / materialized handoff 分层
7. job 路由输出
8. next skill dispatch 合同化

---

# 14. 技术取舍

## 14.1 选择此方案的原因

### 1. 与 ADR-001 完全对齐

它把 `raw-to-src` 从单 skill 闭环推进为双队列架构中的标准执行单元。

### 2. 最小修复闭环更硬

结构问题先收敛，语义问题后收敛，避免 loop 膨胀。

### 3. Retry 行为可审计

budget、升级、停止条件都可被结构化记录。

### 4. Skill 职责更清晰

skill 负责产出结果，gate 负责裁决，queue 负责流转。

### 5. 更适合长链路扩展

后续 `src-to-epic`、`epic-to-feat` 可以复用相同模式。

---

## 14.2 明确不选的方案

### 方案 A：继续保持单 skill 内闭环

不选原因：

* skill 职责过重；
* 无法自然接入双队列；
* gate 无法外挂；
* next skill 路由不清晰。

### 方案 B：不区分结构修复与语义修复

不选原因：

* reviewer 成本高；
* 修复 loop 容易膨胀；
* budget 难以控制；
* 失败升级路径不清晰。

### 方案 C：允许无界 LLM retry

不选原因：

* 成本不可控；
* 漂移风险高；
* 审计不可用；
* 极易形成空转。

---

# 15. 后果与影响

## 15.1 正面结果

* `raw-to-src` 正式升级为双环修复模型；
* Gate、freeze、queue routing 的职责边界被清晰外置；
* job 化输出接口开始形成；
* 结构 budget 与语义 budget 正式进入治理合同；
* 为后续产品主链各 skill 提供统一范式。

## 15.2 负面结果

* 架构比单 skill 闭环更复杂；
* 对 decision layer 和 queue contract 的要求更高；
* 当前实现与目标方案之间存在过渡期；
* 后续必须补 job schema、gate schema、queue routing 细节；
* 为了得到真正可审计的双 agent 分权，需要接受更多 runtime 对象与更严格的 ownership 约束。

---

# 16. 实施计划

## 16.1 P0：当前开发阶段必须完成

1. 将“逐步闭环”从章节原则落实到 runtime contract：
   * 输入闭环
   * intake 闭环
   * candidate 闭环
   * source semantic 闭环
   * acceptance semantic 闭环
2. 将 `retry` 作为正式 action 打通：
   * `proposed-next-actions.json`
   * `job-proposal.json`
   * queue routing
   * 测试与审计统计
3. 让 budget 进入控制流，而不是只落盘：
   * 结构 budget
   * 语义 budget
   * total budget 保险丝
4. 将 executor / supervisor 从“文件分开”提升为“运行时硬分权”：
   * 至少拆出命令边界
   * 明确 candidate 只读审查
   * 明确 readiness recommendation 的 ownership
5. 补齐阶段状态机：
   * `run-state.json`
   * `result-summary.json` 与 run state 的边界
6. 强化 ADR bridge SRC 的可消费性：
   * 为 `adr` 输入增加专门的 `bridge synthesis`
   * 将治理对象、失控点、新原则、下游继承点、非目标写入正文与 `Bridge Context`
   * 禁止关键章节停留在通用模板句或标题复写
   * 增加 `downstream_actionability` 与 `problem_statement_quality_check`

## 16.2 P0 的建议实施顺序

### Phase 1：Contract First

先更新 schema / spec / contract，使以下对象先冻结：

* `run-state.json`
* `structural-report.json` 的阶段 patch lineage
* `execution-evidence.json` 的角色与阶段字段
* `supervision-evidence.json` 的 ownership 与 readiness 字段
* `retry` action / job contract
* `governance_bridge_src` 的最低信息密度规则
* ADR bridge 专属 acceptance 维度与 defect 类型

### Phase 2：Runtime Refactor

再调整 `raw-to-src` runtime：

* 把结构环拆成输入闭环、intake 闭环、candidate 闭环
* 把语义环拆成 source semantic 闭环、acceptance semantic 闭环
* 让 patch 事件显式落盘
* 让 budget 决定是否继续修补
* 为 `adr` 输入增加专门的 bridge synthesis
* 将 `治理变更摘要` 或等价治理章节写入 candidate
* 将模板句拦截、标题复写检测、下游可消费性检测纳入 semantic review

### Phase 3：Dual-Agent Boundary

最后拆出 executor / supervisor 的实际运行边界：

* executor 只产出 candidate、structural report、execution evidence
* supervisor 只读消费 candidate package，并产出 semantic findings、acceptance findings、supervision evidence
* external gate 再消费两侧结果形成最终 decision

## 16.3 P1：建议尽快补

1. 将 `freeze-guard` 重命名为更窄语义的 package guard
2. 区分 `skill-result.json` 与 `gate-decision.json`
3. 将 freeze 抽为单独 gate handler
4. 为 `--allow-update` 引入版本与队列规则
5. 补齐 queue routing 的 materialization 细节

## 16.4 P2：可后补

1. job 幂等键
2. defect patch lineage 的跨 run 聚合视图
3. 通用 supervisor / human gate decision schema
4. 通用 gate input validator 命名与复用

---

# 17. 最终结论

`raw-to-src` 不是一个“把原始内容整理成文档”的脚本，而是 LL 产品需求主链的正式入口治理层。

本 ADR 冻结的不是“当前代码已经怎么做”，而是“正式方案以后必须怎么做”：

* 用结构环和语义环替代单一 defect loop；
* 用 budget 替代无界重试；
* 用外挂 gate 替代 skill 内审批与冻结；
* 用 job 输出和 next skill dispatch 替代单 skill 自闭环；
* 用 result / evidence / decision 分层替代混合职责。

自本 ADR 通过后，`raw-to-src` 的正式目标架构应为：

## **一个消费输入 job、产出 freeze-ready candidate 与结构化 next actions 的 governed skill**

而不是一个在内部完成全部 gate、freeze、routing 决策的重型单 skill 工作流。
