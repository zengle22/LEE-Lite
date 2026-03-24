下面是可直接落库的正式版本。我把它定位为：

* **ADR-001 的支撑性 ADR**
* 不重复定义“双会话双队列闭环模型”本身
* 专门解决该模型下 **文件化 handoff 如何承载流转、门禁、证据、观测与恢复**

---

# ADR-003：LL 在双会话双队列闭环模型下采用文件化 Handoff Runtime 作为流转治理机制

* 状态：Accepted
* 日期：2026-03-20
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x
* 相关 ADR：ADR-001

---

# 1. 背景

在 ADR-001 中，LL 已正式确定采用 **双会话双队列闭环模型** 作为 v0.1 的执行架构。
该决策明确了以下基础事实：

1. LL 采用 **skill-first** 路线，而不是优先建设独立调度平台。
2. 执行推进由 **Execution Loop** 与 **Human Gate Loop** 两个长期运行会话协同完成。
3. 自动推进与人工审批通过 **文件化 job / gate / decision / artifact / evidence / report** 闭环。
4. human gate 必须外置，不能由 skill 内部等待，也不能由 LLM 自判通过。
5. runtime 临时态不进入工程主树，工程目录只保留正式产物、审计结果与流程真相。

ADR-001 解决的是 **“LL 用什么执行架构”** 的问题。
但在该架构落地过程中，仍然存在一个尚未正式冻结的关键问题：

> 在双会话双队列闭环模型中，文件不仅是产物存储形式，也同时承担消息、状态、证据、路由与观测职责。
> 那么，skill 之间的 handoff 应如何设计，才能在不引入重型 runtime 的前提下，稳定支撑流转、门禁、证据、修复与观测？

如果该问题不被正式决策，会很快出现以下风险：

* artifact、job、gate、evidence 混放，职责边界模糊；
* 文件存在即被误认为“完成”，状态语义失真；
* 下游 skill 依赖隐式上下文，handoff 不稳定；
* gate 结果不能结构化承载，无法自动回流；
* repair 只能整单重跑，运行时间与调试成本迅速膨胀；
* 运行状态只能靠人工看目录猜测，系统可观测性迅速下降。

因此，需要在 ADR-001 的基础上，进一步冻结一套 **文件化 handoff runtime 治理机制**，作为双会话双队列闭环模型的正式支撑方案。

---

# 2. 问题陈述

LL 当前要解决的，不是再建设一个独立 orchestration platform，而是：

* 如何让 skill 之间通过文件稳定 handoff；
* 如何区分业务产物、流程指令、门禁结论与审计证据；
* 如何保证每一步都是“先生成、再校验、再最小修补、再流转”；
* 如何让执行会话与监督会话职责清晰，不出现“又做又判”；
* 如何让 job、artifact、gate、handoff、evidence 在工程目录中保持可追溯、可恢复、可观测；
* 如何在不引入数据库、事件总线、复杂状态机平台的前提下，提供最小但完整的 runtime 治理能力。

如果缺少正式的 handoff runtime 设计，ADR-001 所定义的双会话双队列模型虽然能以讨论形态成立，但在实现层面会出现以下结构性缺口：

1. **流转缺口**
   文件可生成，但下游 skill 无法可靠判断“该接什么、何时接、以什么上下文接”。

2. **门禁缺口**
   文件可审，但 gate 结论若不对象化，就无法稳定进入下一步决策。

3. **证据缺口**
   结果可能看起来合理，但无法回答“为什么通过”“基于哪些检查通过”。

4. **修复缺口**
   失败后若没有标准 patch/repair 机制，只能大面积重跑，严重拖慢迭代。

5. **观测缺口**
   如果状态只是散落在目录中的隐含信息，系统将很快失去 legibility。

因此，需要一份正式 ADR，定义 LL 在 ADR-001 架构下的 **文件化 handoff runtime 标准**。

---

# 3. 决策

## 3.1 决策摘要

LL 在 ADR-001 定义的 **双会话双队列闭环模型** 之上，正式采用：

## **文件化 Handoff Runtime**

作为 skill 流转与治理机制。

