# AGENT.md

## 1. 目的

本文件是本仓库中 agent 的默认入口文件。

它的作用包括：

- 项目知识地图
- 权威内容的文件索引
- 任务路由指南
- 先读后做的行为规则

本文件**不是**业务 SSOT 本身。
它不能变成另一份并行的事实来源。

如果本文件中的任何内容与权威来源冲突，以权威来源为准。

---

## 2. 权威顺序

当多个文件看起来在描述同一件事时，使用以下优先级：

1. 冻结的 SSOT / spec / contract
2. 工作流定义的任务输入输出约束
3. 技能本地 contract 与校验规则
4. 架构 / 设计文档
5. 本文件（`AGENT.md`）
6. 临时笔记 / 运行时产物

当来源冲突时，不要凭空发明第三个版本。
回溯到权威级别最高的文件。

---

## 3. 项目使命

- 项目：`<PROJECT_NAME>`
- 简称：`<PROJECT_SHORT_NAME>`
- 类型：`<framework | app | infra | workflow-platform | skill-repo>`
- 当前阶段：`<MVP | stabilization | pilot | production>`
- 当前最高优先级：`<ONE_SENTENCE>`
- 当前非目标：
  - `<NON_GOAL_1>`
  - `<NON_GOAL_2>`

---

## 4. 工作原则

所有 agent 都必须遵守以下原则：

1. 修改前先阅读。
2. 新建前先复用。
3. 决策前先确认权威来源。
4. 不要绕过 contract、校验或目录规则。
5. 除非明确允许，不要在工作流失败后手工即兴绕过。
6. 重要执行步骤要留下证据。
7. 优先做最小、局部、风格一致的修改，而不是大范围的猜测式重构。
8. 除非任务明确要求，否则不要创建重复文档、重复 spec 或并行实现。

---

## 5. 仓库地图

### 5.1 顶层目录

| Path | Role | Authority | Notes |
|---|---|---:|---|
| `agent.md` / `AGENT.md` | 项目入口知识地图 | 否 | 仅用于导航 |
| `docs/` | 项目文档与指南 | 部分 | 某些文件若被明确标记则可能是权威来源 |
| `ssot/` | 冻结的事实来源文档 | 是 | 业务/流程层面的最高权威 |
| `specs/` | 规范化结构化 specs | 是 / 部分 | 取决于文件类型与冻结状态 |
| `skills/` | 可复用技能包 | 部分 | 对执行行为具有技能本地权威 |
| `workflows/` | 工作流定义 | 部分 / 是 | 对编排行为具有权威 |
| `contracts/` | 输入/输出 contracts | 是 | 接口约束的权威来源 |
| `src/` | 源代码 | 否 | 是实现，不是首要业务事实 |
| `scripts/` | 可执行脚本 | 否 | 辅助与自动化 |
| `tests/` | 测试与校验 | 否 | 是校验层，不是事实来源 |
| `artifacts/` | 执行证据与报告 | 否 | 以追加记录为主的证据目录 |
| `.runtime/` | 运行时状态 | 否 | 绝不能当作长期项目事实 |

> 注意：
> 运行时状态不能被视为设计事实。
> 实现代码不能悄悄覆盖冻结的 spec。

---

## 6. 核心权威索引

请将下面的路径替换为本仓库中的真实文件位置。

### 6.1 项目级权威文件

- 项目概览：`<PATH_PROJECT_OVERVIEW>`
- 架构概览：`<PATH_ARCHITECTURE_OVERVIEW>`
- 目录规则：`<PATH_DIRECTORY_RULES>`
- 命名 / 术语规则：`<PATH_TERMINOLOGY>`
- 治理规则：`<PATH_GOVERNANCE_RULES>`

### 6.2 SSOT 权威文件

- 源需求 SSOT：`<PATH_SRC_SSOT>`
- Epic SSOT：`<PATH_EPIC_SSOT>`
- Feature SSOT：`<PATH_FEAT_SSOT>`
- 技术 / 架构 SSOT：`<PATH_TECH_SSOT>`
- 决策记录 / 合并后的 ADR-SRC 文档：`<PATH_DECISION_SSOT>`

### 6.3 工作流 / 技能 / contract 权威文件

