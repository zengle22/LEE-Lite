# ADR-048：SSOT 与双链测试接入 Droid Missions 的统一治理架构

> **SSOT ID**: ADR-048
> **Title**: SSOT 与双链测试接入 Droid Missions 的统一治理架构
> **Status**: Proposed
> **Version**: v1.0
> **Effective Date**: 2026-04-10
> **Scope**: LL / LEE 项目执行引擎接入与运行时统一
> **Owner**: 测试架构 / 质量治理 / 运行时工程
> **Governance Kind**: TRANSFER
> **Audience**: 产品、架构、后端、前端、测试、AI 实施代理、Droid 运行时维护者
> **Depends On**: ADR-047 (v1.4, Trial Approved), SRC-003 (Execution Loop Job Runner)

---

## 1. 背景

### 1.1 One-Sentence Summary

> **SSOT 是需求真相源，双链是测试真相源，Droid Missions 是执行与验证运行时——三者通过 Mission Compiler 串成一条可消费、可结算、可回流的闭环。**

### 1.2 现状分析

ADR-047 完成了双链测试治理架构的定义（v1.4, Trial Approved），覆盖了：

- API 测试链锚定 feat 的功能契约
- E2E 测试链锚定 prototype 的用户旅程
- 四层资产结构（plan → manifest → spec → settlement）
- Manifest 状态机与 gate 统计口径
- 6 层防偷懒机制

SRC-003 定义了 Execution Loop Job Runner 的自动推进运行时语义：

- `ready -> claimed -> running -> done/failed/waiting-human/deadletter` 状态机
- `progression_mode`（auto-continue / hold）控制下游推进
- `input_refs` + `authoritative_input_ref` 结构化消费

**缺口**：双链测试目前停留在"治理定义很好，但还没有与执行引擎打通"的状态。具体表现：

1. **双链的 spec/manifest 是静态文档**，没有被编译为执行器可消费的结构化 mission
2. **执行器没有统一的运行时语义**——当前靠人工接力或松散 skill 调用
3. **gate 决策后的回流路径不清晰**——fail 项如何变成可执行的 fix feature 缺少规范
4. **旧 testset 仍作为独立对象层存在**，造成治理噪声和路径猜测

### 1.3 目标

把双链测试从"治理态"升级为"运行时态"，使其成为 Droid Missions 可直接消费、自动推进、闭环回流的输入。

---

## 2. 决策

### 2.1 分层关系——三真相源

| 真相源 | 职责 | 产出 | 消费者 |
|--------|------|------|--------|
| **SSOT** | 需求真理源（feat/prototype/tech/api） | 冻结的功能契约、用户旅程、技术约束 | Mission Compiler |
| **双链测试** | 测试真理源（manifest/spec/evidence） | 覆盖账本、测试合同、证据结算 | Mission Compiler + Gate |
| **Droid Missions** | 执行与验证运行时 | mission 执行、证据采集、状态回写 | Gate + Fix Feature 回流 |

**关键原则**：

- SSOT 决定"做什么"
- 双链决定"怎么验证"
- Droid 决定"怎么跑"
- 三层不得混层：Droid 不得猜测需求，双链不得替代需求定义，SSOT 不得定义执行细节

### 2.2 完整接入架构

