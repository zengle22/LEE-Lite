# ADR-057：LL v2 SSOT 文件管理规范

> 状态：Draft
> 日期：2026-05-10
> 决策者：Le Zeng
> 适用范围：LL v2 SSOT 对象的文件组织、命名规则与 YAML 模板定义
> 关联文档：ADR-008（v1 文件标准基线）、ADR-056（LL v2 架构）、`ITERATION-DOCUMENT-CHECKLIST.md`

---

## 1. 背景

ADR-056 定义了 LL v2 的架构（frz-ingest + impl-verify），但未覆盖以下实现细节：

1. v2 的 SSOT 文件如何组织目录
2. 每个 SSOT 对象类型的文件命名规则
3. 每个 SSOT 对象的 YAML 模板结构
4. Checklist 中的 6 大维度内容如何映射到具体 SSOT 文件和字段
5. v1 与 v2 文件如何共存与区分

本 ADR 补充这些设计，作为 frz-ingest 编译输出的文件标准基线。

### 1.1 与现有 ADR 的关系

| ADR | 关系 |
|-----|------|
| ADR-008 (v1 文件标准基线) | 本 ADR 继承 ADR-008 的对象模型和命名哲学，但针对 v2 容器-章节结构做调整 |
| ADR-056 (LL v2 架构) | 本 ADR 是 ADR-056 §8.3 (SRC schema) 的文件级实现规范 |
| ITERATION-DOCUMENT-CHECKLIST.md | 本 ADR 确保所有 Checklist 条目在 SSOT 文件中有明确归属 |

---

## 2. 问题

### 2.1 v1 文件标准的局限

ADR-008 为 v1 定义了文件标准，但存在以下与 v2 不兼容的点：

1. **独立文件模型 vs 容器-章节模型**：v1 每个 SSOT 对象一个独立文件，v2 的 EPIC/FEAT 是 SRC 的章节
2. **Markdown 格式 vs YAML 格式**：v1 大部分 SSOT 对象用 Markdown，v2 统一使用 YAML
3. **目录混合 vs 目录分离**：v1/v2 文件需要明确区分，避免混淆

### 2.2 Checklist 条目归属不清

`ITERATION-DOCUMENT-CHECKLIST.md` 定义了 6 大维度共 40+ 条必输要素，但未明确每条要素在 SSOT 文件中的具体归属（哪个文件、哪个字段）。

---

## 3. 决策

### 3.1 总体决策

1. **v2 文件与 v1 文件目录分离**，各自独立管理
2. **所有 SSOT 对象统一使用 YAML 格式**，PROTOTYPE 使用 HTML
3. **每个 SSOT 对象类型定义标准 YAML 模板**
4. **Checklist 每条必输要素映射到具体 SSOT 文件和字段**
5. **文件命名继承 ADR-008 的 lineage-first 哲学**，适配 v2 容器结构

### 3.2 格式决策

| 对象类型 | 格式 | 理由 |
|---------|------|------|
| FRZ | YAML | 冻结包元数据，结构化 |
| SRC（含 EPIC/FEAT） | YAML | 需求容器，结构化，机器可解析 |
| TECH | YAML | 技术设计，结构化 |
| ARCH | YAML | 架构设计，结构化 |
| API | YAML | 契约定义，与 OpenAPI 天然兼容 |
| UI | YAML | 交互设计规格，结构化 |
| IMPL | YAML | 实施包，结构化 |
| PROTOTYPE | HTML | 高保真交互原型，需要浏览器渲染 |

---

## 4. 目录结构

### 4.1 v2 目录拓扑

```text
ssot/v2/
  ├── frz/                          # FRZ Package（冻结包元数据）
  │   └── FRZ-{id}__{slug}.yaml
  ├── src/                          # SRC 容器（含嵌套 EPIC/FEAT）
  │   └── SRC-{id}__{slug}.yaml
  ├── tech/                         # TECH 技术设计
  │   └── TECH-{src_id}-{slot}__{slug}.yaml
  ├── arch/                         # ARCH 架构设计
  │   └── ARCH-{src_id}-{slot}__{slug}.yaml
  ├── api/                          # API 契约
  │   └── API-{src_id}-{slot}__{slug}.yaml
  ├── ui/                           # UI 交互设计
  │   └── UI-{src_id}-{slot}__{slug}.yaml
  ├── impl/                         # IMPL 实施包
  │   └── IMPL-{src_id}-{slot}__{slug}.yaml
  └── prototype/                    # PROTOTYPE 高保真原型
      └── PROTO-{src_id}-{slot}__{slug}.html
```

