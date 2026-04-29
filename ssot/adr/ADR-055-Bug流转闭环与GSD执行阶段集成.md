# ADR-055：Bug 流转闭环与 GSD Execute-Phase 集成

> **SSOT ID**: ADR-055
> **Title**: 在 ADR-054 测试执行闭环基础上，建立 Bug 发现→验收确认→修复→再验证的完整流转机制，并与 GSD execute-phase 研发流程无缝集成
> **Status**: Draft
> **Version**: v1.1-draft
> **Effective Date**: TBD
> **Scope**: 测试治理 / Bug 生命周期 / GSD 研发流程集成
> **Owner**: 架构 / QA 治理 / 研发流程
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、QA 技能编排层、GSD 执行代理、开发者
> **Depends On**: ADR-047 (双链测试架构), ADR-054 (实施轴桥接与执行闭环), ADR-053 (需求轴统一入口)
> **Supersedes**: 无

---

## 1. 背景

### 1.1 One-Sentence Summary

> **ADR-054 打通了 feat→spec→执行→settlement→gate 的测试链路，但测试发现的失败用例没有下游消费者：失败信息散落在 execution artifacts 中，无状态流转、无修复追踪、无法与 GSD execute-phase 研发流程对接，导致"发现 Bug 但无人修复、修复后无人验证"的断裂。**

### 1.2 问题

#### 1.2.1 测试失败无持久化追踪

当前 `ll-qa-test-run` 执行后：

```
ll-qa-test-run
    ↓
test_exec_execution.py 执行测试
    ↓
test_exec_reporting.py 生成 case_results (passed/failed/blocked)
    ↓
test_exec_reporting.py:174 build_bug_bundle() → output_root/bugs/*.json
    ↓
[执行目录可能被后续运行覆盖]
    ↓
[bug 信息丢失]
```

`build_bug_bundle()` 生成的 bug 文件只存在于执行输出目录 `artifacts/active/qa/executions/{run_slug}/bugs/`，**没有持久化到 SSOT**，后续运行会生成新的执行目录，历史 bug 信息无法追溯。

#### 1.2.2 执行层越界做决策

如果让 `ll-qa-test-run` 在发现失败时直接生成 GSD fix phase，存在三个问题：

1. **执行层越界**：test-run 的职责是执行测试、产出证据，不应该做"是否需要修复"的决策
2. **假失败未过滤**：flaky test、环境问题、spec 漂移都可能在 test-run 阶段表现为失败，但只有经过 settlement + gate 的完整分析才能确认"这确实是需要修复的缺陷"
3. **waiver 信息不可见**：test-run 时不知道哪些失败项已被 waiver approved，可能为已豁免的项生成修复 phase

#### 1.2.3 验收层与修复层未分离

当前流程：

```
test-run (执行)
    ↓
settlement (统计) ←── 知道 failed items，但不知道是否是"真缺陷"
    ↓
gate-evaluate (决策) ←── 做最终决策，但不触发修复
    ↓
[流程终止，无人修复]
```

Gate 返回 FAIL 后，没有机制将"需要修复的事项"转化为可执行的研发任务。

#### 1.2.4 GSD 研发流程与测试流程割裂

当前 GSD execute-phase 用于实现功能（如 Phase 20-24），但测试发现的 bug 没有自动成为 GSD phase。开发者需要：
1. 手动阅读 test report
2. 手动分析失败原因
3. 手动创建修复计划
4. 手动执行修复
5. 手动重新测试

### 1.3 相关 ADR 关系

| ADR | 关系 | 说明 |
|-----|------|------|
| ADR-047 | 依赖 | 双链测试架构提供测试执行基础 |
| ADR-054 | 依赖 | 实施轴桥接层提供 spec→执行通路 |
| ADR-053 | 依赖 | 需求轴统一入口提供 spec 来源 |
| ADR-050 | 参考 | SSOT 语义治理定义持久化规范 |

---

## 2. 决策

