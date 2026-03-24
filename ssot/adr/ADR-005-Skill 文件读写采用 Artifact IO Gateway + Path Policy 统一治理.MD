# ADR-005：Skill 文件读写采用 Artifact IO Gateway + Path Policy 统一治理

* 状态：Draft
* 日期：2026-03-23
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x skill-first 执行体系
* 相关 ADR：ADR-001、ADR-002、ADR-003、ADR-004

---

# 1. 背景

在 ADR-001 中，LL 已确定采用“双会话双队列闭环模型”作为 v0.1 执行架构，优先以最小平台复杂度跑通需求治理主链，并将复杂度优先压到 skill、contract、validation、evidence、artifact 上，而不是先建设重型 runtime 平台。

在 ADR-002 中，`raw-to-src` 已明确采用“双环修复、外挂 Gate、Job 路由”的标准治理方案，强调：

* 每一步生成后立即校验；
* 不合格则只做最小修补，而不是整段返工；
* 执行 agent 与监督 agent 分离；
* gate 作为外挂治理点存在，而不是内嵌在 skill 内部自判。

在 ADR-003 中，LL 已进一步明确将文件化 handoff runtime、artifact 交接、标准输入输出等内容作为支撑 skill-first 执行链路的重要基础设施。

在 ADR-004 中，LL 又冻结了公共 Skill Kernel 与统一 Skill Execution Contract，进一步明确 skill 应主要承载业务语义与声明式 contract，而不应自行复写通用治理运行时能力。

但随着 skill 数量增加，一个持续暴露的问题越来越严重：

* agent 虽然被反复要求遵守目录规范；
* 各类 skill 也已经开始声明输入输出；
* 项目中也存在目录地图、路径约定、文件管理规则；

**但 agent 仍然倾向于：**

* 在不合规目录中落正式产物；
* 私自创建临时目录、复制目录、`new/`、`final/`、`tmp/` 一类目录；
* 将同类输出散落到多个位置；
* 在没有注册、没有声明、没有审批的情况下覆盖已有文件；
* 通过路径猜测而不是 artifact 绑定来消费上下游文件。

这类问题在单 agent、小规模实验阶段尚可容忍，但在 skill-first、多阶段、多产物、多 agent 协作的执行体系下，会快速侵蚀整个治理基础。

因此，LL 需要将“目录规范”从提示层要求，升级为正式的 **文件系统 IO 治理机制**。

---

# 2. 问题定义

当前问题的本质，不是“agent 不够听话”，而是：

# **文件系统读写仍然是自由能力，而不是受控能力。**

也就是说，当前多数 skill 仍然同时承担了两类职责：

1. 生成内容；
2. 决定把内容写到哪里。

这会导致如下后果：

## 2.1 正式产物落点不稳定

同类产物可能被写入多个目录，例如：

* `docs/spec/`
* `docs/output/`
* `outputs/`
* 临时目录
* 根目录下新增目录

从而导致下游 skill 与人类 gate 都无法稳定判断“哪个才是正式版本”。

## 2.2 路径命名持续漂移

agent 常会引入：

* `final`
* `new`
* `v2`
* `copy`
* `latest`
* `fixed`
* 时间戳拼接
* 语义不清晰的文件名

从而导致目录结构逐渐失控。

## 2.3 输入输出契约失效

skill 虽然声明了输入输出，但如果实际执行时仍可自由读写任意路径，那么：

* contract 只是软提示；
* gate 只能事后发现问题；
* 审计成本越来越高；
* artifact registry 很难可信。

## 2.4 下游消费依赖路径猜测

当上下游以路径猜测或目录扫描来找文件时，会出现：

* 找错文件；
* 用到旧版本；
* 用到临时文件；
* 用到未注册产物；
* 用到“看起来像正式输出”的脏文件。

## 2.5 人类对系统信任下降

最终结果不是“目录有点乱”，而是：

* SSOT 被污染；
* evidence bundle 不可信；
* 修补 agent 容易修错对象；
* gate 校验对象不稳定；
* 人类无法确认系统当前真实状态。