### 4.2 v1 目录（保持不变）

```text
ssot/
  ├── src/                          # v1 SRC（Markdown）
  ├── epic/                         # v1 EPIC（Markdown，独立文件）
  ├── feat/                         # v1 FEAT（Markdown，独立文件）
  ├── tech/                         # v1 TECH（Markdown）
  ├── api/                          # v1 API（YAML）
  ├── impl/                         # v1 IMPL（Markdown）
  ├── testset/                      # v1 TESTSET（YAML）
  ├── ui/                           # v1 UI（Markdown）
  ├── prototype/                    # v1 PROTOTYPE（HTML）
  ├── mapping/                      # 代码落地图
  ├── release_note/                 # 发布记录
  └── adr/                          # 架构决策记录
```

### 4.3 v1/v2 共存规则

```yaml
coexistence_rules:
  directory_separation:
    principle: v2 文件统一放在 ssot/v2/ 下，v1 文件保持原位
    enforcement: frz-ingest 输出时自动写入 ssot/v2/ 目录

  format_detection:
    method: 通过文件 frontmatter 中的 format_version 字段区分
    v1_indicator: format_version 不存在或为 "0.x"
    v2_indicator: format_version: "2.0"

  cross_reference:
    allowed: v2 SSOT 可以引用 v1 SSOT（通过 source_refs）
    constraint: 同一 FRZ Package 内部的 SSOT 链必须格式一致（ADR-056 §8.2 mixed_chain_rules）

  migration:
    strategy: 渐进迁移，不强制
    rule: 新需求使用 v2 格式，旧需求可保持 v1 格式
```

---

## 5. 文件命名规范

### 5.1 命名格式

继承 ADR-008 的 lineage-first 哲学，适配 v2 容器结构：

```text
{TYPE}-{src_id}__{slug}.yaml       # SRC 容器
{TYPE}-{src_id}-{slot}__{slug}.yaml # FEAT 派生对象（TECH/ARCH/API/UI/IMPL）
{TYPE}-{frz_ref}__{slug}.yaml       # FRZ Package
{TYPE}-{src_id}-{slot}__{slug}.html # PROTOTYPE
```

### 5.2 命名示例

```text
# FRZ Package
FRZ-20260510-001__ll-v2-compiler.yaml

# SRC 容器（含 EPIC/FEAT 章节）
SRC-001__bug-lifecycle-closed-loop.yaml

# FEAT 派生对象（同一 FEAT 共享 slot）
TECH-001-004__bug-fix-tech-design.yaml
ARCH-001-004__bug-fix-architecture.yaml
API-001-004__bug-fix-api-contract.yaml
IMPL-001-004__bug-fix-implementation.yaml
UI-001-004__bug-fix-ui-spec.yaml
PROTO-001-004__bug-fix-prototype.html
```

### 5.3 字段说明

| 字段 | 说明 |
|------|------|
| `{TYPE}` | 对象类型前缀：FRZ / SRC / TECH / ARCH / API / UI / IMPL / PROTO |
| `{src_id}` | 所属 SRC 链编号（3 位数字，如 001） |
| `{slot}` | 该对象在 SRC 链内的稳定槽位（3 位数字，如 004） |
| `{slug}` | 人类可读的简短描述（kebab-case） |
| `{frz_ref}` | FRZ Package 唯一标识（格式 FRZ-{YYYYMMDD}-{序号}） |

### 5.4 SRC 容器内的 EPIC/FEAT 编号

SRC 容器内的 EPIC 和 FEAT 不生成独立文件，通过嵌套编号标识：

```yaml
# SRC 容器内
epics:
  - epic_id: EPIC-001-001      # SRC编号-EPIC序号
    feats:
      - feat_id: FEAT-001-001-001  # SRC编号-EPIC序号-FEAT序号
      - feat_id: FEAT-001-001-002
  - epic_id: EPIC-001-002
    feats:
      - feat_id: FEAT-001-002-001
```

---

## 6. YAML 模板定义

### 6.1 FRZ Package 模板

