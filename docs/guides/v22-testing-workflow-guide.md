# ADR-053/ADR-054 双链测试 — 用户使用指南 (v2.2)

> **ADR**: ADR-053 (需求轴统一入口) + ADR-054 (实施轴桥接与验收闭环)
> **文档类型**: 用户操作指南
> **适用范围**: 所有需要通过 Skill 入口完成双链测试的用户
> **创建日期**: 2026-04-24
> **基于里程碑**: v2.2（Phase 17-19 完成）

---

## 一、实施状态总览

### 当前可用（v2.2 已交付）

| 模块/能力 | 状态 | 产出物 |
|-----------|------|--------|
| **需求轴统一入口** | ✓ 完成 | `ll-qa-api-from-feat`, `ll-qa-e2e-from-proto` |
| **用户统一入口** | ✓ 完成 | `ll-qa-test-run` |
| **SPEC 桥接层** | ✓ 完成 | `spec_adapter.py` |
| **环境管理层** | ✓ 完成 | `environment_provision.py` |
| **实施轴执行** | ✓ 完成 | `run_manifest_gen.py`, `scenario_spec_compile.py`, `state_machine_executor.py` |
| **验收闭环** | ✓ 完成 | `independent_verifier.py`, `settlement_integration.py`, `gate_integration.py` |
| **单元测试** | ✓ 完成 | 144 tests passing |

### TESTSET 废弃

| 组件 | 状态 | 替代方案 |
|------|------|----------|
| `ll-qa-feat-to-testset` | ⚠️ 已废弃 | `ll-qa-api-from-feat` / `ll-qa-e2e-from-proto` |
| `ll-test-exec-cli` (旧) | ⚠️ 已废弃 | `ll-qa-test-run` |
| `ll-test-exec-web-e2e` (旧) | ⚠️ 已废弃 | `ll-qa-test-run` |

---

## 二、核心架构：需求轴 → 实施轴 → 验收闭环

```
需求轴统一入口                    实施轴                       验收闭环
─────────────────              ──────────────              ──────────────
ll-qa-api-from-feat     ll-qa-test-run         independent_verifier
      │                       │                        │
      ├── feat-to-apiplan    ├── env → adapter        ├── verify()
      ├── api-manifest-init  ├── exec → manifest      └── VerdictReport
      └── api-spec-gen       ├── update manifest
                              │
ll-qa-e2e-from-proto         │
      │                       │
      ├── proto-to-e2eplan   ├── e2e exec (Playwright)
      ├── e2e-manifest-init ─┘
      └── e2e-spec-gen
                                    │
                                    ▼
                         ll-qa-settlement
                                    │
                                    ▼
                         ll-qa-gate-evaluate
                                    │
                                    ▼
                         release_gate_input.yaml
```

---

## 三、快速开始：从零跑通一条黄金路径

> 本节演示从一份冻结的 FEAT 文档出发，跑完双链测试的完整流程。

### 前置准备

1. **确认 FEAT 文档已冻结** — 检查你的 FEAT 文档中 `feat_freeze_package.status = "frozen"`。如果尚未冻结，需要先走 FRZ 冻结流程。
2. **确认 Skills 已安装** — 在 Claude Code 中运行 `/help` 或直接尝试调用 Skill。

### 简化流程（使用统一入口）

```
# API 链：从 FEAT 到测试计划
/ll-qa-api-from-feat
# 提供冻结的 FEAT 文档引用 → 自动产出 api-test-plan + api-manifest + api-spec

# E2E 链：从 Prototype 到测试计划
/ll-qa-e2e-from-proto
# 提供 Prototype 或 FEAT 引用 → 自动产出 e2e-plan + e2e-manifest + e2e-spec

# 执行测试 + 验收闭环
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain both
# → 执行测试 → 独立验证 → settlement → gate → release_gate_input.yaml
```

---

## 四、详细流程：分步说明

### 4.1 需求轴 — API 链统一入口

#### `/ll-qa-api-from-feat`

**你得到什么：** 从冻结的 FEAT 文档自动产出完整的 API 测试链（plan → manifest → spec）。

**前置条件：** FEAT 文档已冻结（`status = frozen`）

**用法：**
```
/ll-qa-api-from-feat
# 提供冻结的 FEAT 文档引用（包含 feat_id、feat_ref、Scope 定义）
```

**可选参数：**
| 参数 | 说明 |
|------|------|
| `--preview` | 仅产出 api-test-plan，停在 manifest-init 之前 |
| `--no-spec` | 停在 api-coverage-manifest，跳过 spec 生成 |
| `--target P0` | 仅生成 P0 优先级的测试项 |

**内部编排：**
```
ll-qa-feat-to-apiplan → api-test-plan.md (含 Acceptance Traceability)
        ↓
ll-qa-api-manifest-init → api-coverage-manifest.yaml
        ↓
ll-qa-api-spec-gen → api-test-spec/SPEC-*.md
```

