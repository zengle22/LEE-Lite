# ADR-009：Gate Runtime 采用 CLI-First File Runtime 承载

* 状态：Accepted
* 日期：2026-03-24
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x 主链治理运行时
* 相关 ADR：ADR-001、ADR-003、ADR-004、ADR-005、ADR-006

---

# 1. 背景

LL 当前已经冻结了以下前提：

* 主链采用 `skill-first + dual-session dual-queue` 闭环，而不是重型调度器。
* `job / handoff / gate decision / evidence / materialization object` 等结构化文件对象是正式流转载体。
* `Gateway / Policy / Registry / Auditor / External Gate` 需要组成统一治理主链。
* `Human Gate` 必须外置，不能回到 skill 内自判。

但在进入正式开发实现前，仍存在一个实现承载歧义：

> Gate runtime 以及与之协作的主链治理组件，究竟应优先实现为服务化前后端系统，还是优先实现为 CLI + file runtime？

如果这一点不先冻结，后续开发容易出现三种漂移：

* 一部分实现按 CLI/file runtime 落地，另一部分直接转向服务化 API；
* `Human Gate` 被误解为必须先建设页面，导致主链无法先跑通；
* runtime 载体的争论盖过对象边界与治理语义本身。

---

# 2. 决策

LL v0.x 正式冻结以下默认实现承载方案：

## **Gate Runtime 与主链治理运行时采用 CLI-first + file-based runtime 承载。**

具体含义是：

1. `External Gate`、`Gateway`、`Auditor`、相关 validator / materializer / dispatcher，优先实现为：
   * CLI 命令；
   * Python runtime helper；
   * 文件对象消费者；
   * loop / watcher 触发器。
2. 主链状态推进优先依赖结构化文件对象与目录状态迁移，而不是先建设 HTTP service、数据库驱动状态机或前后端平台。
3. `Human Gate` 在 v0.x 阶段优先通过文件对象、CLI 与 human gate loop 承载，不要求先冻结独立前端。
4. 如后续补充 UI、HTTP API、后台常驻进程，它们只能作为派生承载层消费同一组正式对象，不得绕过或重写既有 CLI/file runtime 边界。

---

# 3. 为什么这样定

## 3.1 与既有 ADR 一致

该决策与既有 ADR 是一致收敛，而不是新增另一条路线：

* ADR-001 已冻结双会话双队列、gate 外置与 CLI 边界。
* ADR-003 已冻结文件化 handoff runtime，而非独立调度平台。
* ADR-004 已冻结执行协议优先由外部 agent CLI 承载。
* ADR-005 已明确 Gateway 在 v0.x 不要求先做成 daemon 或平台服务。

因此，这次决策只是把这些隐含前提收敛成明确的默认技术承载方案。

## 3.2 为什么不先做服务化前后端

当前不优先选择独立服务化/前后端承载，原因是：

* 会过早引入常驻进程、数据库、API 生命周期与部署复杂度；
* 会让 runtime 载体争议先于对象边界、状态语义与 gate 分权冻结；
* 会把 `Human Gate` 错误推向“必须先有页面才能工作”；
* 与 LL v0.x 的“先跑通 skill-first 主链、再逐步增强承载层”路线不一致。

---

# 4. 约束边界

本 ADR 冻结的是默认承载方案，不冻结具体框架、库或部署形态。

这意味着：

* 可以用 Python CLI 实现；
* 可以用 shell / PowerShell / watcher 辅助；
* 可以在 `cli/`、`src/backend/` 中组织实现；
* 可以补充测试用 scanner、validator、repair helper；

但当前不冻结：

* 必须使用哪一个 Python CLI 框架；
* 必须先做成统一常驻 daemon；
* 必须先提供 Web UI；
* 必须先暴露 HTTP API。

---

# 5. 不允许的退化

以下实现被视为违反本 ADR：

1. 以服务化或页面化为理由，绕过正式文件对象与 CLI/runtime contract。
2. 在业务 skill 内直接嵌入最终 gate decision 与 formal materialization。
3. 在没有冻结新 ADR 前，把 HTTP service 或前后端平台宣称为默认唯一承载形态。
4. 因为尚未建设 UI，就让 human gate 回退为自然语言确认或人工随意改文件。

---

# 6. 对开发实现的直接影响

这份 ADR 对当前仓库的直接含义是：

* `src/backend/` 与 `cli/` 可以作为正式实现落点；
* 当前应优先交付文件对象 schema、CLI command surface、runtime helper、watcher/loop consumer；
* E2E 验证应先围绕 `CLI + file runtime` 跑通真实主链；
* 若未来引入服务化或前端载体，应新增 ADR 或等效正式决策说明其与本承载方案的关系。

---

# 7. 结论

LL v0.x 在主链治理运行时上的默认技术路线正式确定为：

## **CLI-first + file-based runtime**

这是一条为 `skill-first`、`file-handoff`、`gate externalized` 与最小运行时复杂度服务的承载决策，而不是对未来服务化能力的永久否定。
