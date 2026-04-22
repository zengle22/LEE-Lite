# ADR-047 双链测试完整工作流文档

> 本文档从设计（8个正式QA技能）到执行（test_exec_runtime → test_exec_execution → playwright/shell）到报告（test_exec_reporting → gate-evaluator → ci-gate-consumer），全面梳理双链测试体系如何生成和管理测试环境、测试数据、测试用例、Bug和测试报告。

---

## 一、整体架构概览

### 1.1 双链并行结构

```
需求锚点                    产出链                      执行与结算
─────────────────────────────────────────────────────────────────
FEAT需求 ──→ API链 ──→ API-Plan ──→ Manifest ──→ Spec ──→ Settlement
                      (技能1)     (技能2)    (技能3)    (技能7)

原型设计 ──→ E2E链 ──→ E2E-Plan ──→ Manifest ──→ Spec ──→ Settlement
                      (技能4)     (技能5)    (技能6)    (技能7)
```

### 1.2 四层资产分离

| 层级 | 文件 | 内容 | 生命周期 |
|------|------|------|----------|
| **Plan** | `{chain}-plan.yaml` | 需求→测试的映射规划 | 需求变更时更新 |
| **Manifest** | `{chain}-manifest.yaml` | 测试项清单+四维状态机 | 持续演进，永不删除 |
| **Spec** | `{chain}-spec-*.md` | 可读规范文档 | 随Manifest同步更新 |
| **Settlement** | `{chain}-settlement-report.yaml` | 结算报告+覆盖率+决策 | 每次Gate评估生成 |

### 1.3 八个正式QA技能

| 序号 | 技能 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| 1 | `ll-qa-feat-to-apiplan` | FEAT需求→API测试计划 | FEAT文档 | `api-plan.yaml` |
| 2 | `ll-qa-api-manifest-init` | API计划→API清单 | api-plan.yaml | `api-manifest.yaml` |
| 3 | `ll-qa-api-spec-gen` | API清单→API规范 | api-manifest.yaml | `api-spec-*.md` |
| 4 | `ll-qa-prototype-to-e2eplan` | 原型→E2E测试计划 | 原型文件 | `e2e-plan.yaml` |
| 5 | `ll-qa-e2e-manifest-init` | E2E计划→E2E清单 | e2e-plan.yaml | `e2e-manifest.yaml` |
| 6 | `ll-qa-e2e-spec-gen` | E2E清单→E2E规范 | e2e-manifest.yaml | `e2e-spec-*.md` |
| 7 | `ll-qa-settlement` | 执行结果→结算报告 | 执行产出 | `{chain}-settlement-report.yaml` |
| 8 | `ll-qa-gate-evaluate` | 双链合并→发布决策 | 双链结算 | `release-gate-input.yaml` |

---

## 二、测试环境生成与管理

### 2.1 环境定义

测试环境通过 `environment.yaml` 文件定义，位于 `ssot/tests/.artifacts/environment/`：

```yaml
# environment.yaml 结构
execution_modality: playwright | shell | hybrid
base_url: "http://localhost:3000"
browser: chromium | firefox | webkit
headless: true
viewport: { width: 1280, height: 720 }
timeout: 30000
coverage:
  enabled: true
  branch_coverage: true
  minimum_percent: 80
  include: ["src/**/*.ts"]
  exclude: ["**/*.test.ts", "**/*.spec.ts"]
```

### 2.2 环境加载流程

**入口**: `cli/lib/test_exec_runtime.py:execute_test_exec_skill()`

```
1. 加载 environment.yaml
   ↓
2. _validate_environment() — 校验必需字段
   ↓
3. 应用覆盖率默认值（如未指定则启用）
   ↓
4. 将配置传递给执行层
```

**关键函数**: `_validate_environment(env: dict)`:
- 检查 `execution_modality` 是否合法（playwright/shell/hybrid）
- 检查 `base_url` 格式
- 验证 `timeout` 范围
- 确保 `coverage` 配置完整

### 2.3 Playwright 环境初始化

**文件**: `cli/lib/test_exec_playwright.py:write_playwright_project()`