---

# 3. 决策

LL 决定：

# **将 skill 的文件读写治理从“路径自由写入”升级为“Artifact IO Gateway + Path Policy 统一治理”。**

具体来说：

## 3.1 skill 不再拥有默认的自由路径选择权

skill 可以声明：

* 需要读取什么类型的输入；
* 需要产出什么类型的输出；
* 临时工作区是否需要；
* 是否拥有特定范围内的代码写权限；

但 **不再默认拥有“任意选择最终输出路径”的权限**。

---

## 3.2 逻辑产物与物理路径分离

skill 侧只面向：

* artifact type
* logical name
* stage
* role
* format

而由统一治理层根据 Path Policy 决定最终路径。

即：

* skill 负责“产出什么”
* 系统负责“写到哪里”

---

## 3.3 正式输出统一纳入 Artifact Registry

所有正式产物都必须：

* 有明确 artifact type；
* 有唯一 logical identity；
* 有受控物理路径；
* 有来源 skill；
* 有输入依赖；
* 有状态与可追踪元数据。

未进入 registry 的文件，不应被视为正式产物。

---

## 3.4 文件系统读写纳入 skill contract 与 gate 治理

每个 skill 必须显式声明 IO Contract，包括：

* 允许读取的 artifact 类型；
* 允许写入的 artifact 类型；
* 是否允许临时目录；
* 是否允许代码范围内写入；
* 禁止行为列表。

运行期由 executor 分配能力，执行后由 auditor 与 supervisor 进行校验，并可接入 gate。

---

## 3.5 目录治理采用“硬约束 + 软约束 + 事后审计”三层组合

LL 不再仅依赖 prompt 提醒，而采用：

* **硬约束**：受控写入、路径白名单、目录策略、越权拒绝；
* **软约束**：AGENT.md、skill spec、目录地图、命名规范；
* **事后审计**：workspace diff、违规检测、最小修补、人工 gate。

---

## 3.6 治理权威边界

本 ADR 进一步冻结三类权威边界：

* **Path Policy** 是路径合法性的唯一政策源；
* **Artifact Registry** 是 Managed Artifact 身份的唯一登记源；
* **Artifact IO Gateway** 是运行期正式落盘与晋升的唯一执行入口。

也就是说：

* Policy 决定“某类东西能不能写到某类位置”；
* Registry 决定“某个对象是否已成为正式 Managed Artifact”；
* Gateway 负责在运行期按 Policy 解析路径、执行写入、登记 Registry，并返回标准 handoff。

Registry 不授予路径合法性，Policy 不授予 artifact 身份，二者均通过 Gateway 在运行期联结生效。

---

## 3.7 术语约定

本 ADR 将所有进入正式链路、可被下游消费、可进入 gate / evidence / SSOT 的正式产物统一称为：

# **Managed Artifact（受管产物）**

“正式产物”仅作为解释性表述保留；在 contract、schema、registry、gateway 与 auditor 语境下，应优先使用 `managed_artifact` 这一主术语。

---

## 3.8 正式链路输入规则

凡未进入 Artifact Registry 的文件，一律不得作为任何正式 skill 的受管输入消费。

如需将 staging、scratch 或其他临时文件纳入正式链路，必须先经 Gateway 的 `commit` / `promote` 流程完成：

* Policy 校验；
* 路径解析；
* Registry 登记；
* lineage / inputs 补全；
* 审计记录落地。

在未完成上述步骤前，临时文件不构成 Managed Artifact。

---

## 3.9 受管写入唯一入口

对所有 Managed Artifact，Gateway 是唯一合法落盘入口。

任何绕过 Gateway 的正式输出写入，即使物理上成功，也视为治理失败，不构成有效 artifact；auditor 必须将其记为违规，且实现不得在 Gateway 失败时 silent fallback 到直接路径写入。

---

# 4. 设计原则

本 ADR 采用以下原则：

## 4.1 路径不是 skill 的语义职责

skill 的职责应当是处理语义对象与业务内容，而不是发明目录结构。

---

## 4.2 正式产物与临时产物必须分离

