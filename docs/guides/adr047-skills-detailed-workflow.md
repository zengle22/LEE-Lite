# ADR-047/053/054 Skills 详细工作流程文档 (v2.2)

> **ADR**: ADR-047 (v1.4), ADR-053 (需求轴统一入口), ADR-054 (实施轴桥接与验收闭环)
> **文档类型**: Skill 详细工作流程参考手册
> **适用范围**: 所有使用 v2.2 双链测试治理架构的项目
> **创建日期**: 2026-04-11
> **更新日期**: 2026-04-24 (v2.2)

---

## 目录

1. [总体架构与 Skill 编排](#1-总体架构与-skill-编排)
2. [统一入口 Skills](#2-统一入口-skills-v22)
3. [Skill 1-6: 需求轴基础 Skills](#3-skill-1-6-需求轴基础-skills)
4. [Skill 7-8: 验收闭环](#4-skill-7-8-验收闭环-v22)
5. [独立验证模块](#5-独立验证模块-v22)
6. [完整执行链路示例](#6-完整执行链路示例-v22)
7. [四维状态字段详解](#7-四维状态字段详解)

---

## 1. 总体架构与 Skill 编排

### 1.1 v2.2 架构

```
需求轴统一入口                    实施轴                       验收闭环
─────────────────              ──────────────              ──────────────
ll-qa-api-from-feat     ll-qa-test-run         independent_verifier
      │                       │                        │
      ├── feat-to-apiplan  ├── env → adapter        ├── verify()
      ├── api-manifest-init ├── exec → manifest       └── VerdictReport
      └── api-spec-gen      └── update manifest
                              │
ll-qa-e2e-from-proto          │
      │                       │
      ├── proto-to-e2eplan  ├── e2e exec
      ├── e2e-manifest-init ─┘
      └── e2e-spec-gen
                                    │
                                    ▼
                         ll-qa-settlement
                                    │
                                    ▼
                         ll-qa-gate-evaluate
```

### 1.2 v2.2 Skills (10 个)

| 类别 | 序号 | 技能 | 状态 |
|------|------|------|------|
| **统一入口** | — | `ll-qa-api-from-feat` | ✓ v2.2 |
| | — | `ll-qa-e2e-from-proto` | ✓ v2.2 |
| | — | `ll-qa-test-run` | ✓ v2.2 |
| **需求轴** | 1 | `ll-qa-feat-to-apiplan` | ✓ v2.1 |
| | 2 | `ll-qa-api-manifest-init` | ✓ v2.1 |
| | 3 | `ll-qa-api-spec-gen` | ✓ v2.1 |
| | 4 | `ll-qa-prototype-to-e2eplan` | ✓ v2.1 |
| | 5 | `ll-qa-e2e-manifest-init` | ✓ v2.1 |
| | 6 | `ll-qa-e2e-spec-gen` | ✓ v2.1 |
| **验收闭环** | 7 | `ll-qa-settlement` | ✓ v2.2 |
| | 8 | `ll-qa-gate-evaluate` | ✓ v2.2 |

### 1.3 Skill 依赖矩阵 (v2.2)

| Skill | 上游依赖 | 下游产出 | 输出路径 |
|-------|----------|----------|----------|
| ll-qa-api-from-feat | 冻结的 FEAT 文档 | api-plan + manifest + spec | ssot/tests/api/{feat_id}/ |
| ll-qa-e2e-from-proto | Prototype/FEAT | e2e-plan + manifest + spec | ssot/tests/e2e/{proto_id}/ |
| ll-qa-test-run | spec + ENV | 执行结果 + manifest 更新 | ssot/tests/.artifacts/ |
| ll-qa-feat-to-apiplan | FEAT 文档 | api-test-plan.md | ssot/tests/api/{feat_id}/ |
| ll-qa-api-manifest-init | api-test-plan.md | api-coverage-manifest.yaml | ssot/tests/api/{feat_id}/ |
| ll-qa-api-spec-gen | api-coverage-manifest.yaml | SPEC-*.md | ssot/tests/api/{feat_id}/api-test-spec/ |
| ll-qa-prototype-to-e2eplan | Prototype 流程图 | e2e-journey-plan.md | ssot/tests/e2e/{proto_id}/ |
| ll-qa-e2e-manifest-init | e2e-journey-plan.md | e2e-coverage-manifest.yaml | ssot/tests/e2e/{proto_id}/ |
| ll-qa-e2e-spec-gen | e2e-coverage-manifest.yaml | JOURNEY-*.md | ssot/tests/e2e/{proto_id}/e2e-journey-spec/ |
| ll-qa-settlement | 执行后的 manifests | settlement reports | ssot/tests/.artifacts/settlement/ |
| ll-qa-gate-evaluate | manifests + settlements | release_gate_input.yaml | ssot/tests/.artifacts/tests/settlement/ |

---

## 2. 统一入口 Skills (v2.2)

### 2.1 ll-qa-api-from-feat

#### 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-api-from-feat` |
| **ADR** | ADR-053 |
| **用途** | 一键从冻结的 FEAT 文档到 API spec |
| **触发场景** | 新 FEAT 通过 gate 后 |
| **上游** | FEAT 文档（冻结状态） |
| **下游** | `ll-qa-test-run` |
| **状态** | ✓ v2.2 |

#### 内部编排

```
1. ll-qa-feat-to-apiplan → api-test-plan.md (含 Acceptance Traceability)
2. ll-qa-api-manifest-init → api-coverage-manifest.yaml
3. ll-qa-api-spec-gen → api-test-spec/*.md
```

#### 可选参数

| 参数 | 说明 |
|------|------|
| `--preview` | 仅产出 api-test-plan |
| `--no-spec` | 停在 manifest，跳过 spec |
| `--target P0\|P1\|P2` | 按优先级过滤 |

---

### 2.2 ll-qa-e2e-from-proto

#### 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-e2e-from-proto` |
| **ADR** | ADR-053 |
| **用途** | 一键从 Prototype/FEAT 到 E2E spec |
| **触发场景** | Prototype 设计完成后 或 FEAT 就绪时 |
| **上游** | Prototype 流程图 / FEAT 文档 |
| **下游** | `ll-qa-test-run` |
| **状态** | ✓ v2.2 |

#### 内部编排

```
1. ll-qa-prototype-to-e2eplan → e2e-journey-plan.md (含 Acceptance Traceability)
2. ll-qa-e2e-manifest-init → e2e-coverage-manifest.yaml
3. ll-qa-e2e-spec-gen → e2e-journey-spec/*.md
```

#### 双模式支持

| 模式 | 说明 | 标记 |
|------|------|------|
| `derivation_mode: prototype` | 有完整 Prototype 流程图 | 从页面流提取旅程 |
| `derivation_mode: api-derived` | 无 Prototype | 从 FEAT 能力推导 |

---

### 2.3 ll-qa-test-run

#### 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-test-run` |
| **ADR** | ADR-054 |
| **用途** | 用户统一入口，执行测试 + 验收闭环 |
| **触发场景** | spec 文件已存在，需要执行测试 |
| **上游** | api-test-spec + e2e-journey-spec |
| **下游** | independent_verifier → settlement → gate |
| **状态** | ✓ v2.2 |

#### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| `--app-url` | 前端应用 URL | 是 |
| `--api-url` | API 服务 URL | 是 |
| `--chain` | `api` / `e2e` / `both` | 是 |
| `--browser` | `chromium` / `firefox` / `webkit` | 否 |
| `--resume` | 从上次失败的步骤继续 | 否 |
| `--resume-from <step>` | 从指定步骤继续 | 否 |

#### 内部编排

```
1. environment_provision → ENV-{feat_id}.yaml
2. spec_adapter → SPEC_ADAPTER_COMPAT
3. state_machine_executor → 执行 + 证据收集
4. independent_verifier → VerdictReport
5. ll-qa-settlement → settlement reports
6. ll-qa-gate-evaluate → release_gate_input.yaml
```

---

## 3. Skill 1-6: 需求轴基础 Skills

> Skills 1-6 的详细工作流程与 v2.1 相同，详见原始文档。
> 主要变更：
> - 输出增加 Acceptance Traceability 表
> - 产出物由统一入口 Skills 编排调用

### 3.1 Skill 1: ll-qa-feat-to-apiplan

**新增**: Acceptance Traceability 表

```markdown
## Acceptance Traceability

| Acceptance Ref | Acceptance Scenario | Capability IDs | Covered |
|----------------|-------------------|---------------|---------|
| AC-001 | Given 包已创建 When 提交 Then 状态变为已提交 | CAND-SUBMIT-001 | ✅ |
```

### 3.2 Skill 4: ll-qa-prototype-to-e2eplan

**新增**: Acceptance Traceability 表

```markdown
## Acceptance Traceability

| Acceptance Ref | Acceptance Scenario | Journey IDs | Covered |
|---------------|---------------------|-------------|---------|
| AC-001 | 用户成功提交候选人包 | JOURNEY-MAIN-001 | ✅ |
```

---

## 4. Skill 7-8: 验收闭环 (v2.2)

### 4.1 ll-qa-settlement

#### 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-settlement` |
| **ADR** | ADR-054 Phase 3 |
| **用途** | 生成结算报告，包含 verdict + confidence |
| **触发场景** | 测试执行完成后 |
| **上游** | 执行后的 manifests + independent_verifier |
| **下游** | `ll-qa-gate-evaluate` |
| **状态** | ✓ v2.2 |

#### 详细执行步骤

##### Step 1: 接收 VerdictReport

从 `independent_verifier.verify()` 获取 VerdictReport：
- `verdict`: PASS / CONDITIONAL_PASS / FAIL
- `confidence`: 0.0 ~ 1.0
- `details`: main_flow + non_core_flow metrics

##### Step 2: 计算统计信息

```python
statistics = {
    "total": len(manifest_items),
    "designed": count(lifecycle_status == "designed"),
    "executed": count(lifecycle_status in (passed, failed, blocked)),
    "passed": count(lifecycle_status == "passed"),
    "failed": count(lifecycle_status == "failed"),
    "blocked": count(lifecycle_status == "blocked"),
    "uncovered": count(lifecycle_status == "designed"),
    "pass_rate": passed / max(executed, 1),
}
```

##### Step 3: 注入 verdict + confidence

```yaml
api_settlement:
  verdict: "pass"                    # ← from independent_verifier
  confidence: 0.85                   # ← from independent_verifier
  statistics: {...}
  gap_list: [...]
  waiver_list: [...]
```

#### 输出

```yaml
# ssot/tests/.artifacts/settlement/api-settlement-report.yaml
api_settlement:
  feature_id: "{feat_id}"
  generated_at: "{timestamp}"
  verdict: "pass"                    # D-07
  confidence: 0.85                   # D-07
  statistics:
    total: N
    designed: N
    executed: N
    passed: N
    failed: N
    blocked: N
    uncovered: N
    pass_rate: 0.XX
  gap_list: [...]
  waiver_list: [...]
```

---

### 4.2 ll-qa-gate-evaluate

#### 基本信息

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-gate-evaluate` |
| **ADR** | ADR-054 Phase 3 |
| **用途** | 基于 settlement 产出最终 gate 决策 |
| **触发场景** | 两条链的 settlement reports 都生成后 |
| **上游** | `ll-qa-settlement` |
| **下游** | CI/CD 流水线 |
| **状态** | ✓ v2.2 |

#### Gate 决策真值表 (D-08)

| API verdict | E2E verdict | Final decision |
|-------------|-------------|----------------|
| `pass` | `pass` | `PASS` |
| `pass` | `conditional_pass` | `CONDITIONAL_PASS` |
| `pass` | None | `PASS` |
| `pass` | `fail` | `FAIL` |
| `conditional_pass` | `pass` | `CONDITIONAL_PASS` |
| `conditional_pass` | `conditional_pass` | `CONDITIONAL_PASS` |
| `conditional_pass` | `fail` | `FAIL` |
| `fail` | * | `FAIL` |
| None | `pass` | `PASS` |
| None | `conditional_pass` | `CONDITIONAL_PASS` |
| None | `fail` | `FAIL` |

#### 输出

```yaml
# ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml
gate_evaluation:
  evaluated_at: "{timestamp}"
  feature_id: "{feat_id}"
  final_decision: "pass"  # PASS | CONDITIONAL_PASS | FAIL
  api_settlement:
    verdict: "pass"
    confidence: 0.85
    statistics: {...}
  e2e_settlement:
    verdict: "pass"
    confidence: 1.0
    statistics: {...}
  decision_reason: "{explanation}"
```

---

## 5. 独立验证模块 (v2.2)

### 5.1 independent_verifier.py

#### Verdict 规则 (D-01, D-02)

| Flow 类型 | scenario_type | 通过条件 | Verdict |
|-----------|--------------|----------|---------|
| **Main** | `main` | 100% coverage + 0 failures | `PASS` |
| **Non-core** | `exception` / `branch` / `retry` / `state` | ≥80% coverage + ≤5 failures | `PASS` |
| — | 任意不满足条件 | — | `FAIL` |

#### Confidence 计算 (D-04, D-05)

```
confidence = executed_items_with_evidence_refs / executed_items
```

**规则**:
- Confidence 仅作参考，不作为 verdict 依据
- 无 executed items 时，confidence = 0.0

#### 数据流

```
manifest_items
      ↓
_categorize_items() → main_items, non_core_items
      ↓
_compute_flow_metrics() → main_metrics, non_core_metrics
      ↓
_determine_flow_verdict() → main_verdict, non_core_verdict
      ↓
_compute_confidence() → confidence
      ↓
综合 → VerdictReport
```

---

## 6. 完整执行链路示例 (v2.2)

### 场景：用户登录功能

#### 阶段一：需求轴（使用统一入口）

```bash
# API 链
/ll-qa-api-from-feat --feat-ref FEAT-SRC-005-001

# E2E 链
/ll-qa-e2e-from-proto --proto-ref PROTOTYPE-FEAT-SRC-005-001
```

**产出**:
- `ssot/tests/api/FEAT-SRC-005-001/api-test-plan.md` (含 AC Traceability)
- `ssot/tests/api/FEAT-SRC-005-001/api-coverage-manifest.yaml`
- `ssot/tests/api/FEAT-SRC-005-001/api-test-spec/SPEC-*.md`
- `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-journey-plan.md` (含 AC Traceability)
- `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-coverage-manifest.yaml`
- `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-journey-spec/JOURNEY-*.md`

#### 阶段二：测试执行

```bash
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain both
```

**内部流程**:
```
environment_provision → ENV-FEAT-SRC-005-001.yaml
spec_adapter → SPEC_ADAPTER_COMPAT
run_manifest_gen → run-manifest.yaml
state_machine_executor → 执行 + 证据收集
manifest_update → 更新 lifecycle_status, evidence_refs
```

#### 阶段三：验收闭环

```
independent_verifier → VerdictReport
ll-qa-settlement → api/e2e settlement reports
ll-qa-gate-evaluate → release_gate_input.yaml
```

#### 最终输出

```yaml
# release_gate_input.yaml
gate_evaluation:
  evaluated_at: "2026-04-24T10:30:00Z"
  feature_id: "FEAT-SRC-005-001"
  final_decision: "pass"
  api_settlement:
    verdict: "pass"
    confidence: 0.92
    statistics:
      total: 18
      executed: 16
      passed: 14
      failed: 1
      blocked: 1
      pass_rate: 0.88
  e2e_settlement:
    verdict: "pass"
    confidence: 1.0
    statistics:
      total: 3
      executed: 3
      passed: 3
      pass_rate: 1.00
```

---

## 7. 四维状态字段详解

### 7.1 lifecycle_status

| 值 | 含义 | v2.2 变更 |
|----|------|-----------|
| `designed` | 已设计，待执行 | — |
| `executing` | 正在执行 | — |
| `passed` | 执行通过 | — |
| `failed` | 执行失败 | — |
| `blocked` | 被阻塞 | — |
| `cut` | 已裁剪 | — |
| `obsolete` | 已废弃 | — |

### 7.2 mapping_status

| 值 | 含义 |
|----|------|
| `unmapped` | 尚未映射到具体测试用例 |
| `mapped` | 已映射到测试用例 |
| `verified` | 映射已验证 |

### 7.3 evidence_status

| 值 | 含义 |
|----|------|
| `missing` | 无证据 |
| `partial` | 部分证据 |
| `complete` | 证据完整 |

### 7.4 waiver_status

| 值 | 含义 | 对门禁的影响 |
|----|------|-------------|
| `none` | 无豁免 | 正常计入 |
| `pending` | 豁免申请中 | **计为 failed** |
| `approved` | 豁免已批准 | 从分母排除 |
| `rejected` | 豁免被拒绝 | 正常计入 |

---

## 附录 A: Skill 触发命令速查 (v2.2)

| Skill | 触发命令 | 说明 |
|-------|----------|------|
| ll-qa-api-from-feat | `/ll-qa-api-from-feat` | 统一入口 |
| ll-qa-e2e-from-proto | `/ll-qa-e2e-from-proto` | 统一入口 |
| ll-qa-test-run | `/ll-qa-test-run --app-url X --api-url Y --chain both` | 用户入口 |
| ll-qa-feat-to-apiplan | `/ll-qa-feat-to-apiplan` | 单独调用 |
| ll-qa-api-manifest-init | `/ll-qa-api-manifest-init` | 单独调用 |
| ll-qa-api-spec-gen | `/ll-qa-api-spec-gen` | 单独调用 |
| ll-qa-prototype-to-e2eplan | `/ll-qa-prototype-to-e2eplan` | 单独调用 |
| ll-qa-e2e-manifest-init | `/ll-qa-e2e-manifest-init` | 单独调用 |
| ll-qa-e2e-spec-gen | `/ll-qa-e2e-spec-gen` | 单独调用 |
| ll-qa-settlement | `/ll-qa-settlement` | 单独调用 |
| ll-qa-gate-evaluate | `/ll-qa-gate-evaluate` | 单独调用 |

---

## 附录 B: TESTSET 废弃清单

| 废弃组件 | 替代方案 | 状态 |
|----------|----------|------|
| `ll-qa-feat-to-testset` | `ll-qa-api-from-feat` + `ll-qa-e2e-from-proto` | ✓ v2.2 替代 |
| `ll-test-exec-cli` (旧) | `ll-qa-test-run` | ✓ v2.2 替代 |
| `ll-test-exec-web-e2e` (旧) | `ll-qa-test-run` | ✓ v2.2 替代 |

---

> **文档版本**: v2.2
> **最后更新**: 2026-04-24
> **基于里程碑**: v2.2 双链执行闭环