### 2.1 核心原则：三层分离与职责边界

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: 执行层 (Execution)                                │
│  ll-qa-test-run                                              │
│  职责：执行测试，产出 case_results，记录 detected bug       │
│  产出：execution artifacts, run-manifest, detected-bug-list │
│  决策权：无 —— 仅记录事实，不做任何"是否需要修复"的判断     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: 验收层 (Acceptance)                               │
│  independent_verifier → settlement → gate-evaluate          │
│  职责：分析执行结果，过滤 flaky/env/spec-drift 假失败，      │
│        应用 waivers，产出 verdict                           │
│  产出：settlement-report, release_gate_input.yaml           │
│  决策权：是否通过 gate —— 但不决定"如何修复"               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (仅当 gate.final_decision == FAIL)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: 修复层 (Remediation)                              │
│  gate_remediation → bug_phase_generator → gsd-execute-phase │
│  职责：将确认的缺陷转化为 GSD fix phase，执行修复，再验证   │
│  产出：.planning/phases/{N}-bug-fix-*/                      │
│  决策权：开发者决定修复方案；系统仅辅助生成 phase 框架      │
└─────────────────────────────────────────────────────────────┘
```

**关键决策**：
1. 执行层只记录，不决策。`detected` 状态的 bug 是原始观察，不代表一定是真缺陷。
2. 验收层做"是否阻塞发布"的决策（gate FAIL/PASS），但不做"如何修复"的决策。
3. 修复层仅在 gate FAIL 时触发，将 `detected` 提升为 `open`，并生成 GSD phase。
4. 三层之间通过 SSOT 文件（bug-registry、settlement-report、gate-input）传递信息，而非内存状态或直接调用。

### 2.2 Bug 状态机

```
                         ┌─────────────┐
                    ┌────┤  duplicate  │
                    │    └─────────────┘
                    │    ┌─────────────┐
                    ├────┤not_reproducible│
                    │    └─────────────┘
                    │    ┌─────────────┐
                    └────┤   wont_fix  │
                         └─────────────┘
                              ▲
                              │ 人工判定
┌─────────┐                   │
│  (无)   │──test-run失败────►├────►┌──────────┐
└─────────┘                   │     │ detected │
                              │     └────┬─────┘
                              │          │ gate FAIL
                              │          ▼
                              │     ┌─────────┐
                              │     │  open   │◄─────────────┐
                              │     └────┬────┘              │
                              │          │ /gsd-execute-phase │
                              │          ▼                    │
                              │     ┌─────────┐  修复提交     │
                              │     │ fixing  │────────────►┐ │
                              │     └─────────┘             │ │
                              │                             │ │
                              │          ◄──────────────────┘ │
                              │          ▼                    │
                              │     ┌─────────┐               │
                              │     │  fixed  │               │
                              │     └────┬────┘               │
                              │          │ --verify-bugs      │
                              │    ┌─────┴─────┐              │
                              │ 通过│re_verify_ │  失败         │
                              │──► │  passed   │──────────────┘
                              │    └─────┬─────┘
                              │          │
                              │          ▼
                              │     ┌─────────┐
                              └────►│ closed  │
                                    └─────────┘