生成的文件结构：
```
ssot/tests/.artifacts/playwright/
├── package.json              # @playwright/test 依赖
├── tsconfig.json             # TypeScript 配置
├── playwright.config.ts      # 浏览器、超时、截图配置
└── e2e/
    └── test.spec.ts          # 测试用例注入入口
```

**关键配置项**:
- `use: { browserName: env.browser }` — 从 environment.yaml 继承
- `use: { headless: env.headless }` — 无头模式
- `use: { viewport: env.viewport }` — 视口尺寸
- `reporter: [['json', { outputFile: 'report.json' }]]` — JSON报告输出

### 2.4 环境生命周期

```
[创建] environment.yaml 手动/脚本创建
  ↓
[加载] 执行开始时由 runtime 加载
  ↓
[应用] 传递给 playwright.config.ts 或 shell 执行器
  ↓
[验证] _validate_environment() 校验
  ↓
[使用] 整个执行生命周期共享同一环境配置
  ↓
[记录] 环境配置写入 evidence manifest（可追溯）
```

---

## 三、测试数据管理

### 3.1 测试数据来源

测试数据存在于三个层面：

| 层级 | 来源 | 存储位置 |
|------|------|----------|
| **用例级** | `test_data` 字段 | case_pack 中每个 case 的 test_data 字典 |
| **Fixture级** | state_model 推导 | fixture_plan.yaml |
| **执行级** | 运行时注入 | subprocess 环境变量 |

### 3.2 用例级测试数据

在 `expand_requirequirement_cases()` 中，每个测试用例会携带 `test_data`：

```yaml
# case_pack.yaml 中的 test_data 示例
cases:
  - case_id: REQ-001-TC01
    title: "用户注册-正常流程"
    test_data:
      username: "testuser"
      email: "test@example.com"
      password: "SecureP@ss1"
    expected:
      status: 201
      response_body:
        success: true
```

### 3.3 Fixture 数据推导

**文件**: `cli/lib/test_exec_fixture_planner.py:plan_fixtures()`

根据 `state_model` 和 `case_family` 推导前置状态：

```python
# case_family → fixture_state 映射规则
case_family_map = {
    "happy_path":       "ready",              # 直接到就绪状态
    "negative_path":    state[-1],            # 到最后一个状态
    "boundary_condition": "ready",            # 边界条件用就绪
    "state_transition":  state[2],            # 状态转移用第三个状态
    "retry_reentry":     state[1],            # 重试用第二个状态
    "read_only_guard":   "initial",           # 只读守卫用初始状态
}
```

**输出**: `fixture_plan.yaml`
```yaml
fixtures:
  - case_id: REQ-001-TC01
    fixture_state: "ready"
    setup_steps:
      - action: "create_user"
        data: { username: "testuser", email: "test@example.com" }
    teardown_steps:
      - action: "cleanup_user"
        selector: "user:testuser"
```

### 3.4 运行时数据注入

**文件**: `cli/lib/test_exec_execution.py:execute_case()`

通过环境变量将测试数据注入 Playwright 进程：

```python
env = {
    **os.environ,
    "TEST_CASE_ID": case.case_id,
    "TEST_DATA": json.dumps(case.test_data),  # JSON序列化
    "EVIDENCE_DIR": evidence_path,              # 证据输出目录
}
subprocess.run(playwright_cmd, env=env, ...)
```

### 3.5 覆盖率数据管理

**文件**: `cli/lib/test_exec_reporting.py:collect_coverage()`

```
1. 每次执行产生 .cov 文件（Python coverage 模块）
   ↓
2. combine() 合并所有 .cov 文件
   ↓
3. json_report() 生成 JSON 覆盖率报告
   ↓
4. markdown_report() 生成 Markdown 覆盖率报告
   ↓
5. 输出到 .artifacts/coverage/
   ├── coverage-combined.json
   └── coverage-report.md
```

---

## 四、测试用例生成与管理

### 4.1 用例生成入口

**文件**: `cli/lib/test_exec_artifacts.py:build_test_case_pack()`