- 工作流标准：`<PATH_WORKFLOW_STANDARD>`
- 技能标准：`<PATH_SKILL_STANDARD>`
- 输入 contract 标准：`<PATH_INPUT_CONTRACT_STANDARD>`
- 输出 contract 标准：`<PATH_OUTPUT_CONTRACT_STANDARD>`
- 证据标准：`<PATH_EVIDENCE_STANDARD>`
- 校验标准：`<PATH_VALIDATION_STANDARD>`

### 6.4 代码权威文件

- 源码树架构：`<PATH_SRC_ARCH>`
- 模块边界：`<PATH_MODULE_BOUNDARIES>`
- 集成规则：`<PATH_INTEGRATION_RULES>`
- 测试策略：`<PATH_TEST_POLICY>`

---

## 7. 任务路由表

开始任何工作之前，先对任务分类，并加载所需文件。

| Task Type | Must Read | Should Read | Avoid |
|---|---|---|---|
| requirement normalization | `AGENT.md`, SRC SSOT, terminology rules | architecture overview | 直接跳到代码 |
| epic design | `AGENT.md`, SRC SSOT, EPIC standard | architecture, existing epic examples | 过早写 feat/code |
| feat design | `AGENT.md`, EPIC SSOT, FEAT standard | related tech/design docs | 发明隐藏需求 |
| workflow design | `AGENT.md`, workflow standard, contracts | skill standard, evidence standard | 手工且无记录的步骤 |
| skill design | `AGENT.md`, skill standard, contracts | adjacent skill examples | 臃肿的多用途 skill |
| code change | `AGENT.md`, module boundaries, source architecture | related tests, related contracts | 在不了解影响时盲改公共接口 |
| doc governance | `AGENT.md`, directory rules, governance rules | terminology rules | 保留重复文档长期存在 |
| bug fix | `AGENT.md`, relevant contract, relevant module docs | logs, artifacts, tests | 猜测式重构 |
| validation / review | `AGENT.md`, validation standard, task contract | evidence standard | 接受无法支持的说法 |

---

## 8. 阅读策略

对于任何非琐碎任务，默认阅读顺序如下：

1. `AGENT.md`
2. 与任务相关的权威 SSOT/spec/contract
3. 架构文档或模块边界文档
4. 需要修改的目标文件
5. 相邻示例或历史实现
6. 如果是在调试或审计，则读取 evidence / artifacts

不要因为某些大段内容存在就全部读取。
只加载完成任务所需的最小上下文。

---

## 9. 文件角色矩阵

使用下表判断某个文件是事实来源、派生产物，还是仅供参考的资料。

| File Class | Typical Location | Role | Editable | Notes |
|---|---|---|---|---|
| frozen SSOT | `ssot/` | 首要事实来源 | 仅受控修改 | 不要随意编辑 |
| normalized spec | `specs/` | 结构化事实来源 | 受控 | 通常由 SSOT 派生 |
| contract | `contracts/` | 接口事实来源 | 受控 | 变更会影响下游 |
| workflow definition | `workflows/` | 编排事实来源 | 受控 | 必须与 contracts 一致 |
| skill manifest/rules | `skills/*/` | 本地执行事实来源 | 受控 | 不能与全局标准冲突 |
| architecture doc | `docs/architecture/` | 设计事实来源 | 谨慎修改 | 可能指导代码结构 |
| code | `src/` | 实现 | 可以 | 必须遵循上游事实来源 |
| tests | `tests/` | 校验 | 可以 | 应反映预期事实 |
| artifacts | `artifacts/` | 证据 | 追加优先 / 尽量不改写 | 不是事实来源 |
| runtime state | `.runtime/` | 临时状态 | 可以 | 绝不是长期事实来源 |

---

## 10. 标准执行流程

对于任何任务，除非任务本身明确定义了其他流程，否则按以下顺序执行：

1. 识别任务类型。
2. 加载所需权威文件。
3. 确认允许修改的范围。
4. 确认哪些文件是事实来源，哪些是派生产物。
5. 执行最小且有效的修改。
6. 校验与 contracts/specs/tests 的一致性。
7. 如有要求，记录输出与证据。
8. 如果结构发生变化，更新索引或引用。

---

## 11. 变更安全检查清单

修改任何内容前，确认以下问题：

