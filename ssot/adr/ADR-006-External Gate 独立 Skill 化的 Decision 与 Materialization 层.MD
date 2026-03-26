# ADR-006：LL 将 External Gate 收敛为独立 Skill 化的 Decision 与 Materialization 层

* 状态：Draft
* 日期：2026-03-23
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x skill-first 主链与通用治理链
* 相关 ADR：ADR-001、ADR-002、ADR-003、ADR-004、ADR-005、ADR-016

> 适用性说明：本 ADR 保留“external gate 独立于业务 skill”“candidate/proposal 与 formal object 分层”“formal 写入必须走受治理链路”这些原则。
> 
> 对 gate skill 标准名、第二会话职责划分、pending queue、claim / decision / dispatch 运行模型，以 `ADR-016` 为当前权威基线。
> 
> 本文中遗留的 `ll-gate-decision-materializer`、`materialized-handoff.json`、`materialized-job.json` 等表述视为历史设计词汇，不再作为当前实现约束。

---

# 1. 背景

在 ADR-001 中，LL 已正式确定采用“双会话双队列闭环模型”作为 v0.1 执行架构，并明确：

* skill-first 是主路线；
* 执行推进依赖文件化 job / gate / decision / artifact / evidence；
* 关键 gate 必须外置；
* 不优先建设独立重型调度器。

在 ADR-002 中，`raw-to-src` 已被正式收敛为：

* 一个消费输入 job、产出 candidate package 的 governed skill；
* 一个只负责生成结果、evidence、proposal，而不负责最终 gate、freeze、queue routing 的标准执行单元。

ADR-002 同时已经留下了一个明确接缝：

* skill 可以产出 `proposed-next-actions.json`
* skill 可以产出 `job-proposal.json`
* skill 可以产出 `handoff-proposal.json`
* 最终的 `gate-decision.json`
* `materialized-ssot.json`
* `materialized-handoff.json`
* `materialized-job.json`

不应再由 skill 自己完成，而应由外挂 gate / decision layer 消费后物化。

在 ADR-003 中，LL 又进一步冻结了文件化 handoff runtime，明确：

* artifact、job、handoff、gate result、evidence bundle 必须分层；
* handoff 必须对象化；
* 状态推进必须有 evidence 或 decision 支撑；
* 文件系统承担最小 runtime 职责，但不回退到重型平台。

在 ADR-004 中，LL 进一步冻结了公共 Skill Kernel 与统一 Skill Execution Contract，明确：

* skill 应主要承载业务语义与声明式 contract；
* 通用治理能力应收敛到统一 runtime / contract；
* Loop / Queue / Human Gate 仍负责上层调度与决策回流。

在 ADR-005 中，LL 又将 Managed Artifact、Artifact Registry、Artifact IO Gateway、Path Policy 作为正式文件治理基础设施冻结下来，从而使：

* gate 消费对象有稳定 artifact identity；
* materialization 有统一受管写入入口；
* 下游消费不再依赖路径猜测。

但到目前为止，LL 仍缺少一个正式决策来回答下面这个问题：

> 当上游 governed skill 已产出 candidate package、proposal 与 evidence 之后，谁来做最终治理裁决，并把“建议”物化为正式 handoff、正式 job 和 run closure？

如果这一层继续停留在临时脚本、特例 handler 或散落逻辑中，就会出现新的结构性倒退：

* skill-first 前段已经标准化，最后一跳却重新变成系统黑盒；
* proposal 与 materialized object 的边界再次混层；
* 不同 skill 各自内嵌一点 gate logic，长期会漂移；
* 双会话模型会重新退化为“一个会话既执行又裁决”；
* 审计链将无法稳定回答“谁批准了推进、为什么推进、推进后正式落了什么对象”。

因此，需要为 LL 正式冻结一层：

## **独立 skill 化的 external gate decision + materialization 层**

---

# 2. 问题陈述

LL 当前需要解决的，不是“再写一个 gate 脚本”，而是：

* 如何让 external gate 成为与 skill-first 架构一致的标准执行单元；
* 如何把最终 decision、handoff materialization、job materialization、run closure 从业务 skill 内彻底抽离；
* 如何让 `raw-to-src`、`src-to-epic`、`epic-to-feat` 乃至后续 skill 共享同一套 gate consumer；
* 如何让 execution loop 与 gate loop 只通过标准对象交互，而不是互相直接调用；
* 如何在不重做业务审查的前提下，基于 package completeness、evidence、budget、proposal 与 supervisor 结论做治理裁决；
* 如何把 candidate package 的“可建议性输出”稳定晋升为正式可消费对象。
* 如何把 freeze-ready SRC candidate 在 gate 批准后稳定物化为正式 `ssot/src/SRC-xxx__slug.md`，而不是在 `raw-to-src` 内提前落盘。