```
需求文档/Manifest
  ↓
infer_functional_areas()      — 从需求推导功能域
infer_logic_dimensions()      — 从需求推导逻辑维度
infer_state_model()            — 从需求推导状态模型
  ↓
expand_requirement_cases()     — 用例扩展（核心函数）
  ↓
case_pack.yaml                 — 输出用例包
```

### 4.2 用例扩展引擎

**文件**: `cli/lib/test_exec_case_expander.py:expand_requirement_cases()`

#### 4.2.1 test_units 结构

```yaml
test_units:
  - id: "TU-001"
    title: "用户注册接口"
    type: "api" | "e2e"
    acceptance_criteria:
      - "POST /users 返回 201"
      - "响应包含 user_id"
    test_mode: "minimal_projection" | "qualification_expansion"
```

#### 4.2.2 case_family 分类

**文件**: `cli/lib/test_exec_case_expander.py:_case_family()`

```python
def _case_family(unit: dict) -> list[str]:
    families = []

    # 1. happy_path — 正常流程（必须有）
    families.append("happy_path")

    # 2. negative_path — 异常流程（必须有）
    if unit.get("error_conditions"):
        families.append("negative_path")

    # 3. boundary_conditions — 边界条件
    if unit.get("boundary_values"):
        families.append("boundary_conditions")

    # 4. state_transition — 状态转移
    if unit.get("state_model"):
        families.append("state_transition")

    # 5. retry_reentry — 重试/重新进入
    if unit.get("retry_scenarios"):
        families.append("retry_reentry")

    # 6. read_only_guard — 只读操作防护
    if unit.get("read_only"):
        families.append("read_only_guard")

    return families
```

#### 4.2.3 用例生成规则

```python
# 每个 case_family 生成规则
for family in case_families:
    for criterion in acceptance_criteria:
        case = {
            "case_id": f"{req_id}-TC{seq:02d}",
            "title": f"{unit.title}-{family}",
            "case_family": family,
            "acceptance_ref": criterion,
            "test_data": unit.get("test_data", {}),
            "expected": criterion.expected,
            "priority": _priority(family),  # P0/P1/P2
        }
        cases.append(case)
```

#### 4.2.4 qualification_expansion 模式

当 `test_mode: "qualification_expansion"` 时：

```
1. 生成基础用例（同 minimal_projection）
   ↓
2. 执行第一轮测试
   ↓
3. 收集覆盖率反馈
   ↓
4. 分析未覆盖分支
   ↓
5. 自动生成补充用例（synthetic cases）
   ↓
6. 重新执行，直到覆盖率达到阈值
```

```python
# qualification_expansion 伪代码
def expand_with_coverage_feedback(requirement, env):
    cases = expand_minimal(requirement)
    while not coverage_met(env, requirement.minimum_coverage):
        runs = execute_cases(cases, env)
        coverage = collect_coverage(runs)
        gaps = find_coverage_gaps(coverage)
        new_cases = generate_synthetic_cases(gaps)
        cases.extend(new_cases)
    return cases
```

### 4.3 用例包结构

**输出**: `case_pack.yaml`
```yaml
case_pack:
  requirement_id: "REQ-001"
  test_mode: "qualification_expansion"
  generated_at: "2026-04-21T10:00:00Z"
  cases:
    - case_id: "REQ-001-TC01"
      title: "用户注册-正常流程"
      case_family: "happy_path"
      priority: "P0"
      acceptance_ref: "POST /users 返回 201"
      test_data: { ... }
      expected: { ... }
  traceability:
    - case_id: "REQ-001-TC01"
      req_refs: ["REQ-001"]
      logic_refs: ["auth", "user_creation"]
      state_refs: ["initial → ready"]
```

### 4.4 用例生命周期

```
[生成] expand_requirement_cases() 从 test_units 生成
  ↓
[打包] build_test_case_pack() 组装为 case_pack.yaml
  ↓
[注入] apply_ui_flow_plan() 附加 UI 流程计划（E2E链）
  ↓
[执行] execute_cases() 逐个执行
  ↓
[判定] judge_case_results() 判定 passed/failed/blocked/invalid/not_executed
  ↓
[追溯] build_traceability_matrix() 链接用例到需求
  ↓
[归档] 执行结果写入 evidence manifest
```

