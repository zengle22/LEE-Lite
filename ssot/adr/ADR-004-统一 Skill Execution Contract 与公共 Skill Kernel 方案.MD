# ADR-004：LL 采用统一 Skill Execution Contract 与公共 Skill Kernel 作为 Skill 治理底座

* 状态：Draft
* 日期：2026-03-23
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x skill-first 架构
* 相关 ADR：ADR-001、ADR-002、ADR-003

---

# 1. 背景

在 ADR-001 中，LL 已正式确定采用“双会话双队列闭环模型”作为 v0.1 执行架构，并明确：

* 采用 skill-first 路线；
* 不优先建设独立调度平台；
* human gate 必须外置；
* runtime 临时态不进入工程主树。

在 ADR-002 与 ADR-003 中，LL 又进一步冻结了：

* `raw-to-src` 这类 governed skill 的双环修复、外挂 gate、job 路由边界；
* 文件化 handoff runtime 作为流转治理机制；
* artifact、job、gate、evidence、handoff 的职责分离。

但随着 skill 数量增多，一个新的结构性问题已经出现：

> 各个 skill 正在重复携带输入装载、预检查、双 agent 分工、最小测试、最小修补、evidence 打包、route 建议等公共治理能力，而这些能力本应是跨 skill 复用的统一运行时能力。

如果不对这部分进行统一收敛，LL 很快会出现以下问题：

* 不同 skill 的治理强度不一致；
* skill 创建方式分散，后续维护成本持续升高；
* agent 在执行 skill 时容易绕过统一生命周期；
* 通用能力散落在 prompt、README、脚本和实现细节里，难以演进；
* 同一类问题在多个 skill 中被重复修复。

因此，需要在不破坏 ADR-001 与 ADR-003 既定路线的前提下，为 LL skill-first 架构补上一层公共能力底座。

---

# 2. 问题陈述

LL 当前需要解决的，不是“如何再建一个独立 skill 平台”，而是：

* 如何把跨 skill 的公共治理能力从具体业务 skill 中抽离；
* 如何统一 skill 的执行边界、输入输出门禁与证据要求；
* 如何让 Claude Code、Codex 等外部执行器在不新增重型 runtime 的前提下，仍然遵循相同协议；
* 如何避免 skill 既做业务语义、又做运行时治理，导致职责混杂；
* 如何让新 skill 默认继承统一治理，而不是每次手工拼装。

如果继续让每个 skill 自带一套治理逻辑，将出现以下结构性缺口：

1. **边界缺口**

   skill 的业务语义边界与治理边界耦合，导致“这个 skill 到底负责业务，还是负责 runtime”越来越不清楚。

2. **一致性缺口**

   pre-check、verify、repair、evidence、route 等行为会在不同 skill 中逐渐漂移。

3. **维护缺口**

   每新增一个 skill，都要复制一遍双 agent、测试、修补、证据逻辑，长期不可维护。

4. **执行缺口**

   如果缺少统一执行协议，外部 agent CLI 容易“读完 skill 就自由发挥”，绕过必要门禁。

5. **演进缺口**

   公共能力分散在 prompt 和脚本中，后续无法进行版本化升级与统一替换。

因此，需要一份正式 ADR，定义 LL 在 skill-first 架构下的 **统一 Skill Execution Contract 与公共 Skill Kernel**。

---

# 3. 决策

## 3.1 决策摘要

LL 在现有离散 skill 架构之上，正式采用：

## **统一 Skill Execution Contract + 公共 Skill Kernel**

作为所有正式 skill 的治理底座。

该方案的正式原则如下：

1. skill 不再承载通用治理逻辑，而只承载业务语义与声明式 contract；
2. 输入标准化、校验、双 agent 分工、最小测试、最小修补、evidence 打包、route 建议等能力统一收敛到 Skill Kernel；
3. LL 不要求先实现一个独立 `Skill Runner` 程序；
4. LL 先冻结 **Skill Execution Contract**，并允许 Claude Code、Codex 等外部执行器作为该 contract 的承载实现；
5. 所有新 skill 必须通过标准 Skill Creator 骨架接入这一治理底座。

