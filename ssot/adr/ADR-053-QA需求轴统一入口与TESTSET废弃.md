# ADR-053：QA 需求轴统一入口与 TESTSET 废弃

> **SSOT ID**: ADR-053
> **Title**: 废弃 ll-qa-feat-to-testset，构建 ll-qa-api-from-feat 和 ll-qa-e2e-from-proto 统一入口 skill，补齐双链 acceptance traceability
> **Status**: Draft
> **Version**: v1.1-draft (评审修复版)
> **Effective Date**: TBD
> **Scope**: QA 技能体系 / Skill 入口 / 需求轴架构
> **Owner**: 架构 / QA 治理
> **Governance Kind**: REFINEMENT
> **Audience**: AI 实施代理、QA 技能编排层
> **Depends On**: ADR-047 (双链测试架构), ADR-052 (测试体系轴化)
> **Supersedes**: 部分替代 ADR-052 §2.2 中的 `feat-to-testset` 模块和 Phase 4 `qa.test-plan` 规划

---

## 1. 背景

### 1.1 One-Sentence Summary

> **废弃 `ll-qa-feat-to-testset`（TESTSET 策略层），在 ADR-047 双链框架内补齐 acceptance traceability，同时提供 `ll-qa-api-from-feat`（API 链）和 `ll-qa-e2e-from-proto`（E2E 链）两个统一入口 skill，将用户操作从 6 个独立 skill 简化为 2 个。**

### 1.2 问题

ADR-052 定义了双轴架构（需求轴 + 实施轴），但当前存在以下问题：

#### 1.2.1 TESTSET 与双链功能冗余

`ll-qa-feat-to-testset` 输出的 `test-set.yaml` 包含两层内容：

| 层级 | 内容 | 与双链等价物 |
|------|------|-------------|
| **策略层** | `coverage_scope`, `risk_focus`, `coverage_matrix`, `acceptance_traceability` | 无等价物（但可由 cut rules 隐式覆盖） |
| **执行层** | `test_units`, `functional_areas`, `state_model` | 完全等价于 `api-test-plan.md` 的 capabilities 和 `e2e-journey-plan.md` 的 journeys |

**结论：TESTSET 的执行层内容与双链产出高度重复，维护两套等价的 artifact 是浪费。策略层的内容（coverage_scope, coverage_matrix）虽然在 TESTSET 中是显式的，但在双链框架下可以通过 cut rules + capability × dimension 矩阵隐式覆盖。**

#### 1.2.2 Skill 入口过碎

当前用户需要手动按顺序调用 6 个 skill：

```
/ll-qa-feat-to-apiplan       → api-test-plan.md
/ll-qa-api-manifest-init     → api-coverage-manifest.yaml
/ll-qa-api-spec-gen          → api-test-spec/SPEC-*.md
/ll-qa-prototype-to-e2eplan  → e2e-journey-plan.md
/ll-qa-e2e-manifest-init     → e2e-coverage-manifest.yaml
/ll-qa-e2e-spec-gen          → e2e-journey-spec/JOURNEY-*.md
```

**用户负担：** 需要理解 6 个 skill 的边界、调用顺序和输入输出关系。认知成本高，容易出错。

#### 1.2.3 Acceptance Traceability 缺失

双链产出（api-test-plan.md, e2e-journey-plan.md）缺少显式的 acceptance 追溯能力：

- `api-test-plan.md` 提取了 capabilities 和优先级，但没有显式建立 acceptance → capability 的映射
- `e2e-journey-plan.md` 定义了 journeys，但没有显式建立 acceptance → journey 的映射

这导致无法快速回答"这个 acceptance 被哪些测试覆盖了"的问题。

### 1.3 核心决策

1. **废弃 `ll-qa-feat-to-testset`**，其执行层价值已被双链完整覆盖
2. **补齐 acceptance traceability**，在 api-plan 和 e2e-plan 中增加显式的 acceptance 追溯表
3. **构建统一入口 skill**：`ll-qa-api-from-feat` 和 `ll-qa-e2e-from-proto`，内部编排双链子 skill