**产出：**
- `ssot/tests/api/{feat_id}/api-test-plan.md` — 含 Acceptance Traceability 表
- `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`
- `ssot/tests/api/{feat_id}/api-test-spec/SPEC-*.md`

---

### 4.2 需求轴 — E2E 链统一入口

#### `/ll-qa-e2e-from-proto`

**你得到什么：** 从 Prototype 或 FEAT 文档自动产出完整的 E2E 测试链（plan → manifest → spec）。

**前置条件：** Prototype 流程图或 FEAT 文档已就绪

**用法：**
```
/ll-qa-e2e-from-proto
# 提供 Prototype 或 FEAT 文档引用
```

**两种模式：**
| 模式 | 说明 | 标记 |
|------|------|------|
| **Prototype-Driven** | 有完整 Prototype 流程图时，从页面流自动提取用户旅程 | `derivation_mode: prototype` |
| **API-Derived** | 没有 Prototype 时，从 FEAT 的用户可见能力推导旅程（降级模式）| `derivation_mode: api-derived` |

**可选参数：**
| 参数 | 说明 |
|------|------|
| `--preview` | 仅产出 e2e-journey-plan，停在 manifest-init 之前 |
| `--no-spec` | 停在 e2e-coverage-manifest，跳过 spec 生成 |
| `--mode proto` | 强制使用 Prototype-Driven 模式 |

**产出：**
- `ssot/tests/e2e/{proto_id}/e2e-journey-plan.md` — 含 Acceptance Traceability 表
- `ssot/tests/e2e/{proto_id}/e2e-coverage-manifest.yaml`
- `ssot/tests/e2e/{proto_id}/e2e-journey-spec/JOURNEY-*.md`

---

### 4.3 实施轴 — 测试执行

#### `/ll-qa-test-run`

**你得到什么：** 从 spec 文件执行测试，更新 manifest，完成验收闭环。

**前置条件：** api-test-spec 和/或 e2e-journey-spec 已存在

**用法：**
```
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain api
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain e2e
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain both
```

**参数说明：**
| 参数 | 说明 | 必需 |
|------|------|------|
| `--app-url` | 前端应用 URL | 是 |
| `--api-url` | API 服务 URL | 是 |
| `--chain` | 执行哪条链：`api`、`e2e` 或 `both` | 是 |
| `--browser` | 浏览器类型：`chromium`、`firefox`、`webkit` | 否（默认 chromium）|
| `--resume` | 从上次失败的步骤继续执行 | 否 |
| `--resume-from <step>` | 从指定步骤继续 | 否 |

**内部编排：**
```
environment_provision → spec_adapter → state_machine_executor → independent_verifier → settlement → gate
```

**产出：**
- `run-manifest.yaml` — 执行上下文（git sha、build 版本、URL 等）
- `ssot/tests/.artifacts/execution/` — 执行结果和证据
- `ssot/tests/.artifacts/settlement/release_gate_input.yaml` — 最终门禁决策

---

### 4.4 验收闭环 — 独立验证

#### `independent_verifier.py`

**你得到什么：** 独立于 runner 的验证报告，包含 verdict 和 confidence。

**Verdict 规则：**
| Flow 类型 | 通过条件 | Verdict |
|-----------|----------|---------|
| **Main Flow** (`scenario_type=main`) | 100% coverage + 0 failures | `PASS` |
| **Non-core Flow** (其他 scenario_type) | ≥80% coverage + ≤5 failures | `PASS` |
| 任意 Flow 不满足条件 | — | `FAIL` |

**Confidence 计算（D-04）：**
```
confidence = executed_items_with_evidence_refs / executed_items
```
注：confidence 仅作为参考，不作为 verdict 依据（D-05）。

**数据流：**
```
manifest_items (with lifecycle_status, evidence_refs, scenario_type)
        ↓
verify() → VerdictReport {
  verdict: PASS | CONDITIONAL_PASS | FAIL,
  confidence: 0.0 ~ 1.0,
  details: {
    main_flow: { coverage, failures, status },
    non_core_flow: { coverage, failures, status }
  }
}
```

---

### 4.5 验收闭环 — Settlement 报告

#### `ll-qa-settlement`

**你得到什么：** 统计报告，包含 verdict、confidence 和各项指标。

**统计指标：**
| 指标 | 说明 |
|------|------|
| `total` | 总 item 数量 |
| `designed` | 设计中的 item 数量 |
| `executed` | 已执行的 item 数量 |
| `passed` | passed 数量 |
| `failed` | failed 数量 |
| `blocked` | blocked 数量 |
| `uncovered` | 未覆盖数量 |
| `pass_rate` | 通过率 |
| `verdict` | 来自 independent_verifier |
| `confidence` | 来自 independent_verifier |

**产出：**
- `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`
- `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`

---

### 4.6 验收闭环 — Gate 评估