凡可被下游消费、可被 gate 校验、可纳入 SSOT / evidence 的产物，必须与 scratch / temp / staging 产物明确分离。

---

## 4.3 默认不信任自由文件系统写入

目录规范不能建立在“agent 会自觉遵守”的假设上，而应建立在“agent 会持续偏离”的假设上。

---

## 4.4 路径策略集中定义，不能散落在各 skill 中

路径规则、目录白名单、命名规则、artifact 映射必须有唯一政策源，而不能每个 skill 写一套。

---

## 4.5 下游消费应基于 artifact identity，而不是路径猜测

下游应优先通过 registry 或 artifact handoff 获取输入，而不是依靠目录扫描和模糊路径约定。

---

## 4.6 违规可见、可审计、可修补

系统不要求一步到位完全消灭违规，但要求：

* 违规必须被发现；
* 违规必须可归因；
* 违规必须可进入最小修补闭环。

---

## 4.7 受管写入必须声明操作模式

对 Managed Artifact 的写入必须显式声明 mode，例如：

* `create`
* `replace`
* `patch`
* `append`
* `promote`

不同 mode 对应不同的权限边界、覆盖规则、审计要求与失败处理，不允许由 skill 隐式决定。

---

# 5. 方案总览

本 ADR 将文件治理拆成五个协同部件：

1. **Path Policy**：定义合法目录、artifact 到目录映射、命名规则、禁止区域
2. **Artifact Registry**：定义正式产物身份、来源、路径、状态、依赖
3. **IO Contract**：定义单个 skill 的读写权限与受控边界
4. **Artifact IO Gateway**：统一处理正式读写请求，而非让 skill 直接选择路径
5. **Workspace Auditor**：执行前后对工作区变更做 diff 与违规审计

五者共同构成 LL 的文件 IO 治理基础。

---

# 6. Path Policy

## 6.1 定义

Path Policy 是 LL 文件系统路径治理的唯一政策源，用于定义：

* 合法根目录；
* artifact type 与目标目录映射；
* 命名规则；
* 禁止行为；
* 临时工作区规则；
* 覆盖与替换规则；
* 各类写入 mode 的适用边界。

---

## 6.2 允许写入的根目录

允许 skill 写入的根目录必须显式列出，示例：

* `.project/`
* `.workflow/`
* `.artifacts/`
* `contracts/`
* `docs/`
* `outputs/`
* `src/`

任何未在白名单中的顶层目录，默认视为非法写入目标。

---

## 6.3 禁止行为

Path Policy 至少应禁止以下行为：

* 在仓库根目录散写输出文件；
* 私自创建未注册的顶层目录；
* 将正式产物写入临时目录；
* 将中间产物伪装成正式产物；
* 使用 `../` 等路径穿越写入越界区域；
* 未声明即覆盖已有正式文件；
* 使用无语义、漂移式命名，如 `final`、`new`、`copy`。

---

## 6.4 Artifact Type 到目录映射

Path Policy 必须显式规定不同产物类型的目标目录。例如：

* `src_doc` → `docs/spec/src/`
* `epic_doc` → `docs/spec/epic/`
* `feat_doc` → `docs/spec/feat/`
* `report` → `docs/reports/`
* `guide` → `docs/guides/`
* `evidence_bundle` → `.artifacts/evidence/`
* `run_log` → `.workflow/runs/`
* `patch` → `outputs/patches/`

路径映射由政策统一维护，不应散落在 skill 中硬编码。

---

## 6.5 命名规则

Path Policy 应定义统一命名约束，包括：

* 文件名使用 kebab-case；
* 禁止空格、模糊后缀、重复副本命名；
* 扩展名必须与 artifact 类型匹配；
* 是否允许版本号、日期后缀，必须有明确规则；
* 目录层级不得无限扩张。

---

## 6.6 覆盖与 mode 规则

Path Policy 必须对写入 mode 给出统一规则，至少包括：

