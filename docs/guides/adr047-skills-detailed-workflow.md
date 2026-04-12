# ADR-047 八大 Skill 详细工作流程文档

> **ADR**: ADR-047 (v1.4, Trial Approved)
> **文档类型**: Skill 详细工作流程参考手册
> **适用范围**: 所有使用 ADR-047 双链测试治理架构的项目
> **创建日期**: 2026-04-11
> **维护要求**: 当任一 Skill 的 Execution Protocol 变更时同步更新

---

## 目录

1. [总体架构与 Skill 编排](#1-总体架构与-skill-编排)
2. [Skill 1: ll-qa-feat-to-apiplan](#2-skill-1-ll-qa-feat-to-apiplan)
3. [Skill 2: ll-qa-api-manifest-init](#3-skill-2-ll-qa-api-manifest-init)
4. [Skill 3: ll-qa-api-spec-gen](#4-skill-3-ll-qa-api-spec-gen)
5. [Skill 4: ll-qa-prototype-to-e2eplan](#5-skill-4-ll-qa-prototype-to-e2eplan)
6. [Skill 5: ll-qa-e2e-manifest-init](#6-skill-5-ll-qa-e2e-manifest-init)
7. [Skill 6: ll-qa-e2e-spec-gen](#7-skill-6-ll-qa-e2e-spec-gen)
8. [Skill 7: ll-qa-settlement](#8-skill-7-ll-qa-settlement)
9. [Skill 8: ll-qa-gate-evaluate](#9-skill-8-ll-qa-gate-evaluate)
10. [完整执行链路示例](#10-完整执行链路示例)
11. [四维状态字段详解](#11-四维状态字段详解)
12. [裁剪规则与 cut_record](#12-裁剪规则与-cut_record)
13. [防偷懒治理七项检查](#13-防偷懒治理七项检查)

---

## 1. 总体架构与 Skill 编排

### 1.1 双链架构

ADR-047 将测试体系分为两条独立但最终汇合的测试链：

```
                    ┌─────────────────────────────────┐
                    │        ADR-047 (治理规则)        │
                    └────────────┬────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ FEAT-SRC-*   │   │ PROTOTYPE-*  │   │ BMAD Skills       │
    │ (API 锚点)    │   │ (E2E 锚点)    │   │ (能力层插件)       │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────────┘
           │                  │                  │
           ▼                  ▼                  │
    ┌──────────────┐  ┌──────────────┐           │
    │  API Chain   │  │  E2E Chain   │           │
    │  plan        │  │  plan        │           │
    │    ↓         │  │    ↓         │           │
    │  manifest    │  │  manifest    │           │
    │    ↓         │  │    ↓         │           │
    │  spec        │  │  spec        │           │
    │    ↓         │  │    ↓         │           │
    │  tests       │  │  tests       │           │
    │    ↓         │  │    ↓         │           │
    │  evidence    │  │  evidence    │           │
    │    ↓         │  │    ↓         │           │
    │  settlement  │  │  settlement  │           │
    └──────┬───────┘  └──────┬───────┘           │
           └────────┬────────┘                   │
                    ▼                            │
           ┌──────────────────┐                  │
           │  Gate Evaluator  │◄─────────────────┘
           └────────┬─────────┘
                    ▼
       ┌──────────────────────────┐
       │  release-gate-input.yaml │
       └────────┬────────────────┘
                ▼
       ┌──────────────────┐
       │  CI/CD Consumer  │
       │  (pass/fail)     │
       └──────────────────┘
```

### 1.2 Skill 执行顺序

```
时间线 ─────────────────────────────────────────────────────────────────►

API Chain (左链):
  [1] feat-to-apiplan ──→ [2] api-manifest-init ──→ [3] api-spec-gen
                                                          │
                                                          ▼
                                                   (测试执行引擎)
                                                          │
                                                          ▼
E2E Chain (右链):                                    [7] settlement ──→ [8] gate-evaluate
  [4] prototype-to-e2eplan ──→ [5] e2e-manifest-init ──→ [6] e2e-spec-gen
                                                          │
                                                          ▼
                                                   (测试执行引擎)
                                                          │
                                                          └──────────┘
```

### 1.3 Skill 依赖矩阵

| Skill | 上游依赖 | 下游产出 | 输出路径 |
|-------|----------|----------|----------|
| 1. feat-to-apiplan | 冻结的 FEAT 文档 | api-test-plan.md | `ssot/tests/api/{feat_id}/` |
| 2. api-manifest-init | api-test-plan.md | api-coverage-manifest.yaml | `ssot/tests/api/{feat_id}/` |
| 3. api-spec-gen | api-coverage-manifest.yaml | SPEC-*.md (多个) | `ssot/tests/api/{feat_id}/api-test-spec/` |
| 4. prototype-to-e2eplan | Prototype 流程图 | e2e-journey-plan.md | `ssot/tests/e2e/{prototype_id}/` |
| 5. e2e-manifest-init | e2e-journey-plan.md | e2e-coverage-manifest.yaml | `ssot/tests/e2e/{prototype_id}/` |
| 6. e2e-spec-gen | e2e-coverage-manifest.yaml | JOURNEY-*.md (多个) | `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/` |
| 7. settlement | 执行后的 manifests | settlement reports | `ssot/tests/.artifacts/settlement/` |
| 8. gate-evaluate | manifests + settlements + waivers | release_gate_input.yaml | `ssot/tests/.artifacts/tests/settlement/` |

### 1.4 每个 Skill 的标准结构

每个 Skill 目录包含以下文件：

```
skills/ll-qa-{name}/
├── SKILL.md                 # 主入口：描述 + Execution Protocol + 规则
├── ll.contract.yaml         # 合约定义：治理元数据
├── input/
│   ├── contract.yaml        # 输入契约：前置条件
│   └── semantic-checklist.md # 输入语义检查清单
├── output/
│   ├── contract.yaml        # 输出契约：后置条件
│   └── semantic-checklist.md # 输出语义检查清单
└── agents/
    ├── executor.md          # 执行器代理：负责主要产出
    └── supervisor.md        # 监督器代理：负责验证产出
```

---

## 2. Skill 1: ll-qa-feat-to-apiplan

### 2.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-feat-to-apiplan` |
| **来源** | `ssot/tests/templates/feat-to-api-test-plan.md` 升级 |
| **用途** | 从冻结的 FEAT 文档提取 API capabilities，生成 API 测试计划 |
| **触发场景** | 新 FEAT 通过 gate 后，需要定义 API 测试范围 |
| **上游** | FEAT 文档（冻结状态） |
| **下游** | `ll-qa-api-manifest-init` |
| **执行模式** | 单次执行（FEAT 冻结后执行一次） |

### 2.2 详细执行步骤

#### Step 1: 验证 FEAT 冻结状态

- 读取 FEAT 文档的 `feat_freeze_package`
- 确认 `status = frozen`
- 提取 `feat_id`、`feat_ref`、`generated_at`
- 如果 FEAT 未冻结，拒绝执行并返回错误

#### Step 2: 提取 API Capabilities

- 从 FEAT 的 Scope 部分提取所有 API 相关 capabilities
- 为每个 capability 分配唯一的 `capability_id`（格式：`CAP-{seq}`）
- 根据业务重要性分配 `priority`（P0/P1/P2）：
  - **P0（核心）**: 认证、核心业务 CRUD、状态转换
  - **P1（重要）**: 查询、过滤、排序、辅助操作
  - **P2（边缘）**: 统计、导出、管理操作

#### Step 3: 应用测试维度矩阵

对每个 capability 应用 ADR-047 定义的 8 个测试维度：

| 维度 | 说明 | 默认优先级偏移 |
|------|------|----------------|
| 正常路径 | 标准 happy path | 同 capability |
| 参数校验 | 缺失/类型错误/格式错误的参数 | +0 |
| 边界值 | 空值、极大值、极小值、特殊字符 | +1 |
| 状态约束 | 前置状态不满足时的行为 | +1 |
| 权限与身份 | 未认证、权限不足、角色越权 | +0 |
| 异常路径 | 依赖服务不可用、超时 | +1 |
| 幂等/重试/并发 | 重复提交、并发写入 | +2 |
| 数据副作用 | 数据库状态变更、缓存一致性 | +1 |

#### Step 4: 应用优先级裁剪规则

根据 capability priority 裁剪低优先级维度：

- **P0 capabilities**: 仅裁剪 `幂等/重试/并发` + `边界值` 的极端 case
- **P1 capabilities**: 裁剪 `异常路径` + `幂等/重试/并发` + 部分 `边界值`
- **P2 capabilities**: 仅保留 `正常路径` + `参数校验`

#### Step 5: 生成 api-test-plan.md

生成包含以下部分的测试计划：
- 元数据（feature_id、generated_at、anchor_type=feature）
- 能力范围定义（每个 capability 的 API 端点列表）
- 测试维度矩阵应用结果
- 优先级矩阵（capability × dimension → priority）
- 裁剪说明（被裁剪的项目及原因）

#### Step 6: 输出验证与发射

- 验证：至少 1 个 capability 被提取
- 验证：每个 capability 至少有 2 个测试维度
- 发射到 `ssot/tests/api/{feat_id}/api-test-plan.md`

### 2.3 输入/输出契约

**输入**:
- 冻结的 `feat_freeze_package`（包含 `feat_id`、`status=frozen`、Scope 定义）
- `feat_ref` 指向源文档

**输出**:
- `ssot/tests/api/{feat_id}/api-test-plan.md`

### 2.4 代理分工

- **Executor**: 提取 capabilities、应用维度矩阵、应用裁剪规则、生成计划草案
- **Supervisor**: 验证 capability 完整性、验证维度覆盖、验证裁剪合理性

---

## 3. Skill 2: ll-qa-api-manifest-init

### 3.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-api-manifest-init` |
| **用途** | 从 api-test-plan.md 生成覆盖率清单（manifest），包含四维状态字段 |
| **触发场景** | API 测试计划完成后，需要建立可追踪的覆盖率管理基线 |
| **上游** | `ll-qa-feat-to-apiplan` |
| **下游** | `ll-qa-api-spec-gen` |
| **执行模式** | 单次执行（计划完成后执行一次） |

### 3.2 详细执行步骤

#### Step 1: 验证输入计划

- 读取 `ssot/tests/api/{feat_id}/api-test-plan.md`
- 验证包含 `feature_id`、`capabilities` 数组、`priority_matrix`
- 验证至少 1 个 capability 存在

#### Step 2: 生成覆盖率条目

对每个 `capability × dimension` 组合生成一个 coverage item：

```yaml
- coverage_id: "{capability_id}.{dimension}.{seq}"
  capability: "{capability_name}"
  scenario_type: "{dimension}"
  dimension: "{dimension}"
  priority: P0|P1|P2
  source_feat_ref: "{feat_ref}"
```

#### Step 3: 初始化四维状态字段

每个 item 初始化为：
```yaml
lifecycle_status: designed      # 生命周期：已设计，待执行
mapping_status: unmapped        # 映射状态：尚未映射到具体测试用例
evidence_status: missing        # 证据状态：无证据
waiver_status: none             # 豁免状态：无豁免
```

四维状态的含义和流转：
- `lifecycle_status`: designed → executing → passed|failed|blocked|cut|obsolete
- `mapping_status`: unmapped → mapped → verified
- `evidence_status`: missing → partial → complete
- `waiver_status`: none → pending → approved|rejected

#### Step 4: 应用裁剪规则

- P0 capability 的裁剪项：仅 `幂等/重试/并发` 的极端 case
- P1 capability 的裁剪项：`异常路径` + `幂等/重试/并发` + 部分 `边界值`
- P2 capability 的裁剪项：除 `正常路径` 和 `参数校验` 外的所有维度
- 每个被裁剪的 item 必须有完整的 `cut_record`：
  ```yaml
  cut_record:
    cut_target: lifecycle_status
    cut_reason: "P1 capability, 异常路径裁剪"
    source_ref: "{plan_section_ref}"
    approver: "{approver_id}"
    approved_at: "{timestamp}"
  ```

#### Step 5: 添加辅助字段

每个 item 添加：
```yaml
mapped_case_ids: []          # 映射的测试用例 ID 列表
evidence_refs: []            # 证据文件引用
rerun_count: 0               # 重跑次数
last_run_id: null            # 最后一次运行 ID
obsolete: false              # 是否已废弃
superseded_by: null          # 被哪个 item 替代
```

#### Step 6: 包装元数据

将整个清单包装在 `api_coverage_manifest` 根键下：
```yaml
api_coverage_manifest:
  feature_id: "{feat_id}"
  generated_at: "{timestamp}"
  source_plan_ref: "{plan_file_path}"
  items: [...]
```

#### Step 7-9: 代理执行与验证

- Executor 生成清单草案
- Supervisor 验证：
  - item 数量 >= capability 数量 × 2
  - 所有 item 有完整的四维状态
  - 裁剪项都有 cut_record
  - P0 item 不被裁剪

#### Step 10: 发射

输出到 `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`

### 3.3 不可违反规则

- 没有验证的 plan 输入不得生成 manifest
- 不得跳过任何 capability × dimension 组合
- 不得初始化 lifecycle_status 为 `designed` 或 `cut` 以外的值
- 裁剪项必须有完整 cut_record（approver + source_ref 必填）
- 不得修改 api-test-plan.md 内容（只读）
- item 数量必须 >= plan 中的 capability 数量
- manifest 根键必须是 `api_coverage_manifest`
- P0 item 永远不能被裁剪

---

## 4. Skill 3: ll-qa-api-spec-gen

### 4.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-api-spec-gen` |
| **用途** | 从覆盖率清单生成结构化的 API 测试规范文件 |
| **触发场景** | Manifest 初始化完成后，需要生成可执行的测试规范 |
| **上游** | `ll-qa-api-manifest-init` |
| **下游** | API 测试执行引擎（`ll-test-exec-cli`） |
| **执行模式** | 单次执行（可多次运行以补充新 item） |

### 4.2 详细执行步骤

#### Step 1: 接收 Manifest

- 读取 `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`
- 验证根键为 `api_coverage_manifest`
- 验证 items 数组非空

#### Step 2: 验证 Manifest 结构

- 每个 item 必须有：`coverage_id`、`capability`、`scenario_type`、`dimension`、`priority`
- 每个 item 必须有四维状态字段
- manifest 元数据完整

#### Step 3: 筛选待处理条目

- 仅处理 `lifecycle_status = designed` 的 item
- 跳过 `cut`、`obsolete`、`superseded` 状态的 item

#### Step 4: 为每个条目生成规范文件

在 `ssot/tests/api/{feat_id}/api-test-spec/` 目录下生成 `SPEC-{type}-{seq}.md`：

**规范文件结构**:

```markdown
# SPEC-{TYPE}-{SEQ}: {title}

## Metadata
- spec_id: SPEC-{type}-{seq}
- coverage_id_ref: {coverage_id}
- capability: {capability_name}
- scenario_type: {scenario}
- priority: P0|P1|P2

## Endpoint Definition
- method: GET|POST|PUT|DELETE|PATCH
- path: /api/v1/...
- content_type: application/json
- auth_required: true|false

## Request Schema
- Headers: ...
- Path params: ...
- Query params: ...
- Body: ...

## Expected Response
- Status code: 200|201|400|401|403|404|500
- Response body schema: ...
- Headers: ...

## Assertions
1. Response status matches expected
2. Response body contains required fields
3. ...

## Evidence Required
- response_body: true
- response_headers: true
- request_payload: true
- execution_log: true
- db_state: true|false (if data mutation)

## Anti-False-Pass Checks (P0: at least 3)
1. Verify response is not a generic error page
2. Verify specific field values, not just existence
3. Verify DB state changed as expected
4. ...

## Cleanup
- Test data cleanup steps
- State restoration if needed

## Source References
- FEAT: {feat_ref}
- Coverage: {coverage_id}
```

#### Step 5: Executor 生成 + Supervisor 验证

- Executor 为每个 designed item 生成 spec 文件
- Supervisor 验证每个 spec 包含所有必需章节：
  - metadata 完整
  - endpoint 定义存在
  - request schema 存在
  - expected response 存在
  - assertions 列表非空
  - evidence_required 存在
  - anti_false_pass_checks 存在（P0 至少 3 条）

#### Step 6: 发射

所有 spec 文件输出到 `ssot/tests/api/{feat_id}/api-test-spec/` 目录

### 4.3 不可违反规则

- 不得为 `cut`、`obsolete`、`superseded` 状态的 item 生成 spec
- 每个 spec 必须有完整的 metadata 部分
- 每个 spec 必须有 endpoint 定义
- 每个 spec 必须有 request schema 和 expected response
- 每个 spec 必须有 assertions 列表（非空）
- 每个 spec 必须有 evidence_required 字段
- 每个 spec 必须有 anti_false_pass_checks（P0 至少 3 条）
- 文件名必须唯一
- 请求/响应 schema 必须具体，不得使用泛型描述

### 4.4 输出语义检查清单

- [ ] spec 文件存在于 `ssot/tests/api/{feat_id}/api-test-spec/`
- [ ] spec 文件数量 = 未裁剪的 coverage item 数量
- [ ] 每个 spec 有 metadata 部分
- [ ] 每个 spec 有 endpoint 定义
- [ ] 每个 spec 有 request schema
- [ ] 每个 spec 有 expected response
- [ ] 每个 spec 有 assertions 列表
- [ ] 每个 spec 有 evidence_required
- [ ] 每个 spec 有 anti_false_pass_checks
- [ ] 文件名唯一

---

## 5. Skill 4: ll-qa-prototype-to-e2eplan

### 5.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-prototype-to-e2eplan` |
| **用途** | 从 Prototype 流程图或 FEAT 能力推导 E2E 旅程计划 |
| **触发场景** | Prototype 设计完成后，需要定义 E2E 测试旅程 |
| **上游** | Prototype 流程图 / FEAT 文档 |
| **下游** | `ll-qa-e2e-manifest-init` |
| **执行模式** | 单次执行（Prototype 完成后执行一次） |

### 5.2 双模式支持

本 Skill 支持两种推导模式：

#### 模式 A: Prototype-Driven（原型驱动）

当存在完整的 Prototype 流程图时使用：

```
Prototype 页面流 ──→ 页面间的导航关系 ──→ 用户旅程
```

- 从原型图的页面流提取用户旅程
- 每个页面对应一个 UI 状态检查点
- 页面间的导航对应旅程步骤
- 表单验证点对应异常旅程

#### 模式 B: API-Derived（API 推导）

当没有完整 Prototype 时使用：

```
FEAT Capabilities ──→ 用户可感知的功能 ──→ E2E 旅程
```

- 从 FEAT 的用户可见能力推导
- 将 API capability 映射为用户操作序列
- 至少覆盖主要用户路径

### 5.3 详细执行步骤

#### Step 1: 接收输入

- 接收 Prototype 流程图引用 或 FEAT 文档引用
- 确定 `prototype_id` 或 `feature_id`

#### Step 2: 确定推导模式

- 如果存在完整的 Prototype 流程图 → Prototype-Driven
- 如果仅有 FEAT 能力定义 → API-Derived
- 在计划中标注 `derivation_mode: prototype-driven | api-derived`

#### Step 3: 应用旅程识别规则

使用以下规则表识别旅程：

| 原型元素 | 旅程类型 | 优先级 | 说明 |
|----------|----------|--------|------|
| 完整页面流程 | main | P0 | 从入口到完成的主流程 |
| 表单页面 | validation_failure_exception | P0 | 表单验证失败的处理 |
| 网络请求点 | network_failure_exception | P1 | 网络异常时的降级处理 |
| 条件分支 | branch | P1 | 不同条件下的不同路径 |
| 状态依赖页面 | state_dependency | P1 | 前置状态不满足 |
| 重试/刷新点 | retry | P2 | 重试机制 |
| 跨页面状态保持 | state_persistence | P1 | 数据在页面间的保持 |

#### Step 4: 定义每个旅程

每个旅程包含：
```yaml
- journey_id: "{type}-{seq}"
  journey_type: main|exception|branch|retry|state
  priority: P0|P1|P2
  entry_point:
    page: "{page_name}"
    url: "/path"
    initial_state: {...}
  user_steps:
    - step: 1
      action: "{action_description}"
      expected_feedback: "{expected_ui_response}"
    - step: 2
      ...
  expected_ui_states:
    - checkpoint: "{step_ref}"
      assertions: [...]
  expected_network_events:
    - endpoint: "/api/..."
      method: POST
      expected_status: 200
  expected_persistence:
    - "User data saved to database"
    - "Session token updated"
```

#### Step 5: 验证最小数量

- 至少有 1 个 main journey (P0)
- 至少有 1 个 exception journey
- 如果 P0 journey 数量 = 0，拒绝生成

#### Step 6: 生成计划文档

生成 `e2e-journey-plan.md`：
```markdown
# E2E Journey Plan: {feature_name}

## Metadata
- prototype_id: {id}
- feature_id: {id}
- derivation_mode: prototype-driven|api-derived
- generated_at: {timestamp}
- anchor_type: prototype

## Journeys

### Journey: {journey_id} - {name}
- Type: {journey_type}
- Priority: P0|P1|P2
- Entry Point: ...
- User Steps: ...
- Expected UI States: ...
- Expected Network Events: ...
- Expected Persistence: ...
```

#### Step 7-8: 验证与发射

- Executor 生成计划
- Supervisor 验证：
  - metadata 完整
  - anchor_type = "prototype"
  - derivation_mode 已设置
  - 至少 1 个 P0 journey
  - 至少 1 个 exception journey
  - 每个 journey 有 entry_point 和至少 2 个 user_steps

#### Step 9: 发射

输出到 `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md`

### 5.4 不可违反规则

- 不得在没有验证输入的情况下生成计划
- 不得生成 0 个 journey 的计划
- 每个 journey 必须有 entry_point 和至少 2 个 user_steps
- main journey (P0) 必须存在
- exception journey 必须存在
- 不得将 P0 journey 标记为可裁剪
- 每个 journey 的 user_steps 必须可追溯到原型/FEAT

---

## 6. Skill 5: ll-qa-e2e-manifest-init

### 6.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-e2e-manifest-init` |
| **用途** | 从 e2e-journey-plan.md 生成 E2E 覆盖率清单 |
| **触发场景** | E2E 旅程计划完成后，建立覆盖率管理基线 |
| **上游** | `ll-qa-prototype-to-e2eplan` |
| **下游** | `ll-qa-e2e-spec-gen` |
| **执行模式** | 单次执行 |

### 6.2 详细执行步骤

#### Step 1: 接收旅程计划

- 读取 `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md`
- 验证包含 `prototype_id` 或 `feature_id`、journey 定义
- 验证最小 journey 数量

#### Step 2: 验证计划结构

- 每个 journey 必须有：`journey_id`、`journey_type`、`priority`、`entry_point`、`user_steps`
- 计划元数据完整

#### Step 3: 为每个旅程生成覆盖率条目

```yaml
- coverage_id: "e2e.{journey_type}.{journey_id}"
  journey_id: "{journey_id}"
  journey_type: main|exception|branch|retry|state
  priority: P0|P1|P2
  source_prototype_ref: "{prototype_ref}"
```

#### Step 4: 初始化四维状态字段

```yaml
lifecycle_status: designed
mapping_status: unmapped
evidence_status: missing
waiver_status: none
```

#### Step 5: 应用 E2E 裁剪规则

- P1 exception journey 可在其他位置有等效 P0 覆盖时裁剪
- revisit journey 可被另一个已验证状态的 journey 覆盖时裁剪
- 每个裁剪项必须有 `cut_record`：
  ```yaml
  cut_record:
    cut_target: lifecycle_status
    cut_reason: "等效覆盖已存在"
    source_ref: "{journey_ref}"
    approver: "{approver_id}"
    approved_at: "{timestamp}"
  ```

#### Step 6: 添加辅助字段

```yaml
mapped_case_ids: []
evidence_refs: []
rerun_count: 0
last_run_id: null
obsolete: false
superseded_by: null
```

#### Step 7: 包装元数据

```yaml
e2e_coverage_manifest:
  prototype_id: "{prototype_id}"
  feature_id: "{feature_id}"
  derivation_mode: prototype-driven|api-derived
  generated_at: "{timestamp}"
  source_plan_ref: "{plan_path}"
  items: [...]
```

#### Step 8-10: 代理执行与发射

- Executor 生成清单
- Supervisor 验证：
  - item 数量 >= plan journey 数量
  - 所有 item 有四维状态
  - 裁剪项有完整 cut_record
  - P0 main journey 不被裁剪
- 发射到 `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`

### 6.3 不可违反规则

- 没有验证的 e2e-journey-plan 输入不得生成 manifest
- 不得跳过旅程展开 — 每个旅程至少有一个 coverage item
- 不得初始化 lifecycle_status 为 `designed` 或 `cut` 以外的值
- 裁剪项必须有完整 cut_record（approver + source_ref 必填）
- 不得修改 e2e-journey-plan 内容（只读）
- item 数量必须 >= plan journey 数量
- manifest 根键必须是 `e2e_coverage_manifest`
- main journey (P0) 永远不能被裁剪

### 6.4 输出语义检查清单

- [ ] e2e-coverage-manifest.yaml 存在
- [ ] 根键是 e2e_coverage_manifest
- [ ] 元数据完整（prototype_id, derivation_mode, generated_at, source_plan_ref）
- [ ] items 数组非空
- [ ] 每个 item 有 coverage_id, journey_id, journey_type, priority, 四维状态
- [ ] item 数量 >= plan journey 数量
- [ ] 裁剪项有完整 cut_record
- [ ] P0 main journey 未被裁剪

---

## 7. Skill 6: ll-qa-e2e-spec-gen

### 7.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-e2e-spec-gen` |
| **用途** | 从 E2E 覆盖率清单生成结构化的旅程规范文件 |
| **触发场景** | E2E manifest 初始化完成后，生成可执行的旅程规范 |
| **上游** | `ll-qa-e2e-manifest-init` |
| **下游** | E2E 测试执行引擎（`ll-test-exec-web-e2e`） |
| **执行模式** | 单次执行（可多次运行以补充新 item） |

### 7.2 详细执行步骤

#### Step 1: 接收 Manifest

- 读取 `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`
- 验证根键为 `e2e_coverage_manifest`
- 验证 items 数组非空

#### Step 2: 验证 Manifest 结构

- 每个 item 必须有：`coverage_id`、`journey_id`、`journey_type`、`priority`、`lifecycle_status`
- manifest 元数据完整

#### Step 3: 筛选待处理条目

- 仅处理 `lifecycle_status = designed` 的 item
- 跳过 `cut`、`obsolete`、`superseded` 状态的 item

#### Step 4: 为每个条目生成旅程规范文件

在 `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/` 目录下生成 `JOURNEY-{journey_type}-{seq}.md`：

**规范文件结构**:

```markdown
# JOURNEY-{TYPE}-{SEQ}: {title}

## Spec Metadata
- spec_id: JOURNEY-{type}-{seq}
- coverage_id_ref: {coverage_id}
- journey_id_ref: {journey_id}
- journey_type: {type}
- priority: P0|P1|P2

## Entry Point
- page: "{page_name}"
- url: "/path"
- initial_state:
    - "{state_requirement}"

## User Steps
1. **{action}** → Expected: {ui_feedback}
2. **{action}** → Expected: {ui_feedback}
3. ...

## Expected UI States
- Checkpoint {N}:
    - Element visibility: ...
    - Text content: ...
    - Navigation: ...
    - Error messages: ...
    - Loading states: ...

## Expected Network Events
- Endpoint: {path}
  - Method: {method}
  - Expected status: {code}
  - Response shape: {schema_ref}

## Expected Persistence
- DB records: ...
- Cookies: ...
- Local storage: ...

## Evidence Required
- playwright_trace: true
- screenshot: true
- network_log: true|false
- console_log: true|false
- storage_state: true|false

## Anti-False-Pass Checks
1. Verify page actually navigated (not just URL change)
2. Verify success message is specific, not generic
3. Verify API call was made, not just UI change
4. ...

## Source References
- Prototype: {prototype_ref}
- FEAT: {feat_ref}
- Coverage: {coverage_id}
```

#### Step 5-6: 代理执行与发射

- Executor 生成规范文件
- Supervisor 验证每个 spec：
  - 有 entry_point 部分
  - 有 user_steps 列表
  - 有 expected_ui_states
  - 有 expected_network_events（如果旅程涉及 API 调用）
  - 有 expected_persistence
  - 有 evidence_required（至少 playwright_trace + screenshot）
  - 有 anti_false_pass_checks（P0 至少 3 条）
  - 文件名唯一

#### Step 7: 发射

输出到 `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/` 目录

### 7.3 不可违反规则

- 不得为 `cut`、`obsolete`、`superseded` 状态的 item 生成 spec
- 每个 spec 必须有 evidence_required，至少包含 playwright_trace 和 screenshot
- 每个 spec 必须有 anti_false_pass_checks（至少 1 条，P0 至少 3 条）
- 不得发明无法追溯到原型/FEAT 的 user steps
- 不得生成泛型 UI 断言 — 每个断言必须针对预期状态
- exception journey spec 必须包含错误条件触发器和预期恢复路径
- 如果旅程涉及 API 调用，必须包含 expected_network_events

### 7.4 输出语义检查清单

- [ ] spec 文件存在于 `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/`
- [ ] spec 文件数量 = 未裁剪的 coverage item 数量
- [ ] 每个 spec 有 entry_point 部分
- [ ] 每个 spec 有 user_steps 列表
- [ ] 每个 spec 有 expected_ui_states
- [ ] 每个 spec 有 expected_network_events（如果涉及 API）
- [ ] 每个 spec 有 expected_persistence
- [ ] 每个 spec 有 evidence_required（含 playwright_trace + screenshot）
- [ ] 每个 spec 有 anti_false_pass_checks（P0: 至少 3 条）
- [ ] 文件名唯一

---

## 8. Skill 7: ll-qa-settlement

### 8.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-settlement` |
| **用途** | 测试执行完成后生成结算报告，包含通过/失败/阻塞/未覆盖统计 |
| **触发场景** | API 和 E2E 测试执行全部完成后 |
| **上游** | 测试执行引擎（`ll-test-exec-cli` + `ll-test-exec-web-e2e`） |
| **下游** | `ll-qa-gate-evaluate` |
| **执行模式** | 测试执行完成后执行一次（可重新运行以生成更新报告） |

### 8.2 详细执行步骤

#### Step 1: 接收执行后的 Manifests

- 读取更新后的 `api-coverage-manifest.yaml`（lifecycle_status 和 evidence_status 已更新）
- 读取更新后的 `e2e-coverage-manifest.yaml`（lifecycle_status 和 evidence_status 已更新）

#### Step 2: 计算每条链的统计信息

对每条链计算：

| 统计项 | 计算方式 |
|--------|----------|
| total | manifest 中的总 item 数 |
| designed | lifecycle_status = designed（尚未执行） |
| executed | lifecycle_status ∈ (passed, failed, blocked) 且 evidence_refs 非空 |
| passed | lifecycle_status = passed 且 evidence_status = complete |
| failed | lifecycle_status = failed |
| blocked | lifecycle_status = blocked（依赖失败） |
| uncovered | lifecycle_status = designed（从未执行） |
| cut | lifecycle_status = cut（已批准的裁剪） |
| obsolete | obsolete = true 或 superseded_by 已设置 |
| pass_rate | passed / max(executed - obsolete - approved_waiver, 1) |

**关键规则**:
- 没有 evidence_refs 的 item 不计入 executed
- cut item 不计入 pass rate 的分母
- obsolete item 不计入任何统计（除了 obsolete 计数器）

#### Step 3: 生成 Gap 列表

收集所有 lifecycle_status 为 failed、blocked 或 uncovered 的 item（排除 cut 和 obsolete）：

```yaml
gap_list:
  - coverage_id: "{id}"
    capability: "{cap}"  # API chain
    # or journey_id: "{jid}"  # E2E chain
    lifecycle_status: failed|blocked|uncovered
    reason: "{why}"
```

#### Step 4: 生成 Waiver 列表

收集所有 waiver_status 不为 `none` 的 item：

```yaml
waiver_list:
  - coverage_id: "{id}"
    waiver_status: pending|approved|rejected
    waiver_reason: "{reason}"
```

#### Step 5: 生成链特定的结算报告

**API 结算报告** (`ssot/tests/.artifacts/settlement/api-settlement-report.yaml`):

```yaml
api_settlement:
  feature_id: "{feat_id}"
  generated_at: "{timestamp}"
  statistics:
    total: N
    designed: N
    executed: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    cut: N
    obsolete: N
    pass_rate: X.XX
  gap_list: [...]
  waiver_list: [...]
```

**E2E 结算报告** (`ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`):

```yaml
e2e_settlement:
  prototype_id: "{proto_id}"
  generated_at: "{timestamp}"
  statistics:
    total: N
    designed: N
    executed: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    cut: N
    obsolete: N
    pass_rate: X.XX
    exception_journeys:
      total: N
      executed: N
      passed: N
  gap_list: [...]
  waiver_list: [...]
```

E2E 额外统计：`exception_journeys` 的总数、已执行数、通过数。

#### Step 6-7: 代理执行与验证

- Executor 生成报告
- Supervisor 验证统计自洽性：
  - executed = passed + failed + blocked
  - pass_rate = passed / max(executed, 1)

#### Step 8: 发射

- `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`
- `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`

### 8.3 不可违反规则

- 没有读取更新后的 manifests 不得生成结算报告
- 不得将没有 evidence_refs 的 item 计入 executed
- 不得将 cut item 计入 pass rate 的分母
- obsolete item 只计入 obsolete 计数器
- pass_rate 必须排除 obsolete 和已批准的 waiver item
- Gap 列表必须包含所有 failed、blocked、uncovered item（排除 cut 和 obsolete）
- Waiver 列表必须包含所有 waiver_status 非 none 的 item
- 统计必须自洽：executed = passed + failed + blocked

### 8.4 输出语义检查清单

- [ ] api-settlement-report.yaml 存在
- [ ] e2e-settlement-report.yaml 存在
- [ ] 统计自洽：executed = passed + failed + blocked
- [ ] pass_rate 计算正确
- [ ] gap_list 包含所有 failed/blocked/uncovered
- [ ] waiver_list 包含所有非 none waiver
- [ ] E2E 报告包含 exception_journeys 统计

---

## 9. Skill 8: ll-qa-gate-evaluate

### 9.1 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-gate-evaluate` |
| **用途** | 执行发布门禁评估，读取双链结算报告和豁免记录，生成 pass/fail 决策 |
| **触发场景** | 两条链的结算报告都生成后 |
| **上游** | `ll-qa-settlement` + 测试执行引擎 |
| **下游** | CI/CD 流水线、人类门禁编排器（`ll-gate-human-orchestrator`） |
| **执行模式** | 单次执行（结算完成后执行一次） |

### 9.2 详细执行步骤

#### Step 1: 读取所有输入产物

必须读取以下所有文件：
- `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`
- `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`
- `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`
- `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`
- `ssot/tests/.artifacts/settlement/waiver.yaml`

**缺少任何输入文件，拒绝执行。**

#### Step 2: 计算 API 链指标

从 API manifest 和 settlement 计算：
- total items, designed items, executed items, passed items, failed items, blocked items, uncovered items
- pass_rate = passed / (executed - obsolete - approved_waiver)
- 验证 lifecycle_status=passed 的 item 必须有 evidence_status=complete
- waiver_status=pending 的 item 计为 failed

#### Step 3: 计算 E2E 链指标

同样的指标计算方式，额外验证：
- 异常旅程覆盖：必须有 >= 1 个 exception journey 被执行

#### Step 4: 应用 ADR-047 防偷懒七项检查

| # | 检查项 | 验证内容 | 失败条件 |
|---|--------|----------|----------|
| 1 | manifest_frozen | manifest items 在执行前已存在 | items 在执行后被添加 |
| 2 | cut_records_valid | 所有裁剪项有合法 cut_record（含 approver） | 缺少 approver 或 source_ref |
| 3 | pending_waivers_counted | waiver_status=pending 计为 failed | pending waiver 被计为通过 |
| 4 | evidence_consistent | lifecycle_status=passed → evidence_status=complete | 通过但无完整证据 |
| 5 | min_exception_coverage | E2E 有 >= 1 个异常旅程被执行 | 异常旅程覆盖为零 |
| 6 | no_evidence_not_executed | 没有 evidence_refs 的 item 不计入 executed | 无证据 item 被计为已执行 |
| 7 | evidence_hash_binding | 执行日志哈希存在且可验证 | 哈希缺失或不匹配 |

#### Step 5: 生成门禁决策

决策规则：

| 决策 | 条件 |
|------|------|
| **pass** | 两条链 pass_rate >= 80%，所有防偷懒检查通过，证据完整 |
| **conditional_pass** | 一条链达到阈值但有微小差距，waiver 记录覆盖剩余部分 |
| **fail** | 任何一条链低于阈值 或 任何防偷懒检查失败 |

#### Step 6: 计算证据哈希

- 收集两条链所有 evidence_refs 指向的文件内容
- 计算 SHA-256 哈希值
- 用于后续审计追溯

#### Step 7: 生成 release_gate_input.yaml

```yaml
gate_evaluation:
  evaluated_at: "{timestamp}"
  feature_id: "{feat_id}"
  final_decision: pass|fail|conditional_pass
  api_chain:
    total: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    pass_rate: X.XX
    evidence_status: complete|partial|missing
  e2e_chain:
    total: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    pass_rate: X.XX
    exception_journeys_executed: N
    evidence_status: complete|partial|missing
  anti_laziness_checks:
    manifest_frozen: true|false
    cut_records_valid: true|false
    pending_waivers_counted: true|false
    evidence_consistent: true|false
    min_exception_coverage: true|false
    no_evidence_not_executed: true|false
    evidence_hash_binding: true|false
  evidence_hash: "{sha256}"
  decision_reason: "{explanation}"
```

#### Step 8: 代理执行与验证

- Executor 执行评估
- Supervisor 验证决策逻辑正确性

#### Step 9: 发射

输出到 `ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml`

### 9.3 不可违反规则

- 不得在没有读取所有必需输入产物的情况下生成门禁决策
- 不得将 waiver_status=pending 的 item 计为通过 — 必须计为失败
- 不得将没有 evidence_refs 的 item 计为已执行
- 不得允许 lifecycle_status=passed 但 evidence_status=missing/incomplete — 门禁必须拒绝
- 不得在异常旅程覆盖为零时生成通过决策
- 不得跳过任何 7 项防偷懒检查
- final_decision 必须是 `pass`、`fail` 或 `conditional_pass` 之一
- evidence_hash 必须是所有证据文件内容的 SHA-256

---

## 10. 完整执行链路示例

### 10.1 场景：用户登录功能

假设有一个 "用户登录与认证" 功能，FEAT ID 为 `FEAT-SRC-005-001`。

#### 阶段一：API 链构建

```bash
# Step 1: 从冻结的 FEAT 生成 API 测试计划
# 触发: /ll-qa-feat-to-apiplan
# 输入: FEAT-SRC-005-001 (已冻结)
# 输出: ssot/tests/api/FEAT-SRC-005-001/api-test-plan.md
# 产物: 3 个 capabilities (login, logout, token-refresh)
#        × 8 个维度 = 24 个 coverage items (裁剪后 18 个)

# Step 2: 从 API 测试计划生成覆盖率清单
# 触发: /ll-qa-api-manifest-init
# 输入: api-test-plan.md
# 输出: ssot/tests/api/FEAT-SRC-005-001/api-coverage-manifest.yaml
# 产物: 18 个 coverage items，四维状态初始化为 designed/unmapped/missing/none

# Step 3: 从覆盖率清单生成 API 测试规范
# 触发: /ll-qa-api-spec-gen
# 输入: api-coverage-manifest.yaml
# 输出: ssot/tests/api/FEAT-SRC-005-001/api-test-spec/SPEC-*.md (18 个文件)
# 产物: 每个 spec 含 endpoint 定义、request/response schema、assertions、
#        evidence_required、anti_false_pass_checks
```

#### 阶段二：E2E 链构建

```bash
# Step 4: 从 Prototype 流程图生成 E2E 旅程计划
# 触发: /ll-qa-prototype-to-e2eplan
# 输入: Prototype 流程图（含登录页、首页、错误页）
# 输出: ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-journey-plan.md
# 产物: 1 个 main journey (P0), 2 个 exception journeys (P0/P1)

# Step 5: 从 E2E 旅程计划生成覆盖率清单
# 触发: /ll-qa-e2e-manifest-init
# 输入: e2e-journey-plan.md
# 输出: ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-coverage-manifest.yaml
# 产物: 3 个 journey coverage items，四维状态初始化

# Step 6: 从覆盖率清单生成 E2E 旅程规范
# 触发: /ll-qa-e2e-spec-gen
# 输入: e2e-coverage-manifest.yaml
# 输出: ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-journey-spec/JOURNEY-*.md (3 个文件)
# 产物: 每个 spec 含 user_steps、UI 状态断言、网络事件、证据要求
```

#### 阶段三：测试执行

```bash
# API 测试执行（由 ll-test-exec-cli 完成）
# 读取: SPEC-*.md
# 执行: 实际 API 调用
# 更新: api-coverage-manifest.yaml 的 lifecycle_status 和 evidence_status

# E2E 测试执行（由 ll-test-exec-web-e2e 完成）
# 读取: JOURNEY-*.md
# 执行: Playwright 自动化浏览器测试
# 更新: e2e-coverage-manifest.yaml 的 lifecycle_status 和 evidence_status
```

#### 阶段四：结算与门禁

```bash
# Step 7: 生成结算报告
# 触发: /ll-qa-settlement
# 输入: 执行后的两个 manifests
# 输出:
#   - ssot/tests/.artifacts/settlement/api-settlement-report.yaml
#   - ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml
# 产物: 每条链的通过率统计、gap 列表、waiver 列表

# Step 8: 门禁评估
# 触发: /ll-qa-gate-evaluate
# 输入: 两个 manifests + 两个 settlement reports + waiver records
# 输出: ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml
# 产物: final_decision (pass/fail/conditional_pass) + 7 项防偷懒检查结果
```

### 10.2 最终门禁决策示例

```yaml
gate_evaluation:
  evaluated_at: "2026-04-11T10:30:00Z"
  feature_id: "FEAT-SRC-005-001"
  final_decision: pass
  api_chain:
    total: 18
    passed: 16
    failed: 1
    blocked: 0
    uncovered: 1
    pass_rate: 0.89
    evidence_status: complete
  e2e_chain:
    total: 3
    passed: 3
    failed: 0
    blocked: 0
    uncovered: 0
    pass_rate: 1.00
    exception_journeys_executed: 2
    evidence_status: complete
  anti_laziness_checks:
    manifest_frozen: true
    cut_records_valid: true
    pending_waivers_counted: true
    evidence_consistent: true
    min_exception_coverage: true
    no_evidence_not_executed: true
    evidence_hash_binding: true
  evidence_hash: "a1b2c3d4..."
  decision_reason: "Both chains above 80% threshold. All anti-laziness checks pass. Evidence complete."
```

---

## 11. 四维状态字段详解

### 11.1 lifecycle_status（生命周期状态）

追踪测试项从设计到完成的完整生命周期。

| 值 | 含义 | 何时设置 | 设置者 |
|----|------|----------|--------|
| `designed` | 已设计，待执行 | manifest 初始化时 | manifest-init skill |
| `executing` | 正在执行 | 测试引擎开始时 | 测试执行引擎 |
| `passed` | 执行通过 | 测试通过且证据完整 | 测试执行引擎 |
| `failed` | 执行失败 | 测试断言失败 | 测试执行引擎 |
| `blocked` | 被阻塞 | 前置依赖失败 | 测试执行引擎 |
| `cut` | 已裁剪 | 经批准的裁剪 | manifest-init / 人工 |
| `obsolete` | 已废弃 | 功能删除或替换 | 人工 |
| `superseded` | 被替代 | 被新测试项替代 | 人工 |

**状态流转**:
```
designed ──→ executing ──→ passed
                      ├──→ failed ──→ (rerun) ──→ executing
                      └──→ blocked
designed ──→ cut (需 cut_record)
designed ──→ obsolete
```

### 11.2 mapping_status（映射状态）

追踪测试项与实际测试用例的映射关系。

| 值 | 含义 |
|----|------|
| `unmapped` | 尚未映射到具体测试用例 |
| `mapped` | 已映射到测试用例（mapped_case_ids 非空） |
| `verified` | 映射已验证（测试用例正确实现了规范） |

### 11.3 evidence_status（证据状态）

追踪测试执行证据的收集情况。

| 值 | 含义 |
|----|------|
| `missing` | 无证据 |
| `partial` | 部分证据（有 evidence_refs 但不完整） |
| `complete` | 证据完整（所有 required evidence 已收集） |

### 11.4 waiver_status（豁免状态）

追踪测试项的豁免申请和审批状态。

| 值 | 含义 | 对门禁的影响 |
|----|------|-------------|
| `none` | 无豁免 | 正常计入统计 |
| `pending` | 豁免申请中 | **计为 failed** |
| `approved` | 豁免已批准 | 从 pass rate 分母排除 |
| `rejected` | 豁免被拒绝 | 正常计入统计（failed 仍为 failed） |

---

## 12. 裁剪规则与 cut_record

### 12.1 裁剪决策矩阵

| Capability/Journey 优先级 | 可裁剪的维度/旅程 | 不可裁剪的 |
|--------------------------|-------------------|------------|
| **P0** | 仅裁剪 幂等/并发+边界值 的极端 case | 正常路径、参数校验、状态约束、权限、异常路径、数据副作用 |
| **P1** | 异常路径、幂等/重试/并发、部分边界值 | 正常路径、参数校验 |
| **P2** | 除正常路径和参数校验外的所有 | 正常路径、参数校验 |
| **E2E P0 main** | 不可裁剪 | 全部保留 |
| **E2E P1 exception** | 等效覆盖已存在时可裁剪 | — |

### 12.2 cut_record 结构

每个被裁剪的 item 必须包含：

```yaml
cut_record:
  cut_target: lifecycle_status      # 裁剪的目标状态
  cut_reason: "P1 capability, 异常路径裁剪"  # 裁剪原因
  source_ref: "api-test-plan.md#section-x"   # 来源引用
  approver: "user-id-or-name"       # 审批人
  approved_at: "2026-04-11T10:00:00Z"  # 审批时间
```

### 12.3 裁剪验证

在 gate evaluation 时，`cut_records_valid` 检查会验证：
- 所有 cut 状态的 item 都有 cut_record
- cut_record 包含完整的 approver 和 source_ref
- approved_at 在 manifest 生成时间之后、执行开始时间之前

---

## 13. 防偷懒治理七项检查

### 13.1 检查项详细说明

#### 检查 1: manifest_frozen（清单冻结）

**目的**: 防止执行后修改 manifest 来添加通过项

**验证方式**:
- 比较 manifest 文件的 `generated_at` 时间戳
- 比较 manifest items 在执行前后的数量和内容
- 检查是否有 items 在执行后被添加到 manifest

**失败场景**:
- 执行后新增 items 且直接标记为 passed
- manifest 文件在执行后被修改（通过文件修改时间或 git history 验证）

#### 检查 2: cut_records_valid（裁剪记录有效）

**目的**: 确保所有裁剪都是经过审批的正式决定

**验证方式**:
- 遍历所有 lifecycle_status=cut 的 items
- 检查每个 item 的 cut_record 是否存在
- 验证 cut_record 包含：cut_target, cut_reason, source_ref, approver, approved_at

**失败场景**:
- cut item 缺少 cut_record
- cut_record 缺少 approver 或 source_ref

#### 检查 3: pending_waivers_counted（待处理豁免已计入）

**目的**: 防止将未批准的豁免视为通过

**验证方式**:
- 遍历所有 waiver_status=pending 的 items
- 确认这些 items 在 pass rate 计算中被计入 failed

**失败场景**:
- pending waiver items 被排除在 failed 计数之外

#### 检查 4: evidence_consistent（证据一致性）

**目的**: 确保通过的测试都有完整证据支撑

**验证方式**:
- 遍历所有 lifecycle_status=passed 的 items
- 检查每个 item 的 evidence_status 是否为 complete
- 检查 evidence_refs 是否指向有效的证据文件

**失败场景**:
- passed item 的 evidence_status 为 missing 或 partial
- evidence_refs 指向不存在的文件

#### 检查 5: min_exception_coverage（最小异常覆盖）

**目的**: 确保异常路径也被测试覆盖

**验证方式**:
- 检查 E2E settlement 中的 exception_journeys.executed >= 1
- 确认至少有一个 exception journey 被执行（无论通过或失败）

**失败场景**:
- 所有 exception journeys 都为 uncovered

#### 检查 6: no_evidence_not_executed（无证据不算执行）

**目的**: 防止将没有证据的项计为已执行

**验证方式**:
- 遍历所有被计为 executed 的 items
- 确认每个 item 的 evidence_refs 非空
- 如果有 item 的 evidence_refs 为空但 lifecycle_status 不是 designed，标记失败

**失败场景**:
- evidence_refs 为空的 item 被计入 executed 统计

#### 检查 7: evidence_hash_binding（证据哈希绑定）

**目的**: 确保证据文件在门禁评估后未被篡改

**验证方式**:
- 计算所有 evidence_refs 指向文件内容的 SHA-256 哈希
- 将哈希值记录在 release_gate_input.yaml 中
- 后续审计时可重新计算哈希并比对

**失败场景**:
- 无法计算哈希（文件不存在）
- 哈希值与记录不匹配（证据被篡改）

### 13.2 门禁决策逻辑

```
if (any anti_laziness_check == false):
    decision = "fail"
elif (api_pass_rate >= 0.80 and e2e_pass_rate >= 0.80 and
      api_evidence == complete and e2e_evidence == complete):
    decision = "pass"
elif (one chain >= 0.80 and other chain close to threshold and
      waivers cover the gaps):
    decision = "conditional_pass"
else:
    decision = "fail"
```

### 13.3 特殊规则

| 规则 | 说明 |
|------|------|
| pending waiver = failed | waiver_status=pending 的 item 在 pass rate 计算中计为 failed |
| 无证据 ≠ 已执行 | evidence_refs 为空的 item 不计入 executed |
| 异常旅程必须执行 | E2E 的 exception_journeys_executed 必须 >= 1 |
| SHA-256 证据哈希 | evidence_hash 是所有证据文件内容的 SHA-256 |
| 80% 通过率阈值 | API 和 E2E 链的 pass_rate 都必须 >= 80% 才能 pass |

---

## 附录 A: Skill 触发命令速查

| Skill | 触发命令 | 前置条件 |
|-------|----------|----------|
| ll-qa-feat-to-apiplan | `/ll-qa-feat-to-apiplan` | FEAT 文档已冻结 |
| ll-qa-api-manifest-init | `/ll-qa-api-manifest-init` | api-test-plan.md 已存在 |
| ll-qa-api-spec-gen | `/ll-qa-api-spec-gen` | api-coverage-manifest.yaml 已存在 |
| ll-qa-prototype-to-e2eplan | `/ll-qa-prototype-to-e2eplan` | Prototype 流程图或 FEAT 已就绪 |
| ll-qa-e2e-manifest-init | `/ll-qa-e2e-manifest-init` | e2e-journey-plan.md 已存在 |
| ll-qa-e2e-spec-gen | `/ll-qa-e2e-spec-gen` | e2e-coverage-manifest.yaml 已存在 |
| ll-qa-settlement | `/ll-qa-settlement` | 两个 manifests 都已执行更新 |
| ll-qa-gate-evaluate | `/ll-qa-gate-evaluate` | 两个 settlement reports + waivers 已就绪 |

## 附录 B: 文件路径参考

```
ssot/
├── tests/
│   ├── api/
│   │   └── {feat_id}/
│   │       ├── api-test-plan.md                    ← Skill 1 输出
│   │       ├── api-coverage-manifest.yaml          ← Skill 2 输出
│   │       └── api-test-spec/                      ← Skill 3 输出
│   │           ├── SPEC-NORMAL-001.md
│   │           ├── SPEC-VALIDATION-001.md
│   │           └── ...
│   ├── e2e/
│   │   └── {prototype_id}/
│   │       ├── e2e-journey-plan.md                 ← Skill 4 输出
│   │       ├── e2e-coverage-manifest.yaml          ← Skill 5 输出
│   │       └── e2e-journey-spec/                   ← Skill 6 输出
│   │           ├── JOURNEY-MAIN-001.md
│   │           ├── JOURNEY-EXCEPTION-001.md
│   │           └── ...
│   ├── gate/
│   │   └── gate-evaluator.py                      ← 门禁评估脚本
│   ├── templates/
│   │   ├── feat-to-api-test-plan.md
│   │   ├── prototype-to-e2e-journey-plan.md
│   │   └── evidence-collection.md
│   └── .artifacts/
│       ├── api/
│       │   └── reports/
│       │       └── api-settlement-report.md       ← 人类可读报告
│       ├── e2e/
│       │   └── reports/
│       │       └── e2e-settlement-report.md       ← 人类可读报告
│       ├── settlement/
│       │   ├── api-settlement-report.yaml         ← Skill 7 输出
│       │   ├── e2e-settlement-report.yaml         ← Skill 7 输出
│       │   └── waiver.yaml                        ← 豁免记录
│       └── tests/
│           └── settlement/
│               └── release_gate_input.yaml        ← Skill 8 输出
```

## 附录 C: 治理合规检查清单

在每个 Skill 执行完成后，验证以下合规项：

### API Chain 合规

- [ ] api-test-plan.md 包含完整的 capability 提取和维度矩阵
- [ ] api-coverage-manifest.yaml 根键正确，四维状态初始化完整
- [ ] api-test-spec 文件数量 = 未裁剪 coverage item 数量
- [ ] 每个 spec 有 anti_false_pass_checks（P0 ≥ 3）
- [ ] 所有裁剪项有完整 cut_record

### E2E Chain 合规

- [ ] e2e-journey-plan.md 有至少 1 个 P0 + 1 个 exception journey
- [ ] e2e-coverage-manifest.yaml 根键正确，四维状态初始化完整
- [ ] e2e-journey-spec 文件数量 = 未裁剪 coverage item 数量
- [ ] 每个 spec 有 evidence_required（playwright_trace + screenshot）
- [ ] 每个 spec 有 anti_false_pass_checks（P0 ≥ 3）

### Gate 合规

- [ ] 两条链的 settlement reports 已生成
- [ ] 统计自洽：executed = passed + failed + blocked
- [ ] 7 项防偷懒检查全部通过（或 fail 有明确原因）
- [ ] evidence_hash 已计算并记录
- [ ] final_decision 为 pass/fail/conditional_pass 之一