### 1.4 TESTSET 依赖分析（Phase 1 前置）

> ⚠️ 以下依赖分析由架构师评审发现，需要在 Phase 1 执行前完成验证。

#### 1.4.1 执行引擎依赖

| 组件 | 依赖方式 | 影响 |
|------|---------|------|
| `ll-test-exec-cli` | `ll.contract.yaml` 声明 `upstream_skill: ll-qa-feat-to-testset`，`input/contract.yaml` 要求 `test_set_ref` 来自 TESTSET | 需要更新为接受双链产出（api-coverage-manifest / e2e-coverage-manifest） |
| `ll-test-exec-web-e2e` | 同上 | 同上 |
| `render-testset-view` | 渲染 TESTSET artifact | 废弃 TESTSET 后此 skill 失去输入源，需要废弃或改造 |

#### 1.4.2 CLI 命令层依赖

| 文件 | 依赖方式 | 影响 |
|------|---------|------|
| `cli/commands/skill/command.py:19` | `feat-to-testset` 在合法 action 列表中 | 保留（仅删除 skill 目录，不影响 CLI 路由） |
| `cli/commands/gate/command.py` | `formal.testset.` 前缀的 hold 逻辑 | 需要更新 gate 命令处理双链 formal ref |
| `cli/lib/enum_guard.py:57` | `FEAT_TO_TESTSET = "feat-to-testset"` | 需要保留（enum 值），但标记为 deprecated |
| `cli/lib/formalization_materialize.py` | `materialize_testset()` 函数 | 需要保留（处理历史 TESTSET），但标记为 deprecated |

#### 1.4.3 脚本依赖（需要完全移除）

```
skills/ll-qa-feat-to-testset/scripts/
├── feat_to_testset.py                    # 主入口，可安全移除
├── feat_to_testset_cli_integration.py   # CLI 集成，仅用于 feat-to-testset
├── feat_to_testset_gate_integration.py  # ⚠️ 需要检查 gate 依赖
├── feat_to_testset_review.py            # Review 逻辑，可能被其他 skill 引用
├── feat_to_testset_candidate.py         # Candidate 包构建
├── feat_to_testset_runtime.py           # Runtime 逻辑
├── feat_to_testset_derivation.py       # 派生逻辑
├── feat_to_testset_semantics.py        # 语义分析
├── feat_to_testset_support.py          # 支持函数
├── feat_to_testset_common.py           # 通用函数
├── feat_to_testset_coverage.py         # 覆盖率计算
├── feat_to_testset_profiles.py          # Profile 处理
├── feat_to_testset_units.py            # Units 处理
├── feat_to_testset_units_common.py     # Units 通用
├── feat_to_testset_runner_units.py     # Runner units
├── feat_to_testset_environment.py      # 环境处理
├── feat_to_testset_document_test.py    # 文档测试
├── collect_evidence.sh                  # 证据收集脚本
├── freeze_guard.sh                      # 冻结守卫脚本
├── validate_input.sh                    # 输入验证脚本
└── validate_output.sh                   # 输出验证脚本
```

**关键发现**：
- `feat_to_testset_gate_integration.py` 可能与 gate 评估有依赖，需要单独分析
- 其他脚本均为 feat-to-testset 专用，可安全移除

#### 1.4.4 ADR 引用

| ADR | 引用位置 | 影响 |
|-----|---------|------|
| ADR-012 | 定义 feat-to-testset 为标准方案 | 标记为 deprecated |
| ADR-035 | TESTSET 驱动的需求覆盖 | 需要更新，引用双链方案 |
| ADR-047 | QA skill 架构 | 需要补充 ll-qa-api-from-feat 等新 skill |
| ADR-052 | Phase 4 qa.test-plan 规划 | 被本 ADR 替代 |

---

## 2. 决策

### 2.1 TESTSET 废弃路径

#### 2.1.1 保留内容（迁移）