* `create`：仅创建新受管产物，不允许隐式覆盖；
* `replace`：替换既有受管产物，必须满足显式授权与审计要求；
* `patch`：仅允许最小范围修改，不得借机重命名或迁移路径；
* `append`：仅允许追加型日志或证据对象；
* `promote`：仅允许将 staging 产物晋升为 Managed Artifact。

是否允许某类 artifact 使用某种 mode，必须由 Path Policy 与 IO Contract 共同约束，而不能由 skill 临时决定。

其中：

* `patch` 面向保持 artifact identity 与路径不变的最小范围修改；
* 凡涉及 identity 变化、路径变化、主语义重置、整体替换，或虽保留同名但本质上重写主体内容的变更，应视为 `replace` 或按统一版本策略处理。

---

# 7. Artifact Registry

## 7.1 定义

Artifact Registry 是 Managed Artifact 的注册表，是 LL 认定“哪些对象已进入正式交付链路”的权威来源。

---

## 7.2 注册要求

凡满足以下任一条件的文件，必须进入 registry：

* 将被下游 skill 消费；
* 将进入 gate 校验；
* 将进入 evidence bundle；
* 将被人类评审；
* 将构成 SSOT 链路的一部分；
* 将作为修补对象或交付对象存在。

并且：

* 未进入 Registry 的文件，不得被任何正式 skill 作为受管输入消费；
* 目录扫描、模糊匹配、约定式猜路径不能替代 Registry 绑定；
* 临时文件如需被后续使用，必须先完成 `promote` / `commit`。

---

## 7.3 Registry 记录字段

一个正式 artifact 至少应记录：

* `artifact_id`
* `artifact_type`
* `logical_name`
* `path`
* `owner_skill`
* `producer_run_id`
* `inputs`
* `status`
* `created_at`
* `updated_at`

必要时可扩展：

* `hash`
* `format`
* `stage`
* `lineage`
* `evidence_refs`

其中，`artifact_id` 应由统一主键策略生成，并与 `artifact_type + logical_name + stage` 或其等效规范化标识一一对应；skill 不得自行发明、重载或绕过该身份规则。

---

## 7.4 唯一身份与版本原则

Artifact Registry 中 Managed Artifact 的唯一身份，至少应由 `artifact_type + logical_name + stage` 或等效主键组合定义。

本 ADR 同时冻结以下原则：

* 是否允许 revision 并存，应由统一版本策略决定，而不是由 skill 自行命名实现；
* patch 产物、主产物、派生产物之间的关系应通过 lineage 表达，而不是靠文件名猜测；
* 重跑是覆盖、派生 revision，还是生成新实例，必须服从统一版本策略。

---

## 7.5 Registry 的作用

Artifact Registry 用于：

* 明确正式产物身份；
* 解除上下游对路径猜测的依赖；
* 支持 artifact handoff；
* 支持 workspace 审计；
* 支持 gate 输入绑定；
* 支持最小修补与追踪归因。

---

# 8. IO Contract

## 8.1 定义

每个 skill 必须具备显式的 IO Contract，用于声明：

* 可读取什么；
* 可写入什么；
* 可否使用 staging；
* 是否拥有受限代码写权限；
* 写入 mode 与 operation scope；
* path scope 与 artifact scope；
* 哪些行为是禁止的。

正式 skill 的受管读取应优先通过 Registry、Gateway 或 artifact handoff 完成；对 workspace 的自由扫描仅可作为受限辅助能力，且不得替代正式 artifact 绑定。

---

## 8.2 目标

IO Contract 的目标不是描述目录细节，而是定义 **能力边界**。

例如，一个 skill 可以声明：

* 读取 `raw_doc`
* 写入 `src_doc` 与 `analysis_report`
* 不允许自由创建目录
* 不允许覆盖未托管文件
* 不允许根目录散写

对于 Level 3 / 4 skill，IO Contract 还必须能表达至少三类 scope：

* **artifact scope**：允许处理哪些 artifact type / stage / role；
* **path scope**：允许触达哪些路径范围，例如 `src/services/payment/**`；
* **operation scope**：允许执行哪些 mode，例如仅 `patch` 不允许 `replace` 或 `rename`。

---