```

**核心状态（ happy path ）**：

| 状态 | 触发条件 | 责任方 | 说明 |
|------|----------|--------|------|
| `detected` | test-run 发现 case failed | 系统（自动） | 原始记录，尚未经过 gate 确认。允许存在假失败（flaky、环境问题、spec 漂移） |
| `open` | gate FAIL 后确认 | 系统（自动） | 验收层确认为真缺陷，进入修复队列 |
| `fixing` | 开发者开始修复 | 开发者 / GSD phase | 可选中间态。可由开发者手动标记，或由 GSD phase 执行状态推断 |
| `fixed` | 修复代码已提交 | 系统（自动） | 等待再验证。由 bug transition CLI 或 phase 完成 hook 自动流转 |
| `re_verify_passed` | --verify-bugs 通过 | 系统（自动） | 验证通过的中间态，等待人工确认关闭 |
| `closed` | 验证通过且无争议 | 开发者（人工） | 缺陷生命周期结束。人工确认防止自动化误关闭 |

**终止状态（terminal states）**：

| 状态 | 触发条件 | 责任方 | 说明 |
|------|----------|--------|------|
| `wont_fix` | 确认为 false positive / 已知限制 / 业务接受 | 开发者（人工） | 任意时刻可转入，需填写 `resolution_reason` |
| `duplicate` | 与已有 bug 重复 | 开发者 / 系统 | 需关联 `duplicate_of` 字段 |
| `not_reproducible` | 无法复现且 settlement 通过 | 系统（自动） | 连续 N 次 test-run 未复现后自动标记 |

**状态流转矩阵**：

| 从 \ 到 | open | fixing | fixed | re_verify_passed | closed | wont_fix | duplicate | not_reproducible |
|---------|------|--------|-------|------------------|--------|----------|-----------|------------------|
| detected | ✓ (gate FAIL) | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |
| open | ✗ | ✓ (人工) | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |
| fixing | ✗ | ✗ | ✓ (commit) | ✗ | ✗ | ✓ | ✓ | ✗ |
| fixed | ✗ | ✗ | ✗ | ✓ (verify pass) | ✗ | ✓ | ✓ | ✗ |
| re_verify_passed | ✗ | ✗ | ✗ | ✗ | ✓ (人工) | ✓ | ✓ | ✗ |
| 任意 → | — | — | — | — | — | ✓ | ✓ | ✓ (系统) |

> **注**：`re_verify_failed` 不是独立状态，验证失败后直接回退到 `open`，保持状态机扁平。

### 2.3 Bug 注册表格式与存储位置

**存储位置**：`artifacts/bugs/{feat_ref}/bug-registry.yaml`

> 选择 `artifacts/` 而非 `ssot/` 的理由：bug 是执行过程的**观察产物**，不是需求或设计决策的权威来源。bug 注册表可以被删除后通过重新执行 test-run + gate 流程重建，符合 artifacts 的语义。`ssot/` 应保留给不可推导的权威信息（spec、ADR、manifest）。

```yaml
# artifacts/bugs/{feat_ref}/bug-registry.yaml
bug_registry:
  schema_version: "1.0"
  registry_id: BUG-REG-FEAT-SRC-003-001
  feat_ref: FEAT-SRC-003-001
  proto_ref: null
  generated_at: "2026-04-28T10:00:00Z"
  last_synced_at: "2026-04-28T12:00:00Z"
  last_sync_run_id: RUN-20260428-ABC12345
  bugs:
    - bug_id: BUG-api.job.gen.invalid-progression-A1B2C3
      case_id: api.job.gen.invalid-progression
      coverage_id: api.job.gen.invalid-progression
      title: "JOB-GEN-001: invalid-progression"
      status: open
      severity: high
      gap_type: functional_failure
      actual: "HTTP 200 with invalid progression state"
      expected: "HTTP 400 with validation error"
      evidence_ref: artifacts/active/qa/executions/run-xxx/evidence/result.json
      stdout_ref: artifacts/active/qa/executions/run-xxx/evidence/stdout.txt
      stderr_ref: artifacts/active/qa/executions/run-xxx/evidence/stderr.txt
      diagnostics:
        - "AssertionError: expected status 400, got 200"
      run_id: RUN-20260428-ABC12345
      discovered_at: "2026-04-28T10:00:00Z"
      fixed_at: null
      verified_at: null
      closed_at: null
      resolution: null
      fix_commit: null
      duplicate_of: null
      resolution_reason: null
      re_verify_result: null
      trace:
        - event: discovered
          at: "2026-04-28T10:00:00Z"
          run_id: RUN-20260428-ABC12345
        - event: status_changed
          at: "2026-04-28T11:00:00Z"
          from: detected
          to: open
      manifest_ref: ssot/tests/api/FEAT-SRC-003-001/api-coverage-manifest.yaml
```

**字段说明（新增/关键）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `gap_type` | enum | 失败根因分类：`functional_failure`（功能缺陷）、`coverage_gap`（覆盖缺失）、`performance_regression`（性能回退）、`contract_violation`（契约违反）、`env_flake`（环境波动） |
| `duplicate_of` | string \| null | 指向被重复的 bug_id |
| `resolution_reason` | string \| null | 终止状态的说明（如 "known limitation", "false positive"） |
| `closed_at` | datetime \| null | 最终关闭时间 |

### 2.4 GSD Fix Phase 生成机制

**触发时机**：`gate-evaluate` 产出 `final_decision: FAIL` 后，由开发者主动触发（pull model），而非系统自动推送（push model）。

**触发命令**：
```bash
ll-bug-remediate --feat-ref FEAT-SRC-003-001 [--batch] [--severity high,critical]
```

> **Pull vs Push 说明**：Gate 产出 FAIL  verdict 后，系统**仅更新 bug-registry** 并将 `detected` 提升为 `open`。是否生成 phase、生成多少个 phase，由开发者根据上下文决定。这避免了：
> 1. Gate 假 FAIL 时自动生成无意义的 phase
> 2. 开发者正在手动修复时系统干扰
> 3. 批量修复场景被拆成过多细碎 phase

**生成流程**：

```
gate-evaluate → release_gate_input.yaml (final_decision=FAIL)
    ↓