- 这是应该修改的正确文件吗？
- 是否存在更高权威的上游文件？
- 这个文件是生成物、派生物还是冻结文件？
- 这次修改会不会制造重复的事实来源？
- 相关 contracts 是否也需要更新？
- 相关 workflows 或 skills 是否也需要更新？
- 文档或索引是否需要同步？
- 这次修改是否要求证据或校验输出？

如果任何答案不明确，停止猜测并回溯到权威来源。

---

## 12. 禁止行为

Agent 不得：

1. 跳过权威文件，仅凭记忆或假设行动。
2. 未经明确授权，为同一概念创建并行 spec。
3. 将实现代码当作业务事实来源。
4. 将长期知识写入运行时目录。
5. 隐式覆盖 contract。
6. 绕过 workflow/skill 限制后再隐瞒绕过行为。
7. 在已有标准路径时，仍在临时位置随意创建新文件。
8. 将大量权威内容复制进本文件。

---

## 13. 输出放置规则

输出内容应放在正确位置。

### 13.1 Specs 与治理文档
- source requirement docs：`<PATH_SRC_DIR>`
- epic docs：`<PATH_EPIC_DIR>`
- feat docs：`<PATH_FEAT_DIR>`
- tech / architecture docs：`<PATH_TECH_DIR>`

### 13.2 Skills 与 workflows
- skill packages：`<PATH_SKILLS_DIR>`
- workflow definitions：`<PATH_WORKFLOWS_DIR>`
- contracts：`<PATH_CONTRACTS_DIR>`

### 13.3 代码与脚本
- application/framework code：`<PATH_SRC_DIR>`
- helper scripts：`<PATH_SCRIPTS_DIR>`
- tests：`<PATH_TESTS_DIR>`

### 13.4 证据与报告
- execution logs：`<PATH_ARTIFACT_LOGS>`
- validation outputs：`<PATH_ARTIFACT_VALIDATION>`
- review reports：`<PATH_ARTIFACT_REPORTS>`

---

## 14. 冲突处理

如果文件之间存在冲突：

1. 优先选择冻结的 SSOT / contract / standard。
2. 然后优先当前任务的 workflow 输入输出约束。
3. 然后优先模块文档或架构文档。
4. 最后才使用本文件做路由与解释。
5. 绝不能静默合并彼此冲突的含义。

当冲突无法解决时：
- 列出冲突文件
- 识别缺失或不明确的更高权威来源
- 不要发明新规则
- 将问题路由回治理流程 / SSOT 更新流程

---

## 15. 何时更新本文件

在以下情况更新 `AGENT.md`：

- 顶层权威文件路径发生变化
- 新增了重要顶层目录
- 某类任务变得常见
- 权威边界发生变化
- 默认路由规则发生变化

以下情况**不要**更新 `AGENT.md`：
- 普通业务内容编辑
- 小型代码修改
- 临时调试笔记
- 运行时状态变化
- 一次性实验

---

## 16. 当前阶段约束

在此设置当前项目约束。

- 允许大规模重构：`<yes/no>`
- 允许临时性 workaround：`<yes/no>`
- 允许手工绕过：`<yes/no>`
- 当前优先稳定而非扩张：`<yes/no>`
- 默认修改风格：`<minimal-local-consistent | broader-structural>`
- 已知活跃风险：
  - `<RISK_1>`
  - `<RISK_2>`

---

## 17. 快速链接

- 项目概览：`<PATH_PROJECT_OVERVIEW>`
- 路线图：`<PATH_ROADMAP>`
- 当前优先级：`<PATH_CURRENT_PRIORITY>`
- 架构：`<PATH_ARCHITECTURE_OVERVIEW>`
- 工作流标准：`<PATH_WORKFLOW_STANDARD>`
- 技能标准：`<PATH_SKILL_STANDARD>`
- contracts：`<PATH_CONTRACTS_DIR>`
- 目录规则：`<PATH_DIRECTORY_RULES>`

---

## 18. 给 Agent 的提醒

本文件告诉你**事实在哪里**，以及**如何找到它**。

它并不赋予你以下权限：
- 跳过权威阅读
- 发明缺失规则
- 将摘要变成首要事实来源
- 把便利性当成正确性

如果拿不准：
先追溯权威来源，再行动。