---

## 五、Bug 生成与管理

### 5.1 Bug 触发条件

**文件**: `cli/lib/test_exec_reporting.py:build_bug_bundle()`

当用例执行结果为 `failed` 时触发 Bug 生成：

```python
def build_bug_bundle(case_results: list) -> dict:
    bugs = []
    for case in case_results:
        if case.status == "failed":
            bug = _create_bug_record(case)
            bugs.append(bug)
    return {"bugs": bugs, "total": len(bugs)}
```

### 5.2 Bug ID 生成规则

```python
def _generate_bug_id(case: dict) -> str:
    # SHA-1 前8位作为Bug ID
    slug = case["case_id"].lower().replace("-", "_")
    digest = hashlib.sha1(
        f"{case['case_id']}:{case['title']}:{case['actual']}".encode()
    ).hexdigest()[:8]
    return f"BUG-{slug}-{digest}"
    # 示例: BUG-req_001_tc01-a1b2c3d4
```

### 5.3 Bug 记录结构

**输出**: `.artifacts/bugs/BUG-{slug}-{digest}.json`
```json
{
  "bug_id": "BUG-req_001_tc01-a1b2c3d4",
  "case_id": "REQ-001-TC01",
  "title": "用户注册-正常流程",
  "expected": {
    "status": 201,
    "response_body": { "success": true, "user_id": "string" }
  },
  "actual": {
    "status": 500,
    "response_body": { "error": "Internal Server Error" }
  },
  "evidence_ref": {
    "hash": "a1b2c3d4e5f6g7h8",
    "file": "e2e.onboarding.create-plan.main.evidence.yaml"
  },
  "severity": "high",
  "created_at": "2026-04-21T10:05:00Z",
  "chain": "e2e"
}
```

### 5.4 Bug 生命周期

```
[发现] execute_case() 返回 failed 状态
  ↓
[判定] judge_case_results() 确认为 failed（非 blocked/invalid）
  ↓
[创建] build_bug_bundle() 生成 BUG-{slug}-{digest}.json
  ↓
[证据] 附加 evidence_ref（SHA-256 16位哈希前缀）
  ↓
[归档] 写入 .artifacts/bugs/ 目录
  ↓
[报告] 包含在测试报告的 bug_summary 中
  ↓
[Gate] 影响 Gate 评估的 pass_rate 计算
```

### 5.5 Bug 与 Gate 评估的关系

**文件**: `ssot/tests/gate/gate-evaluator.py:evaluate_chain()`

```python
# Bug 数量影响 pass_rate
def evaluate_chain(manifest, execution_results):
    total = len(manifest.items)
    passed = sum(1 for r in execution_results if r.status == "passed")
    failed = sum(1 for r in execution_results if r.status == "failed")

    # waiver 处理：批准的 waiver 不计入分母
    waived_ids = {w.case_id for w in waivers if w.status == "approved"}
    denominator = total - len(waived_ids)

    pass_rate = passed / denominator if denominator > 0 else 1.0

    return {
        "pass_rate": pass_rate,
        "total": total,
        "passed": passed,
        "failed": failed,
        "waived": len(waived_ids),
        "bugs": failed,  # 每个 failed 对应一个 Bug
    }
```

---

## 六、测试报告生成

### 6.1 报告生成入口

**文件**: `cli/lib/test_exec_artifacts.py:render_report()`

```python
def render_report(execution_outputs: dict) -> str:
    """生成 Markdown 格式测试报告"""
    sections = [
        _header(execution_outputs),
        _run_status(execution_outputs),
        _compliance(execution_outputs),
        _coverage_summary(execution_outputs),
        _traceability_matrix(execution_outputs),
        _case_results(execution_outputs),
        _bug_summary(execution_outputs),
        _freeze_metadata(execution_outputs),
    ]
    return "\n\n".join(sections)
```

### 6.2 报告结构

**输出**: `.artifacts/reports/test-report-{timestamp}.md`