---

## 3.2 正式定义

LL v0.x 在 ADR-001、ADR-002、ADR-003 的基础上，正式定义以下原则：

1. **Skill 是声明式业务单元**

   * skill 是业务语义插件，不是自由执行脚本；
   * skill 主要由 contract、assets、少量 adapter 组成；
   * skill 不负责复写公共治理运行时。

2. **Kernel 是公共治理层**

   * Kernel 负责统一生命周期约束、共享模块边界与治理协议；
   * Kernel 负责输入解析、校验、测试、修补、证据与路由建议的统一定义；
   * Kernel 不关心具体业务主题，只关心治理协议与公共模块；
   * 在 LL v0.x 中，Kernel 优先是逻辑治理层，而不预设必须先实现为中心化常驻程序或统一 CLI。

3. **正式执行遵循统一 Skill Execution Contract**

   * 正式 skill 必须通过统一执行协议执行；
   * 执行协议定义输入、阶段顺序、必需产物、失败处理与禁止动作；
   * 执行协议是逻辑概念，不预设必须新增独立 CLI 程序。

4. **外部执行器可以承载该 contract**

   * Claude Code CLI、Codex CLI、未来其他 agent CLI，均可作为 execution contract 的实现载体；
   * 外部执行器负责按协议执行，而不是自由解释 skill；
   * 执行器差异应收敛在 adapter 层，不应回灌到 skill 本体。

5. **Skill Creator v2 是标准接入入口**

   * 所有新 skill 默认由 Creator 生成标准骨架；
   * Creator 负责生成 contract、prompt、tests、evidence 占位与 README 使用约定；
   * Creator 不复制 runtime 逻辑进每个 skill。

---

# 4. 架构边界

## 4.1 组件分工

LL 在该方案下冻结以下组件边界：

### 1. Skill Creator

职责：

* 创建标准 skill 包；
* 生成 `skill.yaml`、prompt、tests、schemas、evidence spec、README 等骨架；
* 确保新 skill 天生接入统一治理。

不负责：

* 执行 skill；
* 承载双 agent、test、repair 等 runtime 逻辑。

### 2. Skill Contract

职责：

* 定义 skill 类型、输入输出、生命周期策略、verify 策略、repair 策略、evidence 策略与 route 建议；
* 约束 skill 的边界与必需行为；
* 作为 Kernel 与执行器读取的统一声明源。

### 3. Skill Assets

职责：

* 承载业务 prompt、模板、规则、测试定义、修补提示模板；
* 提供领域语义，而不提供治理运行时代码。

### 4. Skill Kernel

职责：

* 定义标准 lifecycle、共享治理模块边界与必需执行约束；
* 约束 contract、assets、validator、test、repair、evidence、route 的接缝；
* 为执行器提供统一的治理协议载体；
* 在需要最小实现时，承载共享的 context、validator、test、repair 与 artifact 模块。

硬约束：

* 在 LL v0.x 中，Skill Kernel 首先是治理协议与共享边界，不预设必须先落成中心化程序、常驻服务或统一 CLI。

### 5. External Executor Adapter

职责：

* 将统一 execution contract 适配到具体执行器；
* 对接 Claude Code、Codex 等外部 CLI；
* 屏蔽执行器差异，而不是改变 skill 语义或治理边界。

硬约束：

* Adapter 只能适配执行器交互方式、上下文注入方式与结果回收方式；
* Adapter 不得修改 lifecycle 顺序、必需产物、fail policy、repair policy、evidence policy、route policy 的语义定义；
* Adapter 不得改写 skill contract，只能承载 contract。

### 6. Loop / Queue / Human Gate

职责：

* 继续负责上层调度、gate 外置、决策回流与长程串联；
* 不被 Skill Kernel 替代。

---

## 4.2 关系说明

该方案的核心关系如下：

