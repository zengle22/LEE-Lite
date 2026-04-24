# ADR-047/053/054 双链测试完整工作流文档 (v2.2)

> 本文档从设计（统一入口 Skills）到执行（state_machine_executor → independent_verifier → settlement → gate）到报告，全面梳理 v2.2 双链测试体系的完整流程。
>
> **基于里程碑**: v2.2 双链执行闭环
> **关键 ADR**: ADR-047, ADR-053, ADR-054

---

## 一、整体架构概览

### 1.1 双链并行结构 (v2.2)

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
                                    │
                                    ▼
                         release_gate_input.yaml
```

### 1.2 四层资产分离

| 层级 | 文件 | 内容 | 生命周期 |
|------|------|------|----------|
| **Plan** | `{chain}-plan.yaml` | 需求→测试的映射规划，含 Acceptance Traceability | 需求变更时更新 |
| **Manifest** | `{chain}-manifest.yaml` | 测试项清单+四维状态机 | 持续演进，永不删除 |
| **Spec** | `{chain}-spec-*.md` | 可读规范文档 | 随 Manifest 同步更新 |
| **Settlement** | `{chain}-settlement-report.yaml` | 结算报告+覆盖率+决策 | 每次 Gate 评估生成 |

### 1.3 v2.2 Skills (10 个)

| 序号 | 技能 | 职责 | 状态 |
|------|------|------|------|
| — | `ll-qa-api-from-feat` | API 链统一入口 | ✓ v2.2 |
| — | `ll-qa-e2e-from-proto` | E2E 链统一入口 | ✓ v2.2 |
| 1 | `ll-qa-feat-to-apiplan` | FEAT需求→API测试计划 | ✓ v2.1 |
| 2 | `ll-qa-api-manifest-init` | API计划→API清单 | ✓ v2.1 |
| 3 | `ll-qa-api-spec-gen` | API清单→API规范 | ✓ v2.1 |
| 4 | `ll-qa-prototype-to-e2eplan` | 原型→E2E测试计划 | ✓ v2.1 |
| 5 | `ll-qa-e2e-manifest-init` | E2E计划→E2E清单 | ✓ v2.1 |
| 6 | `ll-qa-e2e-spec-gen` | E2E清单→E2E规范 | ✓ v2.1 |
| 7 | `ll-qa-settlement` | 执行结果→结算报告 | ✓ v2.2 |
| 8 | `ll-qa-gate-evaluate` | 双链合并→发布决策 | ✓ v2.2 |

---

## 二、需求轴统一入口 (v2.2)

### 2.1 ll-qa-api-from-feat

**统一入口**，一键从冻结的 FEAT 文档到 API spec。

```
输入: 冻结的 FEAT 文档 (feat_freeze_package)
      ↓
内部编排:
  ll-qa-feat-to-apiplan (含 Acceptance Traceability)
      ↓
  ll-qa-api-manifest-init
      ↓
  ll-qa-api-spec-gen
      ↓