## 8.3 治理作用

IO Contract 应作为：

* executor 分配能力的依据；
* supervisor 审查行为的依据；
* auditor 判断违规的依据；
* gate 是否通过的依据之一。

---

## 8.4 staging 晋升机制

IO Contract 必须显式说明临时文件是否允许晋升为 Managed Artifact。

一旦允许晋升，则必须满足：

* staging 文件不能直接被下游正式消费；
* 必须经 Gateway 的 `commit` / `promote` 执行晋升；
* 晋升时必须补齐 Registry、Policy 校验、lineage 与审计记录；
* 未完成晋升的临时文件，不得被视为正式输出。

---

# 9. Artifact IO Gateway

## 9.1 定义

Artifact IO Gateway 是统一的正式读写入口。

它负责将 skill 声明的逻辑产物请求，映射为受控的物理路径落盘行为，并同步完成 registry 更新、命名检查、覆盖检查、mode 校验等操作。

---

## 9.2 核心原则

Gateway 的核心原则是：

# **对正式产物，不再暴露默认的任意 `write(path)` 能力。**

取而代之的是：

* `read_artifact(...)`
* `write_artifact(...)`
* `commit_artifact(...)`
* `append_run_log(...)`
* `stage_temp_file(...)`

这类以 artifact 语义为中心的能力。

对所有 Managed Artifact，Gateway 是唯一合法落盘入口。任何绕过 Gateway 的正式写入，即使物理上成功，也不构成有效 artifact。

---

## 9.3 Gateway 职责

Gateway 至少负责：

* 检查 artifact type 是否允许；
* 根据 Path Policy 解析物理路径；
* 检查命名是否合法；
* 检查 mode 是否允许；
* 检查是否越权覆盖；
* 完成 registry 注册或更新；
* 返回标准 handoff 信息给下游。

同时，Gateway 不得在关键步骤失败时 silent fallback 到直接 `write(path)`。

---

## 9.4 一致性与失败处理原则

对 Managed Artifact 的写入，物理落盘、Registry 更新、Auditor 记录应被视为同一治理事务。

本 ADR 在治理层冻结以下失败处理原则：

* 若任一关键步骤失败，则该产物不得进入正式链路；
* 写成功但注册失败，不得视为正式成功；
* 注册成功但 Policy / mode 校验失败，不得补救为“例外通过”；
* Gateway 失败时允许保留 staging 或 error evidence，但不允许将结果伪装为正式输出。

---

## 9.5 与当前 LL 架构的关系

在 LL v0.x 阶段，Gateway 不要求立即做成重型 daemon 或平台服务。
它可以先以：

* CLI 包装层
* runtime helper
* 统一 shell / Python 小模块
* skill SDK 公共函数

等轻量方式实现。

关键不是技术形态，而是：

# **正式产物路径必须由受控层决定。**

---

# 10. Workspace Auditor

## 10.1 定义

Workspace Auditor 在 skill 执行前后对工作区做 diff，用于识别：

* 新增文件；
* 修改文件；
* 新增目录；
* 非法目录；
* 未注册正式输出；
* 越权覆盖；
* contract 外写入行为。

---

## 10.2 输出

Auditor 应输出结构化审计结果，可进入：

* evidence bundle；
* gate 评估；
* supervisor 反馈；
* 最小修补任务。

---

## 10.3 分级规则

Auditor 至少应输出 `blocker`、`warn`、`info` 三类等级。

### Blocker

必须 fail、阻断正式链路或进入最小修补：

* 非法顶层目录创建；
* Managed Artifact 绕过 Gateway 落盘；
* 未声明覆盖已有 Managed Artifact；
* path traversal / 越界写入；
* 下游消费未注册 artifact。

### Warn

可放行但必须留痕，并可进入后续修补：

* 命名不规范；
* staging 未清理；
* 多余临时文件残留；
* 非受管区域内的非正式实验文件。

### Info

仅记录，用于优化与后续治理：

* 读操作范围偏大；
* 冗余目录访问；
* 可清理但无风险的残留。