1. 上层 Loop / Queue 决定当前应该执行哪个 skill；
2. 外部执行器读取 skill package；
3. 外部执行器按统一 Skill Execution Contract 承载 Skill Kernel 所定义的治理阶段；
4. agent 负责语义工作，共享治理模块负责 validator/test/repair 等公共能力；
5. 最终产出 artifact、report、evidence 与 route suggestion，交回 ADR-003 所定义的文件化 handoff runtime；
6. 其中 route suggestion 只是建议，不直接触发调度动作。

---

# 5. Skill 的标准形态

## 5.1 Skill 只保留三类内容

每个正式 skill 只应保留以下三类内容：

### A. Contract

用于描述：

* skill 是什么；
* 接受什么输入；
* 产出什么输出；
* 使用什么 lifecycle、verify、repair、evidence 与 route 策略。

### B. Assets

用于承载：

* `prompt.md`
* `supervisor_prompt.md`
* `repair_prompt.md`
* `tests/minimum_tests.yaml`
* `evidence/evidence.spec.yaml`
* templates / rules / schemas

### C. Thin Adapter

用于接入：

* 该 skill 的特殊输入映射；
* 该 skill 的特殊输出映射；
* 该 skill 的模板变量组装。

硬约束：

* Thin Adapter 不得在 skill 内引入 lifecycle 分支、治理决策或通用运行时逻辑。

---

## 5.2 Skill 不再承载的内容

以下能力不应在每个 skill 内重复实现：

* 输入装载与标准化；
* pre-check / post-check；
* 双 agent 主从执行框架；
* minimum verify；
* minimal repair；
* evidence pack；
* route decision 解析；
* 通用 artifact io；
* 通用 validator / test runner。

这些能力统一下沉到 Skill Kernel。

---

# 6. 标准生命周期

Skill Kernel v1 统一定义以下生命周期阶段：

## Stage 1：Resolve Input

读取输入文件、上下文 bundle、环境配置，构造原始执行上下文。

输出：

* `input_snapshot.json`

## Stage 2：Normalize Input

将输入标准化为 skill 内部统一格式。

输出：

* `normalized_input.json`

## Stage 3：Pre-Check

执行输入 schema 校验、必需字段检查、路径合法性检查、依赖可用性检查。

输出：

* `precheck_report.json`

失败处理：

* fail fast；
* 写 evidence；
* 返回 `precheck_failed`。

## Stage 4：Execute

调用 Executor Agent 生成 draft 产物。

输出：

* `draft_output.*`
* `executor_notes.json`

## Stage 5：Supervise

调用 Supervisor Agent 审查 draft 的结构、边界、完整性与风险。

输出：

* `supervisor_report.json`

## Stage 6：Minimum Verify

运行 minimum test suite。

至少包括：

* 结构检查；
* schema 检查；
* required sections 检查；
* 术语一致性检查；
* 依赖引用检查；
* 可选语义检查。

约束：

* 可选语义检查不得替代 deterministic 检查成为硬门禁主路径。

输出：

* `minimum_test_report.json`

## Stage 7：Minimal Repair

若 verify 失败，则进入最小修补阶段。

要求：

* 仅 patch findings 涉及范围；
* 禁止整篇重写；
* 禁止改变用户意图；
* 禁止扩大修改范围。

输出：

* `patched_output.*`
* `repair_report.json`

## Stage 8：Finalize

确定最终输出、结果状态与版本元数据。

边界：

* Finalize 只确定本次 skill 的候选最终输出与元数据；
* Finalize 不等于 approve；
* Finalize 不等于 freeze；
* Finalize 不替代上层 gate 或 human approval。

输出：

* `final_output.*`
* `finalization_report.json`

## Stage 9：Evidence & Route

打包中间证据，并生成下一步建议。

边界：

* route 只表达建议，不直接触发调度、跳转或 freeze 动作。

输出：

* `evidence_bundle.json`
* `route_decision.json`

---

# 7. Shared Governance Modules

这些模块是公共治理能力的正式承载面，应集中于 Kernel 层；它们首先是共享边界与协议对象，其次才是按需落地的程序模块。

## 7.1 Contract Loader

负责读取并解析 `skill.yaml`。

## 7.2 Context Builder

负责构造 execution context、run metadata 与 prompt context。

## 7.3 Validators

负责 deterministic 校验，包括：