如果不正式冻结这层，会出现以下缺口：

## 2.1 职责缺口

上游 skill 已被 ADR-002 要求只负责 candidate package 与 proposal，但系统没有一个正式、可治理、可复用的消费者来完成最终裁决与物化。

## 2.2 复用缺口

若每个 skill 各自附带一点 gate materialize 逻辑，那么 `raw-to-src`、`src-to-epic`、`epic-to-feat` 会很快出现不同版本的 queue routing、retry、handoff、run closure 规则。

## 2.3 双会话缺口

若 gate 不是独立 consumer，而只是执行会话尾部的一段附属逻辑，则 execution 与 governance 的分离会失效。

## 2.4 审计缺口

没有统一的 `gate-decision`、`materialized-handoff`、`materialized-job`、`run-closure` 产物，就无法稳定审计：

* 为什么推进；
* 推进到了哪里；
* 是否走了 retry / revise / handoff；
* 当前 run 是否已经正式结案。

## 2.5 架构一致性缺口

ADR-004 已要求 skill 只承载业务语义与声明式 contract；ADR-005 已要求正式产物通过 Gateway / Registry 进入正式链路。

如果 gate 仍是系统特例脚本，则：

* 它不受标准 skill contract 管理；
* 不受统一 evidence、tests、input/output contract 管理；
* 不受统一 artifact materialization 纪律管理；
* 最终会成为 skill-first 架构中的新中枢黑盒。

因此，需要一份正式 ADR，定义：

## **External Gate 应作为独立 governed skill / 独立 consumer 存在，并承担统一的 decision 与 materialization 职责。**

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **独立 External Gate Skill + Gate Loop Consumer**

作为 candidate package 进入正式下游链路之前的统一治理裁决与物化层。

本 ADR 冻结以下正式原则：

1. external gate 不再作为某个业务 skill 的附属脚本存在；
2. external gate 采用独立 skill 化形态，推荐标准名为：
   * `ll-gate-decision-materializer`
3. 该 skill 的职责固定为：
   * decision
   * formal object materialization
   * handoff materialization
   * job materialization
   * run closure
4. 该 skill 不是业务语义大总管，不负责重做上游业务审查；
5. 该 skill 的主要输入是 candidate package、proposal、evidence、budget 与 run state；
6. gate loop 与 execution loop 不直接互相调用，而只通过结构化文件对象协作；
7. 每个 run 一旦被 gate 消费并产出正式 decision，当前 run 必须立即结案；
8. `revise` 与 `retry` 一律创建新 run，而不是改写原 run；
9. 当需要人工或特殊 consumer 介入时，external gate 输出 `handoff` 决策并物化 human-review job；
10. v1 不给 external gate 自己再套一层 external gate，以避免递归治理。

---

## 3.2 正式定义

LL v0.x 在 ADR-001 至 ADR-005 的基础上，正式定义以下原则：

1. **External Gate 是标准 skill，而不是特例脚本**

   * 拥有 `SKILL.md`
   * 拥有 input / output contract
   * 拥有 evidence、tests 与最小实现入口
   * 作为受治理的标准执行单元存在

2. **External Gate 是通用裁决与物化层，而不是业务内容再审层**

   * 判断 package 是否具备推进条件
   * 判断 evidence、budget、proposal、run-state 是否允许推进
   * 只消费上游已经产出的治理结论与证据
   * 不生产新的业务语义判断标准
   * 不重复做一次 `raw-to-src`、`src-to-epic` 等业务语义审查

3. **Execution Loop 与 Gate Loop 职责分离**

   * execution loop 只消费 execution job，负责产出 candidate package
   * gate loop 只消费 `gate-ready` jobs，负责做最终 decision 与 materialization
   * 两者通过文件对象协作，而不是直接调用彼此

4. **proposal 与 materialized object 强制分离**

   * 上游 skill 只能提出 proposal
   * `raw-to-src` 只能产出 SRC candidate package，不得直接写正式 `ssot/src/SRC-xxx__slug.md`
   * formal SSOT object 只能在 gate 批准后的 materialization 环节落盘
   * external gate 才能产出最终 `materialized-ssot.json`
   * external gate 才能产出最终 `materialized-handoff.json`
   * external gate 才能产出最终 `materialized-job.json`