```markdown
# 测试报告: REQ-001

## 执行状态
- **模式**: playwright
- **时间**: 2026-04-21T10:00:00Z
- **环境**: http://localhost:3000 (chromium)

## 合规性
- **最低证据要求**: 满足
- **用例执行率**: 95% (19/20)

## 覆盖率摘要
- **行覆盖率**: 87.5%
- **分支覆盖率**: 82.3%
- **最低要求**: 80%
- **状态**: ✅ 通过

## 追溯矩阵
| 用例ID | 需求引用 | 逻辑引用 | 状态 |
|--------|----------|----------|------|
| REQ-001-TC01 | REQ-001 | auth, user_creation | ✅ passed |
| REQ-001-TC02 | REQ-001 | auth, validation | ❌ failed |

## 用例结果
### REQ-001-TC01: 用户注册-正常流程
- **状态**: passed
- **执行时间**: 2.3s
- **证据**: e2e.onboarding.create-plan.main.evidence.yaml

### REQ-001-TC02: 用户注册-异常流程
- **状态**: failed
- **期望**: status=400
- **实际**: status=500
- **Bug**: BUG-req_001_tc02-b2c3d4e5

## Bug 汇总
| Bug ID | 用例 | 严重度 | 状态 |
|--------|------|--------|------|
| BUG-req_001_tc02-b2c3d4e5 | REQ-001-TC02 | high | open |

## 冻结元数据
- **Checksums**: SHA-256 校验和列表
- **Patch Context**: 相关 Patch 摘要
```

### 6.3 报告生成管线

**文件**: `cli/lib/test_exec_reporting.py:finalize_execution_outputs()`

```
原始执行结果 (raw_runs)
  ↓
1. evaluate_compliance() — 检查证据完整性
  ↓
2. judge_case_results() — 判定用例结果
  ↓
3. build_bug_bundle() — 为 failed 用例生成 Bug
  ↓
4. collect_coverage() — 合并覆盖率数据
  ↓
5. render_report() — 生成 Markdown 报告
  ↓
6. _validate_outputs() — 验证输出完整性
  ↓
7. TSE payload — 打包交付物
```

### 6.4 合规性检查

**文件**: `cli/lib/test_exec_reporting.py:evaluate_compliance()`

```python
def evaluate_compliance(case_results: list, minimum_evidence: int = 1) -> dict:
    """检查每个用例是否满足最低证据要求"""
    compliant = 0
    non_compliant = 0
    for case in case_results:
        evidence_count = len(case.evidence_refs)
        if evidence_count >= minimum_evidence:
            compliant += 1
        else:
            non_compliant += 1

    return {
        "compliant": compliant,
        "non_compliant": non_compliant,
        "rate": compliant / len(case_results) if case_results else 1.0,
    }
```

### 6.5 用例判定规则

**文件**: `cli/lib/test_exec_reporting.py:judge_case_results()`

```python
def judge_case_results(raw_runs: list) -> list[dict]:
    results = []
    for run in raw_runs:
        if run.status == "passed":
            judgment = "passed"
        elif run.status == "failed":
            judgment = "failed"
        elif run.status == "skipped" and run.skip_reason == "dependency":
            judgment = "blocked"
        elif run.status == "invalid":
            judgment = "invalid"
        else:
            judgment = "not_executed"

        results.append({
            "case_id": run.case_id,
            "judgment": judgment,
            "evidence_refs": run.evidence_refs,
        })
    return results
```

---

## 七、Gate 评估与发布决策

### 7.1 单链评估

**文件**: `ssot/tests/gate/gate-evaluator.py:evaluate_chain()`

```python
def evaluate_chain(chain_name: str, manifest_path: str) -> dict:
    manifest = load_manifest(manifest_path)
    waivers = load_waivers()
    cuts = load_cut_records()

    results = {}
    for item in manifest.items:
        # 1. waiver 检查：批准的 waiver 跳过
        if item.case_id in waivers.approved:
            results[item.case_id] = "waived"
            continue

        # 2. obsolete 检查：过期项跳过
        if item.lifecycle_status == "obsolete":
            results[item.case_id] = "obsolete"
            continue

        # 3. cut 检查：裁剪记录跳过
        if item.case_id in cuts:
            results[item.case_id] = "cut"
            continue

        # 4. 正常评估
        results[item.case_id] = item.evidence_status

    total = len([r for r in results.values() if r not in ("waived", "obsolete", "cut")])
    passed = sum(1 for r in results.values() if r == "complete")

    return {
        "chain": chain_name,
        "pass_rate": passed / total if total > 0 else 1.0,
        "total": total,
        "passed": passed,
        "waived": len(waivers.approved),
        "cut": len(cuts),
    }
```