| TESTSET 内容 | 迁移目标 | 方式 |
|-------------|---------|------|
| `acceptance_traceability` | `api-test-plan.md` + `e2e-journey-plan.md` | 新增 Acceptance Traceability 表 |
| `test_units` → `capabilities` 追溯 | `api-test-plan.md` | capability 关联 acceptance_ref |
| `test_units` → `journeys` 追溯 | `e2e-journey-plan.md` | journey 关联 acceptance_ref |

#### 2.1.2 移除内容

| 内容 | 移除理由 |
|------|----------|
| `coverage_scope` | cut rules 已隐式定义 scope |
| `risk_focus` | 双链产出不需要显式 risk focus |
| `coverage_matrix` | capability × dimension 矩阵已隐式覆盖 |
| `functional_areas` | 等价于 api-plan capabilities 按对象分组 |
| `state_model` | 等价于 e2e-plan 中的 state constraints |

#### 2.1.3 废弃清单

| 组件 | 废弃方式 | 时间 |
|------|---------|------|
| `skills/ll-qa-feat-to-testset/` | Phase 1 标记废弃，Phase 2 完全移除 | v2.2 |
| `scripts/feat_to_testset*.py` | Phase 2 完全移除 | v2.2 |
| `ssot/tests/templates/test-set-production-l3-template.md` | 如无引用，Phase 2 移除 | v2.2 |
| ADR-052 中 feat-to-testset 引用 | 本 ADR 发布后更新 | 发布时 |

#### 2.1.4 废弃状态标注

在 `ll-qa-feat-to-testset/SKILL.md` frontmatter 中添加：

```yaml
---
name: ll-qa-feat-to-testset
deprecated: true
superseded_by:
  - ll-qa-api-from-feat   # 双链 API 链，含 acceptance traceability
  - ll-qa-e2e-from-proto  # 双链 E2E 链，含 acceptance traceability
deprecation_reason: "执行层价值已被 ADR-047 双链完整覆盖，策略层价值迁移至双链产出"
removal_version: "2.2"
migration_guide: |
  - API 链：使用 /ll-qa-api-from-feat
  - E2E 链：使用 /ll-qa-e2e-from-proto
  - acceptance traceability：已在两个统一入口 skill 的产出物中补齐
---
```

**同时在 SKILL.md 首行添加强提示**（确保用户调用时能看到警告）：

```markdown
> ⚠️ DEPRECATED: This skill is deprecated as of v2.1 and will be removed in v2.2.
> Use `/ll-qa-api-from-feat` for API test chain or `/ll-qa-e2e-from-proto` for E2E test chain.
>
> **Migration Guide:**
> - API 链：`/ll-qa-api-from-feat`（一次性跑完 api-plan → manifest → spec）
> - E2E 链：`/ll-qa-e2e-from-proto`（一次性跑完 e2e-plan → manifest → spec）
> - Acceptance traceability：已在统一入口 skill 的产出物中补齐
```

#### 2.1.5 执行引擎适配

> ⚠️ **关键发现**：执行引擎（`ll-test-exec-cli`、`ll-test-exec-web-e2e`）依赖 TESTSET 的 `test_set_ref`。
> 废弃 TESTSET 后需要适配双链产出。

**适配方案：**

| 执行引擎 | 当前输入 | 适配后输入 |
|---------|---------|-----------|
| `ll-test-exec-cli` | `test_set_ref` 指向 TESTSET (`test-set.yaml`) | `test_set_ref` 指向 api-coverage-manifest.yaml |
| `ll-test-exec-web-e2e` | `test_set_ref` 指向 TESTSET | `test_set_ref` 指向 e2e-coverage-manifest.yaml |

**合约更新：**

```yaml
# ll-test-exec-cli/input/contract.yaml 更新
test_set_ref:
  description: |
    替换为双链产出：
    - API 链：指向 api-coverage-manifest.yaml (由 ll-qa-api-from-feat 或 ll-qa-api-manifest-init 生成)
    - E2E 链：指向 e2e-coverage-manifest.yaml (由 ll-qa-e2e-from-proto 或 ll-qa-e2e-manifest-init 生成)
    - 遗留支持：仍支持旧的 test-set.yaml（但标记为 deprecated）
  deprecated: false
```