```yaml
# FRZ-{frz_ref}__{slug}.yaml
frz_ref: string                   # FRZ 唯一标识，格式 FRZ-{YYYYMMDD}-{序号}
version: string                   # 版本号，格式 v{major}.{minor}
created_at: timestamp             # 创建时间
format_version: "2.0"             # v2 格式标识
source_package_ref: string        # 源 Design Package 引用

frozen_sot_chain:
  src_ref: string                 # SRC 文件路径引用
  tech_refs: list                 # TECH 文件路径引用列表
  arch_refs: list                 # ARCH 文件路径引用列表
  api_refs: list                  # API 文件路径引用列表
  ui_refs: list                   # UI 文件路径引用列表（可选）
  impl_refs: list                 # IMPL 文件路径引用列表
  prototype_refs: list            # PROTOTYPE 文件路径引用列表（可选）

acceptance_test_cases:
  api_tests: list                 # API 测试用例
  e2e_tests: list                 # E2E 测试用例
  coverage_map: map               # AC → 测试用例映射
  total_ac: int                   # 总 AC 数
  covered_ac: int                 # 已覆盖 AC 数

completeness_check:
  verdict: pass | blocked | partial
  missing_items: list
  warnings: list

alignment_check:
  verdict: pass | fail
  issues: list

drift_check:
  verdict: pass | drift_found
  drift_items: list

evidence_refs:
  source_docs: list               # 源文档引用
  compilation_log: string         # 编译日志引用
```

### 6.2 SRC 容器模板（含 EPIC/FEAT 章节）

```yaml
# SRC-{src_id}__{slug}.yaml
src_id: string
title: string
version: string                   # SRC 版本号
format_version: "2.0"             # v2 格式标识
status: draft | frozen | revised
frozen_at: timestamp              # 冻结时间（冻结后填写）

# === 商业设计维度（Checklist §2.1）===
problem_domain: string            # 问题陈述
business_goal: string             # 产品愿景/业务目标
target_users: list                # 用户画像
triggering_scenarios: list        # 触发场景
scope_boundaries: list            # In Scope 清单
non_goals: list                   # Out of Scope 清单
global_constraints: list          # 全局约束（含成功指标、优先级）
source_refs: list                 # 段落级来源追溯
open_questions: list              # 未关闭问题

# === EPIC 章节（Checklist §2.2 用户旅程）===
epics:
  - epic_id: string               # 格式 EPIC-{src_id}-{序号}
    capability_name: string       # 能力域名称
    user_value: string            # 用户价值
    business_closure: string      # 业务闭环描述
    priority: string              # 优先级（P0/P1/P2）
    included_scenarios: list      # 包含的用户旅程场景
    excluded_scenarios: list      # 排除的场景
    acceptance_theme: string      # 验收主题
    cross_axis_refs:
      ui_refs: list               # 引用的 UI 对象
      tech_refs: list             # 引用的 TECH 对象
      test_refs: list             # 引用的测试对象

    # === FEAT 章节（Checklist §2.2 用户故事 + AC）===
    feats:
      - feat_id: string           # 格式 FEAT-{src_id}-{epic序号}-{feat序号}
        title: string
        user_value: string        # 用户价值（As a / I want / So that）
        trigger: string           # 触发条件
        main_flow: list           # Happy Path（Checklist §5.2）
        alternative_flows: list   # 分支流程
        state_changes: list       # 状态转换（Checklist §2.6）
        business_rules: list      # 业务规则（Checklist §2.4）
        exception_flows: list     # 异常流程（Checklist §2.5）
        acceptance_criteria: list # 验收标准 AC（Checklist §5.1）
        uat_scenarios: list       # UAT 场景
        non_goals: list           # FEAT 级排除项
        dependencies: list        # 依赖关系
        cross_axis_refs:
          ui_refs: list
          tech_refs: list
          api_refs: list
          e2e_refs: list
        gsd_phase_hint:
          recommended_phase: string
          can_be_independently_uat: boolean
          blocking_dependencies: list
        source_refs: list         # 段落级来源追溯
```

### 6.3 TECH 模板