### 7.2 双链合并决策

**文件**: `ssot/tests/gate/gate-evaluator.py:generate_release_gate_input()`

```python
def generate_release_gate_input(api_result: dict, e2e_result: dict) -> dict:
    api_pass = api_result["pass_rate"] >= 0.8
    e2e_pass = e2e_result["pass_rate"] >= 0.8

    if api_pass and e2e_pass:
        decision = "pass"
        action = "release"
    elif api_pass or e2e_pass:
        decision = "conditional_pass"
        action = "conditional_release"
    else:
        decision = "fail"
        action = "block"

    return {
        "final_decision": decision,
        "action": action,
        "api_chain": api_result,
        "e2e_chain": e2e_result,
        "evaluated_at": datetime.utcnow().isoformat(),
    }
```

### 7.3 CI 消费

**文件**: `ssot/tests/gate/ci-gate-consumer.py`

```python
def ci_gate_consumer():
    gate_input = load_release_gate_input()
    decision = gate_input["final_decision"]

    exit_code = {
        "pass": 0,
        "conditional_pass": 0,
        "fail": 1,
    }.get(decision, 1)

    sys.exit(exit_code)
```

### 7.4 反懒惰检查（7项）

Gate 评估时执行7项反懒惰检查：

```python
ANTI_LAZINESS_CHECKS = [
    "manifest_not_empty",          # 清单不能为空
    "evidence_refs_present",       # 必须有证据引用
    "evidence_hash_valid",         # SHA-256 哈希有效
    "traceability_complete",       # 追溯矩阵完整
    "coverage_threshold_met",      # 覆盖率达到阈值
    "waiver_justified",            # Waiver 有正当理由
    "cut_record_valid",            # 裁剪记录有效
]
```

---

## 八、内外部能力调用

### 8.1 内部能力调用链

```
test_exec_runtime.py:execute_test_exec_skill()
  ├── test_exec_runtime.py:_validate_environment()
  ├── test_exec_runtime.py:_apply_coverage_defaults()
  ├── test_exec_execution.py:run_narrow_execution()
  │   ├── test_exec_execution.py:_execute_round()
  │   │   ├── test_exec_ui_flow.py:derive_ui_flow_plan()
  │   │   ├── test_exec_ui_resolution.py:derive_ui_intent()
  │   │   ├── test_exec_ui_resolution.py:resolve_ui_binding()
  │   │   ├── test_exec_execution.py:_build_flow_plan()
  │   │   ├── test_exec_script_mapper.py:map_scripts()
  │   │   └── test_exec_execution.py:execute_cases()
  │   │       ├── test_exec_playwright.py:write_playwright_project()
  │   │       ├── test_exec_playwright.py:run_playwright_project()
  │   │       ├── test_exec_playwright.py:parse_playwright_report()
  │   │       └── test_exec_execution.py:execute_case() [subprocess]
  │   └── test_exec_execution.py:_collect_evidence()
  ├── test_exec_artifacts.py:build_test_case_pack()
  │   └── test_exec_case_expander.py:expand_requirement_cases()
  ├── test_exec_artifacts.py:build_script_pack()
  ├── test_exec_artifacts.py:build_freeze_meta()
  ├── test_exec_artifacts.py:resolve_patch_context()
  ├── test_exec_reporting.py:finalize_execution_outputs()
  │   ├── test_exec_reporting.py:evaluate_compliance()
  │   ├── test_exec_reporting.py:judge_case_results()
  │   ├── test_exec_reporting.py:build_bug_bundle()
  │   ├── test_exec_reporting.py:collect_coverage()
  │   ├── test_exec_reporting.py:render_report()
  │   └── test_exec_reporting.py:_validate_outputs()
  └── test_exec_runtime.py:governed_write()
  └── test_exec_runtime.py:submit_handoff()
```