**向后兼容策略：**

- Phase 3（标记废弃）期间：同时接受 TESTSET 和双链 manifest
- Phase 4（完全移除）之后：只接受双链 manifest

### 2.2 Acceptance Traceability 补齐

#### 2.2.1 api-test-plan.md 新增章节

```markdown
## Acceptance Traceability

| Acceptance Ref | Acceptance Scenario (Given-When-Then) | Capability IDs | Covered | Cut Reason |
|----------------|----------------------------------------|----------------|---------|------------|
| AC-001 | Given 候选人包已创建 When 用户提交包 Then 包状态变为已提交 | CAND-SUBMIT-001 | ✅ | — |
| AC-002 | Given 候选人包已提交 When Gate 审批通过 Then 包状态变为已批准 | GATE-APPROVE-001 | ✅ | — |
| AC-003 | Given 候选人包已批准 When 用户发起 handoff Then 启动 handoff 流程 | HANDOFF-INIT-001 | ⚠️ P2 裁剪 | 边界路径 |
```

**要求：**
- 每个 capability 必须关联至少一个 acceptance_ref
- 每个 acceptance 必须映射到至少一个 capability
- cut 记录必须包含 cut_reason

#### 2.2.2 e2e-journey-plan.md 新增章节

```markdown
## Acceptance Traceability

| Acceptance Ref | Acceptance Scenario | Journey IDs | Covered | Notes |
|----------------|---------------------|-------------|---------|-------|
| AC-001 | 用户成功提交候选人包 | JOURNEY-MAIN-001 | ✅ | 主路径覆盖 |
| AC-002 | 提交失败时显示错误并保留输入 | JOURNEY-EXCEPTION-001 | ✅ | 异常路径覆盖 |
```

**要求：**
- 每个 journey 必须关联至少一个 acceptance_ref
- 每个 acceptance 必须映射到至少一个 journey（主路径必须）

### 2.3 统一入口 Skill 定义

#### 2.3.1 ll-qa-api-from-feat

```yaml
---
name: ll-qa-api-from-feat
version: "1.0"
adr: ADR-047, ADR-052, ADR-053
category: qa
chain: api-test
phase: full-chain
supersedes: []  # 保留原 skill 供独立调用
---

# LL QA API From FEAT

One-shot skill that runs the complete API test chain from a frozen FEAT document.

## Input
- feat_freeze_package from ll-product-epic-to-feat
- feat_ref: the selected feature identifier

## Output
- ssot/tests/api/{feat_id}/api-test-plan.md       # 含 Acceptance Traceability
- ssot/tests/api/{feat_id}/api-coverage-manifest.yaml
- ssot/tests/api/{feat_id}/api-test-spec/SPEC-*.md

## Internal Pipeline
1. ll-qa-feat-to-apiplan    (FEAT → api-test-plan, 含 acceptance traceability)
2. ll-qa-api-manifest-init (api-test-plan → api-coverage-manifest)
3. ll-qa-api-spec-gen      (api-coverage-manifest → api-test-specs)

## Options
- --preview: only run up to api-test-plan, stop before manifest-init
- --no-spec: stop after api-coverage-manifest, skip spec-gen
- --target P0|P1|P2: filter by priority

## Orchestrator Behavior

### Error Handling Strategy
```yaml
error_handling:
  strategy: fail-fast  # 在指定阶段失败时停止整个 pipeline
  failure_at:
    apiplan: abort           # api-plan 失败 → 终止
    manifest_init: abort      # manifest-init 失败 → 终止
    spec_gen: continue        # spec-gen 失败 → 保留已生成的 manifest
  artifacts_on_failure: keep # 保留已生成的中间产物供调试
  retry: disabled            # 重试暂不支持