```
                    ┌──────────────────────────────────────────┐
                    │              SSOT 需求层                   │
                    │  feat / prototype / tech / api            │
                    └──────────────────┬───────────────────────┘
                                       │
                    ┌──────────────────┼───────────────────────┐
                    ▼                  ▼                       ▼
          ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐
          │  API 双链     │  │  E2E 双链       │  │  Tech/Arch 约束  │
          │  manifest +  │  │  manifest +     │  │  (可选输入)      │
          │  spec        │  │  spec           │  │                  │
          └──────┬───────┘  └──────┬──────────┘  └────────┬─────────┘
                 │                 │                      │
                 ▼                 ▼                      ▼
          ┌─────────────────────────────────────────────────────────┐
          │              Mission Compiler（编译器层）                 │
          │                                                          │
          │  输入: feat + prototype + manifest + spec               │
          │  输出: features.json + validation-contracts +           │
          │         execution-manifest                               │
          └────────────────────────┬────────────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────────────┐
          │              Droid Missions Runtime（执行层）             │
          │                                                          │
          │  ├─ Worker: API test executor                           │
          │  ├─ Worker: E2E test executor                           │
          │  ├─ Validator: scrutiny-validator (合约验证)             │
          │  └─ Validator: user-testing-validator (用户体验验证)     │
          │                                                          │
          │  输出: execution-evidence + validation-state             │
          └────────────────────────┬────────────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────────────┐
          │              Gate（裁决层）                              │
          │                                                          │
          │  输入: validation-state + evidence + waiver             │
          │  输出: release / conditional_release / block             │
          │         -> milestone decision                            │
          └────────────────────────┬────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────┐  ┌──────────────┐  ┌──────────────┐
            │ Release  │  │ Conditional  │  │ Block ->     │
            │ -> 发布  │  │ -> 带豁免发布 │  │ Fix Feature  │
            └──────────┘  └──────────────┘  └──────┬───────┘
                                                   │
                                                   ▼
                                    ┌──────────────────────────┐
                                    │   Fix Feature 回流        │
                                    │   (新建，非修改原 feat)    │
                                    └────────────┬─────────────┘
                                                 │
                                                 ▼
                                    回到 Mission Compiler 重新进入闭环
```

### 2.3 对象映射规范

旧 testset 正式退出体系，不再作为独立对象层存在。后续统一采用以下映射：

#### 2.3.1 需求对象 -> Droid Feature

| SSOT 对象 | 映射为 | 说明 |
|-----------|--------|------|
| `feat` | `feature` | Droid mission 的基本执行单元，包含 capabilities 列表 |
| `prototype` | `feature` (ui-travel 类型) | 用户旅程类 feature，与 API feature 并行执行 |
| `tech` / `api` | `feature` (technical 类型) | 技术约束类 feature，作为 validation-contract 补充输入 |

#### 2.3.2 双链资产 -> Droid Validation Contract

| 双链资产 | 映射为 | 说明 |
|----------|--------|------|
| `api-coverage-manifest item` | `validation-contract` | 每个 coverage item 编译为一个可执行验证合约 |
| `e2e-coverage-manifest item` | `validation-contract` | 每个 journey coverage item 编译为一个可执行验证合约 |
| `api-test-spec` | `validation-contract.assertions[]` | spec 中的断言、证据要求直接映射 |
| `e2e-journey-spec` | `validation-contract.assertions[]` | journey spec 中的 UI 状态、网络事件、持久化断言直接映射 |

#### 2.3.3 双链状态 -> Droid Validation State

| 双链状态字段 | 映射为 | Droid 行为 |
|-------------|--------|-----------|
| `lifecycle_status: designed` | `validation-state: pending` | 等待调度执行 |
| `lifecycle_status: executed` | `validation-state: running` | 正在执行中 |
| `lifecycle_status: passed` + `evidence_status: complete` | `validation-state: passed` | 验证通过 |
| `lifecycle_status: failed` | `validation-state: failed` | 验证失败，等待 fix |
| `lifecycle_status: blocked` | `validation-state: blocked` | 阻塞，需要人工介入 |
| `waiver_status: approved` | `validation-state: waived` | 已豁免，不计入失败 |

### 2.4 字段级 Mapping Spec

这是编译器实现所需的精确字段映射，一条条钉死。

#### 2.4.1 API Coverage Manifest Item -> Assertion

