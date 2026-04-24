# SSOT 语义治理与 Agent Skill 调用指南

> **项目**: LEE-Lite-skill-first
> **版本**: v2.1
> **发布日期**: 2026-04-23
> **核心原则**: 前置 FRZ 统一语义 → SSOT 结构化抽取 → Task Pack 顺序执行 → 双链双轴验证 → 变更分级回流

---

## 目录

1. [系统概览](#1-系统概览)
2. [快速开始](#2-快速开始)
3. [FRZ 冻结层](#3-frz-冻结层)
4. [语义抽取链](#4-语义抽取链)
5. [变更分级与体验修正](#5-变更分级与体验修正)
6. [实施前质量门禁](#6-实施前质量门禁)
7. [Task Pack 任务编排](#7-task-pack-任务编排)
8. [双链双轴测试](#8-双链双轴测试)
9. [常见操作场景](#9-常见操作场景)

---

## 1. 系统概览

v2.0/v2.1 将 SSOT 从"逐层生成链"升级为**语义治理闭环**。核心变化：

```
旧流程（逐层生成，语义漂移）:
  SRC → EPIC → FEAT → TECH/UI/TEST  ❌ 每层都可能脑补

新流程（FRZ 前置，抽取非生成）:
  FRZ（唯一语义真相源）
    ↓ 冻结验证
  SRC → EPIC → FEAT                 ✓ 只能从 FRZ 抽取，不能改写语义
    ↓
  TECH/UI/TEST ← Task Pack 执行 ← 双链验证
    ↓
  变更发生 → 分级（Minor/Major）→ Minor 回写 / Major 回流 FRZ
```

### 7 条核心原则

| # | 原则 | 一句话 |
|---|------|--------|
| 1 | FRZ 唯一语义真相源 | 所有 SSOT 分层语义必须从 FRZ 冻结包中抽取，不得脑补 |
| 2 | 抽取非生成 | SSOT 是 FRZ 的结构化表达，不是 AI 生成物 |
| 3 | 执行语义稳定 | 实施前检测 FRZ 语义是否被静默改写 |
| 4 | 变更分级 | Minor 变更回写 SSOT，Major 变更回流 FRZ |
| 5 | 三轴管理 | FEAT/TECH/UI 各自独立治理 |
| 6 | Task Pack 驱动 | 任务以 Pack 为单位组织，按依赖顺序执行 |
| 7 | 双链双轴验证 | API + E2E 双链，需求轴/实施轴两维治理 |

---

## 2. 快速开始

### 前置条件

- Python 3.9+（推荐 3.13+）
- 项目根目录：`cd E:\ai\LEE-Lite-skill-first`
- 已配置 Claude Code 或 Codex CLI 环境

### 调用方式

本项目的所有功能均通过 **Agent Skill** 方式调用。在 Claude Code 或 Codex CLI 中，直接用自然语言描述你的意图即可触发相应的 skill：

```
"使用 frz-manage skill 验证 <doc-dir> 目录中的文档"
"调用 product-raw-to-src skill 从 FRZ-001 抽取 SRC"
```

### 你的角色对应什么操作？

| 角色 | 你需要做什么 | 从哪节开始读 |
|------|-------------|-------------|
| 产品经理 | 冻结产品文档为 FRZ 包 | [§3 FRZ 冻结层](#3-frz-冻结层) |
| 架构师 | 从 FRZ 抽取 SRC → EPIC → FEAT | [§4 语义抽取链](#4-语义抽取链) |
| 开发者 | 执行 Task Pack 中的任务 | [§7 Task Pack](#7-task-pack-任务编排) |
| 测试工程师 | 双链测试执行（API + E2E） | [ADR-052 双链测试指南](adr052-dual-chain-testing-guide.md) |
| 测试工程师 | 实施前质量门禁检查 | [§6 质量门禁](#6-实施前质量门禁) |
| 任何人提变更 | 描述变更、走分级流程 | [§5 变更分级](#5-变更分级与体验修正) |

---

## 3. FRZ 冻结层

FRZ（Freeze Package）是**唯一语义真相源**。所有 downstream 的分层语义只能从 FRZ 抽取。

### 3.1 验证文档（validate）

将你的产品文档（PRD、UX、架构文档）放入一个目录，然后：

**调用方式**：
```
使用 frz-manage skill 验证文档
输入: <doc-dir>（包含 FRZ YAML 和相关产品文档的目录）
```

**输出**: MSC（Minimum Semantic Completeness）5 维验证报告

MSC 5 个维度：
- **M**inimum — 最小语义完整
- **S**tructured — 结构化表达
- **C**ompleteness — 需求覆盖

如果报告中有缺失维度，你需要补全文档再重新验证。

### 3.2 冻结 FRZ（freeze）

验证通过后，将文档冻结为正式的 FRZ 包：

**调用方式**：
```
使用 frz-manage skill 冻结文档
输入: <doc-dir>（文档目录）
FRZ ID: FRZ-001
```

这个操作会：
1. 自动重新运行 MSC 验证（如果验证失败则拒绝冻结）
2. 将 FRZ 包写入 artifacts 目录，同时保存输入快照
3. 注册到 FRZ 注册表，状态标记为 `frozen`

**注意**: 不允许冻结未通过 MSC 验证的包。

### 3.3 查询 FRZ 注册表（list）

查看所有已注册的 FRZ 包：

**调用方式**：
```
# 查看所有
使用 frz-manage skill 列出所有 FRZ 包

# 只看已冻结的
使用 frz-manage skill 列出状态为 frozen 的 FRZ 包
```

输出包含：FRZ ID、状态、创建时间、MSC 有效性。

### 3.4 FRZ ID 格式

必须是 `FRZ-xxx` 格式（3 位以上数字），例如 `FRZ-001`、`FRZ-042`。

---

## 4. 语义抽取链

从冻结的 FRZ 包出发，按层级抽取 SRC → EPIC → FEAT。每一层都**只能从上游的冻结包抽取**，不能脑补。

### 4.1 FRZ → SRC

> **使用技能**: `product-raw-to-src`

**调用方式**：
```
使用 product-raw-to-src skill 从 FRZ 包抽取 SRC
FRZ 引用: FRZ-001
输出目录: <src-dir>
```

从冻结的 FRZ 包中抽取 SRC（Solution Requirements Candidate）候选。
抽取结果必须保持与 FRZ 的锚点 ID 可追溯。

### 4.2 SRC → EPIC

> **使用技能**: `product-src-to-epic`

**调用方式**：
```
# 步骤 1: Executor 运行
使用 product-src-to-epic skill 执行 SRC 到 EPIC 的抽取
输入: <src-package-dir>
模式: executor-run

# 步骤 2: Supervisor 审查
使用 product-src-to-epic skill 审查 EPIC 输出
输入: <epic-package-dir>
模式: supervisor-review

# 步骤 3: 冻结守卫（语义通过后才能冻结）
使用 product-src-to-epic skill 执行冻结守卫检查
输入: <epic-package-dir>
模式: freeze-guard
```

**关键规则**:
- Executor 不能自我批准自己的输出
- 必须 Supervisor 记录语义通过后才允许冻结
- 输出是一个 `epic_freeze_package`，可直接交给下游 EPIC → FEAT

### 4.3 EPIC → FEAT

> **使用技能**: `product-epic-to-feat`

**调用方式**：
```
# 步骤 1: Executor 运行
使用 product-epic-to-feat skill 执行 EPIC 到 FEAT 的抽取
输入: <epic-package-dir>
模式: executor-run

# 步骤 2: Supervisor 审查
使用 product-epic-to-feat skill 审查 FEAT 输出
输入: <feat-package-dir>
模式: supervisor-review

# 步骤 3: 冻结守卫
使用 product-epic-to-feat skill 执行冻结守卫检查
输入: <feat-package-dir>
模式: freeze-guard
```

**关键规则**:
- 只接受从 `product-src-to-epic` skill 产出的冻结就绪的 EPIC 包
- 不接受原始需求文档或 ADR 文本
- 输出的 FEAT 必须足够强，能直接驱动下游 TECH 和 TESTSET 推导
- 会同步生成 `integration-context.json` 作为 TECH 推导的下游种子

### 4.4 完整链路验证

```
FRZ-001 (冻结)
  ↓
SRC-001 (冻结)
  ↓
EPIC-001 (冻结)
  ↓
FEAT-001 (冻结) → TECH + TESTSET 推导
```

每一步都必须经过 Supervisor 审查和 freeze-guard 守卫。

---

## 5. 变更分级与体验修正

当产品需求发生变化时，不是直接修改 SSOT，而是走**变更分级流程**。

### 5.1 提交变更（patch-capture）

有两种输入方式：

#### 方式 A: 用户自由描述（Prompt-to-Patch）

直接告诉 AI 你要改什么：

```
"把登录页的标题从 'Welcome' 改成 'Sign In'"
```

AI 会：
1. 自动分类变更类型（visual / interaction / semantic）
2. 生成 Patch YAML 草案
3. Supervisor 验证后自动注册

#### 方式 B: 结构化文档输入（Document-to-SRC）

如果你已经有结构化的变更文档：

**调用方式**：
```
使用 product-raw-to-src skill 处理变更文档
输入: <doc-path>
```

AI 会检测文档中是否包含体验层变更，自动生成语义 Patch。

### 5.2 三分类规则

| 变更类型 | 子类型 | 等级 | 后续处理 | 示例 |
|---------|--------|------|---------|------|
| visual | ui_flow, copy_text, layout, navigation, data_display, accessibility | **Minor** | 回写 SSOT | 改按钮文案 |
| interaction | interaction | **Minor** | 回写 UI Spec + Flow Spec + TESTSET | 改按钮交互 |
| semantic | semantic | **Major** | 回流 FRZ，重新冻结 | 新增业务规则 |

**分类逻辑**:
- 扫描所有指标列表，如果语义指标匹配 → GradeLevel.MAJOR
- 如果是 visual + interaction 混合 → confidence=medium
- 如果无指标匹配 → fallback 到文件模式分类

### 5.3 Minor 变更处理（experience-patch-settle）

Minor Patch 验证通过后，自动执行 settlement：

**调用方式**：
```
# 上游 patch-capture skill 已验证并批准的 Minor Patch 会自动进入 settlement
# 也可以手动指定 Patch 文件
使用 experience-patch-settle skill 处理 Minor Patch
输入: <patch-yaml>
```

Settlement 会：
1. 验证 Patch grade_level 必须是 minor（major 会被拒绝）
2. 根据 change_class 确定回写目标
3. 在 `ssot/experience-patches/{feat_ref}/backwrites/` 下生成**回写 RECORD**
4. 将 Patch 状态更新为 `applied`

**重要**: 回写 RECORD 是给人类审核的结构化记录，**不会直接修改 SSOT 文件**。如果需要实际修改 SSOT，需要人工确认。

### 5.4 Major 变更处理（frz-manage revise）

Major Patch 不能走 settlement，必须回流 FRZ：

**调用方式**：
```
使用 frz-manage skill 执行修订冻结
输入: <new-doc-dir>（新文档目录）
前置 FRZ: FRZ-001
原因: "新增 XX 业务规则"
类型: revise
```

这个操作会：
1. 验证新文档的 MSC（与普通 freeze 相同）
2. 检查循环引用链（防止 `FRZ-001 → FRZ-002 → FRZ-001`）
3. 冻结新的 FRZ 包
4. 在 FRZ 注册表中记录 revision chain（parent_frz_ref、reason、revision_type=revise、status=frozen）

**与普通 freeze 的区别**：
- 需要提供 `previous-frz` 和 `reason` 参数
- 注册表中标记为 `revision_type: revise` 而非 `new`
- 会检查循环引用链，防止创建无效的修订环

**revise 之后需要手动重跑抽取链**：
revise 完成后，新的 FRZ 冻结完成，但 SRC/EPIC/FEAT 不会自动更新。
你需要手动重跑：
```
使用 product-raw-to-src skill 从 FRZ-002 抽取 SRC
然后继续 SRC → EPIC → FEAT（executor-run → supervisor-review → freeze-guard）
```

**FRZ 版本链示例**:
```
FRZ-001 (原始冻结)
  ↓ revise（新增业务规则）
FRZ-002 (revised from FRZ-001, reason: "新增 XX 业务规则")
```

---

## 6. 实施前质量门禁

在开始写代码之前，使用 `qa-impl-spec-test` skill 对实施准备情况做压力测试。

### 6.1 运行门禁检查

**调用方式**：
```
使用 qa-impl-spec-test skill 执行实施前质量门禁检查
请求文件: <request.json>
输出文件: <response.json>
```

**request.json** 需要包含：
- IMPL 包引用（已冻结的实现包）
- 关联的 FEAT / TECH / ARCH / API / UI / TESTSET 引用

### 6.2 两种模式

#### Quick Preflight（快速巡检）

轻量级检查，适合日常小变更。

#### Deep Spec Testing（深度测试）

以下情况**强制**走 deep mode：
- 需要迁移
- 涉及核心字段 / 所有权 / 状态边界
- 跨 Surface 主链 + 后链增强
- 新引入 UI / API / State Surface
- 外部门禁候选

### 6.3 Deep Mode 的 9 个维度

| # | 维度 | 检查内容 |
|---|------|---------|
| 1 | 逻辑风险清单 | 失败路径、边界条件 |
| 2 | UX 风险清单 | 交互摩擦、无障碍 |
| 3 | UX 改进清单 | 缺失的体验优化 |
| 4 | 旅程模拟 | 完整用户旅程走通 |
| 5 | 状态不变性检查 | 数据状态转换正确性 |
| 6 | 跨工件追溯 | FEAT→TECH→TEST 一致性 |
| 7 | 开放问题 | 未决决策 |
| 8 | 假阴性挑战 | 是否有遗漏的风险 |
| 9 | 语义稳定性 | FRZ 语义是否被静默改写（Phase 9 新增） |

### 6.4 Verdict 结果

| Verdict | 含义 | 行动 |
|---------|------|------|
| `pass` | 全部通过 | 可以开始实施 |
| `pass_with_revisions` | 有小问题需要修正 | 修完后可以开始 |
| `block` | 有阻塞问题（通常是语义漂移） | **不能开始**，先解决阻塞项 |

---

## 7. Task Pack 任务编排

Task Pack 是**任务组织结构**。每个 Pack 绑定一个 FEAT，包含按依赖关系排序的任务列表。

### 7.1 Task Pack 结构

```yaml
task_pack:
  pack_id: PACK-SRC-001-001-feat001
  feat_ref: FEAT-SRC-001-001
  created_at: "2026-04-20T00:00:00+08:00"
  tasks:
    - task_id: TASK-001
      type: impl
      title: Implement User API endpoint
      depends_on: []
      status: pending
      verifies: [AC-001, AC-002]

    - task_id: TASK-002
      type: test-api
      title: API test for User endpoint
      depends_on: [TASK-001]
      status: pending
      verifies: [AC-001]
```

### 7.2 任务类型

| type | 含义 | 典型内容 |
|------|------|---------|
| `impl` | 实现 | 编写代码 |
| `test-api` | API 测试 | 接口级别测试 |
| `test-e2e` | E2E 测试 | 端到端用户旅程 |
| `review` | 代码审查 | 质量检查 |
| `doc` | 文档 | 文档更新 |
| `gate` | 门禁 | 质量门禁检查 |

### 7.3 任务状态

`pending` → `running` → `passed` / `failed` / `skipped` / `blocked`

### 7.4 验证 Task Pack YAML

**调用方式**：
```
使用 task-pack skill 验证 Task Pack YAML 文件
输入: ssot/tasks/PACK-SRC-001-001-feat001.yaml
```

### 7.5 解析依赖顺序

**调用方式**：
```
使用 task-pack skill 解析依赖顺序
输入: ssot/tasks/PACK-SRC-001-001-feat001.yaml
```

输出示例：
```
OK: ssot/tasks/PACK-SRC-001-001-feat001.yaml
  1. TASK-001
  2. TASK-002
  3. TASK-003
  4. TASK-004
```

### 7.6 手动执行 Task Pack

v2.0/v2.1 的执行循环是**手动顺序执行**：

1. 解析依赖顺序：调用 task-pack skill
2. 按输出顺序逐一执行 task
3. 每个 task 完成后手动更新 `status`
4. 每个 task 完成后运行双链验证（API + E2E）— 详见 [ADR-052 双链测试指南](adr052-dual-chain-testing-guide.md)
5. 如果 task 失败，暂停等待人工介入

**自动执行循环（Pack-03/04/05）已延期到 v2.1 之后的里程碑**。

---

## 8. 双链双轴测试

> **详细操作指南**: [ADR-052 双链测试指南](adr052-dual-chain-testing-guide.md)

v2.0/ADR-047 交付了 11 个 QA 技能。v2.1/ADR-052 在此基础上增加了测试需求轴治理基础设施（Schema 定义层、枚举守卫、治理对象验证器），确保"测什么"由 SSOT 管理。

### 8.1 双链概念

| 链 | 覆盖范围 | 测试类型 |
|---|---------|---------|
| API 链 | 接口级别 | HTTP 请求/响应、参数校验、边界值、异常处理 |
| E2E 链 | 用户旅程级别 | 页面交互、UI 状态、网络事件、数据持久化 |

### 8.2 双轴概念

| 轴 | 管理问题 | 资产性质 |
|---|---------|---------|
| 需求轴 | "测什么？" | 声明性（Plan → Manifest → Spec），可重新编译 |
| 实施轴 | "在哪测？怎么跑？结果是否可信？" | 证据性（执行日志、截图、trace），只追加 |

### 8.3 当前可用的 8 个 QA Skills

| Step | Skill | 产出 |
|------|-------|------|
| 1 | `ll-qa-feat-to-apiplan` | API 测试计划（定义测哪些 API、优先级） |
| 2 | `ll-qa-api-manifest-init` | API 覆盖清单（展开为独立测试项） |
| 3 | `ll-qa-api-spec-gen` | API 测试规范（每个测试项的详细请求/断言） |
| 4 | `ll-qa-prototype-to-e2eplan` | E2E 旅程计划（用户操作流程） |
| 5 | `ll-qa-e2e-manifest-init` | E2E 覆盖清单 |
| 6 | `ll-qa-e2e-spec-gen` | E2E 旅程规范（页面步骤、UI 断言） |
| 7 | `ll-test-exec-cli` / `ll-test-exec-web-e2e` | 实际执行并收集证据 |
| 8 | `ll-qa-settlement` + `ll-qa-gate-evaluate` | 结算报告 + Gate 门禁决策 |

### 8.4 v2.1 新增：治理基础设施

| 模块 | 用途 |
|------|------|
| `testset.yaml` / `environment.yaml` / `gate.yaml` | QA 资产 YAML Schema 定义 |
| `enum_guard.py` | 6 个枚举字段的白名单校验（skill_id、module_id 等） |
| `governance_validator.py` | 11 个治理对象（Skill、Module、Gate 等）的字段校验 |

### 8.5 与 Task Pack 的集成

每个 Task Pack 中的 `test-*` 类型任务对应双链测试中的相应步骤。执行流程：

```
FEAT（冻结）→ Skill 1-6（生成测试计划）
           → Skill 7（执行测试）
           → Skill 8（结算 + Gate 决策）
           → Task Pack 中对应 task 状态更新
```

## 9. 常见操作场景

### 场景 1: 从 0 开始一个新功能

```
1. 准备产品文档（PRD、UX、架构）
2. 使用 frz-manage skill 验证文档
3. 使用 frz-manage skill 冻结文档（FRZ-001）
4. 使用 product-raw-to-src skill 从 FRZ-001 抽取 SRC
5. SRC → EPIC（executor-run → supervisor-review → freeze-guard）
6. EPIC → FEAT（executor-run → supervisor-review → freeze-guard）
7. 创建 Task Pack YAML，定义任务列表
8. 解析依赖顺序，手动执行
9. 每个 task 完成后运行双链验证
```

### 场景 2: 改一个文案（Minor 变更）

```
1. 描述变更："把登录页标题从 Welcome 改成 Sign In"
2. AI 自动分类为 visual → Minor → 生成 UXPATCH
3. Supervisor 验证通过
4. 使用 experience-patch-settle skill 回写 RECORD
5. 人工确认 RECORD，更新 SSOT
```

### 场景 3: 改一个业务规则（Major 变更）

```
1. 描述变更："增加用户角色权限校验"
2. AI 分类为 semantic → Major
3. 使用 frz-manage skill 执行 revise（前置 FRZ-001）
4. 新 FRZ 冻结后，重新走抽取链（SRC → EPIC → FEAT）
5. 更新 Task Pack，重新执行
```

### 场景 4: 实施前检查

```
1. 准备 request.json（包含 IMPL + FEAT/TECH/UI 引用）
2. 使用 qa-impl-spec-test skill 执行门禁检查
3. 查看 verdict：
   - pass → 开始编码
   - block → 先解决问题
```

### 场景 5: 查询所有 FRZ 状态

**调用方式**：
```
使用 frz-manage skill 列出所有 FRZ 包
```

---

## 附录: 文件结构参考

```
ssot/
├── adr/                          # 架构决策记录
│   ├── ADR-050-SSOT语义治理总纲.md
│   ├── ADR-051-TaskPack顺序执行循环模式.md
│   └── ADR-052-测试体系轴化-需求轴与实施轴.md
├── schemas/qa/
│   ├── task_pack.yaml            # Task Pack YAML schema
│   ├── testset.yaml              # TESTSET schema (v2.1)
│   ├── environment.yaml          # Environment schema (v2.1)
│   └── gate.yaml                 # Gate verdict schema (v2.1)
├── tasks/
│   └── PACK-SRC-001-001-feat001.yaml  # Task Pack 示例
└── experience-patches/           # 体验修正 Patch 存储

cli/lib/
├── frz_schema.py                 # FRZ 包 schema + MSC 验证
├── patch_schema.py               # Patch YAML schema
├── task_pack_schema.py           # Task Pack schema 验证
├── task_pack_resolver.py         # Task Pack 依赖解析（拓扑排序）
├── qa_schemas.py                 # QA 资产 schema
├── enum_guard.py                 # 枚举守卫（6 个枚举字段，v2.1）
├── governance_validator.py       # 治理对象验证器（11 个对象，v2.1）
└── protocol.py                   # SSOT 写入路径（集成 enum_guard）

skills/
├── frz-manage/                   # FRZ 生命周期管理技能
├── product-raw-to-src/           # FRZ → SRC 抽取技能
├── product-src-to-epic/          # SRC → EPIC 抽取技能
├── product-epic-to-feat/         # EPIC → FEAT 抽取技能
├── patch-capture/                # 变更捕获 + 三分类技能
├── experience-patch-settle/      # Minor Patch settlement 技能
├── qa-impl-spec-test/            # 实施前质量门禁技能
├── task-pack/                    # Task Pack 管理技能
├── ll-qa-feat-to-apiplan/        # API 测试计划生成（ADR-047）
├── ll-qa-api-manifest-init/      # API 覆盖清单初始化（ADR-047）
├── ll-qa-api-spec-gen/           # API 测试规范生成（ADR-047）
├── ll-qa-prototype-to-e2eplan/   # E2E 旅程计划生成（ADR-047）
├── ll-qa-e2e-manifest-init/      # E2E 覆盖清单初始化（ADR-047）
├── ll-qa-e2e-spec-gen/           # E2E 旅程规范生成（ADR-047）
├── ll-qa-settlement/             # 测试结算报告（ADR-047）
├── ll-qa-gate-evaluate/          # Gate 门禁评估（ADR-047）
├── ll-test-exec-cli/             # API 测试执行引擎（ADR-047）
└── ll-test-exec-web-e2e/         # E2E 测试执行引擎（ADR-047）
```

---

## 附录: Skill 速查表

### FRZ 与语义治理

| Skill 名称 | 用途 | 调用示例 |
|-----------|------|---------|
| `frz-manage` | FRZ 生命周期管理 | "使用 frz-manage skill 验证文档" |
| `product-raw-to-src` | FRZ → SRC 抽取 | "使用 product-raw-to-src skill 从 FRZ-001 抽取 SRC" |
| `product-src-to-epic` | SRC → EPIC 抽取 | "使用 product-src-to-epic skill 执行抽取" |
| `product-epic-to-feat` | EPIC → FEAT 抽取 | "使用 product-epic-to-feat skill 执行抽取" |
| `patch-capture` | 变更捕获与分类 | "描述变更，AI 自动捕获并分类" |
| `experience-patch-settle` | Minor Patch 回写 | "使用 experience-patch-settle skill 处理 Patch" |
| `qa-impl-spec-test` | 实施前质量门禁 | "使用 qa-impl-spec-test skill 执行门禁检查" |
| `task-pack` | Task Pack 管理 | "使用 task-pack skill 解析依赖顺序" |

### 双链测试（ADR-047 / ADR-052）

> **详细操作指南**: [ADR-052 双链测试指南](adr052-dual-chain-testing-guide.md)

| Skill 名称 | 用途 | 对应步骤 |
|-----------|------|---------|
| `ll-qa-feat-to-apiplan` | 从 FEAT 生成 API 测试计划 | Step 1 |
| `ll-qa-api-manifest-init` | 初始化 API 覆盖清单 | Step 2 |
| `ll-qa-api-spec-gen` | 生成 API 测试规范 | Step 3 |
| `ll-qa-prototype-to-e2eplan` | 从原型图生成 E2E 旅程计划 | Step 4 |
| `ll-qa-e2e-manifest-init` | 初始化 E2E 覆盖清单 | Step 5 |
| `ll-qa-e2e-spec-gen` | 生成 E2E 旅程规范 | Step 6 |
| `ll-test-exec-cli` | API 测试执行引擎 | Step 7 |
| `ll-test-exec-web-e2e` | E2E 测试执行引擎（Playwright） | Step 7 |
| `ll-qa-settlement` | 测试结算报告 | Step 8 |
| `ll-qa-gate-evaluate` | Gate 门禁评估（pass/fail） | Step 9 |