```

### Acceptance Traceability Validation
```yaml
validation:
  acceptance_traceability:
    check_mandatory_mapping: true     # 每个 capability 必须有 AC 映射
    check_complete_coverage: true     # 每个 AC 必须有至少一个 capability 覆盖
    fail_on_incomplete: true         # 不完整时拒绝继续
    validation_point: before_manifest_init  # 在 manifest-init 前验证
```

### Orchestrator State Machine
```
┌─────────────┐
│   START     │ → 验证输入 FEAT 是否冻结
└─────────────┘
      ↓
┌─────────────────┐
│ APIPLAN_RUNNING │ → 调用 ll-qa-feat-to-apiplan
└─────────────────┘
      ↓ (成功)
┌─────────────────────────┐
│ TRACEABILITY_VALIDATING │ → 验证 AC 追溯表完整性
└─────────────────────────┘
      ↓ (通过)
┌─────────────────────┐
│ MANIFEST_RUNNING     │ → 调用 ll-qa-api-manifest-init
└─────────────────────┘
      ↓ (成功)
┌────────────────┐
│ SPEC_RUNNING   │ → 调用 ll-qa-api-spec-gen
└────────────────┘
      ↓ (成功)
┌──────────┐
│ COMPLETE │ ← 产出 api-test-plan + manifest + specs
└──────────┘

失败路径：
  任意阶段失败 → 保留已生成产物 → 返回错误 + 阶段信息
```

## Non-Negotiable Rules
- Same as ll-qa-feat-to-apiplan (input validation, acceptance traceability)
- Same as ll-qa-api-manifest-init (cut rules, four-dimensional status)
- Same as ll-qa-api-spec-gen (spec completeness)
- Acceptance traceability table must be complete before proceeding to manifest-init
- orchestrator 不直接生成 artifact，通过调用子 skill 生成
```

#### 2.3.2 ll-qa-e2e-from-proto

```yaml
---
name: ll-qa-e2e-from-proto
version: "1.0"
adr: ADR-047, ADR-052, ADR-053
category: qa
chain: e2e-test
phase: full-chain
supersedes: []  # 保留原 skill 供独立调用
---

# LL QA E2E From Proto

One-shot skill that runs the complete E2E test chain from a prototype or FEAT.

## Input
- prototype_freeze_package from ll-dev-feat-to-proto
- OR feat_ref from ll-product-epic-to-feat (api-derived mode)

## Output
- ssot/tests/e2e/{proto_id}/e2e-journey-plan.md     # 含 Acceptance Traceability
- ssot/tests/e2e/{proto_id}/e2e-coverage-manifest.yaml
- ssot/tests/e2e/{proto_id}/e2e-journey-spec/JOURNEY-*.md

## Internal Pipeline
1. ll-qa-prototype-to-e2eplan (prototype/FEAT → e2e-journey-plan, 含 acceptance traceability)
2. ll-qa-e2e-manifest-init   (e2e-journey-plan → e2e-coverage-manifest)
3. ll-qa-e2e-spec-gen       (e2e-coverage-manifest → e2e-journey-specs)

## Options
- --preview: only run up to e2e-journey-plan, stop before manifest-init
- --no-spec: stop after e2e-coverage-manifest, skip spec-gen
- --mode proto|api-derived: force mode selection

## Orchestrator Behavior

### Error Handling Strategy
```yaml
error_handling:
  strategy: fail-fast
  failure_at:
    e2eplan: abort             # e2e-plan 失败 → 终止
    manifest_init: abort       # manifest-init 失败 → 终止
    spec_gen: continue         # spec-gen 失败 → 保留已生成的 manifest
  artifacts_on_failure: keep
  retry: disabled
```

### Acceptance Traceability Validation
```yaml
validation:
  acceptance_traceability:
    check_mandatory_mapping: true     # 每个 journey 必须有 AC 映射
    check_complete_coverage: true    # 每个 AC 必须有至少一个 journey 覆盖
    fail_on_incomplete: true
    validation_point: before_manifest_init
```

### Orchestrator State Machine
```
┌─────────────┐
│   START     │ → 验证输入（prototype 或 FEAT 已冻结）
└─────────────┘
      ↓