### 8.2 外部能力调用

| 调用 | 模块 | 说明 |
|------|------|------|
| **Playwright** | `test_exec_playwright.py` | 浏览器自动化测试 |
| **coverage 模块** | `test_exec_reporting.py` | Python 覆盖率收集 |
| **hashlib (SHA-256)** | `gate-evaluator.py` | 证据哈希绑定 |
| **hashlib (SHA-1)** | `test_exec_reporting.py` | Bug ID 生成 |
| **subprocess** | `test_exec_execution.py` | 执行 Playwright 进程 |
| **yaml/json** | 全模块 | 配置和产出序列化 |

### 8.3 文件 I/O 接口

| 文件 | 读/写 | 模块 |
|------|------|------|
| `environment.yaml` | 读 | test_exec_runtime |
| `test_set.yaml` | 读 | test_exec_runtime |
| `case_pack.yaml` | 写 | test_exec_artifacts |
| `fixture_plan.yaml` | 写 | test_exec_fixture_planner |
| `e2e/test.spec.ts` | 写 | test_exec_playwright |
| `report.json` | 读 | test_exec_playwright |
| `*.cov` | 读写 | test_exec_reporting |
| `coverage-combined.json` | 写 | test_exec_reporting |
| `coverage-report.md` | 写 | test_exec_reporting |
| `test-report-{ts}.md` | 写 | test_exec_artifacts |
| `BUG-*.json` | 写 | test_exec_reporting |
| `evidence.yaml` | 写 | test_exec_execution |
| `{chain}-manifest.yaml` | 读写 | gate-evaluator |
| `{chain}-settlement-report.yaml` | 写 | gate-evaluator |
| `release-gate-input.yaml` | 写 | gate-evaluator |
| `waiver.yaml` | 读 | gate-evaluator |

---

## 九、四维状态机

Manifest 中每个测试项维护四个维度的状态：

### 9.1 lifecycle_status

```
draft → active → executing → complete → obsolete
```

### 9.2 mapping_status

```
unmapped → mapped → verified → drifted
```

### 9.3 evidence_status

```
none → partial → complete → inconsistent
```

### 9.4 waiver_status

```
none → pending → approved → rejected
```

**规则**:
- `waiver_status == approved` 的项不计入 Gate 评估分母
- `lifecycle_status == obsolete` 的项跳过评估
- `evidence_status == inconsistent` 触发重新执行

---

## 十、完整执行流程

```
[阶段1: 规划]
FEAT/Prototype
  → Skill 1/4: Plan 生成
  → Skill 2/5: Manifest 初始化
  → Skill 3/6: Spec 生成

[阶段2: 准备]
  → load environment.yaml（测试环境）
  → load test_set.yaml（测试集）
  → expand_requirement_cases() → case_pack.yaml（测试用例）
  → plan_fixtures() → fixture_plan.yaml（前置数据）
  → derive_ui_flow_plan() → UI 流程计划
  → resolve_ui_binding() → UI 选择器绑定

[阶段3: 执行]
  → run_narrow_execution()
    → _execute_round()
      → derive_ui_intent()（UI意图推导）
      → resolve_ui_binding()（UI选择器匹配）
      → write_playwright_project()（生成Playwright项目）
      → run_playwright_project()（执行浏览器测试）
      → parse_playwright_report()（解析JSON报告）
      → execute_case()（子进程执行，注入test_data）
      → _collect_evidence()（收集证据，SHA-256哈希）

[阶段4: 报告]
  → finalize_execution_outputs()
    → evaluate_compliance()（合规性检查）
    → judge_case_results()（用例判定）
    → build_bug_bundle()（Bug生成）
    → collect_coverage()（覆盖率合并）
    → render_report()（Markdown报告）
    → _validate_outputs()（输出验证）

[阶段5: 结算]
  → Skill 7: Settlement 生成
  → Skill 8: Gate 评估
    → evaluate_chain("api")
    → evaluate_chain("e2e")
    → generate_release_gate_input()
    → 写入 release-gate-input.yaml

[阶段6: CI消费]
  → ci-gate-consumer.py
    → 读取 release-gate-input.yaml
    → 映射 decision → exit code
    → sys.exit(0) 通过 / sys.exit(1) 阻断
```