```yaml
# 输入: api_coverage_manifest.items[i]
coverage_id: "api.plan.create.happy"           # -> assertion.coverage_id (string, required)
feature_id: "feat.training-plan.create"        # -> assertion.feature_id (string, required)
capability: "create_plan"                      # -> assertion.capability (string, required)
endpoint: "POST /api/plans"                    # -> assertion.endpoint (string, required)
scenario_type: "happy_path"                    # -> assertion.scenario_type (string, required)
priority: "P0"                                 # -> assertion.priority (enum: P0|P1|P2, required)
dimensions_covered: ["正常路径", "数据副作用"]   # -> assertion.dimensions[] (string[], required)

# 从 api-test-spec 中补充映射:
# (通过 coverage_id 关联)
preconditions: [...]                           # -> assertion.preconditions[] (string[])
request: {body: {...}}                         # -> assertion.request (object, required for API)
expected:                                      # -> assertion.expected (object, required)
  status_code: 200                             #   -> expected.status_code (integer)
  response_assertions: [...]                   #   -> expected.response_assertions[] (string[])
  side_effect_assertions: [...]                #   -> expected.side_effect_assertions[] (string[])
evidence_required:                             # -> assertion.evidence_required[] (required)
  - request_snapshot
  - response_snapshot
  - db_assertion_result
```

#### 2.4.2 E2E Coverage Manifest Item -> Assertion

```yaml
# 输入: e2e_coverage_manifest.items[i]
coverage_id: "e2e.onboarding.create-plan.main"  # -> assertion.coverage_id (string, required)
journey_id: "journey.onboarding.create-plan"    # -> assertion.journey_id (string, required)
journey_type: "main"                            # -> assertion.journey_type (enum: main|branch|exception|revisit|state, required)
priority: "P0"                                  # -> assertion.priority (enum: P0|P1|P2, required)

# 从 e2e-journey-spec 中补充映射:
# (通过 coverage_id 关联)
entry_point: "/ai-coach/onboarding"             # -> assertion.entry_point (string, required for E2E)
preconditions: [...]                            # -> assertion.preconditions[] (string[])
user_steps: [...]                               # -> assertion.user_steps[] (string[], required)
expected_ui_states: [...]                       # -> assertion.expected_ui_states[] (string[])
expected_network_events: [...]                  # -> assertion.expected_network_events[] (string[])
expected_persistence: [...]                     # -> assertion.expected_persistence[] (string[])
anti_false_pass_checks: [...]                   # -> assertion.anti_false_pass_checks[] (string[], required)
evidence_required:                              # -> assertion.evidence_required[] (required)
  - playwright_trace
  - screenshot_final
  - network_log
  - persistence_assertion
```

#### 2.4.3 Settlement/Gate -> Validation-State / Milestone Decision

```yaml
# 输入: api-settlement + e2e-settlement + waiver
# 输出: release_gate_input.yaml -> Droid milestone decision

release_gate_input:
  api:
    status: "pass"                              # -> validation-state.api-gate (enum: pass|conditional_pass|fail)
    total_items: 15                             # -> stats.api.total (integer)
    passed_items: 14                            # -> stats.api.passed (integer)
    failed_items: 0                             # -> stats.api.failed (integer)
    blocked_items: 0                            # -> stats.api.blocked (integer)
    uncovered_items: 1                          # -> stats.api.uncovered (integer)
    waiver_refs: ["waiver.api.xxx"]             # -> waiver.api_refs[] (string[])
  e2e:
    status: "pass"                              # -> validation-state.e2e-gate (enum: pass|conditional_pass|fail)
    total_items: 8                              # -> stats.e2e.total (integer)
    passed_items: 8                             # -> stats.e2e.passed (integer)
    failed_items: 0                             # -> stats.e2e.failed (integer)
    blocked_items: 0                            # -> stats.e2e.blocked (integer)
    uncovered_items: 0                          # -> stats.e2e.uncovered (integer)
    waiver_refs: []                             # -> waiver.e2e_refs[] (string[])

  # Gate -> Milestone Decision 映射
  final_decision: "release"                     # -> milestone.decision (enum 见 2.5)
  decision_rationale: "All P0/P1 items passed, 1 P2 uncovered with approved waiver"
  evidence_hash: "sha256:abc123..."             # -> milestone.evidence_hash (string, required)
  evaluated_at: "2026-04-10T15:00:00Z"         # -> milestone.evaluated_at (ISO8601, required)
```