#### `ll-qa-gate-evaluate`

**你得到什么：** 最终的门禁决策。

**Gate 决策规则（D-08）：**
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

**产出：**
- `ssot/tests/.artifacts/settlement/release_gate_input.yaml`

---

## 五、产出物路径参考

```
ssot/tests/
├── api/{feat_id}/
│   ├── api-test-plan.md              ← ll-qa-api-from-feat
│   ├── api-coverage-manifest.yaml    ← ll-qa-api-from-feat
│   └── api-test-spec/
│       └── SPEC-*.md                 ← ll-qa-api-from-feat
│
├── e2e/{proto_id}/
│   ├── e2e-journey-plan.md           ← ll-qa-e2e-from-proto
│   ├── e2e-coverage-manifest.yaml    ← ll-qa-e2e-from-proto
│   └── e2e-journey-spec/
│       └── JOURNEY-*.md              ← ll-qa-e2e-from-proto
│
└── .artifacts/
    ├── execution/
    │   ├── run-manifest.yaml         ← ll-qa-test-run
    │   └── evidence/                  ← 执行证据
    │
    └── settlement/
        ├── api-settlement-report.yaml ← ll-qa-settlement
        ├── e2e-settlement-report.yaml ← ll-qa-settlement
        └── release_gate_input.yaml    ← ll-qa-gate-evaluate
```

---

## 六、关键数据结构

### 6.1 Manifest Item 结构

```yaml
coverage_id: "CAND-SUBMIT-001"
scenario_type: "main"           # main | exception | branch | retry | state
lifecycle_status: "passed"      # designed | executing | passed | failed | blocked
evidence_refs: ["ref1", "ref2"] # 证据引用列表
waiver_status: null             # null | pending | approved | rejected
```

### 6.2 VerdictReport 结构

```python
@dataclass
class VerdictReport:
    run_id: str
    generated_at: str
    verdict: GateVerdict  # PASS | CONDITIONAL_PASS | FAIL
    confidence: float    # 0.0 ~ 1.0
    details: FlowDetails
```

### 6.3 Gate 结构

```python
@dataclass
class Gate:
    final_decision: GateVerdict
    api_settlement_path: str
    e2e_settlement_path: str | None
    generated_at: str
    metadata: dict
```

---

## 七、常见问题

### Q: 如何选择 API 链还是 E2E 链？

**A:** 两条链互补：
- **API 链**：验证后端接口逻辑，执快速，适合接口级别的验证
- **E2E 链**：验证完整用户流程，覆盖前后端集成，适合端到端验证
- **推荐**：先跑 API 链（快），再跑 E2E 链（全面）

### Q: Gate 返回 `fail` 时怎么办？

**A:**
1. 查看 `release_gate_input.yaml` 中的 `decision_reason`
2. 检查是哪条链失败：
   - **Main flow 失败**：检查覆盖率是否达到 100%
   - **Non-core flow 失败**：检查覆盖率是否 ≥80%，失败数是否 ≤5
3. 对于 failed 项：修复后使用 `/ll-qa-test-run --resume` 重跑
4. 重新执行后重跑 settlement + gate

### Q: 如何添加豁免（waiver）？

**A:** 在 manifest item 中设置 `waiver_status`：
- `pending`：待审批，仍计为失败
- `approved`：已审批的豁免
- `rejected`：被拒绝的豁免

### Q: `--resume` 参数如何使用？

**A:**
- `--resume`：从上次失败的步骤继续执行，不重复已完成步骤
- `--resume-from <step>`：从指定步骤继续

---

## 八、v2.2 新增能力

### 8.1 独立验证（independent_verifier）

- 不再依赖执行引擎的内部判断
- 基于 manifest items 的实际状态计算 verdict
- 支持 `scenario_type` 分流（main vs non-core）
- 提供置信度作为参考指标

### 8.2 统一入口 Skills

- `ll-qa-api-from-feat`：一键从 FEAT 到 API spec
- `ll-qa-e2e-from-proto`：一键从 Prototype 到 E2E spec
- `ll-qa-test-run`：一键执行 + 验收闭环

### 8.3 状态机执行器

- 5 状态模型：SETUP → EXECUTE → VERIFY → COLLECT → DONE
- 统一的错误处理和重试逻辑
- 支持断点恢复

---

## 九、后续路线图

| 阶段 | 能力 | 状态 |
|------|------|------|
| v2.2 | 基础执行闭环 | ✓ 完成 |
| v2.3 | ADR-048 Mission Compiler（替换 SPEC_ADAPTER_COMPAT）| 规划中 |
| v2.3 | 完整 9 节点 state_machine_executor | 规划中 |
| v2.3 | 8 类故障分类器（failure-classifier）| 规划中 |

---

> **文档版本**: v2.2
> **基于里程碑**: v2.2 双链执行闭环
> **创建日期**: 2026-04-24
> **更新日期**: 2026-04-24