该 runtime 不构建独立调度器、状态数据库或事件总线，而是以 **job / artifact / handoff / gate result / evidence bundle / patch instruction** 等结构化文件对象为基础，通过目录、状态迁移规则、双队列消费约束与审计视图，实现以下能力：

* skill 间稳定流转；
* gate 外置与回流；
* 证据绑定状态推进；
* 最小修补优先；
* 执行与监督职责分离；
* 文件系统级可观测与可恢复。

该决策是 ADR-001 的支持性决策，而不是替代 ADR-001。
ADR-001 负责定义执行架构；ADR-003 负责定义该架构中的 **文件化 handoff 治理机制**。

---

## 3.2 正式定义

LL v0.x 在 ADR-001 架构下，正式定义以下 handoff runtime 原则：

1. **Artifact 与 Job 强制分离**

   * artifact 是业务产物与正式真相；
   * job 是流程推进指令与运行实例；
   * job 不承载业务正文；
   * artifact 不承担流程控制职责。

2. **Handoff 必须对象化**

   * skill 间流转不得依赖隐式上下文；
   * 每次向下游流转都必须生成结构化 handoff 文件；
   * handoff 文件负责声明输入、约束、gate 结论与下一步目标。

3. **状态推进必须有证据支撑**

   * 任一对象状态推进都必须有对应 evidence 或 decision 支撑；
   * 不允许仅凭自然语言说明或目录存在性推进状态。

4. **每步必须遵循“生成 → 冻结 → 校验 → 修补/通过 → 流转”**

   * 不允许未冻结产物直接被消费；
   * 不允许未通过 gate 的产物进入下游；
   * repair 优先采用最小修补，而不是整单重跑。

5. **监督与执行分离**

   * Execution Loop 负责生成与修补；
   * Human Gate Loop / Supervisor 路径负责校验、裁决、通知与回流；
   * 监督侧不得直接改写业务 artifact。

6. **文件系统承担最小 runtime 职责**

   * 目录不仅保存产物，也保存流程消息、gate 结论、证据包与观测视图；
   * 但不引入独立数据库、事件总线或重型 orchestrator。

7. **观测必须由 runtime 文件直接导出**

   * 当前有哪些 job；
   * 卡在哪一步；
   * 哪些 gate 失败；
   * 哪些队列积压；
   * 哪些 job 进入 deadletter；
   * 必须能从文件系统直接还原。

---

# 4. 设计目标

ADR-003 所定义的文件化 handoff runtime，必须同时满足以下目标。

## 4.1 流转目标

让上游 skill 的输出能够以稳定、显式、可审计的方式交给下游 skill，而不是依赖执行器临时拼接上下文。

## 4.2 门禁目标

让 gate 不再只是审阅动作，而成为可结构化消费、可触发后续动作的正式对象。

## 4.3 证据目标

让“通过/失败/修补/升级”都有可追溯依据，而不是靠会话记忆或人类脑内上下文。

## 4.4 修复目标

让失败优先进入局部 patch / repair 路径，减少整单重跑和长链路回退。

## 4.5 观测目标

让系统外部能够直接看到 runtime 当前健康状况，而不必深入会话内部。

## 4.6 扩展目标

在保持轻量的前提下，为后续 L2/L1 长链、更多 gate、更多 skill 提供统一接缝。

---

# 5. 核心对象模型

ADR-003 冻结以下对象分层。

## 5.1 Artifact

Artifact 是业务产物与正式真相载体。

职责：

* 承载 src / epic / feat / task 等业务正文；
* 记录来源、版本、引用、校验信息；
* 作为 lineage 与审计链的核心节点。

约束：

* artifact 不承载 queue 状态；
* artifact 不直接等同于 job；
* artifact 生成后必须先冻结，再进入 gate。

---

## 5.2 Job

Job 是流程推进实例。

职责：

* 描述当前执行目标；
* 指向输入 artifact；
* 指示当前 step、当前队列、当前状态；
* 作为 runtime 级别的可追踪流程单元。

约束：

* job 不保存业务正文；
* job 只保存结构化流程信息；
* job 必须拥有唯一 ID 与显式状态迁移。

---

## 5.3 Handoff

Handoff 是 skill 之间的显式交接单元。

职责：