---

## 十一、关键设计原则

### 11.1 证据哈希绑定

每个用例执行结果通过 SHA-256 哈希绑定：

```python
def compute_evidence_hash(evidence_refs: list) -> str:
    content = "".join(sorted(evidence_refs))
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

### 11.2 追溯矩阵

需求→用例→执行→Bug 全链路可追溯：

```
FEAT-001
  → api-manifest.yaml:ITEM-001
    → REQ-001-TC01 (case_pack)
      → execution: passed
        → evidence: a1b2c3d4e5f6g7h8
        → traceability: REQ-001 → auth → user_creation
```

### 11.3 不可变性

- Manifest 项永不删除，只标记 `obsolete`
- Bug 记录一旦创建不可修改（只能追加评论）
- Evidence 文件只写不改，通过哈希验证完整性

### 11.4 Waiver 系统

```yaml
# waiver.yaml 结构
waivers:
  - case_id: "REQ-001-TC05"
    reason: "第三方服务不可用，非系统缺陷"
    source_ref: "https://issues.example.com/123"
    status: "approved"  # none | pending | approved | rejected
    approved_by: "tech-lead@example.com"
    approved_at: "2026-04-20T15:00:00Z"
```

**规则**: approved waiver 不计入 Gate 评估分母

### 11.5 Cut 记录

```yaml
# cut record 结构
cuts:
  - case_id: "REQ-001-TC06"
    reason: "功能已废弃"
    mandatory_approver: "product-owner@example.com"
    source_ref: "ADR-048"
    cut_at: "2026-04-20T16:00:00Z"
```

**规则**: 必须有 mandatory_approver + source_ref

---

## 十二、目录结构

```
ssot/tests/
├── .artifacts/
│   ├── environment/
│   │   └── environment.yaml          # 测试环境配置
│   ├── test_set.yaml                 # 测试集定义
│   ├── case_pack.yaml                # 测试用例包
│   ├── fixture_plan.yaml             # Fixture 计划
│   ├── playwright/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── playwright.config.ts
│   │   └── e2e/test.spec.ts
│   ├── coverage/
│   │   ├── *.cov                     # 原始覆盖率数据
│   │   ├── coverage-combined.json    # 合并后覆盖率
│   │   └── coverage-report.md        # 覆盖率报告
│   ├── reports/
│   │   └── test-report-*.md          # 测试报告
│   ├── bugs/
│   │   └── BUG-*.json                # Bug 记录
│   ├── evidence/
│   │   └── e2e/run-*/                # 执行证据
│   └── settlement/
│       ├── api-settlement-report.yaml
│       └── e2e-settlement-report.yaml
├── gate/
│   ├── gate-evaluator.py
│   ├── ci-gate-consumer.py
│   └── release_gate_input.yaml
├── plans/
│   ├── api-plan.yaml
│   └── e2e-plan.yaml
├── manifests/
│   ├── api-manifest.yaml
│   └── e2e-manifest.yaml
└── specs/
    ├── api-spec-*.md
    └── e2e-spec-*.md

cli/lib/
├── test_exec_runtime.py              # 执行入口
├── test_exec_execution.py            # 执行循环
├── test_exec_playwright.py           # Playwright 翻译
├── test_exec_artifacts.py            # 产出构建
├── test_exec_reporting.py            # 报告与验证
├── test_exec_case_expander.py        # 用例扩展
├── test_exec_fixture_planner.py      # Fixture 计划
├── test_exec_ui_flow.py              # UI 流程
├── test_exec_ui_resolution.py        # UI 绑定
├── test_exec_script_mapper.py        # 脚本映射
└── test_exec_traceability.py         # 追溯
```

---

> 文档版本: 1.0
> 最后更新: 2026-04-21
> 基于: ADR-047 v1.4 (Trial Approved)