bug-registry 中 status=detected 的 bug 被提升为 open
    ↓
开发者运行 ll-bug-remediate
    ↓
gate_remediation.py 读取 settlement gap_list + bug-registry
    ↓
模式 A：单 Bug 单 Phase（默认）
    对每个 severity=critical/high 的 open bug：
        生成 .planning/phases/{N}-bug-fix-{bug_id}/

模式 B：批量修复 Phase（--batch）
    对同一 feat 的所有 open bug：
        按模块/根因分组
        生成 .planning/phases/{N}-bug-fix-{feat_ref}-batch/
    ↓
生成 tests/defect/failure-cases/BUG-{id}.md
    ↓
提示开发者：/gsd-execute-phase {N}
```

**Phase 疲劳防护**：

| 条件 | 行为 |
|------|------|
| open bugs ≤ 3 | 默认单 bug 单 phase，清晰可追溯 |
| open bugs > 3 且同根因 | 建议 `--batch`，合并到一个 phase |
| open bugs > 3 且不同根因 | 按模块分组，每组一个 batch phase |
| severity = critical | 强制独立 phase，不批量 |

**生成目录结构**：

```
.planning/phases/{N}-bug-fix-{bug_id}/
├── {N}-CONTEXT.md           # bug 证据 + 约束 + 相关代码引用
├── {N}-01-PLAN.md           # tasks: 分析→修复→verify-bugs
├── {N}-DISCUSSION-LOG.md    # 开发者与 AI 的协作记录
└── {N}-SUMMARY.md           # execute-phase 完成后填写
```

### 2.5 修复 Phase 的标准结构

生成的 PLAN.md 包含 6 个标准 task：

| Task | 类型 | 内容 | 状态流转 |
|------|------|------|----------|
| 1 | human | Root Cause Analysis — 分析 bug 证据，确定根因 | — |
| 2 | auto | Implement Fix — 最小范围修复 | — |
| 3 | auto | Update Bug Status — `transition_bug_status(fixed, fix_commit)` | `fixing` → `fixed` |
| 4 | auto | Verify Fix — `qa-test-run --verify-bugs` | `fixed` → `re_verify_passed` / `open` |
| 5 | human | Review & Close — 确认验证结果，运行 `ll-bug-close` | `re_verify_passed` → `closed` |
| 6 | human | Update Failure Case — 更新 `tests/defect/failure-cases/BUG-{id}.md` | — |

### 2.6 再验证机制

`--verify-bugs` 支持两种验证模式：

**模式 A：Targeted 验证（默认）**

仅运行与 `status=fixed` bug 关联的 test units，快速验证修复是否生效：

```python
def run_spec_test(..., verify_bugs: bool = False, verify_mode: str = "targeted"):
    if verify_bugs:
        fixed_bugs = get_bugs_for_re_verify(workspace_root, target_ref)
        fixed_coverage_ids = {b["coverage_id"] for b in fixed_bugs}

        if verify_mode == "targeted":
            # 只运行关联的 test units
            test_units = filter_by_coverage_ids(test_units, fixed_coverage_ids)
        elif verify_mode == "full-suite":
            # 运行完整 suite，确保修复没有引入回归
            pass  # 使用全部 test_units

        result = execute_test_exec_skill(...)

        for bug in fixed_bugs:
            if result_for_bug(bug) == "passed":
                transition_bug_status(bug, "re_verify_passed")
                # closed 需要人工确认，见 2.8 角色与职责
            else:
                transition_bug_status(bug, "open")  # 回退
