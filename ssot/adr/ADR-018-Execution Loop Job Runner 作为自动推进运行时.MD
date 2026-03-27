# ADR-018：Execution Loop Job Runner 作为自动推进运行时

* 状态：Accepted
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x 主链自动推进运行时
* 相关 ADR：ADR-001、ADR-003、ADR-005、ADR-006、ADR-009

---

# 1. 背景

在 ADR-001 中，LL 已正式冻结：

* 双会话双队列闭环模型；
* Execution Loop 消费自动执行队列；
* Human Gate Loop 负责人工治理闭环；
* 不优先建设重型调度器。

在 ADR-003 中，LL 已冻结：

* `artifact / job / handoff / gate result / evidence` 的对象分层；
* 文件化 handoff runtime 作为正式流转治理机制；
* 下游应消费结构化流转对象，而不是目录猜测。

在 ADR-006 与 ADR-009 中，LL 又进一步冻结：

* external gate 负责 decision、materialization、dispatch 与 closure；
* gate runtime 采用 CLI-first + file-based runtime 承载；
* `materialized-job` 是 gate 批准后进入下一阶段自动推进的正式对象。

当前仓库已经具备以下能力：

* 上游 workflow 可以产出 freeze-ready package；
* gate 可以执行 `submit-handoff -> decide -> materialize -> dispatch -> close-run`；
* formal artifact 可以通过 `publish-formal` 正式落盘并进入 registry；
* `dispatch` 可以物化 `materialized-job`。

但当前仍缺少一个正式 consumer 去自动消费 `artifacts/jobs/ready/` 中的 job，并把它推进到下游 workflow。

这导致系统虽然在架构目标上是“双会话双队列”，但实际运行上仍表现为：

* 会话 1：Producer，产 package；
* 会话 2：Gate，审批与 formalize；
* 会话 3：Executor，人工或 agent 显式读取 job/formal ref 并继续执行。

换句话说，LL 目前已经有：

* queue object
* job object
* gate object
* dispatch object

但还没有：

* 自动消费 ready job 的 execution runner

这使 `dispatch` 目前只完成了“把任务写成可执行对象”，却没有完成“让系统自动推进到下一条 workflow”。

因此，需要一个新的 ADR 来冻结：

## **Execution Loop Job Runner 应如何作为自动推进运行时存在，并把当前三会话过渡形态收敛回 ADR-001 的目标双会话模型。**

---

# 2. 问题陈述

当前 LL 需要解决的核心问题不是“再补一个脚本”，而是：

* 谁来消费 `materialized-job`；
* 谁来把 ready job claim 成 running；
* 谁来根据 job 路由到正确的下游 workflow；
* 谁来把执行结果回写为 `done / failed / waiting-human / deadletter`；
* 谁来保证 execution loop 不重新越权承担 gate 职责；
* 谁来把“第二会话 dispatch”与“下游自动推进”之间的缺口补齐。

如果这一层不冻结，会出现以下结构性问题：

## 2.1 架构偏差固化

ADR-001 定义的是“双会话双队列”。

但如果长期依赖“第三会话人工接力”，则三会话过渡形态会被误当成正式架构，导致 ADR-001 的目标无法收敛落地。

## 2.2 dispatch 语义不完整

当前 `dispatch` 只写出 job 文件。

如果没有 runner，`dispatch` 实际上只是“生成待办说明”，而不是“把任务送入执行环”。

## 2.3 queue 失去执行意义

如果 ready job 不被正式 consumer 消费，那么：

* `jobs/ready/`
* `jobs/running/`
* `jobs/done/`
* `jobs/failed/`

这些目录会退化为静态记录，而不是运行时状态机。

## 2.4 gate 与 execution 边界持续模糊

如果下游推进仍靠 agent 自己读 formal artifact 再手工执行，就会不断出现：

* 是 gate 会话继续执行，还是另一个 agent 执行；
* 是读取 handoff 继续跑，还是直接指路径调用下游；
* 是谁负责回写 running/done/failed。

这会让运行时职责始终悬空。

## 2.5 无法建立统一恢复协议

没有正式 runner，就无法稳定定义：

* claim 超时怎么办；
* job 执行失败写到哪里；
* 哪类失败转 waiting-human；
* 哪类失败进入 retry；
* 哪类失败进入 deadletter。

因此，需要正式冻结一个新的运行时组件：

## **Execution Loop Job Runner**

它不是业务 skill，而是消费标准 job object、推进下游 workflow 的自动执行 consumer。

---

# 3. 决策

## 3.1 决策摘要

LL v0.x 正式采用：

## **Execution Loop Job Runner**

作为 `artifacts/jobs/ready/` 的自动消费运行时。

该 runner 的职责固定为：