* 声明从哪个 step 流转到哪个 skill；
* 指向 primary artifact 与 supporting artifact；
* 绑定 gate 结果；
* 声明 required context、约束与下游预期产出。

约束：

* 没有 handoff 文件，不视为正式流转；
* 下游 skill 不应猜测输入；
* handoff 是 skill 接缝，不是 artifact 替代品。

---

## 5.4 Gate Result

Gate Result 是正式门禁结论。

职责：

* 记录 pass / fail / reject / escalate；
* 记录失败原因、严重性与建议动作；
* 作为是否允许流转、是否要求 patch 的正式依据。

约束：

* gate result 必须结构化；
* 不允许以普通自然语言评论替代 gate result；
* human gate 与 automatic validation 均应输出结构化 gate/result。

---

## 5.5 Evidence Bundle

Evidence Bundle 是状态推进所需的证据集合。

职责：

* 聚合 schema check、semantic check、review、diff、repair 结果；
* 证明当前对象为何可通过、为何被打回、为何需要升级；
* 为审计、回放与后续复盘提供依据。

约束：

* 没有 evidence 的状态推进不合法；
* evidence 可分层，但必须可定位；
* evidence 不等于 report，应是可归档的证据集合。

---

## 5.6 Patch Instruction

Patch Instruction 是监督侧对执行侧发出的最小修补指令。

职责：

* 定义 patch 原因、修补范围、约束与期望 delta；
* 避免执行侧整篇重写或越界扩展；
* 将修补从自由发挥变为结构化操作。

约束：

* patch 默认以 minimal fix 为优先；
* patch 超阈值才允许升级为局部重生成或 step rerun；
* patch instruction 必须可追踪。

---

# 6. 状态机决策

ADR-003 不引入重型 runtime 状态机引擎，但正式冻结最小状态语义。

## 6.1 Artifact 状态

artifact 状态定义为：

* `draft`
* `frozen`
* `validating`
* `validated`
* `rejected`
* `handed-off`
* `consumed`
* `archived`

约束：

1. `draft` 不允许被下游消费。
2. `frozen` 后方可进入验证。
3. 只有 `validated` 的 artifact 才允许进入 handoff。
4. 被打回的 artifact 必须进入 patch/repair，而不是伪装成新通过版本。
5. `handed-off` 与 `consumed` 必须区分，避免“已发送”与“已接收”混淆。

---

## 6.2 Job 状态

job 状态定义为：

* `created`
* `ready`
* `running`
* `waiting-validation`
* `waiting-patch`
* `waiting-human`
* `waiting-handoff`
* `waiting-downstream`
* `done`
* `failed`
* `deadlettered`

约束：

1. job 必须显式迁移，不允许隐式跳转。
2. job 当前状态必须可由文件系统还原。
3. `waiting-human` 必须由 gate request / decision 闭环驱动。
4. `deadlettered` 必须保留完整失败上下文，禁止直接消失。

---

## 6.3 Step Attempt 状态

为支持“每一步生成后校验，再最小修补”，step 级别定义 attempt 语义：

* `created`
* `leased`
* `running`
* `produced`
* `gated`
* `patched`
* `passed`
* `failed`

该语义主要用于：

* 支撑 repair / revalidate / retry；
* 区分“这一步失败了”与“整个 job 失败了”；
* 保持最小修补优先的治理策略。

---

# 7. 目录结构决策

ADR-003 在 ADR-001 的目录基础上，进一步冻结 runtime 相关对象分层。

```text
ll/
├─ artifacts/
│  ├─ src/
│  ├─ epic/
│  ├─ feat/
│  ├─ task/
│  ├─ jobs/
│  │  ├─ ready/
│  │  ├─ running/
│  │  ├─ done/
│  │  ├─ failed/
│  │  └─ deadletter/
│  ├─ handoffs/
│  ├─ gates/
│  │  ├─ requests/
│  │  ├─ decisions/
│  │  ├─ results/
│  │  ├─ approved/
│  │  └─ rejected/
│  ├─ human-queue/
│  │  ├─ waiting-human/
│  │  ├─ approved/
│  │  └─ rejected/
│  ├─ evidence/
│  ├─ reports/
│  ├─ lineage/
│  ├─ views/
│  └─ locks/
```

其中：