┌─────────────────┐
│ E2EPLAN_RUNNING │ → 调用 ll-qa-prototype-to-e2eplan
└─────────────────┘
      ↓ (成功)
┌─────────────────────────┐
│ TRACEABILITY_VALIDATING │ → 验证 AC 追溯表完整性
└─────────────────────────┘
      ↓ (通过)
┌─────────────────────┐
│ MANIFEST_RUNNING     │ → 调用 ll-qa-e2e-manifest-init
└─────────────────────┘
      ↓ (成功)
┌────────────────┐
│ SPEC_RUNNING   │ → 调用 ll-qa-e2e-spec-gen
└────────────────┘
      ↓ (成功)
┌──────────┐
│ COMPLETE │ ← 产出 e2e-journey-plan + manifest + specs
└──────────┘
```

## Non-Negotiable Rules
- Same as ll-qa-prototype-to-e2eplan (input validation, acceptance traceability)
- Same as ll-qa-e2e-manifest-init (cut rules, four-dimensional status)
- Same as ll-qa-e2e-spec-gen (spec completeness)
- Acceptance traceability table must be complete before proceeding to manifest-init
- orchestrator 不直接生成 artifact，通过调用子 skill 生成
```

#### 2.3.3 Skill 目录结构

```
skills/
├── ll-qa-api-from-feat/
│   ├── SKILL.md
│   ├── ll.contract.yaml           # skill: ll-qa-api-from-feat, phase: full-chain
│   ├── input/contract.yaml        # feat_freeze_package + feat_ref
│   ├── output/contract.yaml       # api-test-plan + manifest + specs
│   ├── agents/
│   │   ├── orchestrator.md        # 编排三个子 skill
│   │   └── supervisor.md          # 验证完整性
│   ├── evidence/
│   │   ├── execution-evidence.schema.json
│   │   └── supervision-evidence.schema.json
│   └── options.yaml               # --preview, --no-spec, --target
│
└── ll-qa-e2e-from-proto/
    ├── SKILL.md
    ├── ll.contract.yaml           # skill: ll-qa-e2e-from-proto, phase: full-chain
    ├── input/contract.yaml        # prototype OR feat_ref
    ├── output/contract.yaml       # e2e-journey-plan + manifest + specs
    ├── agents/
    │   ├── orchestrator.md
    │   └── supervisor.md
    ├── evidence/
    │   ├── execution-evidence.schema.json
    │   └── supervision-evidence.schema.json
    └── options.yaml
```

### 2.4 目标架构

```
ll-product-epic-to-feat (FEAT frozen)
        │
        ├────────────────────────────────────────────────────┐
        ↓                                                    ↓
ll-qa-api-from-feat                          ll-qa-e2e-from-proto
（API 链统一入口）                              （E2E 链统一入口）
        │                                                    │
        ├── ll-qa-feat-to-apiplan         ←── 内部编排 ──→  ├── ll-qa-prototype-to-e2eplan
        │   (含 Acceptance Traceability 表)                  │   (含 Acceptance Traceability 表)
        ├── ll-qa-api-manifest-init                             ├── ll-qa-e2e-manifest-init
        └── ll-qa-api-spec-gen                                 └── ll-qa-e2e-spec-gen
        ↓                                                    ↓
api-test-plan.md (含 AC 追溯)              e2e-journey-plan.md (含 AC 追溯)
api-coverage-manifest.yaml                 e2e-coverage-manifest.yaml
api-test-spec/SPEC-*.md                   e2e-journey-spec/JOURNEY-*.md
        │                                                    │
        └────────────────┬─────────────────────────────────┘
                         ↓
               ll-test-exec-cli / ll-test-exec-web-e2e
                         ↓
                   ll-qa-settlement
                         ↓
                  ll-qa-gate-evaluate
```

### 2.5 用户体验变化