#### 2.4.4 Feat/Prototype -> Features.json

```json
{
  "feature_id": "FEAT-SRC-005-001",
  "feature_type": "api",
  "title": "微信登录核心流程",
  "source_refs": {
    "feat": "ssot/feat/FEAT-SRC-005-001__主链候选提交与交接流.md",
    "prototype": "ssot/prototype/PROTOTYPE-FEAT-SRC-005-001.md",
    "tech": "ssot/tech/SRC-005/TECH-SRC-005-001__*.md"
  },
  "capabilities": [
    {
      "capability_id": "wechat-login",
      "endpoint": "POST /v1/auth/login/wechat",
      "description": "微信授权登录",
      "validation_contracts": [
        "vc-api-auth-login-001",
        "vc-e2e-auth-login-001"
      ]
    }
  ],
  "validation_contracts": [
    {
      "contract_id": "vc-api-auth-login-001",
      "chain": "api",
      "source_manifest_item": "api.auth.login.happy",
      "source_spec": "ssot/tests/api/FEAT-SRC-005-001/api-test-spec/SPEC-AUTH-LOGIN-001.md",
      "assertions": [
        {
          "type": "status_code",
          "expected": 200
        },
        {
          "type": "response_field",
          "field": "token",
          "constraint": "present_and_nonempty"
        },
        {
          "type": "side_effect",
          "check": "user_session_created"
        }
      ],
      "evidence_required": ["request_snapshot", "response_snapshot", "db_assertion_result"],
      "priority": "P0"
    }
  ],
  "progression_mode": "auto-continue",
  "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json"
}
```

### 2.5 Gate 与 Milestone 关系

| Gate Decision | Milestone Decision | 含义 | 后续动作 |
|--------------|-------------------|------|---------|
| `release` | `milestone.passed` | 所有 required 项通过，无未豁免失败 | 正式发布，下游消费 |
| `conditional_release` | `milestone.passed_with_waiver` | 存在已审批豁免的 fail/blocked/uncovered | 带条件发布，豁免项进入追踪 |
| `block` | `milestone.failed` | 存在未豁免的 P0/P1 失败 | 创建 Fix Feature 回流 |

**Milestone 决策格式**：

```yaml
milestone:
  feature_id: "FEAT-SRC-005-001"
  decision: "passed" | "passed_with_waiver" | "failed"
  gate_summary:
    api_status: "pass"
    e2e_status: "conditional_pass"
    total_unwaived_failures: 0
    waiver_count: 1
  fix_feature_ids: []                           # decision=failed 时非空
  next_milestone: "release" | "fix-and-retest"
  decided_at: "2026-04-10T15:00:00Z"
```

### 2.6 Fix Feature 回流机制

**为什么必须新建 Fix Feature，而非修改原 feat**：

1. **审计完整性**：原 feat 的 gate 决策是历史事实，不得篡改。修改原 feat 会破坏决策链的不可变性。
2. **状态隔离**：原 feat 已经进入 `block` 里程碑，fix feature 作为新的执行单元从 `ready` 开始推进，避免状态机混乱。
3. **可追踪性**：fix feature 通过 `fixes_for` 字段指向原 feat + 具体失败的 coverage items，形成清晰的修复追踪链。

**Fix Feature 结构**：

```yaml
# ssot/feat/FIX-FEAT-SRC-005-001-001__微信登录-Token-刷新失败修复.md
---
id: FIX-FEAT-SRC-005-001-001
ssot_type: FEAT
parent_feat: FEAT-SRC-005-001
fix_type: gate_remediation
status: proposed
---

# Fix Feature: 微信登录 Token 刷新失败修复

## 修复来源
- **原 Feature**: FEAT-SRC-005-001
- **Gate Decision**: block (2026-04-10T15:00:00Z)
- **Failed Items**:
  - coverage_id: api.auth.token-refresh.expired
    lifecycle_status: failed
    failure_reason: "Token 过期后刷新返回 500 而非 401"
  - coverage_id: e2e.auth.token-refresh.background
    lifecycle_status: failed
    failure_reason: "后台刷新期间 UI 未显示 loading 状态"

## 修复范围
- 仅修复上述 failed coverage items
- 不得引入新的 capability（如引入，需重新走完整 gate 流程）

## 验证要求
- 重新执行 failed items 对应的 validation contracts
- 不得破坏已通过 items（回归验证）

## Acceptance Checks
1. All failed items from source gate are now passed
   Then: 原 failed coverage items 的 lifecycle_status = passed, evidence_status = complete
2. No regression on passed items
   Then: 原 passed coverage items 状态未变
3. Gate re-evaluation passes
   Then: 重新执行 gate evaluator 后 final_decision != block
```