当自由扫描 workspace 超出 IO Contract 声明范围，或被用于替代正式 artifact 绑定时，auditor 应至少记录为 `warn`，并可按统一规则升级为 `blocker`。

---

## 10.4 审计定位

Auditor 是本 ADR 中的关键“收敛器”。

在 v0 阶段，即使 Gateway 还不完整，Auditor 也能先把违规显性化，让系统具备“能发现、能报警、能修补”的基础能力。

---

# 11. Managed Artifact 与临时区分离

## 11.1 Managed Artifact

Managed Artifact 指：

* 有 artifact type；
* 有 registry 记录；
* 有稳定路径；
* 可被下游消费；
* 可进入 gate / evidence / SSOT 的正式产物。

---

## 11.2 Scratch / Staging

Scratch / Staging 用于容纳执行过程中的临时文件。其规则应为：

* 仅允许写入指定 staging 区；
* 与正式输出区隔离；
* 不直接参与下游消费；
* 默认执行结束后清理或归档；
* 不得被误认作正式 artifact。

例如可统一放在：

* `.workflow/staging/<run_id>/`

---

## 11.3 原则

**临时存在不是违规，但临时污染正式目录是违规。**

同时：

* staging 文件不得被正式 skill 直接消费；
* staging 文件只有在完成 `promote` / `commit` 后，才能晋升为 Managed Artifact；
* 人工查看临时文件不构成正式消费。
* 人工可以发起 staging 产物的晋升，但仍必须通过 Gateway 完成 Policy 校验、Registry 登记与审计记录，不得以人工名义绕过受管流程。

---

# 12. 写权限分级

考虑到 LL 中 skill 类型不同，本 ADR 采用分级写权限模型。

## 12.1 Level 1：只读

仅允许读取受控输入，不允许写入正式产物。

适用于：

* 分析类
* 评审类
* 校验类
* 监督类

---

## 12.2 Level 2：受管产物写

允许通过 Gateway 写入 docs / contracts / outputs / artifacts 等受管区域，但不允许自由写代码仓库。

适用于：

* 文档生成类
* 报告类
* handoff 类
* evidence 类

---

## 12.3 Level 3：受限代码写

允许在声明范围内写入代码目录，例如仅限：

* `src/components/**`
* `src/services/payment/**`

适用于：

* 编码类
* patch 类
* 最小修补类

---

## 12.4 Level 4：仓库维护权限

仅少量特殊 skill 才拥有，例如：

* 迁移
* 大规模重构
* 目录整理
* 规范化清理

该等级必须显式授予，不可默认开放。

---

# 13. 与双环修复、外挂 Gate 的关系

本 ADR 不是独立存在的目录规范补丁，而是直接接入 LL 已确定的治理主线。

## 13.1 与双环修复的关系

当 auditor 发现：

* 非法目录；
* 未声明输出；
* 错误命名；
* 越权覆盖；

这些都可以进入“最小修补”闭环，而不是要求整段重做。

修补目标应是：

* 搬正路径；
* 修复命名；
* 更新 registry；
* 删除违规副本；
* 恢复唯一正式产物。

---

## 13.2 与外挂 Gate 的关系

Gate 不负责自己判断目录规范，而应使用：

* IO Contract
* Path Policy
* Registry
* Auditor 结果

作为外部依据。

也就是说：

# **目录治理不内嵌在 skill 自判里，而外挂在执行体系外部。**

这与 ADR-002 保持一致。

---

# 14. 落地路线图

本 ADR 采用分阶段落地。

## 14.1 v0：先把违规显性化

目标：先让系统看见问题，而不是继续隐性积累。

包括：

* 定义唯一的 `path_policy.yaml`
* skill 补齐 `io_contract`
* 执行前后做 workspace diff
* 识别未声明输出、非法目录、根目录散写、命名违规
* 输出结构化违规报告

这一阶段仍允许现有 skill 保持部分自由写入，但违规必须被发现。

迁移原则：

* 现有 skill 先补 contract，再接 auditor；
* 在完成 Gateway 接入前，不得新增新的自由路径写法；
* 所有新增 skill 从创建之初就必须声明受管 IO 边界。