* schema validator；
* required fields validator；
* path policy validator；
* output validator。

## 7.4 Test Runner

负责执行 minimum tests 与生成统一 test report。

## 7.5 Repair Runner

负责调用 Repair Agent 并施加 repair policy。

## 7.6 Artifact Manager

负责路径合法性检查、文件写入、report 落盘与 evidence bundle 组装。

## 7.7 Route Resolver

负责根据 contract、result status 与 reports 输出下一步建议。

---

# 8. Skill Execution Contract

## 8.1 定义

LL 不单独强制引入一个新的 `Skill Runner` 程序。

LL 正式冻结的是：

## **Skill Execution Contract**

也就是“一次标准 skill 执行必须满足的统一协议”。

该协议至少规定以下内容：

### 输入

* skill 目录；
* `skill.yaml`；
* input bundle；
* 当前 job metadata；
* 输出根目录；
* 可选 executor profile。

### 执行步骤

* 先读取 contract；
* 再读取 prompt / rules / templates / tests；
* 按标准 lifecycle 执行；
* verify 失败后优先进入 minimal repair；
* 生成标准 evidence 与 route suggestion。

### 输出

* final artifact；
* reports；
* evidence bundle；
* route decision；
* 标准 result object。

约束：

* route decision 是建议对象，不是直接调度动作。

### 禁止动作

* 绕过 pre-check；
* 绕过 evidence；
* 私自修改输出路径；
* 未经协议定义直接跳下一 skill；
* 未经过上层 gate 自行 freeze 或 approve；
* 以整篇重写替代最小修补。

---

## 8.2 External Executor Adapter

在 LL 当前路线下，真正的执行承载体是外部 agent CLI，而不是 LL 自研重型 runner。

因此，正式定义如下：

1. Claude Code、Codex 等 CLI 可以作为 execution contract 的执行器；
2. 执行器需要适配统一协议，而不是各自定义 skill 生命周期；
3. 执行器差异应通过 adapter spec 收敛；
4. adapter 只允许适配交互方式，不允许改写 contract 语义；
5. 如果未来发现执行器间漂移严重，再考虑是否抽出一个更薄的统一入口；
6. 在此之前，LL 优先冻结协议，而不是先建设程序。

---

# 9. Skill Contract 的最小方向

本 ADR 不展开完整 schema，但冻结以下最小方向：

## 9.1 `skill.yaml` 至少应声明

* `id`
* `name`
* `version`
* `type`
* `inputs`
* `outputs`
* `runtime`
* `execution`
* `verify`
* `repair`
* `evidence`
* `route`

## 9.2 字段设计原则

### `runtime`

声明 skill 采用哪个 lifecycle profile 与执行协议版本，不允许 skill 自定义绕过。

补充说明：

* `runtime` 是声明字段，不等同于本地程序运行时实现。

### `execution`

声明 agent 执行模式、executor/supervisor profile 与轮次预算，而不是 runtime 实现细节。

### `verify`

声明 minimum test suite 与 fail policy。

### `repair`

声明修补边界与 forbidden actions，而不是实现修补逻辑。

### `route`

只提供下一步建议，不直接触发调度。

---

# 10. 与现有 ADR 的关系

本决策不推翻既有架构，而是补齐其公共治理底座。

## 10.1 与 ADR-001 的关系

ADR-001 冻结执行架构。

ADR-004 冻结在该执行架构下，skill 自身与公共治理运行时的边界。

## 10.2 与 ADR-002 的关系

ADR-002 定义 `raw-to-src` 作为一个 governed skill 的专用治理方案。

ADR-004 进一步规定，这类 governed skill 中的公共治理能力应逐步收敛到 Kernel，而不是散落在 skill 内部。

## 10.3 与 ADR-003 的关系

ADR-003 冻结文件化 handoff runtime。

ADR-004 规定单个 skill 在进入 handoff runtime 之前，应如何统一生成 artifact、report、evidence 与 route suggestion。

其中，skill 内的 Finalize 仅确定候选输出，不替代 ADR-003 体系中的 gate、approval 或 freeze。

---