**Fix Feature 执行流程**：

```
Block Gate Decision
  -> 创建 Fix Feature（仅包含 failed items）
  -> Fix Feature 进入 Mission Compiler（同正常流程）
  -> Droid 执行修复后的 validation contracts
  -> 重新收集 evidence
  -> 重新进入 Gate 评估
  -> 通过 -> milestone.passed -> 原 feat 标记为 resolved
  -> 仍失败 -> 创建新的 Fix Feature（迭代上限：3 次）
```

### 2.7 Droid Worker 职责边界

#### Droid Worker 做什么

- 读取 `features.json` 中的 validation contracts
- 按 contract 中的 `assertions[]` 逐项执行验证
- 采集 `evidence_required` 中声明的证据
- 将执行结果写回 `validation-state`
- 遵循 `priority` 排序执行（P0 优先）
- 记录执行日志并生成 evidence hash

#### Droid Worker 不做什么

- **不得**自行决定测什么或不测什么（coverage 由 manifest 冻结）
- **不得**修改 spec 中的断言或证据要求
- **不得**跳过 `anti_false_pass_checks`
- **不得**在没有证据的情况下标记 passed
- **不得**解读 SSOT 中的 prose 来决定测试范围
- **不得**绕过 gate 决策直接推进

### 2.8 Feature 标准执行流程

每个 feature 在 Droid 运行时中的标准执行序列：

```
1. Mission Compiler 编译 features.json
   输入: feat + prototype + api-coverage-manifest + e2e-coverage-manifest + specs
   输出: features.json + execution-manifest.yaml

2. Droid Scheduler 拉取 ready 队列
   条件: progression_mode = auto-continue, gate_decision_ref 已批准

3. Worker Claim + Execute (按 priority 排序)
   a. 读取 validation-contract
   b. 执行 API 或 E2E 验证
   c. 采集证据（满足 evidence_required 声明）
   d. 生成 evidence hash
   e. 回写 validation-state

4. Scrutiny Validator 校验
   检查: lifecycle_status vs evidence_status 一致性
   检查: evidence hash 绑定
   检查: anti_false_pass_checks 通过

5. User Testing Validator 校验（E2E 专属）
   检查: UI 状态断言
   检查: 用户体验闭环
   检查: 持久化验证

6. Settlement + Gate Re-evaluation
   输入: 所有 validation-state + evidence
   输出: updated release_gate_input.yaml
   决策: release / conditional_release / block
```

### 2.9 测试接入规范

#### Scrutiny-Validator

**职责**：验证测试执行的合约合规性

**接入点**：Droid Worker 执行完成后

**验证项**：
- `lifecycle_status=passed` 时 `evidence_status=complete`
- 所有 `evidence_required` 中声明的证据类型均已采集
- evidence hash 与执行日志绑定
- 未声明 waiver 的 failed 项不得标记为 waived

**不做的**：
- 不判断测试逻辑是否正确（这是 spec 层面的事）
- 不执行实际的业务断言（这是 Worker 的事）
- 不决定 release gate（这是 Gate Evaluator 的事）

#### User-Testing-Validator

**职责**：验证 E2E 测试的用户体验完整性

**接入点**：E2E Worker 执行完成后

**验证项**：
- `expected_ui_states` 中声明的所有 UI 状态均已验证
- `expected_network_events` 中的网络请求均已发生
- `expected_persistence` 中的持久化均已确认
- `anti_false_pass_checks` 全部通过