```yaml
# TECH-{src_id}-{slot}__{slug}.yaml
id: string
feat_ref: string                  # 关联的 FEAT ID
src_ref: string                   # 关联的 SRC ID
title: string
format_version: "2.0"
status: draft | frozen | revised

# === 架构设计维度（Checklist §4.1, §4.3, §4.7）===
tech_stack:                       # 技术选型（Checklist §4.1）
  language: string
  framework: string
  database: string
  ai_provider: string
  key_libraries: list

sync_async: list                  # 同步/异步策略（Checklist §4.3）
  # - scenario: string
  #   mode: sync | async
  #   reason: string

non_functional:                   # 非功能性需求（Checklist §4.7）
  performance:
    p99_latency: string
    throughput: string
  security:
    authentication: string
    authorization: string
    data_protection: string
  concurrency: string
  degradation: string

constraints: list                 # 技术约束
risks: list                       # 技术风险
source_refs: list                 # 来源追溯
```

### 6.4 ARCH 模板

```yaml
# ARCH-{src_id}-{slot}__{slug}.yaml
id: string
feat_ref: string
src_ref: string
title: string
format_version: "2.0"
status: draft | frozen | revised

# === 架构设计维度（Checklist §4.2, §4.4, §4.6, §4.8）===
layering:                         # 分层职责（Checklist §4.2）
  # - layer: string
  #   responsibility: string
  #   file_location: string

data_flow:                        # 核心数据流（Checklist §4.4）
  # - step: string
  #   input: string
  #   output: string
  #   transformation: string

storage:                          # 存储方案（Checklist §4.6）
  strategy: string                # 关系型/文档型/混合
  key_entities: list
  jsonb_fields: list
  normalization_notes: string

integration: list                 # 集成点（Checklist §4.8）
  # - service: string
  #   protocol: string
  #   fallback: string

source_refs: list
```

### 6.5 API 模板

```yaml
# API-{src_id}-{slot}__{slug}.yaml
id: string
feat_ref: string
src_ref: string
title: string
format_version: "2.0"
status: draft | frozen | revised

# === 架构设计维度（Checklist §4.5, §4.9）===
version_strategy: string          # 版本策略

endpoints:                        # API 契约（Checklist §4.5）
  - path: string
    method: GET | POST | PUT | PATCH | DELETE
    purpose: string
    consumer: string
    provider: string
    request_schema:
      fields:
        # - name: string
        #   type: string
        #   required: boolean
        #   description: string
    response_schema:
      fields:
        # - name: string
        #   type: string
        #   description: string
    error_codes: list
    compatibility: string
    security_constraints: string
    rate_limit: string
    examples: list

sequence_diagrams:                # 时序图（Checklist §4.9）
  # - scenario: string
  #   diagram: string              # Mermaid/PlantUML 格式
  #   timeout: string
  #   retry_strategy: string
  #   degradation_path: string

source_refs: list
```

### 6.6 UI 模板

```yaml
# UI-{src_id}-{slot}__{slug}.yaml
id: string
feat_ref: string
src_ref: string
title: string
format_version: "2.0"
status: draft | frozen | revised

# === UX 设计维度（Checklist §3.1-3.7）===
design_principles: list           # 设计原则（Checklist §3.1，≥3 条）
  # - principle: string
  #   description: string
  #   example: string

interaction_flow:                 # 核心页面交互流程（Checklist §3.2）
  # - page: string
  #   interactions:
  #     - trigger: string
  #       action: string
  #       result: string

state_expression:                 # 状态表达规则（Checklist §3.3）
  # - state: string
  #   level: string
  #   color: string
  #   icon: string
  #   copy: string

design_tokens:                    # 设计令牌（Checklist §3.4）
  reference: string               # 引用的变量文件
  new_tokens: list                # 新增令牌

copy_style:                       # 文案风格（Checklist §3.5）
  tone: string                    # 口吻
  forbidden_words: list           # 禁忌词
  examples: list                  # 微文案示例（≥3 个场景）

platform_strategy:                # 平台差异（Checklist §3.6）
  h5: list
  miniprogram: list

error_state_ux:                   # 错误状态 UX（Checklist §3.7）
  # - error_type: string
  #   display: string              # toast / empty_state / skeleton / degraded
  #   copy_style: string

prototype_ref: string             # PROTOTYPE 文件路径引用（可选）

source_refs: list
```

### 6.7 IMPL 模板（自包含设计）

> **设计原则**：IMPL 文件是**自包含的（Self-Contained）**。frz-ingest 在编译时将上游对象（FEAT、TECH、ARCH、API、UI）的关键内容完整复制到 IMPL 中，冻结后不再依赖上游链式查找。下游 GSD 执行者拿到 IMPL 即可直接开工。
> 
> **理由**：单文档完整性提升 AI 处理准确率（避免跨文件引用丢失上下文），冻结后上游变更不影响已冻结 IMPL，审计回溯更清晰。