---

## 14.2 v1：收口正式产物写入

目标：让正式输出路径不再由 skill 自己决定。

包括：

* 引入 `write_artifact()` / `read_artifact()` 一类统一入口
* skill 不再直接生成最终正式输出路径
* registry 自动登记正式产物
* 下游通过 artifact handoff 获取输入，而不是猜路径
* staging 区独立出来

这一阶段会显著提升稳定性，是推荐优先完成的版本。

迁移顺序：

1. 先补 `io_contract`
2. 再接 `workspace auditor`
3. 再将 Managed Artifact 写入切到 Gateway
4. 最后收缩自由写权限

---

## 14.3 v2：默认禁止自由写路径

目标：将“乱写文件”从高频问题降为异常情况。

包括：

* 普通 skill 默认禁用任意路径写入
* 目录创建也纳入 policy
* 覆盖行为必须带 mode
* 代码写入按 scope 控制
* 少数特殊 skill 才拥有豁免权

到该阶段，普通 skill 的 Managed Artifact 写入不得再绕过 Gateway；保留的自由写权限仅限明确声明的 scratch / staging 范围与少数豁免 skill。

---

# 15. 备选方案与拒绝原因

## 15.1 仅靠 prompt 强约束

拒绝原因：

* 成本低，但长期不稳定；
* 无法阻止 drift；
* 不能成为正式治理基础。

---

## 15.2 每个 skill 自带一套路径规范

拒绝原因：

* 规则分散；
* 难以统一演化；
* 维护成本高；
* 容易互相冲突。

---

## 15.3 完全依赖事后人工 review

拒绝原因：

* 发现太晚；
* 人工成本高；
* 无法支撑多 skill 持续运行。

---

## 15.4 直接上重型沙箱 / 重型平台文件系统代理

暂不采用，原因是：

* 当前 LL v0.x 优先跑通主链，而不是先建设重平台；
* 工程量与收益比在当前阶段不优；
* 可先通过 Gateway + Policy + Auditor 组合实现大部分治理收益。

---

# 16. 影响与收益

采用本 ADR 后，LL 将获得以下收益：

## 16.1 正式产物路径稳定

输出路径从“agent 决定”变成“系统决策”，可显著减少目录漂移。

---

## 16.2 上下游交接更稳

下游依赖 artifact identity 与 registry，而不是猜目录。

---

## 16.3 gate 与 evidence 更可信

因为其校验对象、输入来源、产物身份都更明确。

---

## 16.4 最小修补更容易落地

违规可以被精确定位为：

* 路径问题
* 命名问题
* 注册问题
* 越权问题

从而支持定点修补。

---

## 16.5 为后续 evolution 打基础

后续无论做：

* artifact manager
* 更强 runtime
* 目录清理器
* 产物 lineage
* 自动归档
* 仓库治理

都需要这一层作为底座。

---

# 17. 风险与折中

## 17.1 风险：早期接入成本上升

每个 skill 需要补齐 IO Contract，现有路径写法需要逐步收口。

### 折中

采用 v0 -> v1 -> v2 分阶段演进，而不是一次性强切。

---

## 17.2 风险：部分技能会觉得“不方便”

尤其是编码类、实验类、临时修复类 skill，习惯直接写文件。

### 折中

保留 staging 区与分级权限，而不是一刀切禁写。

---

## 17.3 风险：Gateway 初期实现不完整

### 折中

先保证正式产物写入收口，其他部分逐步纳管。

---

# 18. 最终结论

LL 正式决定：

# **将文件目录规范从软提示升级为文件 IO 治理机制。**

其核心不是继续要求 agent “记住该写哪里”，而是：

# **让 skill 只声明产物语义，不再默认决定物理路径；让正式文件读写通过 Artifact IO Gateway、Path Policy、Artifact Registry 与 Workspace Auditor 统一治理。**

这项能力是 LL skill-first 架构继续扩展的基础支撑，也是维持 SSOT、gate、evidence、handoff、最小修补能够长期成立的必要条件。