**不做的**：
- 不验证 API 业务规则（这是 API chain + Scrutiny-Validator 的事）
- 不决定 UI 设计好坏（这是 prototype 的事）
- 不替代 functional assertions

#### 职责边界总结

| 组件 | 验证什么 | 不验证什么 |
|------|---------|-----------|
| **API Worker** | 业务规则、状态机、权限、幂等 | 用户体验、UI 交互 |
| **E2E Worker** | 用户旅程、UI 状态、前后端集成 | API 全量边界规则 |
| **Scrutiny-Validator** | 证据完整性、合约合规性 | 测试逻辑正确性 |
| **User-Testing-Validator** | 用户体验闭环、持久化、anti-false-pass | API 业务规则 |
| **Gate Evaluator** | 覆盖率结算、放行决策 | 单个测试的对错 |

---

## 3. 目录结构

### 3.1 编译器输出

```
ssot/tests/
├── compiled/                              # Mission Compiler 产出
│   ├── features.json                      # 所有 feature 的 Droid 可消费格式
│   └── execution-manifest.yaml            # 执行调度清单
│
├── api/
│   └── {FEAT-ID}/
│       ├── api-test-plan.md               # 已有，不变
│       ├── api-coverage-manifest.yaml     # 已有，不变
│       ├── api-test-spec/                 # 已有，不变
│       └── api-settlement-report.md       # 已有，不变
│
├── e2e/
│   └── PROTOTYPE-{FEAT-ID}/
│       ├── e2e-journey-plan.md            # 已有，不变
│       ├── e2e-coverage-manifest.yaml     # 已有，不变
│       ├── e2e-journey-spec/              # 已有，不变
│       └── e2e-settlement-report.md       # 已有，不变
│
├── gate/
│   ├── release_gate_input.yaml            # 已有，不变
│   └── milestone-decisions/               # 新增
│       └── {feature-id}-{timestamp}.yaml  # Gate 决策记录
│
└── fix-features/                          # 新增
    └── FIX-{feat-id}-{slot}__{title}.md   # Fix Feature 对象
```

### 3.2 Droid 运行时目录

```
.droid/                                    # Droid 运行时
├── missions/
│   ├── active/                            # 当前正在执行的 mission
│   │   └── {mission-id}.json
│   ├── completed/                         # 已完成的 mission
│   │   └── {mission-id}.json
│   └── failed/                            # 失败的 mission
│       └── {mission-id}.json
├── evidence/
│   ├── api/
│   │   └── {coverage-id}/
│   │       ├── request_snapshot.yaml
│   │       ├── response_snapshot.yaml
│   │       ├── db_assertion_result.yaml
│   │       └── evidence_hash.txt
│   └── e2e/
│       └── {coverage-id}/
│           ├── playwright_trace.zip
│           ├── screenshot_final.png
│           ├── network_log.har
│           └── evidence_hash.txt
├── state/
│   ├── validation-state.yaml              # 当前验证状态
│   └── execution-log.jsonl                # 不可变执行日志
└── config/
    └── droid-missions-config.yaml         # Droid 配置
```

---

## 4. 实施顺序

### Phase 1: 试点接入（当前阶段）

**目标**：在 ADR-047 试点（FEAT-SRC-005-001）上验证 Mission Compiler -> Droid Runtime -> Gate 的最小闭环

**范围**：
- 手工编写第一个 `features.json`（验证 mapping spec 正确性）
- 手工编写第一个 `execution-manifest.yaml`
- 在现有试点资产上运行完整执行流程
- 验证 Gate -> milestone decision 映射
- 验证一个 Fix Feature 回流（模拟 block 场景）

**产出**：
- `ssot/tests/compiled/features.json` (v0.1, 手工编写)
- `ssot/tests/compiled/execution-manifest.yaml`
- `ssot/tests/gate/milestone-decisions/` 第一条记录
- `ssot/tests/fix-features/` 第一个 Fix Feature（如需要）