1. 扫描 ready job；
2. claim job；
3. 将 job 迁移到 running；
4. 根据 job 的 `target_skill` 与输入引用路由到正确 workflow；
5. 调用下游 workflow；
6. 回写 `done / failed / waiting-human / deadletter`；
7. 保留完整执行证据与状态迁移记录。

该 runner 的边界也同时冻结为：

1. runner 不负责 gate approve/reject；
2. runner 不替代 `publish-formal`；
3. runner 不绕过 `validate-admission`；
4. runner 不猜测输入，不扫描目录推断业务对象；
5. runner 只消费结构化 job object 与 formal/handoff refs；
6. runner 是自动执行 consumer，不是业务语义决策者。

---

## 3.2 正式定义

Execution Loop Job Runner 在 LL v0.x 中被定义为：

* 一个 CLI-first + file-based runtime consumer；
* 一个标准 execution loop 的自动化承载层；
* 一个对 `jobs/ready/` 具有单消费者 claim 语义的 job 执行器；
* 一个以标准 job schema、状态迁移和 evidence writeback 为基础的流程推进组件。

它不是：

* 业务 skill；
* gate runtime；
* registry authority；
* formalization authority；
* 人工审批替代物；
* 新的重型调度平台。

因此，本 ADR 的核心取舍是：

## **把当前第三会话的“人工执行接力”收编为正式 Execution Loop runtime，而不是让三会话模型长期成为事实标准。**

---

# 4. 与既有 ADR 的关系

## 4.1 与 ADR-001 的关系

ADR-001 冻结的是目标执行架构：

* 双会话双队列闭环；
* Execution Loop 自动推进；
* Human Gate Loop 负责人工治理。

ADR-018 不是替代 ADR-001，而是补足 ADR-001 中尚未具体冻结的 Execution Loop 实现接缝。

换句话说：

* ADR-001 回答“系统为什么应是双会话双队列”
* ADR-018 回答“Execution Loop 具体如何落地成 job runner”

## 4.2 与 ADR-003 的关系

ADR-003 冻结了文件化 handoff runtime 与 job/handoff/gate/evidence 的分层。

ADR-018 进一步规定：

* runner 只能消费这些正式对象；
* runner 不得通过目录猜测业务输入；
* runner 的状态迁移也必须是正式文件对象的一部分。

## 4.3 与 ADR-005 的关系

ADR-005 冻结了 Artifact IO Gateway、Registry、Path Policy。

ADR-018 规定：

* runner 可以消费 formal artifact ref；
* runner 不能直接把 candidate 文件当成正式输入；
* runner 不得绕过 Gateway/Registry/Admission 纪律。

## 4.4 与 ADR-006 的关系

ADR-006 冻结了 external gate 的 decision/materialization/dispatch 职责。

ADR-018 规定：

* gate 负责 dispatch
* runner 负责 consume dispatched job

两者边界必须清晰：

* gate 决定“是否允许自动推进”
* runner 负责“已经允许后如何自动执行”

## 4.5 与 ADR-009 的关系

ADR-009 冻结了 CLI-first + file-based runtime 承载。

ADR-018 沿用该承载路线，不引入先行服务化依赖。

因此，runner 的推荐形态是：

* CLI 命令
* watcher / loop consumer
* 文件状态迁移

而不是：

* 必须先做 daemon + DB + HTTP service

---

# 5. Job Runner 的职责边界

## 5.1 runner 必须负责的事情

runner 至少必须负责：

1. 读取 `artifacts/jobs/ready/` 中的结构化 job；
2. 对单个 job 做 claim；
3. 将 job 迁移到 `running`；
4. 解析 `job_type`、`target_skill`、`input_refs`、`gate_decision_ref`、`formal_artifact_ref` 等输入；
5. 路由到正确的下游 workflow 入口；
6. 执行 workflow；
7. 写回 result summary、run linkage、job outcome；
8. 将 job 移入 `done / failed / deadletter / waiting-human`；
9. 记录最小执行证据。

## 5.2 runner 不得负责的事情

runner 不得负责：

1. 自判 gate 通过；
2. 代替 human 审批；
3. 直接 `publish-formal` 一个未被 gate 批准的对象；
4. 绕过 admission 直接读取 candidate layer；
5. 把一个 skill 的业务语义重新解释成别的流程；
6. 静默修改 job intent。

## 5.3 runner 与业务 skill 的边界

业务 skill 负责：

* 消费标准输入；
* 生成 candidate 或 freeze-ready package；
* 产出 evidence、report、handoff proposal、job proposal。

runner 负责：

* 把标准 job 路由给正确 skill；
* 承担执行会话自动推进职责；
* 将 skill 执行结果写回运行时状态。

因此：

* skill 是执行单元
* runner 是执行调度 consumer

两者不是同一个层次的对象。

---

# 6. Job 模型决策

ADR-018 要求 runner 只消费正式 job object。