5. **gate decision 必须是互斥单选**

   * 不允许多个 approve flag 并列
   * 不允许既 approve next skill 又 approve retry
   * 每次 gate 消费必须产出唯一最终 decision

6. **run 一旦被 gate 消费，必须立即结案**

   * 原 run 保存该次执行的 candidate package 与证据
   * gate 决策后原 run 进入终态并 closure
   * 若需 revise 或 retry，则创建新的 child run / sibling run 继承 lineage

---

# 4. 架构边界

## 4.1 execution skill 的职责

业务 skill，例如：

* `raw-to-src`
* `src-to-epic`
* `epic-to-feat`

其职责固定为：

* 消费受管输入；
* 产出 candidate package；
* 产出 execution / supervision evidence；
* 产出 proposed next actions；
* 可选产出 job proposal 与 handoff proposal；
* 将 run 标记为 `awaiting_gate`，并同时物化 gate-input job。

其不负责：

* 最终批准推进；
* 最终 freeze；
* 正式分配 SRC ID；
* 正式写入 `ssot/src/SRC-xxx__slug.md`；
* 最终 queue routing；
* 最终 materialized handoff；
* 最终 materialized job；
* run closure。

这延续 ADR-002 已冻结的边界，不得回退。

## 4.2 external gate skill 的职责

`ll-gate-decision-materializer` 的职责固定为：

* 读取 candidate package；
* 校验 package completeness 与治理前置条件；
* 消费 result summary、run state、evidence、proposal、retry budget；
* 形成唯一的 `gate-decision.json`；
* 当 decision 允许 formalize / approve 时，将 freeze-ready candidate 晋升为正式对象；
* 按 decision 物化正式 handoff 或正式 job；
* 写出 `run-closure.json`；
* 将当前 run 移入正式结案状态。

其不负责：

* 重新生成上游 candidate 的业务语义内容；
* 直接改写上游 candidate package；
* 重新进行完整业务设计或内容评审；
* 直接调用下游 execution session；
* 替代人工审批。

在当前阶段，ADR-006 明确采用：

## **由 external gate 一并完成 formal SRC materialization**

也就是说，当 `raw-to-src` 的 candidate package 被 external gate 批准推进时：

* 正式 `ssot/src/SRC-xxx__slug.md` 由 gate 后的 materialization 环节写入；
* 不允许由 `raw-to-src` 在 candidate 生成阶段直接写入正式 SSOT 路径。

未来如有必要，可以再进一步拆出：

* `ssot-materialize-src`

这类更窄职责的 materializer skill；

但在 ADR-006 v1 中，优先采用：

* `external gate = decision + formal SSOT materialization + handoff/job materialization + run closure`

## 4.3 human loop 的职责

external gate 不等于 human gate。

当治理决策要求人工介入时：

* external gate 输出 `handoff` decision；
* external gate 物化 `materialized-handoff.json`；
* external gate 物化 human-review job；
* 后续仍由 ADR-001 所定义的 human loop 消费。

也就是说：

* external gate 是治理裁决 consumer；
* human loop 是人工处理 consumer；
* 两者不是同一个层级。

## 4.4 与 ADR-004 / ADR-005 的关系

ADR-004 要求 skill 只承载业务语义与声明式 contract，而通用治理能力应统一收敛。

ADR-006 进一步明确：

* gate decision + materialization 也是一种通用治理能力；
* 它不应散落在业务 skill 内；
* 它应以独立 skill 形式收敛，并通过统一 contract 暴露能力。

ADR-005 要求 Managed Artifact 的正式写入通过 Gateway / Registry / Path Policy 统一治理。

ADR-006 进一步规定：

* `gate-decision.json`
* `materialized-ssot.json`
* `materialized-handoff.json`
* `materialized-job.json`
* `run-closure.json`

进入正式链路时，必须遵守同一套受管写入与登记约束。

---

# 5. 双会话驱动模型

ADR-006 正式规定：

## **LL 的 L2 主链采用 `execution skill -> external gate -> next execution skill -> external gate` 的链式结构。**

例如：

```text
raw-to-src
  -> external-gate
  -> src-to-epic
  -> external-gate
  -> epic-to-feat
  -> external-gate
  -> ...
```

其中：

* formal SRC materialization 在 ADR-006 v1 中不是独立 skill；
* formal SRC materialization 是 external gate 内部的 materialization phase；
* 当前不把它定义为第三个 consumer，也不把它定义为独立链路节点。

因此，当前推荐理解为：

```text
raw-to-src
  -> external-gate(decision + formal-src materialization)
  -> src-to-epic
```

但这里的“链式结构”不表示会话之间直接调用。

正式驱动方式如下：