* `src/`、`epic/`、`feat/`、`task/`：业务产物层
* `jobs/`：流程实例层
* `handoffs/`：skill 交接层
* `gates/`：门禁对象层
* `human-queue/`：人工处理层
* `evidence/`、`reports/`、`lineage/`：治理与审计层
* `views/`：观测派生层
* `locks/`：最小并发保护层

---

# 8. 职责边界决策

## 8.1 Execution Loop 职责

Execution Loop 负责：

* 消费 ready job；
* 读取 handoff；
* 调用 skill；
* 生成 artifact draft；
* 冻结 artifact；
* 提交 validation / gate；
* 根据 patch instruction 执行最小修补；
* 在通过后生成新的 handoff 或下游 job。

Execution Loop 不负责：

* 自判 human gate；
* 越权改写 gate result；
* 直接裁定最终通过；
* 以自然语言说明替代结构化结果。

---

## 8.2 Human Gate Loop / Supervisor 职责

Human Gate Loop / Supervisor 路径负责：

* 消费 waiting-human 项；
* 监控 gate request；
* 提示人类处理；
* 生成 decision 文件；
* 输出 gate result；
* 生成 patch instruction 或升级结论。

Human Gate Loop / Supervisor 不负责：

* 直接编写业务 artifact；
* 绕过 decision 推进流程；
* 代替执行器产出业务正文。

---

## 8.3 Human 职责

人类仅在以下场景介入：

* 关键 gate 审批；
* 需求边界冲突裁决；
* 连续 patch 或 rerun 超阈值；
* SSOT 发生冲突；
* 自动校验无法给出可执行修补结论。

该边界保证人类参与治理，但不被拖入低价值手工接力。

---

# 9. 流转协议决策

ADR-003 冻结标准流转协议如下：

## 9.1 标准流转链

每一步标准流程为：

1. job 被 Execution Loop claim；
2. skill 读取输入与 required context；
3. 生成 artifact draft；
4. 冻结 artifact；
5. 写入初始 evidence；
6. 进入 validation / gate；
7. 若失败，则生成 gate result + patch instruction；
8. 执行侧按 patch instruction 做最小修补；
9. 重新校验；
10. 校验通过后生成 handoff；
11. 写入下游 ready job 或 human queue；
12. 更新当前 job 状态。

---

## 9.2 流转不变量

以下规则为硬约束：

1. 没有 handoff，不算正式流转。
2. 没有 gate result，不允许正式通过。
3. 没有 evidence，不允许推进状态。
4. 未冻结 artifact 不得被消费。
5. patch 优先，rerun 次之，整链回退最后。
6. 下游 skill 不应直接扫描上游目录猜输入。

---

# 10. 门禁与修补决策

## 10.1 三层 Gate

ADR-003 建议并冻结以下三层 gate 语义：

### Structural Gate

检查：

* schema 合法；
* 必填字段完整；
* 文件齐全；
* 引用存在；
* checksum 与 manifest 一致。

### Semantic Gate

检查：

* 是否忠实承接上游输入；
* 是否发生范围漂移；
* 是否遗漏关键信息；
* 是否违反当前 skill contract；
* 是否越权扩展内容。

### Transition Gate

检查：

* handoff 是否完整；
* required context 是否足够；
* 下游目标是否明确；
* 当前对象是否可被安全消费。

---

## 10.2 最小修补优先

ADR-003 正式规定，失败后的默认恢复顺序为：

1. **Minimal Patch**
2. **Local Regeneration**
3. **Step Rerun**
4. **Escalate / Human Review**
5. **Upstream Rollback**

禁止失败后默认整单重跑。

---

## 10.3 Patch 阈值

应至少定义：

* 单 gate 连续 patch 最大轮数；
* 单 step 最大 rerun 次数；
* 超阈值后的升级路径；
* 升级后是否允许人工裁决、回退或 deadletter。

该阈值由 recovery policy 配套细化，但 ADR-003 先冻结其必要性与优先顺序。

---

# 11. 观测与恢复决策

## 11.1 观测原则

LL 的 runtime 可观测性必须从文件系统直接导出，而不是依赖会话记忆或隐藏状态。

至少必须可直接回答：