```yaml
# IMPL-{src_id}-{slot}__{slug}.yaml
id: string
feat_ref: string                  # 关联的 FEAT ID（仅元数据，用于审计追溯）
src_ref: string                   # 关联的 SRC ID（仅元数据，用于审计追溯）
title: string
format_version: "2.0"
status: draft | frozen | revised
frozen_at: timestamp              # 冻结时间（冻结后填写）

# === 需求上下文（编译时从 FEAT 复制，自包含）===
requirement_context:
  user_value: string              # 用户价值（As a / I want / So that）
  trigger: string                 # 触发条件
  main_flow: list                 # Happy Path（从 FEAT.main_flow 复制）
  alternative_flows: list         # 分支流程（从 FEAT.alternative_flows 复制）
  business_rules: list            # 业务规则（从 FEAT.business_rules 复制）
  exception_flows: list           # 异常流程（从 FEAT.exception_flows 复制）
  state_changes: list             # 状态转换（从 FEAT.state_changes 复制）
  acceptance_criteria: list       # 验收标准 AC（从 FEAT.acceptance_criteria 复制）
  uat_scenarios: list             # UAT 场景（从 FEAT.uat_scenarios 复制）
  non_goals: list                 # FEAT 级排除项（从 FEAT.non_goals 复制）

# === 技术上下文（编译时从 TECH 复制，自包含）===
tech_context:
  tech_stack:                     # 技术选型
    language: string
    framework: string
    database: string
    ai_provider: string
    key_libraries: list
  sync_async: list                # 同步/异步策略
  non_functional:                 # 非功能性需求
    performance:
      p99_latency: string
      throughput: string
    security:
      authentication: string
      authorization: string
      data_protection: string
    concurrency: string
    degradation: string
  constraints: list               # 技术约束
  risks: list                     # 技术风险

# === 架构上下文（编译时从 ARCH 复制，自包含）===
arch_context:
  layering: list                  # 分层职责
  data_flow: list                 # 核心数据流
  storage:                        # 存储方案
    strategy: string
    key_entities: list
    jsonb_fields: list
    normalization_notes: string
  integration: list               # 集成点

# === API 上下文（编译时从 API 复制，自包含；UI 驱动 FEAT 可选）===
api_context:
  version_strategy: string
  endpoints: list                 # 完整端点定义
    # - path: string
    #   method: GET | POST | PUT | PATCH | DELETE
    #   purpose: string
    #   consumer: string
    #   provider: string
    #   request_schema: map
    #   response_schema: map
    #   error_codes: list
    #   compatibility: string
    #   security_constraints: string
    #   rate_limit: string
    #   examples: list
  sequence_diagrams: list         # 时序图
    # - scenario: string
    #   diagram: string
    #   timeout: string
    #   retry_strategy: string
    #   degradation_path: string

# === UI 上下文（编译时从 UI 复制，可选；仅 UI 驱动 FEAT 需要）===
ui_context:
  design_principles: list
  interaction_flow: list
  state_expression: list
  design_tokens: map
  copy_style: map
  platform_strategy: map
  error_state_ux: list
  prototype_ref: string

# === 工程实施维度（Checklist §6.1-6.5）===
allowed_scope:                    # 实施范围（Checklist §6.1）
  directories: list               # 允许修改的目录
  files: list                     # 允许修改的文件

forbidden_scope: list             # 禁止修改的文件/目录

key_decisions: list               # 关键实现决策（Checklist §6.2）
  # - decision: string
  #   choice: string
  #   rationale: string

dependencies: list                # 依赖关系（Checklist §6.3）
  # - type: phase | feature | pr
  #   ref: string
  #   description: string

rollback_strategy: string         # 回滚策略（Checklist §6.4）

capacity_estimate:                # 性能预估（Checklist §6.5）
  data_volume: string
  qps: string
  ai_token_consumption: string
  storage_growth: string

# === 测试指导（Checklist §5.3-5.6，从 test_design 映射）===
test_guidance:
  boundary_conditions: list       # 边界条件（Checklist §5.3）
    # - field: string
    #   condition: string
    #   expected_behavior: string
  ai_uncertainty_scenarios: list  # AI 不确定性（Checklist §5.4）
    # - scenario: string
    #   system_behavior: string
  test_layering: string           # 测试分层策略（Checklist §5.5）
  testability_notes: string       # 可测性评审结论（Checklist §5.6）

source_refs: list                 # 来源追溯（段落级，冻结后不可修改）
```