## 5.1 execution loop 如何驱动 gate loop

execution loop 在完成某个业务 skill 后：

* 落 candidate package；
* 落 proposal / evidence / run-state；
* 将当前 run 标记为 `awaiting_gate`；
* 必须同时物化一个 gate-input job 到 gate-ready 队列。

ADR-006 v1 明确采用：

* gate loop 只消费 `gate-ready` jobs；
* 不再保留“扫描 `awaiting_gate` runs”作为并行正式入口。

## 5.2 gate loop 如何驱动 execution loop

gate loop 在完成 decision 后：

* 若决定继续自动推进，则物化一个新的 execution job 到 `artifacts/jobs/ready/`
* execution loop 仅通过 ready 队列感知下一步，不接受 direct call

## 5.3 正式协作原则

* execution loop 消费 execution job
* gate loop 消费 `gate-ready` job
* human loop 消费 human-review job

因此 LL 的稳定形态应是：

## **双主 consumer + 文件状态机**

而不是两个 agent 会话彼此发消息或直接调用。

---

# 6. Gate 输入标准

external gate 的最小输入集至少应包括：

* `result-summary.json`
* `run-state.json`
* `proposed-next-actions.json`
* `job-proposal.json`
* `execution-evidence.json`
* `supervision-evidence.json`
* `retry-budget-report.json`
* `freeze-readiness` 相关结论或等价字段

可选输入包括：

* `handoff-proposal.json`
* `defect-list.json`
* `acceptance-report.json`

其中，external gate 的主要判断对象不是“业务内容本身是否足够完美”，而是：

* package 是否完整；
* evidence 是否齐备；
* supervisor 结论是否支持推进；
* retry budget 是否允许；
* 当前 run-state 是否允许继续；
* proposal 是否满足最小合法结构；
* target queue / target skill / target handoff 是否合法。

因此，本 ADR 明确要求：

## **gate 主要消费治理结论，而不是重做业务审查。**

同时，本 ADR 明确要求：

## **formal SSOT object 只能由 gate 消费完 package 并批准后物化，不得在 candidate 生成阶段提前存在。**

---

# 7. Decision 模型

## 7.1 正式 decision_type

ADR-006 采用以下互斥单选决策类型：

* `approve`
* `revise`
* `retry`
* `handoff`
* `reject`

不再采用多个并列 approve flag 的表达方式。

## 7.2 各决策的含义

### `approve`

含义：

* 当前 package 满足推进条件；
* 允许进入下一步自动执行，或允许进入 freeze / dispatch handler。

约束：

* `approve` 必须携带明确的 approved dispatch target；
* target 可以是 formal SSOT materialization 后的下一个 skill，也可以是更窄的 freeze handler；
* 不允许只有“通过”而没有去向。

当 `approve` 用于 `raw-to-src` 输出时，还必须同时满足：

* package 完整；
* structural pass；
* semantic pass；
* budget 未违规；
* supervisor evidence 齐备；
* `freeze_readiness = true`。

### `revise`

含义：

* 当前 package 基本方向成立；
* 但不允许直接进入下一 skill；
* 需要在当前 skill 语义边界内做受限修订。

约束：

* 必须产出 `revision-request.json`
* 必须限制 patch scope
* 必须新建 revision job
* 不得直接改写原 run 的 package

### `retry`

含义：

* 当前结果不通过；
* 但问题更像运行失败、预算内重试、非定向重跑；
* 适合重新执行当前 skill，而不是局部 patch。

### `handoff`

含义：

* 不继续自动推进；
* 需要人工或特殊 consumer 介入。

约束：

* 必须物化正式 handoff
* 必须物化 human-review job 或特定 consumer job

### `reject`

含义：

* 当前自动链路在 gate 层被否决；
* 不允许直接自动继续；
* 默认终止当前自动推进。

约束：

* `reject` 是自动链路终止态；
* `reject` 不派生新的 execution job；
* `reject` 不默认派生 human-review job；
* 需要人工复核时，不应使用 `reject`，而应显式使用 `handoff`。

## 7.3 为什么采用这一组 decision

采用 `approve / revise / retry / handoff / reject` 的原因是：

* 它们表达治理语义，而不是目录动作；
* 它们可以稳定映射到 run 状态转换；
* 它们同时保留“最小修补”和“完全重跑”的区别；
* 它们避免了 `approve_next_skill`、`approve_retry` 一类多 flag 冲突。

## 7.4 decision_type 与 target 约束矩阵

为避免 target 字段在不同 decision 中漂移，ADR-006 明确采用以下硬约束：