| Before | After |
|--------|-------|
| 需要手动调用 6 个独立 skill | 只需调用 2 个统一入口 skill |
| 需要理解 skill 边界和调用顺序 | 一个命令跑完全链路 |
| acceptance traceability 分散/缺失 | 统一入口产出物自带 acceptance traceability 表 |
| TESTSET 和双链产出需要维护两套等价 artifact | 单一来源（双链产出），无冗余 |

---

## 3. 实施计划

### Phase 0：依赖分析验证（Phase 1 前置任务）

| 任务 | 负责 | 验收标准 |
|------|------|---------|
| 执行 grep 搜索 `feat_to_testset`、`ll-qa-feat-to-testset` 引用 | - | 完整列出所有依赖方 |
| 检查 `feat_to_testset_gate_integration.py` 与 gate 评估的依赖 | - | 确定是否有不可移除的依赖 |
| 检查 `render-testset-view` 是否有替代方案 | - | 确定该 skill 是否需要废弃或改造 |
| 分析 `ll-test-exec-cli` / `ll-test-exec-web-e2e` 的合约更新需求 | - | 确定适配工作量和方案 |

### Phase 1：增强 acceptance traceability（可独立进行）

| 任务 | 负责 skill | 验收标准 |
|------|-----------|---------|
| 修改 `ll-qa-feat-to-apiplan` 输出模板，新增 `Acceptance Traceability` 表 | ll-qa-feat-to-apiplan | api-test-plan.md 包含 acceptance → capability 映射 |
| 修改 `ll-qa-prototype-to-e2eplan` 输出模板，新增 `Acceptance Traceability` 表 | ll-qa-prototype-to-e2eplan | e2e-journey-plan.md 包含 acceptance → journey 映射 |
| 更新两个 skill 的 semantic-checklist | ll-qa-feat-to-apiplan, ll-qa-prototype-to-e2eplan | 验收清单包含 traceability 检查 |

### Phase 2：创建统一入口 skill（可独立进行）

| 任务 | 负责 skill | 验收标准 |
|------|-----------|---------|
| 创建 `ll-qa-api-from-feat/` 目录结构 | ll-qa-api-from-feat | 目录结构符合 ADR-053 §2.3.3 |
| 编写 `SKILL.md`、`ll.contract.yaml`、`agents/orchestrator.md` | ll-qa-api-from-feat | orchestrator 正确编排三个子 skill |
| 创建 `ll-qa-e2e-from-proto/` 目录结构 | ll-qa-e2e-from-proto | 目录结构符合 ADR-053 §2.3.3 |
| 编写 `SKILL.md`、`ll.contract.yaml`、`agents/orchestrator.md` | ll-qa-e2e-from-proto | orchestrator 正确编排三个子 skill |
| 安装 skill 到全局：`ll skill-install ll-qa-api-from-feat --replace` | - | skill 可被 /ll-qa-api-from-feat 调用 |
| 安装 skill 到全局：`ll skill-install ll-qa-e2e-from-proto --replace` | - | skill 可被 /ll-qa-e2e-from-proto 调用 |

### Phase 3：标记 TESTSET 废弃 + 执行引擎适配

| 任务 | 负责 skill | 验收标准 |
|------|-----------|---------|
| 修改 `ll-qa-feat-to-testset/SKILL.md` 添加 deprecated 标记 + 首行警告 | ll-qa-feat-to-testset | SKILL.md 包含 deprecated frontmatter 和首行警告 |
| 在 `ll.lifecycle.yaml` 添加废弃状态 | ll-qa-feat-to-testset | lifecycle 包含 `archived` 状态 |
| 更新 `ll-test-exec-cli/input/contract.yaml` 支持双链 manifest | ll-test-exec-cli | contract 接受 api-coverage-manifest.yaml |
| 更新 `ll-test-exec-web-e2e/input/contract.yaml` 支持双链 manifest | ll-test-exec-web-e2e | contract 接受 e2e-coverage-manifest.yaml |
| 更新 `ll-test-exec-cli/ll.contract.yaml` 上游 skill 引用 | ll-test-exec-cli | upstream_skill 包含 ll-qa-api-from-feat |
| 更新 `ll-test-exec-web-e2e/ll.contract.yaml` 上游 skill 引用 | ll-test-exec-web-e2e | upstream_skill 包含 ll-qa-e2e-from-proto |
| 更新 `docs/guides/adr052-dual-chain-testing-guide.md` 添加废弃说明 | - | 文档标注 TESTSET 已废弃 |