1. 当前有哪些 active job；
2. 哪些 job 正在等待 human gate；
3. 哪些 gate 失败最多；
4. 哪些 skill patch 率过高；
5. 哪些队列积压；
6. 哪些 job 已 deadletter；
7. 哪些 artifact 正等待验证；
8. 哪些步骤反复重试未收敛。

---

## 11.2 观测视图

`artifacts/views/` 应作为派生视图层，至少支持：

* `job-index`
* `queue-status`
* `blocked-jobs`
* `failed-gates`
* `retry-backlog`
* `deadletters`
* `aging-jobs`

这些视图可以由扫描器、CLI 或 watcher 生成，但不得另建为独立真相源。

---

## 11.3 恢复原则

恢复分三层：

### 自动恢复

* lease 超时回收；
* queue 项回补；
* views 重建；
* 明显中断后的继续执行。

### 半自动恢复

* 从最后一个 validated artifact 重建 handoff；
* 从 patch 前快照恢复；
* 重投当前 step。

### 人工恢复

* 处理冲突 decision；
* 裁定是否回退；
* 处理死信与异常对象。

---

# 12. 技术取舍

## 12.1 选择该方案的原因

### 1. 直接支撑 ADR-001

ADR-001 定义了双会话双队列模型；ADR-003 为该模型补上正式接缝与治理对象。

### 2. 不引入重型平台

该方案把复杂度放在文件对象与治理协议上，而不是另造 runtime 平台。

### 3. 最符合当前阶段

当前阶段主目标仍是把需求链路跑稳，不是做大而全 orchestrator。

### 4. 更适合最小修补闭环

通过 patch instruction、gate result 与 handoff object 化，可以天然支持“先修补，再复核”。

### 5. 便于调试、审计与回放

文件天然可见，状态与证据都可回放，适合当前 LL 的工作方式。

---

## 12.2 明确不选的方案

### 方案 A：让 artifact 兼做 job

不选原因：

* 业务内容与流程状态耦合；
* 很快失去边界清晰性；
* 不利于复用、追踪与观测。

### 方案 B：只靠目录扫描，不定义 handoff 对象

不选原因：

* 下游只能猜输入；
* 流转不稳定；
* 无法表达约束、预期与 gate 结论。

### 方案 C：失败后默认整步重跑

不选原因：

* 成本过高；
* 调试效率过低；
* 无法支撑长链路稳定迭代。

### 方案 D：由执行器顺手做监督裁决

不选原因：

* 违背 ADR-001 的双会话分离原则；
* 容易形成“自己做、自己判、自己放行”的伪闭环。

---

# 13. 风险与不足

## 13.1 主要风险

### 1. 文件规范复杂度会上升

虽然不建设平台，但对象模型会变多，初期需要严格 schema 治理。

### 2. 对命名与状态纪律依赖很强

如果对象命名、状态迁移、目录边界执行不严，系统很快腐化。

### 3. 单机文件系统方案吞吐有限

该方案适合当前 v0.x 稳定优先阶段，不适合高并发高吞吐生产场景。

### 4. 观测质量依赖 views 生成质量

若不补齐 scanner / watcher / report，文件虽在，但 legibility 仍可能不足。

### 5. recovery policy 仍需后续细化

ADR-003 冻结了原则与对象，但 repair/requeue 细则仍需配套协议补强。

---

# 14. 实施优先级

## 14.1 P0：当前必须完成

### 模型冻结

* 冻结 artifact / job / handoff / gate result / evidence bundle / patch instruction 六类对象；
* 冻结对象边界与目录分层。

### 最小 schema

* 定稿各对象最小字段集；
* 定稿状态字段与基本状态迁移约束。

### 最小运行链

至少在以下链路中落地该 handoff runtime：

* `raw-to-src`
* `src-to-epic`
* `epic-to-feat`

### 最小 gate/patch 闭环

至少覆盖：

* 一次结构化 gate fail；
* 一次 minimal patch；
* 一次 revalidate 后继续 handoff。

---

## 14.2 P1：短期补强

* scanner / views 生成机制；
* patch threshold 与 rerun policy；
* deadletter 规范；
* handoff packet 模板；
* lineage 与 evidence bundle 标准化。

---