### 6.8 PROTOTYPE 模板

PROTOTYPE 使用 HTML 格式，无 YAML 模板。文件要求：

```html
<!-- PROTO-{src_id}-{slot}__{slug}.html -->
<!-- 格式：静态 HTML，无外部依赖 -->
<!-- 必须包含的交互：-->
<!--   - button_responses: 按钮交互响应 -->
<!--   - page_navigation: 页面跳转 -->
<!--   - happy_path: 主流程可走通 -->
<!--   - error_retry_paths: 错误/重试路径 -->
<!-- scope: journey_level（一个 journey 一个原型）-->
```

---

## 7. Checklist 条目完整映射表

### 7.1 商业设计 → SRC

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 1.1 产品愿景/简报 | SRC | business_goal |
| 1.2 需求范围声明 | SRC | scope_boundaries + non_goals |
| 1.3 成功指标 | SRC | global_constraints |
| 1.4 用户画像 | SRC | target_users |
| 1.5 优先级 | SRC > EPIC | priority |

### 7.2 产品设计 → SRC (EPIC/FEAT)

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 2.1 问题陈述 | SRC | problem_domain |
| 2.2 用户故事 + AC | SRC > FEAT | acceptance_criteria |
| 2.3 范围界定 | SRC | scope_boundaries + non_goals |
| 2.4 业务规则 | SRC > FEAT | business_rules |
| 2.5 异常流程 | SRC > FEAT | exception_flows |
| 2.6 状态转换 | SRC > FEAT | state_changes |
| 2.7 Happy Path | SRC > FEAT | main_flow |
| 2.8 分支流程 | SRC > FEAT | alternative_flows |
| 2.9 用户旅程场景 | SRC > EPIC | included_scenarios |

### 7.3 UX 设计 → UI

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 3.1 设计原则 | UI | design_principles |
| 3.2 交互流程 | UI | interaction_flow |
| 3.3 状态表达 | UI | state_expression |
| 3.4 设计令牌 | UI | design_tokens |
| 3.5 文案风格 | UI | copy_style |
| 3.6 平台差异 | UI | platform_strategy |
| 3.7 错误状态 UX | UI | error_state_ux |

### 7.4 架构设计 → TECH / ARCH / API

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 4.1 技术选型 | TECH | tech_stack |
| 4.2 分层职责 | ARCH | layering |
| 4.3 同步/异步 | TECH | sync_async |
| 4.4 核心数据流 | ARCH | data_flow |
| 4.5 API 契约 | API | endpoints |
| 4.6 存储方案 | ARCH | storage |
| 4.7 非功能性需求 | TECH | non_functional |
| 4.8 集成点 | ARCH | integration |
| 4.9 时序图 | API | sequence_diagrams |

### 7.5 测试设计 → SRC > FEAT + IMPL

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 5.1 可测试 AC | SRC > FEAT | acceptance_criteria |
| 5.2 Happy Path | SRC > FEAT | main_flow |
| 5.3 边界条件 | IMPL | test_guidance.boundary_conditions |
| 5.4 AI 不确定性 | IMPL | test_guidance.ai_uncertainty_scenarios |
| 5.5 测试分层策略 | IMPL | test_guidance.test_layering |
| 5.6 可测性评审 | IMPL | test_guidance.testability_notes |

### 7.6 工程实施 → IMPL

| Checklist 条目 | SSOT 文件 | 字段 |
|---|---|---|
| 6.1 实施范围 | IMPL | allowed_scope + forbidden_scope |
| 6.2 关键决策 | IMPL | key_decisions |
| 6.3 依赖关系 | IMPL | dependencies |
| 6.4 回滚策略 | IMPL | rollback_strategy |
| 6.5 性能预估 | IMPL | capacity_estimate |

### 7.7 跨维度/流程性条目