**验收**：
- [ ] `features.json` 中的 validation contracts 与 manifest items 1:1 对应
- [ ] Droid 能消费 `features.json` 并正确执行至少 1 个 API + 1 个 E2E contract
- [ ] Gate 决策能正确映射为 milestone decision
- [ ] Fix Feature 回流路径验证（可模拟）

### Phase 2: 编译器化

**目标**：将 Phase 1 手工编写的 `features.json` 和 `execution-manifest.yaml` 升级为自动生成的编译器产物

**范围**：
- 实现 Mission Compiler skill：读取 feat/prototype/manifest/spec，输出 features.json
- 实现字段级映射的自动化（Section 2.4 的 mapping spec 编码化）
- 验证编译器输出与 Phase 1 手工版本一致

**产出**：
- `skills/l3/ll-mission-compiler/` Mission Compiler skill
- 自动化脚本替代手工编写

### Phase 3: Droid 运行时集成

**目标**：将 Droid Missions 运行时与 Execution Loop Job Runner (SRC-003) 统一

**范围**：
- Mission Compiler 输出对接 `ll loop dispatch`
- Droid Worker 作为 runner 的 `target_skill`
- 统一 `progression_mode` 控制语义
- 统一 evidence writeback 路径

### Phase 4: 规模化推广

**目标**：将 Phase 1-3 验证的流程推广到所有 feat/prototype 对

**范围**：
- 批量编译所有已冻结 feat 的 features.json
- 批量调度 Droid missions
- 建立 Gate -> milestone -> fix feature 的自动化闭环
- 旧 testset 完全退役

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Mapping Spec 与实际 runner schema 不一致 | 高 | Phase 1 用最小集验证，先跑通 1 条链 |
| Droid Worker 执行超时 | 中 | 设 claim timeout + lease recovery |
| Fix Feature 迭代爆炸 | 中 | 限制迭代上限 3 次，超限后 escalation |
| 编译器生成错误的 validation contracts | 高 | Phase 2 用手工版本做 diff 校验 |
| 证据存储膨胀 | 低 | 按 coverage_id 归档，定期清理旧证据 |

---

## 6. 不采纳的方案

### 方案 A：直接在旧 testset 上对接 Droid

**不采纳原因**：旧 testset 是 narrative 驱动的不可消费对象，直接对接会让 Droid 回退到目录猜测模式，违反 SRC-003 的 runner 关键约束（不得扫描目录猜业务输入）。

### 方案 B：修改原 feat 来回流修复

**不采纳原因**：破坏 gate 决策的不可变性和审计完整性，原 feat 的 block 决策是历史事实。

### 方案 C：让 Droid 直接消费 prose spec 文档

**不采纳原因**：prose spec 不可机器消费，会导致 Droid 用 LLM 猜测而非结构化验证，丧失防偷懒机制的价值。

---

## 7. 一句话结论

> **旧 testset 正式退出体系，不再作为独立对象层存在。后续统一采用"SSOT + 双链 + Mission Compiler + Droid Runtime + Gate"这一套闭环，通过字段级 mapping spec 把治理结论钉死为可编译、可执行、可结算的运行时对象。**

---

## 8. 附录：关键决策记录

| # | 决策 | 原因 |
|---|------|------|
| D1 | 旧 testset 退出体系 | 避免治理噪声，消除目录猜测输入 |
| D2 | Fix Feature 必须新建 | 保持 gate 决策不可变性，审计完整性 |
| D3 | 三层真相源分离（SSOT/双链/Droid） | 防止职责混层导致的治理退化 |
| D4 | 字段级 mapping spec 先行 | 编译器实现需要精确映射，不能停留在原则层 |
| D5 | Scrutiny-Validator 与 User-Testing-Validator 职责分离 | 合约验证与用户体验验证是不同关注点 |
| D6 | Gate decision 映射为 milestone decision | 使治理决策与项目里程碑对齐，支持条件发布 |
| D7 | Fix Feature 迭代上限 3 次 | 防止无限修复循环，强制 escalation |