* `approve`：必须有 `approved_target`
* `revise`：必须有 `followup_target`
* `retry`：必须有 `followup_target`
* `handoff`：必须有 `followup_target`
* `reject`：默认不得有任何 target

进一步约束：

* `approve` 不得写 `followup_target`
* `revise` / `retry` / `handoff` 不得写 `approved_target`
* 若某实现希望在 `reject` 后触发人工复核，应改写 decision_type 为 `handoff`，而不是给 `reject` 增加 target

---

# 8. 状态机

## 8.1 run 状态机

每个 run 至少支持以下状态：

* `created`
* `running`
* `produced_candidate`
* `awaiting_gate`
* `approved`
* `revise_requested`
* `retry_requested`
* `handed_off`
* `rejected`
* `completed`

推荐转换如下：

### execution 侧

* `created -> running`
* `running -> produced_candidate`
* `produced_candidate -> awaiting_gate`

### gate 侧

* `awaiting_gate -> approved`
* `awaiting_gate -> revise_requested`
* `awaiting_gate -> retry_requested`
* `awaiting_gate -> handed_off`
* `awaiting_gate -> rejected`

### 结案

* `approved -> completed`
* `revise_requested -> completed`
* `retry_requested -> completed`
* `handed_off -> completed`
* `rejected -> completed`

这里的 `completed` 只表示：

* 当前 run 的 gate 决策已完成；
* 不表示整条业务主链结束。

本 ADR 进一步明确：

* `completed` 仅是 run-scope terminal state；
* `completed` 不代表 workflow terminal state；
* `completed` 不等同于 downstream job succeeded。

## 8.2 job 状态机

job 至少支持：

* `ready`
* `claimed`
* `running`
* `succeeded`
* `failed`
* `cancelled`
* `deadletter`

## 8.3 handoff 状态机

handoff 至少支持：

* `proposed`
* `materialized`
* `consumed`
* `expired`
* `cancelled`

## 8.4 三层状态边界

ADR-006 明确区分以下三层状态：

### run state

用于表达某一次 skill run 本身的状态。

### job state

用于表达某一个 queue job 的领取、运行、成功、失败、死信状态。

### workflow / lineage aggregate state

用于表达更长链路或整个 lineage 的聚合推进状态。

因此：

* `run completed` 不等于 `job done`
* `job succeeded` 不等于 downstream 已成功消费
* `workflow completed` 不应从单个 run 或单个 job 直接推断

---

# 9. Materialization 规则

## 9.1 approve

external gate 至少产出：

* `gate-decision.json`
* `materialized-job.json`
* `run-closure.json`

状态转换：

* run: `awaiting_gate -> approved -> completed`
* new execution job: `ready`

当当前 run 来自 `raw-to-src` 且满足 formalization 条件时，approve 阶段还必须额外执行以下动作：

* 正式分配 `SRC-xxx` 身份；
* 生成或渲染正式 `ssot/src/SRC-xxx__slug.md`；
* 回填 `workflow_run_id`、`source_refs`、`gate_decision_ref`、`candidate_package_ref`；
* 写出 `materialized-ssot.json`，记录 formal SSOT object 与 candidate package 的绑定关系；
* 后续 `src-to-epic` job 必须以 formal SSOT SRC 作为输入，而不是直接读取 candidate package。

也就是说：

* candidate package 是 gate 消费对象；
* formal SSOT SRC 是下游 skill 的正式输入对象。

## 9.2 revise

external gate 至少产出：

* `gate-decision.json`
* `revision-request.json`
* `materialized-job.json`
* `run-closure.json`

状态转换：

* old run: `awaiting_gate -> revise_requested -> completed`
* new revision job: `ready`

要求：

* 原 run package 不得被改写；
* 新 revision run 必须继承 lineage；
* revision job 必须携带 patch base 与 patch scope。

## 9.3 retry

external gate 至少产出：

* `gate-decision.json`
* `materialized-job.json`
* `run-closure.json`

状态转换：

* old run: `awaiting_gate -> retry_requested -> completed`
* new retry job: `ready`

## 9.4 handoff

external gate 至少产出：

* `gate-decision.json`
* `materialized-handoff.json`
* `materialized-job.json`
* `run-closure.json`

状态转换：

* run: `awaiting_gate -> handed_off -> completed`
* handoff: `proposed -> materialized`
* human-review job: `ready`

## 9.5 reject

external gate 至少产出：

* `gate-decision.json`
* `run-closure.json`

可选产出：

* `rejection-report.json`

状态转换：

* run: `awaiting_gate -> rejected -> completed`