输出: api-test-plan.md + api-coverage-manifest.yaml + api-test-spec/*.md
```

**可选参数**:
- `--preview`: 仅产出 api-test-plan
- `--no-spec`: 停在 manifest，跳过 spec 生成
- `--target P0|P1|P2`: 按优先级过滤

### 2.2 ll-qa-e2e-from-proto

**统一入口**，一键从 Prototype/FEAT 到 E2E spec。

```
输入: Prototype 流程图 或 FEAT 文档
      ↓
内部编排:
  ll-qa-prototype-to-e2eplan (含 Acceptance Traceability)
      ↓
  ll-qa-e2e-manifest-init
      ↓
  ll-qa-e2e-spec-gen
      ↓
输出: e2e-journey-plan.md + e2e-coverage-manifest.yaml + e2e-journey-spec/*.md
```

**两种模式**:
- `derivation_mode: prototype` — 有完整 Prototype 时
- `derivation_mode: api-derived` — 无 Prototype 时

---

## 三、实施轴桥接层 (ADR-054)

### 3.1 SPEC_ADAPTER_COMPAT 桥接格式

spec 文件 → SPEC_ADAPTER_COMPAT → test_exec_runtime

| 字段映射 | API Spec | TESTSET Unit |
|----------|----------|--------------|
| `case_id` | → | `unit_ref` |
| `endpoint.method/path` | → | `trigger_action` |
| `assertions` | → | `pass_conditions` |
| `source_feat_ref` | → | `acceptance_ref` |

### 3.2 spec_adapter.py

```python
# cli/lib/spec_adapter.py
def adapt_api_spec(spec_path: str) -> dict:
    """API spec → SPEC_ADAPTER_COMPAT"""
    # 读取 api-test-spec/*.md
    # 映射到 TESTSET unit 格式
    # 输出: ssot/tests/.spec-adapter/{id}.yaml
    return spec_adapter_compat

def adapt_e2e_spec(spec_path: str) -> dict:
    """E2E spec → SPEC_ADAPTER_COMPAT"""
    # 读取 e2e-journey-spec/*.md
    # 映射到 TESTSET unit 格式
    return spec_adapter_compat
```

### 3.3 environment_provision.py (v2.2)

```python
# cli/lib/environment_provision.py
def generate_environment(
    feat_ref: str,
    base_url: str,
    api_url: str = None,
    browser: str = "chromium"
) -> EnvConfig:
    """从 FEAT + 用户参数生成 ENV YAML"""
    return EnvConfig(
        id=f"ENV-{feat_ref}",
        base_url=base_url,
        api_url=api_url,
        browser=browser,
        execution_modality="web_e2e"
    )
```

**输出**: `ssot/environments/ENV-{feat_id}.yaml`

### 3.4 test_orchestrator.py (v2.2)

线性编排执行流程:

```
environment_provision → spec_adapter → state_machine_executor → manifest_update
```

```python
# cli/lib/test_orchestrator.py
async def orchestrate(
    feat_ref: str,
    chain: str,  # "api" | "e2e" | "both"
    base_url: str,
    api_url: str,
    resume: bool = False
):
    # 1. 生成/加载环境配置
    env = await environment_provision.generate(feat_ref, base_url, api_url)

    # 2. 适配 spec 文件
    adapted_specs = await spec_adapter.adapt(chain, feat_ref)

    # 3. 状态机执行
    result = await state_machine_executor.execute(
        env, adapted_specs, resume=resume
    )

    # 4. 更新 manifest
    await manifest_update.apply(result)

    return result
```

---

## 四、测试执行 (ADR-054 Phase 2)

### 4.1 run_manifest_gen.py (v2.2)

每次执行生成唯一的 `run-manifest.yaml`:

```yaml
run_id: "run-2026-04-24-001"
git_sha: "abc1234"
frontend_build: "build-456"
backend_build: "build-789"
base_url: "http://localhost:3000"
api_url: "http://localhost:8000"
browser: "chromium"
executed_at: "2026-04-24T10:00:00Z"
```

### 4.2 state_machine_executor.py (v2.2)

5 状态模型:

```
SETUP → EXECUTE → VERIFY → COLLECT → DONE
                  ↓
            (任意失败)
                  ↓
                  ↓
              COLLECT
```

```python
# cli/lib/state_machine_executor.py
class StateMachineExecutor:
    STATES = ["SETUP", "EXECUTE", "VERIFY", "COLLECT", "DONE"]

    async def execute(self, env: EnvConfig, specs: list) -> StepResult:
        state = "SETUP"
        while state != "DONE":
            if state == "SETUP":
                state = await self._setup(env, specs)
            elif state == "EXECUTE":
                state = await self._execute(env, specs)
            elif state == "VERIFY":
                state = await self._verify(env, specs)
            elif state == "COLLECT":
                state = await self._collect(env)
        return self.result
```

---

## 五、验收闭环 (ADR-054 Phase 3)

### 5.1 independent_verifier.py (v2.2)

**独立于 runner 的验证报告**，基于 manifest items 计算 verdict。

```python
# cli/lib/independent_verifier.py
@dataclass
class VerdictReport:
    run_id: str
    generated_at: str
    verdict: GateVerdict  # PASS | CONDITIONAL_PASS | FAIL
    confidence: float      # 0.0 ~ 1.0
    details: FlowDetails   # main_flow + non_core_flow metrics

def verify(manifest_items: list, run_id: str) -> VerdictReport:
    # 1. 按 scenario_type 分类
    main_items, non_core_items = _categorize_items(manifest_items)

    # 2. 计算 flow metrics
    main_metrics = _compute_flow_metrics(main_items)
    non_core_metrics = _compute_flow_metrics(non_core_items)

    # 3. 判定 flow verdict
    main_verdict = _determine_flow_verdict(main_metrics)  # D-01
    non_core_verdict = _determine_flow_verdict(non_core_metrics)  # D-02

    # 4. 计算 confidence (D-04, 仅作参考 D-05)
    confidence = _compute_confidence(manifest_items)

    # 5. 汇总 verdict
    overall = FAIL if any flow fails else PASS

    return VerdictReport(...)
```

**Verdict 规则 (D-01, D-02)**:

| Flow 类型 | 通过条件 | Verdict |
|-----------|----------|---------|
| **Main** (`scenario_type=main`) | 100% coverage + 0 failures | `PASS` |
| **Non-core** (其他) | ≥80% coverage + ≤5 failures | `PASS` |
| 不满足条件 | — | `FAIL` |

**Confidence 计算 (D-04)**:
```
confidence = executed_items_with_evidence_refs / executed_items
```
注：confidence 仅作参考，不作为 verdict 依据 (D-05)。

### 5.2 settlement_integration.py (v2.2)

```python
# cli/lib/settlement_integration.py
def generate_settlement(
    manifest_items: list,
    verdict_report: VerdictReport,
    chain: str  # "api" | "e2e"
) -> dict:
    settlement = {
        "verdict": verdict_report.verdict.value,
        "confidence": verdict_report.confidence,
        "statistics": _compute_statistics(manifest_items),
        "gap_list": _build_gap_list(manifest_items),
        "waiver_list": _build_waiver_list(manifest_items),
    }
    return {f"{chain}_settlement": settlement}
```

### 5.3 gate_integration.py (v2.2)

```python
# cli/lib/gate_integration.py
def evaluate_gate(
    api_settlement_path: str,
    e2e_settlement_path: str = None
) -> Gate:
    api_verdict = _load_verdict(api_settlement_path)
    e2e_verdict = _load_verdict(e2e_settlement_path) if e2e_settlement_path else None

    final_decision = _derive_gate_decision(api_verdict, e2e_verdict)

    return Gate(
        verdict=final_decision,
        evaluated_at=datetime.utcnow().isoformat()
    )
```

**Gate 决策真值表 (D-08)**:

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

---

## 六、完整执行链路

### 6.1 简化流程 (v2.2 推荐)

```
# API 链
/ll-qa-api-from-feat --feat-ref FEAT-SRC-XXX-YYY
        ↓
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain api
        ↓
release_gate_input.yaml

# E2E 链
/ll-qa-e2e-from-proto --proto-ref PROTOTYPE-XXX
        ↓
/ll-qa-test-run --app-url http://localhost:3000 --api-url http://localhost:8000 --chain e2e
        ↓
release_gate_input.yaml
```

### 6.2 完整分步流程

```
需求轴 (ADR-053)
═══════════════════════════════════════════════════════
FEAT 冻结
  → ll-qa-feat-to-apiplan → api-test-plan.md (含 AC Traceability)
  → ll-qa-api-manifest-init → api-coverage-manifest.yaml
  → ll-qa-api-spec-gen → api-test-spec/*.md

  → ll-qa-prototype-to-e2eplan → e2e-journey-plan.md (含 AC Traceability)
  → ll-qa-e2e-manifest-init → e2e-coverage-manifest.yaml
  → ll-qa-e2e-spec-gen → e2e-journey-spec/*.md

实施轴桥接 (ADR-054 Phase 1)
═══════════════════════════════════════════════════════
environment_provision → ENV-{feat_id}.yaml
spec_adapter → SPEC_ADAPTER_COMPAT

实施轴执行 (ADR-054 Phase 2)
═══════════════════════════════════════════════════════
run_manifest_gen → run-manifest.yaml
state_machine_executor → 执行 + 证据收集
manifest_update → 更新 lifecycle_status, evidence_refs

验收闭环 (ADR-054 Phase 3)
═══════════════════════════════════════════════════════
independent_verifier → VerdictReport
ll-qa-settlement → settlement reports
ll-qa-gate-evaluate → release_gate_input.yaml
```

---

## 七、产出物路径

```
ssot/tests/
├── api/{feat_id}/
│   ├── api-test-plan.md              ← ll-qa-api-from-feat
│   ├── api-coverage-manifest.yaml   ← ll-qa-api-from-feat
│   └── api-test-spec/
│       └── SPEC-*.md
│
├── e2e/{proto_id}/
│   ├── e2e-journey-plan.md          ← ll-qa-e2e-from-proto
│   ├── e2e-coverage-manifest.yaml   ← ll-qa-e2e-from-proto
│   └── e2e-journey-spec/
│       └── JOURNEY-*.md
│
├── .artifacts/
│   ├── environments/
│   │   └── ENV-{feat_id}.yaml      ← environment_provision
│   ├── execution/
│   │   ├── run-manifest.yaml       ← run_manifest_gen
│   │   └── evidence/                ← state_machine_executor
│   └── settlement/
│       ├── api-settlement-report.yaml ← ll-qa-settlement
│       ├── e2e-settlement-report.yaml ← ll-qa-settlement
│       └── release_gate_input.yaml   ← ll-qa-gate-evaluate
│
└── gate/
    └── release_gate_input.yaml
```

---

## 八、关键设计原则 (v2.2)

### 8.1 Acceptance Traceability (ADR-053)

每个 plan 包含显式的 Acceptance Traceability 表:

```markdown
## Acceptance Traceability

| Acceptance Ref | Acceptance Scenario | Capability IDs | Covered |
|----------------|---------------------|----------------|---------|
| AC-001 | Given 包已创建 When 提交 Then 状态变为已提交 | CAND-SUBMIT-001 | ✅ |
```

### 8.2 独立验证

independent_verifier 不依赖执行引擎的内部判断，基于 manifest items 的实际状态计算 verdict。

### 8.3 TESTSET 废弃 (ADR-053)

| 废弃组件 | 替代方案 |
|----------|----------|
| `ll-qa-feat-to-testset` | `ll-qa-api-from-feat` / `ll-qa-e2e-from-proto` |
| `ll-test-exec-cli` (旧) | `ll-qa-test-run` |
| `ll-test-exec-web-e2e` (旧) | `ll-qa-test-run` |

---

## 九、后续路线图

| 版本 | 能力 | 状态 |
|------|------|------|
| v2.2 | 基础执行闭环 | ✓ 完成 |
| v2.3 | ADR-048 Mission Compiler | 规划中 |
| v2.3 | 完整 9 节点 state_machine_executor | 规划中 |
| v2.3 | 8 类故障分类器 | 规划中 |

---

> **文档版本**: v2.2
> **基于里程碑**: v2.2 双链执行闭环
> **最后更新**: 2026-04-24