# 11. 非目标

Skill Kernel v1 不做以下事情：

## 11.1 不做重型中心化调度器

不引入任务数据库、复杂状态机、事件总线或服务化 orchestrator。

## 11.2 不强制先实现独立 `ll run-skill` 程序

先冻结 execution contract，再按需要补 executor adapter 或薄入口。

## 11.3 不替代上层 human gate

Kernel 只负责 skill 治理，不替代关键节点的人类决策。

## 11.4 不让 skill 失去业务表达能力

skill 仍负责业务语义、领域规则与模板资产，不被压平为纯配置文件。

---

# 12. 风险与治理点

## 12.1 风险：skill 继续绕过统一协议

对策：

* 正式 skill 必须声明 execution contract 版本；
* Creator 默认生成标准骨架；
* review 时将“是否绕过 contract”作为硬检查项。

## 12.2 风险：公共逻辑再次复制进 skill

对策：

* 明确 skill 禁止内嵌 runner / verify / repair 的通用实现代码；
* 将公共模块沉到 Kernel 或 shared governance modules。

## 12.3 风险：prompt 过重，skill 维护性下降

对策：

* Creator 只生成最小必需文件；
* 结构化 contract 与 tests 优先于长篇 prompt 约束。

## 12.4 风险：deterministic 与 semantic 边界不清

对策：

* 可程序化内容优先下沉到 validator/test runner；
* 必要歧义才交给 agent；
* supervisor 负责审查，不直接重写结果。

---

# 13. 实施路线

## Phase 1：P0

目标：先冻结协议与最小骨架。

交付项：

* `skill.yaml` 最小字段集；
* lifecycle v1；
* execution contract v1；
* 标准 result object；
* Creator v2 最小骨架约束。

## Phase 1.5：P0.5

目标：围绕当前关键链路抽最小共享模块，而不是先平台化。

交付项：

* 最小 validator 共享模块；
* 最小 artifact 管理共享模块；
* minimum test spec parser；
* 必要的 repair 调用封装。

## Phase 2：P1

目标：用 Skill Creator v2 固化新 skill 创建标准。

交付项：

* 标准目录骨架；
* prompt / supervisor / repair 模板；
* tests / evidence / schema 占位文件；
* 最小 skill type profile：`transformation`、`analysis`、`validation`。

## Phase 3：P1.5

目标：迁移现有 governed skill。

方式：

* 新 skill 全走 v2；
* 老 skill 按优先级迁移；
* 允许 adapter 层做兼容，不要求一次性改完全部 skill。

## Phase 4：P2

目标：增强可配置性与跨执行器一致性。

可选项：

* 可插拔 stage；
* executor adapter spec；
* 更细粒度 evidence model；
* skill profile registry；
* 必要时的薄 runner 入口。

---

# 14. 一条最重要的工程约束

后续所有设计都应服从以下规则：

> **Skill 的业务语义可以分散，Skill 的治理能力必须集中。**

这是整个统一 Skill Execution Contract 与公共 Skill Kernel 方案的核心约束。

---

# 15. 后续配套文档

本 ADR 草稿通过后，建议优先补齐以下配套文档：

1. `skill.yaml` 完整 schema 设计；
2. Skill Execution Contract v1；
3. External Executor Adapter 约定；
4. Skill Creator v2 骨架规范。

其中优先级最高的是：

## **`skill.yaml` 完整 schema 设计**

因为 schema 先冻结，Creator 与执行协议才容易稳定落地。

---

# 16. 最终定义

LL Skill Kernel 不是先验要求存在的单一程序实体，而是一层统一治理约束。

它通过标准 lifecycle、共享治理模块边界、声明式 skill contract 与受控 agent 调用，为离散 skill 提供一致的输入输出门禁、双 agent 执行监督、最小测试与最小修补能力。

skill 本身仅负责业务语义、领域规则与声明式约束表达。

在 LL 中，正式 skill 的执行不以独立 `Skill Runner` 程序为前提，而以统一 **Skill Execution Contract** 为前提；Claude Code、Codex 等外部执行器可以作为该 contract 的承载实现。