要求：

* 默认不生成新的 execution job；
* 需要人工复核时，必须显式转入 `handoff` 路径，而不是隐式继续。

---

# 10. 最小对象字段

## 10.1 `gate-decision.json`

至少应包含：

* `decision_id`
* `decision_type`
* `source_run_id`
* `source_skill`
* `status_reason`
* `input_package_refs`
* `evidence_bundle_refs`
* `approved_target` 或 `followup_target`
* `budget_judgement`
* `lineage_key`
* `decided_at`

并且必须满足第 7.4 节定义的 target 约束矩阵。

## 10.2 `materialized-handoff.json`

适用范围：

* 仅在 decision_type 为 `handoff`，且需要 human 或特殊 consumer 介入时产出；
* 不作为标准自动推进场景下的默认对象。

至少应包含：

* `handoff_id`
* `from_skill`
* `to_skill`
* `source_run_id`
* `primary_artifact_ref`
* `supporting_artifact_refs`
* `gate_decision_ref`
* `evidence_bundle_refs`
* `required_context`
* `expected_output_type`
* `status_reason`
* `workflow_lineage_ref`
* `materialized_at`

## 10.3 `materialized-ssot.json`

适用范围：

* 仅在 gate 需要把 freeze-ready candidate 晋升为正式 SSOT 对象时产出；
* 在当前阶段，最直接对应 `raw-to-src -> formal SRC` 链路。

至少应包含：

* `materialization_id`
* `ssot_type`
* `assigned_id`
* `version`
* `output_path`
* `source_run_id`
* `source_skill`
* `candidate_package_ref`
* `gate_decision_ref`
* `source_refs`
* `workflow_lineage_ref`
* `materialized_by`
* `materialized_at`

## 10.4 `materialized-job.json`

至少应包含：

* `job_id`
* `job_type`
* `status`
* `queue_name`
* `consumer_type`
* `from_skill`
* `target_skill`
* `source_run_id`
* `source_handoff_id`
* `input_refs`
* `gate_decision_ref`
* `priority`
* `retry_count`
* `retry_budget`
* `created_at`

语义约束：

* `materialized-job.json` 是治理记录对象；
* 实际被 consumer claim 并执行的 job document 可以与其同源生成；
* 但二者在语义上不应被视为同一个层级的对象。

## 10.5 `revision-request.json`

至少应包含：

* `revision_id`
* `source_run_id`
* `requested_by`
* `revision_reason`
* `must_fix_findings`
* `must_not_change`
* `allowed_patch_scope`
* `budget_constraints`
* `created_at`

## 10.6 `run-closure.json`

至少应包含：

* `closure_id`
* `source_run_id`
* `decision_type`
* `terminal_state`
* `gate_decision_ref`
* `spawned_run_refs`
* `spawned_job_refs`
* `spawned_handoff_refs`
* `closed_at`

---

# 11. 目录拓扑

为保持 jobs 体系命名统一，ADR-006 推荐以下最小目录：

* `artifacts/handoffs/`
* `artifacts/jobs/ready/`
* `artifacts/jobs/gate-ready/`
* `artifacts/jobs/human-review/`
* `artifacts/jobs/blocked/`
* `artifacts/jobs/deadletter/`
* `artifacts/jobs/done/`

其中：

* `ready/` 由 execution loop 消费；
* `gate-ready/` 由 gate loop 消费；
* `human-review/` 由 human loop 消费；
* `done/` 表示当前 job 已被正式消费并结案；
* `blocked/` 与 `deadletter/` 负责表达不可继续自动推进的终态。

本 ADR 不再推荐继续扩张 `human-queue/` 这一平行命名体系，而是将 human review 作为 jobs 体系下的一类正式 consumer 队列。

对 formal SRC 而言，正式落盘路径固定为：

* `ssot/src/SRC-xxx__slug.md`

并且该对象一旦由 gate 物化完成，即成为后续 `src-to-epic` 的正式上游真相。

---

# 12. 推荐 Skill 形态

本 ADR 推荐 external gate v1 采用以下 skill 目录：

`skills/ll-gate-decision-materializer/`

至少包含：

* `SKILL.md`
* `ll.contract.yaml`
* `input/contract.yaml`
* `output/contract.yaml`
* `agents/executor.md`
* `tests/`
* `scripts/gate_materialize.py`

v1 推荐先采用单入口脚本，而不是一开始过度拆分：

* `decide`
* `materialize-ssot`
* `materialize-handoff`
* `materialize-job`
* `close-run`
* `run`

其中：

* `run = decide + materialize + close`