```

**模式 B：Full-suite 验证（`--verify-mode=full-suite`）**

运行完整测试 suite，用于：
- 修复涉及公共代码（shared utilities、core framework）时，确认没有引入回归
- 批量修复 phase 完成后，做全面验收
- CI/CD 管道中的预提交检查

**验证后状态流转规则**：

| 结果 | 流转 |
|------|------|
| targeted 通过 | `fixed` → `re_verify_passed`（等待人工 closed） |
| targeted 失败 | `fixed` → `open`（回退） |
| full-suite 通过 | `fixed` → `re_verify_passed`（同上） |
| full-suite 失败（新 bug） | 新 bug 进入 `detected`，当前 bug 保持 `fixed` 或回退 `open` |

### 2.7 与现有 GSD Phase 的兼容性

| 维度 | 兼容性 | 说明 |
|------|--------|------|
| Phase 编号 | 自动递增 | 从 `.planning/phases/` 现有最大编号 +1 |
| PLAN.md 格式 | 标准格式 | tasks + verify + success_criteria |
| CONTEXT.md | 新增 | 包含 bug 证据和约束 |
| SUMMARY.md | 人工填写 | execute-phase 完成后写 |
| `/gsd-execute-phase` | 直接可用 | 无需修改 GSD 技能本身 |
| `tests/defect/failure-cases/` | 现有目录 | v2.2.1 已在使用 |
| autonomous 标志 | `false` | Bug fix 需要 human-in-the-loop |

### 2.8 角色与职责

明确每个阶段的决策权归属，消除 handoff 黑洞：

| 角色 | 职责 | 决策权 | 使用工具 / 命令 |
|------|------|--------|-----------------|
| **AI 测试执行代理** | 运行测试，记录失败，生成 bug 原始记录 | 无决策权 | `ll-qa-test-run` |
| **AI 验收代理** | 分析 settlement，评估 gate，过滤假失败 | FAIL/PASS 决策 | `ll-qa-settlement`, `ll-qa-gate-evaluate` |
| **AI 修复辅助代理** | 读取 bug 证据，生成 phase 框架，辅助代码修复 | 无决策权 | `ll-bug-remediate`, `/gsd-execute-phase` |
| **开发者（人类）** | 根因分析、修复方案决策、人工关闭 bug、标记 wont_fix | 修复方案 + 关闭确认 | 阅读 CONTEXT.md，执行 PLAN.md，运行 `--verify-bugs` |

**关键 handoff 点**：

1. **gate-evaluate → 开发者**：gate 产出 FAIL 后，系统在终端输出 `⚠️ Gate FAILED: X bugs opened. Run 'll-bug-remediate --feat-ref {ref}' to generate fix phases.` 开发者**主动决定是否立即修复**。
2. **re_verify_passed → closed**：系统输出 `✅ Bug {id} verified. Run 'll-bug-close --bug-id {id}' to close.` 开发者**确认无误后手动关闭**，防止自动化误杀。
3. **detected → wont_fix / duplicate**：开发者在 review bug-registry 后，使用 `ll-bug-transition --bug-id {id} --to wont_fix --reason "..."` 人工标记。

---

## 3. 实现计划

### Phase 1：Bug 注册表与状态机

| 任务 | 文件 | 优先级 |
|------|------|--------|
| Bug 注册表模块 | `cli/lib/bug_registry.py` | P0 |
| Bug Phase 生成器 | `cli/lib/bug_phase_generator.py` | P0 |
| test-run 集成 | `cli/lib/test_orchestrator.py` | P0 |
| test-run 输出契约更新 | `skills/ll-qa-test-run/output/contract.yaml` | P0 |

### Phase 2：验收层集成

| 任务 | 文件 | 优先级 |
|------|------|--------|
| Gate Remediation 模块 | `cli/lib/gate_remediation.py` | P0 |
| gate-evaluate 集成 | `cli/commands/skill/command.py` | P0 |
| gate-evaluate 输出契约更新 | `skills/ll-qa-gate-evaluate/output/contract.yaml` | P0 |
| settlement 消费 bug 注册表 | `skills/ll-qa-settlement/input/contract.yaml` | P1 |

### Phase 3：GSD 闭环验证

| 任务 | 文件 | 优先级 |
|------|------|--------|
| `--verify-bugs` 模式 | `cli/lib/test_orchestrator.py` | P0 |
| Bug transition CLI | `cli/commands/skill/command.py` | P1 |
| 集成测试 | `tests/integration/test_bug_closure.py` | P0 |

---

## 4. 向后兼容性

### 4.1 现有测试流程不受影响

- `ll-qa-test-run` 的默认行为不变，新增 `--verify-bugs` 是可选参数
- `ll-qa-settlement` 和 `ll-qa-gate-evaluate` 默认不依赖 bug 注册表
- `build_bug_bundle()` 继续生成 execution output 目录中的 bug 文件（向后兼容）

### 4.2 GSD Phase 格式兼容

- Auto-generated bug fix phase 遵循与 Phase 20-24 完全相同的 PLAN.md 格式
- 现有 `/gsd-execute-phase` 命令无需修改即可执行新生成的 phase

---

## 5. 开放问题

| # | 问题 | 状态 | 决策时机 |
|---|------|------|----------|
| OQ-1 | 多个 bug 是否合并为一个 phase（同一 feat 的批量修复）？ | **已决策**：`--batch` 模式 + 同根因分组，critical 强制独立 | §2.4 |
| OQ-2 | `detected` 状态的 bug 保留多久后自动清理？ | 待决策 | Phase 2 运行时 |
| OQ-3 | Bug severity 是否影响 GSD phase 的优先级排序？ | **已决策**：critical/high 默认独立 phase，其他可批量 | §2.4 |
| OQ-4 | `not_reproducible` 的"连续 N 次未复现"阈值 N=？ | 待决策 | Phase 1 review |
| OQ-5 | Severity 分级标准（谁定？ settlement 自动定还是人工定？） | 待决策 | Phase 1 review |
| OQ-6 | `ll-bug-remediate` 是否支持 `--auto-close` 跳过人工确认？ | 待决策 | Phase 3 review（默认禁止，可选开启） |

---

## 6. 验收标准

### Phase 1 验收

- [ ] `cli/lib/bug_registry.py` 能创建、读取、更新 `artifacts/bugs/{feat_ref}/bug-registry.yaml`
- [ ] Bug 核心状态机完整流转：`detected → open → fixing → fixed → re_verify_passed`
- [ ] Bug 终止状态可用：`wont_fix`、`duplicate`、`not_reproducible`
- [ ] `build_bug_bundle()` 产出包含 `status: detected` 和 `gap_type` 的 bug JSON
- [ ] `sync_bugs_to_registry()` 将 detected bug 持久化到 `artifacts/bugs/`

### Phase 2 验收

- [ ] `gate_remediation.py` 在 gate FAIL 时读取 bug-registry 和 settlement gap_list
- [ ] 确认的 detected bug 状态变为 `open`
- [ ] 单 bug 单 phase 生成：`.planning/phases/{N}-bug-fix-{bug_id}/` 目录结构正确
- [ ] 批量修复 phase 生成：`--batch` 模式按模块/根因分组
- [ ] 生成 `tests/defect/failure-cases/BUG-{id}.md`
- [ ] `/gsd-execute-phase {N}` 可直接执行生成的 phase
- [ ] Pull model 验证：gate FAIL 后不自动生成 phase，需开发者运行 `ll-bug-remediate`

### Phase 3 验收

- [ ] `--verify-bugs` 默认 targeted 模式，只运行 `status=fixed` 关联测试
- [ ] `--verify-mode=full-suite` 运行完整 suite 并检测回归
- [ ] 验证通过后 bug 自动流转为 `re_verify_passed`
- [ ] 验证失败后 bug 回退为 `open`
- [ ] `re_verify_passed` 需人工确认后才可变为 `closed`
- [ ] 完整闭环：`qa-test-run` → `gate-evaluate` → `ll-bug-remediate` → `gsd-execute-phase` → `--verify-bugs` → 人工 `closed`

---

## 7. 修订记录

| 版本 | 日期 | 修订者 | 变更内容 |
|------|------|--------|----------|
| v1.0-draft | 2026-04-28 | 架构 / AI 代理 | 初始草案：三层分离、6 状态机、ssot/bugs/ 存储、自动 push 生成 phase |
| v1.1-draft | 2026-04-28 | 多角色评审后修订 | **架构**：明确 pull model，增加批量修复（--batch），迁移存储到 artifacts/bugs/；**状态机**：扩展终止状态（duplicate, not_reproducible），简化核心路径；**验收**：增加 full-suite 验证模式、gap_type 分类；**职责**：新增角色与 handoff 定义；**开放问题**：增加 severity 仲裁、auto-close 开关 |