最小 job 至少应包含：

* `job_id`
* `job_type`
* `status`
* `queue_path`
* `target_skill`
* `source_run_id`
* `gate_decision_ref`
* `input_refs`
* `authoritative_input_ref`
* `formal_ref` 或 `handoff_ref`
* `source_artifacts`（兼容镜像字段，可选）
* `retry_count`
* `retry_budget`
* `created_at`

其中：

* `target_skill` 用于决定路由到哪个 workflow；
* `source_run_id` 是当前 gate/materialization run 的稳定追溯主键；
* `input_refs` 是 runner 可消费的正式输入集合；
* `authoritative_input_ref` 标明 runner 首选消费的主输入；
* `formal_ref` 用于消费 formal layer 输入；
* `handoff_ref` 用于承接 gate materialized handoff；
* `source_artifacts` 仅用于兼容已有 writer/reader，不得替代 `input_refs` 与 `authoritative_input_ref`；
* `gate_decision_ref` 用于追溯该 job 的治理来源。

为兼容早期 ADR 草案中的命名，`source_run_ref` 与 `formal_artifact_ref` 在 v0.x runtime 中统一收敛为：

* `source_run_id`
* `formal_ref`

runner 不得消费：

* 裸 package 路径猜测；
* 任意自然语言说明；
* 没有 schema 的临时文件。

---

# 7. 状态迁移决策

runner 至少冻结以下 job 状态机：

* `ready`
* `claimed`
* `running`
* `done`
* `failed`
* `waiting-human`
* `deadletter`

## 7.1 标准迁移

标准迁移顺序为：

1. `ready -> claimed`
2. `claimed -> running`
3. `running -> done`

## 7.2 失败迁移

失败迁移为：

1. `running -> failed`
2. `failed -> ready`  
   仅当通过 `retry-reentry` 动作且 retry policy 允许
3. `failed -> waiting-human`  
   当需要人工判定
4. `failed -> deadletter`  
   当超出 retry budget 或出现不可恢复错误

## 7.3 claim 约束

runner 必须提供最小 claim 语义：

* 同一个 job 在同一时刻只能被一个 runner claim；
* claim 后必须留下结构化 lease/claim 痕迹；
* 超时未完成的 running job 必须可恢复。

v0.x 阶段不要求复杂分布式锁，但至少要保证：

* 单工作区下不存在两个 consumer 同时执行同一个 job

---

# 8. 路由决策

runner 的核心职责之一是路由。

路由规则冻结如下：

## 8.1 路由依据

runner 只能基于 job 字段路由：

* `target_skill`
* `job_type`
* `formal_artifact_ref`
* `handoff_ref`

不允许基于：

* 目录名猜测
* artifact slug 模糊匹配
* 会话记忆
* 自然语言说明

## 8.2 路由结果

runner 必须能够把 job 路由到至少以下 workflow 入口：

* `raw-to-src`
* `src-to-epic`
* `epic-to-feat`
* `feat-to-tech`
* `tech-to-impl`
* `feat-to-testset`

v0.x 允许先实现白名单映射，而不是动态插件发现。

## 8.3 formal 优先

如果 job 提供 formal artifact ref，则 runner 优先消费 formal ref。

如果 job 只提供 handoff，则 runner 通过 handoff 指向的正式对象消费输入。

runner 不应回退到直接扫描 candidate package 目录。

---

# 9. 失败、重试与死信

ADR-018 正式要求 runner 具备最小恢复能力。

## 9.1 可重试失败

以下类型失败可进入 retry：

* 子进程异常退出
* 临时文件冲突
* 可恢复的依赖错误
* 明确标记为 retryable 的 workflow 失败

## 9.2 不可重试失败

以下类型失败默认不得自动重试：

* admission denied
* formal ref 缺失
* target skill 未注册
* job schema 非法
* gate decision 不允许执行

这类失败应直接进入：

* `failed`
* 或 `waiting-human`
* 或 `deadletter`

## 9.3 死信规则

以下情形进入 deadletter：

* retry 次数超过预算；
* 连续失败且无人工接管路径；
* job 缺少最低必需字段；
* runner 无法确定合法恢复策略。

进入 deadletter 后必须保留：

* 原始 job
* 最后一次错误
* 失败上下文
* lineage 指针

---

# 10. Evidence 与观测

runner 必须留下最小 evidence：

* claim 时间
* runner identity
* target skill
* 输入引用
* 调用命令
* exit code
* 结果状态

同时 runner 至少应支持导出以下观测：

* ready backlog
* running jobs
* aging jobs
* failed jobs
* deadletters
* waiting-human jobs

这些观测可以是：

* CLI scan 输出
* 派生 report
* 目录视图

但不得变成新的真相源。

---

# 11. 技术承载决策

ADR-018 明确选择：

## **CLI-first watcher / consumer**