这样可以先打通主链，再按需要细拆为多个模块。

---

# 13. 与现有 ADR 的关系

## 13.1 与 ADR-001 的关系

ADR-001 冻结的是双会话双队列闭环架构。

ADR-006 不是替代 ADR-001，而是进一步明确在该架构中：

* execution loop 如何把 candidate package 交给 gate loop；
* gate loop 如何把裁决结果物化为正式 job 与 handoff；
* 双会话如何通过标准对象协作，而不是直接调用。

## 13.2 与 ADR-002 的关系

ADR-002 已经要求 `raw-to-src`：

* 只产出 result、evidence、proposal；
* 不内置最终 gate、freeze、queue routing；
* skill 可以提出 proposal，但不得直接等同于 materialized object。

ADR-006 进一步补上了 ADR-002 中明确留出的最后一层：

* 谁来消费 proposal；
* 谁来产生最终 `gate-decision.json`；
* 谁来产生 `materialized-ssot.json`、`materialized-handoff.json` 与 `materialized-job.json`；
* 谁来负责 run closure。

## 13.3 与 ADR-003 的关系

ADR-003 冻结的是文件化 handoff runtime 与对象边界。

ADR-006 在其基础上进一步规定：

* external gate 是这些对象的正式生产者之一；
* formal SSOT、handoff、job、decision、closure 如何在 gate 层被物化；
* revise / retry / handoff / reject 如何映射到对象状态与队列去向。

## 13.4 与 ADR-004 的关系

ADR-004 要求通用治理能力从业务 skill 中抽离，并通过统一 contract / kernel / executor adapter 承载。

ADR-006 进一步明确：

* gate decision + materialization 也是通用治理能力；
* 它应作为独立 skill 收敛，而不是散落在各业务 skill 内；
* 它与上层 Loop / Queue 并列，不被单个业务 skill 吸收。

## 13.5 与 ADR-005 的关系

ADR-005 冻结 Managed Artifact、Gateway、Registry、Path Policy。

ADR-006 进一步明确：

* gate 输出对象进入正式链路时也属于受管对象；
* external gate 物化 formal SSOT / handoff / job / closure 时，应遵守同一套 Gateway 与 Registry 纪律；
* 下游继续通过 artifact identity 与 handoff 消费输入，而不是退回路径猜测。

---

# 14. 非目标

ADR-006 v1 不做以下事情：

## 14.1 不做业务语义超级总管

external gate 不负责重新做一遍上游 skill 的业务审查。

并且：

* external gate 只消费上游已有治理结论；
* external gate 不新增新的业务语义判定标准。

## 14.2 不做两个会话的直接 RPC

gate loop 与 execution loop 不互相直接调用，只通过标准对象和队列协作。

## 14.3 不给 gate 自己再套一层 gate

v1 中 external gate 本身就是主链最高治理物化器，不再递归外包给另一个 gate。

## 14.4 不替代 human gate

涉及人工判断、人工补信息、人工审批的情形，external gate 只负责物化 handoff 与 human-review job。

## 14.5 不要求先建设重型服务化 runtime

ADR-006 冻结的是对象边界与 consumer 拓扑，不要求立即实现独立 daemon、事件总线或数据库。

## 14.6 不要求当前就拆出独立 `ssot-materialize-src` skill

ADR-006 v1 允许先把 formal SRC materialization 保持在 external gate 的 materialization 环节内。

---

# 15. 备选方案与拒绝原因

## 15.1 方案 A：继续作为 `raw-to-src` 的附属脚本

不选原因：

* 违背 ADR-002 已冻结的 skill 边界；
* 会让业务 skill 再次长回 freeze、decision、routing、closure 职责；
* 无法为 `src-to-epic`、`epic-to-feat` 提供统一复用面。

## 15.2 方案 B：当前阶段立即拆出独立 `ssot-materialize-src`

不选原因：

* 从长期边界看这是可行方向；
* 但在当前阶段会额外增加一个 skill 与一段 queue/contract 接缝；
* 不利于先把 `raw-to-src -> external-gate -> src-to-epic` 主链尽快打通。

因此 ADR-006 v1 采用折中：

* formal SRC 仍在 external gate 的 materialization 环节完成；
* 后续如物化职责继续膨胀，再拆出独立 `ssot-materializer` skill。

## 15.3 方案 C：让 approve 默认也产出 `materialized-handoff.json`

不选原因：

* 会把自动推进与 handoff 语义混为一谈；
* 会把 handoff 稀释成“所有跨 skill 流转都算 handoff”；
* 不利于区分自动 dispatch 与 human / special consumer 介入。