| Checklist 条目 | 处理方式 |
|---|---|
| PRD 可测性预审 (P1-P5) | frz-ingest step_1 输入预检 |
| 质量门 (Q1-Q5) | frz-ingest step_1 内置检查 |
| 红色警戒线 (§3.2) | frz-ingest 编译约束 |
| 语义漂移防控 (§4) | frz-ingest step_3/4 检查逻辑 |
| 变更控制 (§4.4) | FRZ Revise 流程（ADR-056 §12.1） |
| GSD 编码前检查 (§5) | GSD 流程约束 |

---

## 8. 对象关系图

```text
FRZ Package (冻结包)
  │
  ├──→ SRC 容器 (需求基线)
  │      ├──→ EPIC 001 (能力域)
  │      │      ├──→ FEAT 001-001 (功能切片)
  │      │      └──→ FEAT 001-002
  │      └──→ EPIC 002
  │             └──→ FEAT 002-001
  │
  ├──→ TECH (技术设计) ←── feat_ref ──→ FEAT
  ├──→ ARCH (架构设计) ←── feat_ref ──→ FEAT
  ├──→ API  (契约定义)  ←── feat_ref ──→ FEAT
  ├──→ UI   (交互设计)  ←── feat_ref ──→ FEAT (可选)
  ├──→ IMPL (实施包)    ←── feat_ref ──→ FEAT
  └──→ PROTOTYPE (原型) ←── feat_ref ──→ FEAT (可选，HTML)
```

---

## 9. 与 ADR-008 的兼容策略

### 9.1 继承的规则

| ADR-008 规则 | v2 处理 |
|---|---|
| lineage-first 命名 | 继承，适配为 `{TYPE}-{src_id}-{slot}__{slug}` |
| 一份文件一个对象 | 继承（SRC 容器内的 EPIC/FEAT 是章节，不是独立文件） |
| 对象类型前缀 | 继承（FRZ / SRC / TECH / ARCH / API / UI / IMPL / PROTO） |
| 派生对象共享 slot | 继承（同一 FEAT 的 TECH/ARCH/API/IMPL 共享 slot） |

### 9.2 调整的规则

| ADR-008 规则 | v2 调整 |
|---|---|
| 文件格式 Markdown | v2 统一 YAML（PROTOTYPE 用 HTML） |
| EPIC/FEAT 独立文件 | v2 嵌套在 SRC 容器内 |
| 目录混合 | v2 独立目录 `ssot/v2/` |

### 9.3 不变的规则

| ADR-008 规则 | v2 保持 |
|---|---|
| TASK 不作为正式对象 | v2 继续使用 IMPL |
| DEVPLAN/TESTPLAN 不是 SSOT | v2 不引入新的编排视图对象 |
| FEAT 派生对象不串成伪主链 | v2 保持 FEAT → 各派生对象的扁平关系 |

---

## 10. Consequences

### 10.1 正向影响

1. **Checklist 完整覆盖**：40+ 条必输要素每条都有明确的 SSOT 归属，frz-ingest 编译时有据可查
2. **v1/v2 零干扰**：目录完全分离，格式通过 frontmatter 区分，不会混淆
3. **YAML 统一**：所有 SSOT 对象结构化程度一致，机器解析友好，工具链适配成本低
4. **模板明确**：每个对象类型有标准模板，frz-ingest 编译输出格式确定，不自由发挥

### 10.2 代价

1. **可读性下降**：YAML 的长文本可读性不如 Markdown，需依赖 YAML 注释和 block scalar 缓解
2. **迁移成本**：v1 的 Markdown SSOT 需要工具转换才能迁移到 v2 YAML（渐进迁移，非强制）
3. **模板维护**：8 个对象类型的 YAML 模板需要随架构演进同步更新

---

## 11. Rejected Alternatives

### 11.1 继续使用 Markdown 作为 SSOT 格式

拒绝。Markdown 结构化程度不足，不利于机器解析和字段约束校验。YAML 天然支持类型约束和嵌套结构，更适合 AI 处理。

### 11.2 v1/v2 混合目录

拒绝。混合目录增加认知负担，容易混淆格式版本。分离目录更清晰。

### 11.3 EPIC/FEAT 生成独立文件

拒绝。违背 ADR-056 的容器-章节语义。EPIC/FEAT 作为 SRC 章节嵌套，保持需求链的内聚性。

### 11.4 使用 JSON 替代 YAML

拒绝。JSON 不支持注释，长文本处理不如 YAML 的 block scalar，且 v1 的 API 已经使用 YAML。保持一致性更重要。

---

*文档版本：v1.0*
*创建日期：2026-05-10*