## 14.3 P2：中期扩展

* 更强 watcher/daemon；
* 更细粒度 lock/lease；
* 多 worker 兼容；
* 外部审批系统适配；
* 更完整的 runtime dashboard。

---

# 15. 路线图

## 阶段 0：决策冻结

输出：

* ADR-003 通过；
* 对象模型冻结；
* 目录分层冻结；
* 状态语义冻结。

## 阶段 1：最小 handoff 闭环

输出：

* handoff 文件模板；
* gate result 模板；
* patch instruction 模板；
* evidence bundle 模板；
* 首条链路跑通。

## 阶段 2：最小恢复闭环

输出：

* repair / revalidate / requeue 初版协议；
* retry 阈值；
* deadletter 处理规则。

## 阶段 3：最小观测闭环

输出：

* queue / job / deadletter 视图；
* aging / backlog 报表；
* patch 率与 gate failure 统计。

## 阶段 4：L2/L1 复用扩展

输出：

* L2 pipeline handoff 模板；
* 更长链路的标准接缝；
* 一套可复用的 skill handoff contract。

---

# 16. 成功判定标准

ADR-003 落地成功，不是看目录里多了多少文件，而是看以下能力是否成立：

1. 上游 skill 输出能通过结构化 handoff 稳定交给下游；
2. artifact、job、gate、evidence 边界清晰，不再混用；
3. 每一步都能做到“生成后校验，再最小修补，再流转”；
4. 失败后优先进入 patch/revalidate，而不是默认整单重跑；
5. 当前运行状态、积压、失败、死信可从文件系统直接还原；
6. 执行与监督职责没有重新混回单 agent 自判模型。

---

# 17. 结果与后果

## 17.1 正面结果

* 为 ADR-001 提供正式落地接缝；
* 让文件真正承担最小 runtime 职责；
* 强化 gate、evidence、repair 的可治理性；
* 降低长链路调试与恢复成本；
* 为后续 L2/L1 扩展提供统一 handoff 接口。

## 17.2 负面结果

* schema、命名与状态纪律要求更高；
* 文件数量会增加；
* 初期需要更多模板与校验工具支撑；
* 若不持续做 anti-entropy，仍可能出现格式漂移与对象污染。

---

# 18. 后续动作

## 立即动作

1. 基于 ADR-003 定稿 handoff runtime 对象 schema；
2. 建立 `handoffs/` 目录与模板；
3. 建立 gate result / patch instruction / evidence bundle 模板；
4. 在 `raw-to-src` 先完整跑通一条 handoff + gate + patch + revalidate 闭环；
5. 在 invariants 中补充 artifact/job/handoff/gate/evidence 的边界约束。

## 下一阶段动作

1. 补 scanner 与 views；
2. 补 retry / deadletter / recovery 规则；
3. 为 `src-to-epic` 与 `epic-to-feat` 复用该 handoff contract；
4. 评估是否需要更强 watcher，但仍不回退到独立调度器路线。

---

# 19. 最终结论

ADR-003 正式规定：

在 ADR-001 所定义的 **双会话双队列闭环模型** 下，LL 采用 **文件化 Handoff Runtime** 作为 skill 流转与治理机制。

该决策的核心不是再建设新的平台，而是将文件系统中的对象边界、状态推进、门禁结果、证据绑定、修补回路与观测视图正式化，使 ADR-001 的执行架构从“可以讨论的模型”变成“可以稳定落地的运行机制”。

其本质取舍是：

* 用 **结构化文件对象** 代替隐式上下文；
* 用 **handoff/gate/evidence/patch** 代替口头流转；
* 用 **最小修补闭环** 代替默认整单重跑；
* 用 **文件系统级观测** 代替隐藏状态；
* 在不引入独立调度平台的前提下，为 LL v0.x 提供最小但完整的 runtime 治理能力。

本 ADR 通过后，LL 后续相关设计应以本决策为准，不再将 handoff 视为普通文件传递问题，而应视为 **ADR-001 执行架构中的正式治理接缝**。

---

如果你愿意，我下一条可以继续把这份 ADR-003 再压一版，做成 **更像你 ADR-001 文风的“正式定稿版”**，把句式、层级和术语进一步统一。