ADR-006 因此明确：

* `approve` 默认不产出 `materialized-handoff.json`
* `materialized-handoff.json` 只保留给 human 或特殊 consumer 介入场景

## 15.4 方案 D：做成“所有 gate 的超级业务审查中枢”

不选原因：

* 会把 external gate 重新做成重型中心；
* 会让治理层重新侵入业务语义；
* 与 ADR-004 提倡的治理集中但业务边界清晰相冲突。

## 15.5 方案 E：两个会话彼此直接调用

不选原因：

* 会让耦合重新升高；
* 审计链不稳定；
* 不利于文件系统级观测与回放；
* 违背 ADR-003 的对象化 handoff 路线。

## 15.6 方案 F：让 artifact 目录状态隐式代表 gate 结果

不选原因：

* proposal / decision / materialization 边界会重新消失；
* 难以表达 revise、retry、handoff 等治理语义；
* 违背 ADR-003 “状态推进必须有 evidence 或 decision 支撑”的原则。

---

# 16. 实施优先级

## 16.1 P0：模型冻结

优先冻结以下对象与语义：

* `gate-decision.json`
* `materialized-ssot.json`
* `materialized-handoff.json`
* `materialized-job.json`
* `run-closure.json`
* `revision-request.json`
* `approve / revise / retry / handoff / reject` decision model
* `gate-ready` 作为 gate loop 唯一正式消费入口

## 16.2 P1：先在 `raw-to-src` 链路打通

第一条落地链路建议为：

* `raw-to-src -> ll-gate-decision-materializer -> src-to-epic`

要求至少覆盖：

* 一次 approve 后 formal SRC 落盘
* 一次 formal SRC 作为 `src-to-epic` 输入被消费
* 一次 revise 闭环
* 一次 retry 闭环
* 一次 handoff 到 human-review
* 一次 reject 结案

## 16.3 P1.5：补 Gate Input Job 与 Queue 规范

补齐：

* `gate-ready` job schema
* queue naming 与状态迁移
* run closure 与 lineage 聚合视图

## 16.4 P2：推广到 L2 全链

将同一 external gate 模式扩展到：

* `src-to-epic`
* `epic-to-feat`
* 其他 governed skill

---

# 17. 结果与后果

## 17.1 正面结果

采用本 ADR 后，LL 将获得以下收益：

* skill-first 架构在最后一跳也保持一致，不再出现特例黑盒；
* 正式 `ssot/src` 对象的落盘时机被明确固定在 gate 批准之后；
* decision、handoff、job、run closure 的职责边界正式冻结；
* execution loop 与 gate loop 的双主会话模型更清晰；
* `raw-to-src`、`src-to-epic`、`epic-to-feat` 可复用同一 gate consumer；
* `src-to-epic` 可以稳定消费 formal SSOT SRC，而不是 candidate package；
* approve 与 handoff 的语义边界更清楚，不再把自动推进误写成 handoff；
* proposal 与 materialized object 的分层可审计；
* revise 与 retry 被正式区分，最小修补闭环更稳定；
* human review 被收敛为显式 consumer，而不是口头接力。

## 17.2 负面结果

采用本 ADR 也会带来：

* runtime 对象增多；
* queue / schema / closure 纪律要求更高；
* 初期需要补齐更多模板与校验；
* 对 Gate Loop 的 contract 完整性要求更高。

但这些复杂度属于：

## **对原本已存在的治理职责进行显式化，而不是新增一层无关平台复杂度。**

---

# 18. 最终结论

ADR-006 正式规定：

## **External Gate 不再作为业务 skill 的附属脚本存在，而应收敛为独立 skill 化的 decision 与 materialization 层。**

它消费的是：

* candidate package
* evidence
* proposal
* budget
* run state

它产出的是：

* `gate-decision.json`
* `materialized-ssot.json`
* `materialized-handoff.json`
* `materialized-job.json`
* `run-closure.json`

其本质取舍是：

* 用独立 governed skill 代替散落 gate 脚本；
* 用 gate 后 formal SSOT materialization 代替 skill 内提前 freeze；
* 用互斥单选 decision 代替多 flag 审批；
* 用 materialized object 代替 proposal 直入队列；
* 用双 consumer + 文件状态机 代替会话间直接调用；
* 用 run 立即结案 + 新 run 继承 lineage，代替长期改写同一个 run。

本 ADR 通过后，LL 后续相关设计应以本决策为准，不再把 gate 理解为某个 skill 的尾部补丁逻辑，而应视为：

## **LL skill-first 主链中的正式裁决与物化层。**