### Phase 4：完全移除（v2.2）

| 任务 | 验收标准 |
|------|---------|
| 删除 `skills/ll-qa-feat-to-testset/` 目录 | 目录不存在 |
| 删除 `scripts/feat_to_testset*.py` 所有文件 | 文件不存在 |
| 更新 ADR-052 中 feat-to-testset 引用 | ADR-052 不再引用 feat-to-testset |

---

## 4. 风险与缓解

| 风险 | 缓解措施 | 残余风险 |
|------|---------|---------|
| 统一入口失败时定位困难 | 每个阶段产出物都落盘，失败后可从中间阶段恢复 | 低 |
| 合并后失去独立调用的灵活性 | 保留原 skill（ll-qa-feat-to-apiplan 等），仅新增统一入口 | 无 |
| TESTSET 废弃后有依赖方未迁移 | Phase 3 标记废弃 + migration_guide，Phase 4 前不影响 | 低 |
| Acceptance traceability 补齐不完整 | Phase 1 单独验收 traceability 表完整性 | 中 |

---

## 5. 与 ADR-052 的关系

### 5.1 ADR-052 需要更新的部分

| 章节 | 当前内容 | 更新为 |
|------|---------|-------|
| §2.2 用户入口 Skill | `qa.test-plan` 编排 `feat-to-testset` | `qa.test-plan` 已被本 ADR 的 `ll-qa-api-from-feat` + `ll-qa-e2e-from-proto` 替代 |
| §2.3 需求轴内部模块 | `feat-to-testset` 模块 | 移除，TESTSET 策略层已迁移 |
| §3.1 端到端流程 | `feat-to-testset` → TESTSET → Plan/Manifest/Spec | 直接 `FEAT → ll-qa-api-from-feat / ll-qa-e2e-from-proto` |
| §5.2 模块状态表 | `feat-to-testset` 已实现 | 标记为 deprecated |
| §9 迁移路径 Phase 4 | 实现 `qa.test-plan` | 实现本 ADR 的统一入口 skill |

### 5.2 保留的 ADR-052 内容

| 章节 | 保留理由 |
|------|---------|
| 实施轴全部内容 | 本 ADR 不涉及实施轴 |
| Phase 1-3 迁移路径 | 与本 ADR 正交 |
| Gate 评估逻辑 | 与本 ADR 正交 |
| 双轴架构 | 基础架构，本 ADR 依赖 |

---

## 6. 约束

### 6.1 不可变性约束

- Acceptance traceability 表一旦生成不可修改（新增 acceptance_ref 除外）
- Cut 记录不可删除，只能更新 approver + source_ref
- 每个 capability 必须关联至少一个 acceptance_ref
- 每个 acceptance 必须映射到至少一个 capability

### 6.2 执行边界约束

- 统一入口 skill 内部不直接生成 artifact，通过调用子 skill 生成
- Acceptance traceability 表必须在进入 manifest-init 阶段前完成验证
- 统一入口 skill 的 `--preview` 模式不得修改任何文件系统状态

### 6.3 向后兼容约束

- 保留原 skill（ll-qa-feat-to-apiplan 等）供独立调用
- 原 skill 的输出格式不变，新增的 traceability 表作为额外章节
- 废弃的 TESTSET skill 在 Phase 3 前仍可正常调用（仅标记废弃）

---

> 文档版本: v1.1-draft (评审修复版)
> 评审修复内容: 添加 Phase 0 依赖分析、orchestrator 错误处理策略、acceptance traceability 验证、执行引擎适配方案、deprecated 警告提示
> 创建日期: 2026-04-24
> 最后更新: 2026-04-24
> 状态: 待评审（修复后）