作为 v0.x 的默认承载形态。

推荐形态包括：

* `ll loop run-execution`
* `ll job claim`
* `ll job run`
* `ll job complete`
* `ll job fail`

也允许先以：

* 单个 Python runner
* 单消费者循环
* 定时扫描 ready queue

的方式落地。

当前不要求：

* 独立 daemon
* 数据库状态机
* HTTP API
* UI 控制台

---

# 12. 明确不选的方案

## 12.1 方案 A：继续保留第三会话人工接力

不选原因：

* 会把过渡态固化；
* dispatch 无法真正构成自动推进；
* ADR-001 目标双会话无法收敛。

## 12.2 方案 B：让 gate 会话继续直接调用下游

不选原因：

* gate 与 execution 重新混层；
* dispatch/job 语义被绕过；
* 无法形成统一 execution loop。

## 12.3 方案 C：每个 skill 自己带一个 job consumer

不选原因：

* 会产生多套局部 runner；
* 状态迁移、retry、deadletter 规则会漂移；
* 与统一 execution loop 相冲突。

## 12.4 方案 D：直接跳到服务化 orchestrator

不选原因：

* 超出 v0.x 当前目标；
* 会把复杂度重新推回平台工程；
* 与 ADR-009 的 CLI-first 承载路线不一致。

---

# 13. 实施优先级

## 13.1 P0：模型冻结

必须先冻结：

* runner 职责边界
* job schema
* claim 语义
* 状态迁移
* retry / deadletter 最小规则

## 13.2 P1：单消费者最小实现

优先交付：

* 单工作区单消费者 runner
* ready -> running -> done/failed
* target skill 白名单路由
* 最小 evidence writeback

## 13.3 P1.5：接入主链

至少打通：

* `raw-to-src -> gate dispatch -> src-to-epic`
* `src-to-epic -> gate dispatch -> epic-to-feat`

使第二会话 dispatch 后，不再需要第三会话人工启动下游。

## 13.4 P2：恢复与观测补强

补齐：

* retry budget
* deadletter
* aging job scan
* waiting-human 回流
* claim timeout recovery

---

# 14. 成功判定标准

ADR-018 落地成功的标志不是“多了一个 runner 脚本”，而是：

1. gate dispatch 后，系统能自动消费 ready job；
2. 不再需要第三会话人工显式启动下游 workflow；
3. ready/running/done/failed/deadletter 状态具有真实运行意义；
4. runner 不越权承担 gate、formal publish、admission 职责；
5. 主链至少两段下游推进可自动闭环；
6. 失败路径可追溯，可重试，可转 waiting-human 或 deadletter。

---

# 15. 结果与后果

## 15.1 正面结果

采用本 ADR 后，LL 将获得：

* ADR-001 双会话目标的真实落地；
* `dispatch` 从“写 job”升级为“把任务送入执行环”；
* queue 目录重新具有运行时意义；
* gate 与 execution 边界更加清晰；
* 当前三会话过渡模型可逐步收敛回正式双会话模型。

## 15.2 负面结果

采用本 ADR 也会带来：

* 运行时状态纪律要求提升；
* claim / timeout / retry 规则需要严格实现；
* 错误恢复与死信处理需要额外测试；
* 初期只能先支持单消费者，不适合高并发。

---

# 16. 后续动作

## 立即动作

1. 基于本 ADR 冻结 `job-runner` 最小 contract；
2. 定稿 ready/running/done/failed/deadletter 状态语义；
3. 设计 `target_skill -> workflow entrypoint` 映射表；
4. 设计 claim / lease 最小协议；
5. 先在 `raw-to-src -> src-to-epic` 链路打通。

## 下一阶段动作

1. 补 retry / deadletter / waiting-human 回流；
2. 补 runner evidence 与 queue status 视图；
3. 将同一 runner 推广到 `epic-to-feat`、`feat-to-tech` 等链路；
4. 再评估是否需要 watcher/daemon 常驻化。

---

# 17. 最终结论

ADR-018 正式提出：

## **Execution Loop Job Runner 应作为 LL v0.x 的自动推进运行时存在。**

它的本质作用是：

* 把当前第三会话的人工执行接力收编为正式 runtime；
* 让 `dispatch` 真正连接到下游执行；
* 让 ADR-001 的双会话双队列架构从过渡态回到目标态。

其核心取舍是：

* 用标准 runner 消费 ready job；
* 用结构化 job 状态迁移承载执行过程；
* 用 file runtime 而不是重型平台承载自动推进；
* 用清晰边界保证 gate、formal、admission 与 execution 不重新混层。

本 ADR 通过后，LL 后续设计不应再默认接受“三会话长期共存”作为正式架构，而应以 `job-runner` 的落地为标志，把系统收敛回：

## **双会话双队列 + external gate + automatic execution loop**

