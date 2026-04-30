# ADR-055：Bug 流转闭环与 GSD Execute-Phase 集成

> **SSOT ID**: ADR-055
> **Title**: 在 ADR-054 测试执行闭环基础上，建立 Bug 发现→验收确认→修复→再验证的完整流转机制，并与 GSD execute-phase 研发流程无缝集成
> **Status**: Draft
> **Version**: v1.6-final-2
> **Effective Date**: TBD
> **Scope**: 测试治理 / Bug 生命周期 / GSD 研发流程集成
> **Owner**: 架构 / QA 治理 / 研发流程
> **Governance Kind**: NEW
> **Audience**: AI 实施代理、QA 技能编排层、GSD 执行代理、开发者
> **Depends On**: ADR-047 (双链测试架构), ADR-054 (实施轴桥接与执行闭环), ADR-053 (需求轴统一入口)
> **Supersedes**: 无
>
> 状态：Draft
> 日期：2026-04-28
> 相关 ADR：ADR-047, ADR-053, ADR-054

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
2. 验收层做"是否阻塞发布"的决策（gate FAIL/PASS）。**gate FAIL 的语义隐含"将 detected 确认为 open（真缺陷）"**，验收层由此天然携带"确认缺陷"的决策权，但不决定"如何修复"。
3. 修复层仅在 gate FAIL 时触发，将 `detected` 提升为 `open`，并生成 GSD phase。
4. 三层之间通过 SSOT 文件（bug-registry、settlement-report、gate-input）传递信息，而非内存状态或直接调用。

#### v1.6 立场：MVP 阶段所有修复人工确认

v1.6 采用**砍半 MVP**策略：取消 autonomy grant 机制，所有 bug-fix phase 统一标记为 `autonomous: false`（人工确认）。

**理由**（基于多角色评审共识）：
1. **John（PM）**：Autonomy 是规模化后的效率优化，不是 MVP 的必需品。先跑通单条 bug 的完整生命周期，比完美设计一百条但每条都半死不活强一百倍。
2. **Quinn（QA）**：Y 键确认在 batch 场景下是形式主义，但保留作为最后护栏。去掉 autonomy 后，diff 审查由既有 PR review 承担，不额外增加人类动作。
3. **Winston（架构）**：Autonomy 阈值（reopen_rate、escalation_rate、break-glass 频率）需要 2-4 周的数据积累才能校准，MVP 阶段没有数据，阈值是虚构的。

**保留的约束**（不依赖 autonomy 数据）：
- Diff size 提示（§2.6）：系统仍计算并展示 diff 统计，但不阻断 commit，仅作为开发者参考
- Coverage 提示（§2.6）：系统仍对比覆盖率变化，但不阻断关闭，仅标注在 registry 中供审阅

**Autonomy 的后续路线**：v2 阶段（预计 MVP 运行 4 周后）根据实际数据评估是否引入。届时将重新评估 §2.1 的 4 条件和撤销阈值。

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
| `not_reproducible` | 无法复现且 settlement 通过 | 系统（自动） | 按测试层级设置 N 阈值（见 §2.12 NFR）。**终止状态，不复活**；若再次失败，创建新的 `bug_id` 记录 |

**终止状态复活策略**：

`not_reproducible` / `archived` / `wont_fix` 为终止状态，语义上不允许状态回退。若同一 case 在新一轮 test-run 中再次失败：
- **不修改原记录**（保持终止状态的审计纯粹性）
- **创建新 bug 记录**（新的 `bug_id`，`trace` 中可关联原记录 `resurrected_from: {old_bug_id}`）
- 新记录进入 `detected` 状态，重新走完整验收流程

这保证了审计链清晰——"该 bug 曾被认为是不可复现的，但新的观察推翻了这一结论"。

**状态流转矩阵**：

| 从 \ 到 | open | fixing | fixed | re_verify_passed | closed | wont_fix | duplicate | not_reproducible |
|---------|------|--------|-------|------------------|--------|----------|-----------|------------------|
| detected | ✓ (gate FAIL) | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |
| open | ✗ | ✓ (人工) | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |
| fixing | ✗ | ✗ | ✓ (commit) | ✗ | ✗ | ✓ | ✓ | ✗ |
| fixed | ✗ | ✗ | ✗ | ✓ (verify pass) | ✗ | ✓ | ✓ | ✗ |
| re_verify_passed | ✗ | ✗ | ✗ | ✗ | ✓ (人工) | ✓ | ✓ | ✗ |
| archived | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ (系统，3-strike) |
| 任意 → | — | — | — | — | — | ✓ | ✓ | — |

> **注**：
> - `re_verify_failed` 不是独立状态，验证失败后直接回退到 `open`，保持状态机扁平。
> - `archived` 是 `detected` 经 gate PASS 后的降级状态（见 §2.2A 清理策略），不是核心流转路径。
> - `not_reproducible` 仅能从 `archived` 经系统规则进入，核心状态不可直接转入。

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
      fix_hypothesis:
        root_cause: "Cache invalidation lacks mutex around hash map update"
        expected_behavior_change: "Add locking around cache.put() and cache.invalidate()"
        affected_files: ["src/cache/LRUCache.java", "src/cache/CacheManager.java"]
        # confidence 字段（high | medium | low）预留于 schema，v1.6 不启用。v2 引入 autonomy 后用于自动验证门限。
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
| `gap_type` | enum | 失败根因分类：`functional_failure`（功能缺陷）、`coverage_gap`（覆盖缺失）、`performance_regression`（性能回退）、`contract_violation`（契约违反）、`env_flake`（环境波动）、`test_defect`（测试代码缺陷）、`state_leak`（测试间状态污染） |
| `duplicate_of` | string \| null | 指向被重复的 bug_id |
| `resolution_reason` | string \| null | 终止状态的说明（如 "known limitation", "false positive"） |
| `closed_at` | datetime \| null | 最终关闭时间 |
| `resurrected_from` | string \| null | 若由终止状态重新创建，指向原 bug_id |
| `fix_hypothesis` | object \| null | LLM 生成的修复假设（`root_cause`, `expected_behavior_change`, `affected_files`, `confidence`）。**Schema 稳定性承诺**：v1.5 为信息透明，v1.6 将扩展为自动化验证门限，schema 不可随意变更 |

**Schema 稳定性承诺**：

`fix_hypothesis` 的结构（`root_cause`, `expected_behavior_change`, `affected_files`, `confidence`）被声明为 **stable schema**。v1.5 仅将其用于信息透明和审计追溯；v1.6 将基于此 schema 实现语义验证（比对 diff 与 `expected_behavior_change` 的匹配度）。因此：
- 实现层不得省略这些字段
- `confidence` 字段（`high`/`medium`/`low`）由 LLM 在 Root Cause Analysis 阶段自评，为未来低置信度自动升级人工 review 做准备

#### 引用持久化策略

bug-registry 中的引用分为两类：

| 类型 | 字段示例 | 持久性 | 重建后可用性 |
|------|----------|--------|-------------|
| **持久引用** | `fix_commit`, `manifest_ref`, `duplicate_of`, `resurrected_from` | 指向 git / ssot | ✅ 始终有效 |
| **易失引用** | `evidence_ref`, `stdout_ref`, `stderr_ref` | 指向 execution artifacts 目录 | ⚠️ 重建后可能失效 |

**缓解措施**：
1. 易失引用保留 `run_id`，重建时可通过 `run_id` 重新关联到新的执行目录
2. 关键诊断信息（stdout/stderr 前 100 行、核心断言失败文本）内联到 `diagnostics[]`，不依赖外部文件
3. `evidence_persisted: bool` 字段标记证据是否已归档到长期存储（如 S3）

### 2.4 GSD Fix Phase 生成机制

**触发时机**：`gate-evaluate` 产出 `final_decision: FAIL` 后，系统自动生成 draft phase 并推送通知（push model），开发者确认后执行。

**触发命令**：
```bash
ll-bug-remediate --feat-ref FEAT-SRC-003-001 --bug-id {id}
```

> **v1.6 改为 Push Model**：Gate 产出 FAIL verdict 后，系统自动创建修复任务（生成 draft phase 并通知开发者），开发者确认后执行。这解决了 Pull model 下开发者"知道但不去处理"的流失问题（John 评估流失率 40-60%）。
> 
> **但保留开发者选择权**：生成的 draft phase 需开发者运行 `ll-bug-remediate --feat-ref {ref}` 确认后才正式生成 PLAN.md 并触发 `/gsd-execute-phase`。开发者可以选择忽略（任务留在队列），但不能"不知道"。

**遗忘防护机制（Forget-Guard）**：

Push model 降低了遗忘风险，但仍需兜底：

| 触发条件 | 系统行为 | 执行者 |
|----------|---------|--------|
| Gate FAIL 瞬间 | 终端高亮输出 + Slack 通知：`⚠️ Gate FAILED: X bugs opened. Draft phase ready. Run 'll-bug-remediate --feat-ref {ref}'` | 脚本 |
| T+4h 未确认 | 向开发者发送提醒（CLI 通知 / Slack / 邮件，可配置） | 脚本 |
| T+24h 未确认 | 升级通知至 Tech Lead，并在每日站会摘要中标记 | 脚本 |
| T+48h 未确认 | 升级至 Team Lead，由 Team Lead 人工决策是否代为确认或标记为 `wont_fix` | 脚本 + 人类 |
| T+72h 未确认 | 系统仅发送最终告警，记录到 `artifacts/bugs/escalation-log.yaml`，由 Tech Lead 在站会中处理 | 脚本 |

**度量指标**：
- `bug_remediation_latency`：gate FAIL 到 `ll-bug-remediate` 触发的时间分布（P50/P95）
- `remediate_adoption_rate`：gate FAIL 后 24h 内触发 remediate 的比率（目标 > 80%）
- `shadow_fix_rate`：检测到影子修复的比率（见 §2.10）

**生成流程（v1.6-final：默认单 bug 单 phase，支持 mini-batch）**：

```
gate-evaluate → release_gate_input.yaml (final_decision=FAIL)
    ↓
bug-registry 中 status=detected 的 bug 被提升为 open
    ↓
系统按 module + gap_type 聚合生成 draft phase 预览（默认单 bug 单 phase，满足条件时 mini-batch）
    ↓
开发者运行 ll-bug-remediate --feat-ref {ref} [--batch]
    ↓
gate_remediation.py 读取 settlement gap_list + bug-registry
    ↓
模式 A：单 Bug 单 Phase（默认）
    对每个 open bug：
        生成 .planning/phases/{N}-bug-fix-{bug_id}/

模式 B：Mini-Batch Phase（--batch，max 2-3）
    对同一 feat 的 open bug 按模块/根因分组：
        每组 ≤3 个 bug，生成 .planning/phases/{N}-bug-fix-{batch_id}/
    ↓
生成 tests/defect/failure-cases/BUG-{id}.md
    ↓
提示开发者：/gsd-execute-phase {N}
```

> **Mini-Batch（v1.6-final 恢复，max 2-3）**：Quinn 指出单 bug 单修复的实际耗时是 batch 的 2-3 倍，且通知轰炸影响体验。v1.6-final 恢复 mini-batch，但上限从 v1.5 的 4 个收紧为 **2-3 个**，降低 PLAN.md 复杂度同时减少开发者重复劳动。v2 根据数据评估是否恢复到 4 个。

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
| 1 | auto | Root Cause Analysis — LLM 分析 bug 证据与代码路径，确定根因 | — |
| 2 | auto | Implement Fix — 最小范围修复 | — |
| 3 | auto | Update Bug Status — `transition_bug_status(fixed, fix_commit)` | `fixing` → `fixed` |
| 4 | auto | Verify Fix — `qa-test-run --verify-bugs` | `fixed` → `re_verify_passed` / `open` |
| 5 | auto | Review & Close — 生成修复总结，满足 2 条件后自动关闭并通知开发者 | `re_verify_passed` → `closed`（自动），通知开发者 |
| 6 | auto | Update Failure Case — LLM 更新 `tests/defect/failure-cases/BUG-{id}.md` | — |

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
                # 满足 2 条件后系统提示关闭，开发者确认后 closed，见 §2.14
            else:
                transition_bug_status(bug, "open")  # 回退
```

**模式 B：Full-suite 验证（`--verify-mode=full-suite`）**

运行完整测试 suite，用于：
- 修复涉及公共代码（shared utilities、core framework）时，确认没有引入回归
- 多个 bug 修复完成后（v2 batch 场景），做全面验收
- CI/CD 管道中的预提交检查

**验证后状态流转规则**：

| 结果 | 流转 |
|------|------|
| targeted 通过 | `fixed` → `re_verify_passed`（等待人工 closed） |
| targeted 失败 | `fixed` → `open`（回退） |
| full-suite 通过 | `fixed` → `re_verify_passed`（同上） |
| full-suite 失败（新 bug） | 新 bug 进入 `detected`，当前 bug 保持 `fixed` 或回退 `open` |

#### Severity 分层验证提示（v1.6 修订：门限改为提示，不阻断）

v1.6 取消 autonomy 后，原 severity 分层矩阵从**强制门限**降级为**参考提示**。系统计算并展示以下指标，但不阻断 commit 或关闭流程，由开发者和既有 PR review 承担质量兜底。

| Bug Severity | Diff Size 参考 | 建议验证模式 | 系统提示行为 |
|-------------|----------------|-------------|-------------|
| **critical** | 建议 ≤3 files / ≤50 lines | full-suite 强制 + 性能基线比对 | 终端输出 ⚠️ 高亮："critical bug，建议人工 review diff" |
| **high** | 建议 ≤3 files / ≤50 lines | full-suite 建议 | diff 统计超过参考值时，终端输出提示但不阻断 |
| **medium** | 建议 ≤5 files / ≤100 lines | targeted + 采样集成测试 | 同上 |
| **low** | 建议 ≤10 files / ≤200 lines | targeted | 同上 |

> **理由**：MVP 阶段所有修复都经过 `ll-bug-remediate` 确认和既有 PR review，diff size 的强制阻断增加了流程复杂度，但安全收益由 PR review 覆盖。v2 引入 autonomy 后，该矩阵恢复为强制门限。

**Coverage 提示（v1.6 修订：gate 改为提示）**：

| 条件 | 规则 | 行为 |
|------|------|------|
| 修复分支相对基线的覆盖率 | 行覆盖率或分支覆盖率变化 | 标注在 bug-registry 中（`coverage_delta` 字段），供人工审阅参考 |
| 测试数量变化 | 净测试数变化 | 同上标注，不阻断 |

> **理由**：Murat 指出的 coverage gate 在 MVP 阶段仍作为信息透明手段保留，但不作为关闭条件。v2 引入 autonomy 后恢复为强制 gate。

### 2.7 与现有 GSD Phase 的兼容性

| 维度 | 兼容性 | 说明 |
|------|--------|------|
| Phase 编号 | 自动递增 | 从 `.planning/phases/` 现有最大编号 +1 |
| PLAN.md 格式 | 标准格式 | tasks + verify + success_criteria |
| CONTEXT.md | 新增 | 包含 bug 证据和约束 |
| SUMMARY.md | 人工填写 | execute-phase 完成后写 |
| `/gsd-execute-phase` | 直接可用 | 无需修改 GSD 技能本身 |
| `tests/defect/failure-cases/` | 现有目录 | v2.2.1 已在使用 |
| autonomous 标志 | `false`（v1.6） | v1.6 MVP 所有修复人工确认；v2 评估后恢复 autonomy |

### 2.8 角色与职责

明确每个阶段的决策权归属，消除 handoff 黑洞：

| 角色 | 职责 | 决策权 | 使用工具 / 命令 |
|------|------|--------|-----------------|
| **AI 测试执行代理** | 运行测试，记录失败，生成 bug 原始记录 | 无决策权 | `ll-qa-test-run` |
| **AI 验收代理** | 分析 settlement，评估 gate，过滤假失败 | FAIL/PASS 决策 | `ll-qa-settlement`, `ll-qa-gate-evaluate` |
| **AI 修复辅助代理** | 读取 bug 证据，生成 phase 框架，辅助代码修复 | 无决策权 | `ll-bug-remediate`, `/gsd-execute-phase` |
| **开发者（人类）** | 确认修复计划、标记 wont_fix / duplicate、处理冲突告警 | 修复计划确认 + 终止状态判定 | 运行 `ll-bug-remediate`，执行 `ll-bug-transition` |

**关键 handoff 点**：

1. **gate-evaluate → 开发者**：gate 产出 FAIL 后，系统自动生成 draft phase 并通知开发者，终端输出 `⚠️ Gate FAILED: X bugs opened. Draft ready. Run 'll-bug-remediate --feat-ref {ref}' to confirm.` 开发者**确认后执行修复**。
2. **detected → wont_fix / duplicate**：开发者在 review bug-registry 后，使用 `ll-bug-transition --bug-id {id} --to wont_fix --reason "..."` 人工标记。

### 2.8A Handoff 契约

消除 Mary 指出的"责任真空"，每个状态转移定义明确的触发条件、输入、输出与失败回退：

| Handoff | 触发条件 | 输入 | 输出 | 失败回退 | 并发控制 |
|---------|---------|------|------|----------|----------|
| `detected` → `archived` | gate PASS 且 case_id 不在 gap_list | bug-registry + gate verdict | 更新后的 registry（status=archived） | 无（幂等） | 乐观锁（registry version +1） |
| `detected` → `open` | gate FAIL 且 case_id 在 gap_list | bug-registry + settlement gap_list | 更新后的 registry（status=open） | 无（幂等） | 乐观锁 |
| `archived` → `not_reproducible` | 连续 N 次未进入 gap_list（按层级） | bug-registry + 历史 run 记录 | 新 not_reproducible 记录（保留 auto_marked） | 无（终止态） | 乐观锁 |
| gate-evaluate → 开发者 | gate FAIL 产出后 | terminal 高亮提示 + Slack 通知 + draft phase 预览 | 开发者运行 `ll-bug-remediate` 确认 | T+4h/T+24h/T+48h 自动提醒/升级 | 无 |
| 开发者 → AI 修复辅助 | `ll-bug-remediate` 执行 | bug-registry + settlement gap_list | `{N}-bug-fix-*/` 目录 + PLAN.md | phase 生成失败 → 输出错误日志，开发者重试 | 文件系统锁（`.planning/phases/.lock`）防止并发编号冲突 |
| `fixed` → `re_verify_passed` | `--verify-bugs` targeted 通过 | bug-registry + test result | 更新后的 registry | targeted 失败 → 回退 `open` | 乐观锁 |
| `re_verify_passed` → `closed` | 满足 2 条件后自动关闭并通知开发者（§2.14） | bug-registry + verify 结果 | 更新后的 registry（status=closed, closed_by: auto） | 不满足条件 → 保持 `re_verify_passed`，开发者可 override | 乐观锁 |

**关键模糊地带澄清**：

1. **3-strike 计数器**：由 `gate_remediation.py` 在每次 gate-evaluate 完成后自动维护，计数存储在 bug-registry 的 `strike_count` 字段中，与 `last_evaluated_run_id` 关联。
2. **并发控制**：bug-registry 采用**乐观锁**（UUID version 字段，同 `update_manifest()` 机制）。两个开发者同时运行 `ll-bug-remediate` 时，第二个会收到 version conflict 错误，需重新读取最新 registry 后重试。
3. **full-suite 触发决策**：由 §2.6 severity 分层矩阵统一驱动——critical 强制 full-suite + 性能基线比对；high 强制 full-suite；medium 用 targeted + 采样集成测试；low 仅 targeted。开发者本地工作流默认 targeted，full-suite 由 CI 在 PR/merge 前自动补跑，不阻塞本地开发。

### 2.9 执行主体矩阵：LLM / 脚本 / 人类

以下按 Bug 生命周期逐项标明执行主体，消除"这步是 AI 做还是脚本做"的模糊地带。

#### 阶段 1：测试发现（Test Discovery）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| 执行测试用例（API/E2E） | **Python 脚本** | `test_exec_execution.py` 调用 pytest / Playwright，纯工具执行 |
| 聚合 case_results | **Python 脚本** | `test_exec_reporting.py` 按 passed/failed/blocked 分类 |
| 提取 failed case 列表 | **Python 脚本** | `build_bug_bundle()` 过滤 `status=failed` |
| 生成 human-readable 诊断信息 | **LLM** | 分析 stdout/stderr/assertion trace，生成 `diagnostics[]` 描述 |
| 写入 bug-registry.yaml | **Python 脚本** | `sync_bugs_to_registry()` 持久化到 `artifacts/bugs/` |
| **状态流转**：(无) → `detected` | **Python 脚本** | 自动，test-run 完成后触发 |

#### 阶段 2：验收确认（Acceptance）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| 统计 gap_list / waiver_list | **Python 脚本** | settlement 聚合执行结果与豁免清单 |
| 根因分类（gap_type） | **LLM** | `independent_verifier` 分析失败模式，判定是 `functional_failure` / `env_flake` / `contract_violation` 等 |
| 判定是否为 flaky / 环境噪音 | **LLM** | 结合历史 run 数据与日志模式做判断 |
| Gate 决策（FAIL / PASS） | **LLM** | `gate-evaluate` 综合 settlement、waivers、anti-laziness checks 产出 verdict |
| **状态流转**：`detected` → `open` | **Python 脚本** | `gate_remediation.py` 读取 gate FAIL verdict 后自动提升 |

#### 阶段 3：修复触发（Remediation Trigger）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| 确认修复计划 | **人类** | 开发者收到通知后，运行 `ll-bug-remediate --feat-ref {ref} --bug-id {id}` 确认 draft phase（Push Model） |
| 生成 phase 目录结构 | **Python 脚本** | `bug_phase_generator.py` 创建 `{N}-bug-fix-*/` 目录 |
| 生成 `{N}-CONTEXT.md` | **LLM** | 读取 bug 证据、代码引用、相关 ADR，生成修复上下文 |
| 生成 `{N}-01-PLAN.md` | **LLM** | 根据 bug 类型、severity、gap_type 生成 6 个标准 tasks |
| 生成 `tests/defect/failure-cases/BUG-{id}.md` | **LLM** | 基于证据生成失败案例文档 |

#### 阶段 4：修复执行（Fix Implementation）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| Task 1: Root Cause Analysis | **LLM** | `/gsd-execute-phase` 的 `auto` task，分析 bug 证据与代码路径，生成 `fix_hypothesis` |
| Task 2: Implement Fix | **LLM** | `/gsd-execute-phase` 的 `auto` task，生成修复代码 |
| Diff size gate 检查 | **Python 脚本** | 生成修复后执行 `git diff --stat`，按 §2.6 分层矩阵判断是否超出阈值 |
| Task 3: Update Bug Status → `fixed` | **Python 脚本** | `transition_bug_status()` 在 commit 后自动触发 |
| git commit | **GSD auto task** | 修复完成后自动 commit，无需人工审核（安全网由既有 PR review 承担） |
| diff size / coverage 提示 | **Python 脚本** | 生成修复后计算 diff 统计和覆盖率变化，终端输出提示但不阻断 |

#### 阶段 5：再验证（Re-verification）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| 筛选 fixed bug 关联的 coverage_ids | **Python 脚本** | `get_bugs_for_re_verify()` 读取 registry |
| 运行 targeted / full-suite 测试 | **Python 脚本** | `--verify-bugs` / `--verify-mode=full-suite` |
| 断言比对（actual vs expected）| **Python 脚本** | 测试框架自动判定 pass/fail |
| **状态流转**：`fixed` → `re_verify_passed` | **Python 脚本** | 验证通过，自动流转 |
| **状态流转**：`fixed` → `open`（回退）| **Python 脚本** | 验证失败，自动回退 |

#### 阶段 6：关闭（Closure）

| 功能 / 动作 | 执行者 | 说明 |
|-------------|--------|------|
| **状态流转**：`re_verify_passed` → `closed` | **Python 脚本** | 满足 2 条件后自动关闭，并通知开发者（§2.14） |
| 更新 failure-case 文档（记录根因与修复）| **LLM** | `/gsd-execute-phase` 的 `auto` task，自动补充修复方法和根因总结 |
| 标记 `wont_fix` / `duplicate` / `not_reproducible` | **混合** | `wont_fix`/`duplicate` **人类**标记；`not_reproducible` **脚本**自动标记（按层级：Unit N=3, Integration N=4, E2E N=5） |

### 2.10 影子修复检测（Shadow Fix Detection）

**问题**：开发者可能绕过 `ll-bug-remediate` 和 bug registry，直接手动改代码、提交，导致 registry 状态与实际修复脱节（John 指出的重大漏洞）。

**检测机制**：

| 层级 | 检测方式 | 行为 |
|------|---------|------|
| **Commit Hook** | 扫描 commit diff，若修改了与 `status=open` bug 关联的源文件或测试文件 | 终端输出警告：`⚠️ Shadow fix detected: your changes overlap with open bug {id}. Consider running 'll-bug-remediate --feat-ref {ref}' for tracking.` |
| **PR Check** | CI 阶段比对 PR diff 与 bug registry 的 `coverage_id` / 文件关联 | PR 评论自动标注：`This PR touches files related to open bug(s): {list}. Please verify these bugs are addressed.` |
| **Registry Reconciliation** | 每日定时任务扫描最近 24h 的 commits，比对 `fix_commit` 与 `status=open` bug | 发现修复已提交但 bug 状态未更新 → 自动将 bug 流转为 `fixed`（附带 `auto_detected: true`），并通知开发者确认 |

**原则**：不阻止影子修复（开发者有权选择最高效的方式工作），但**提高绕过流程的可见性**，让走流程的成本低于绕过的成本。

### 2.11 多 Feat 并行冲突策略

**问题**：多个 feat 的 bug 修复可能修改同一文件，导致文件冲突、状态机冲突、registry 并发写入（Mary 指出）。

**Registry 隔离**：

```
artifacts/bugs/
├── FEAT-SRC-003-001/
│   └── bug-registry.yaml
├── FEAT-SRC-003-002/
│   └── bug-registry.yaml
└── FEAT-SRC-004-001/
    └── bug-registry.yaml
```

每个 feat 独立 registry，天然隔离。跨 feat 的同一根因 bug 通过 `resurrected_from` 和 `duplicate_of` 字段建立弱关联。

**冲突检测**：

`bug_phase_generator.py` 在生成 phase 前，执行**跨 feat 影响分析**：
1. 读取目标修复文件列表（通过静态分析或历史 coverage 映射）
2. 查询其他活跃 feat（`status=open`）的 bug registry
3. 若目标文件出现在其他 feat 的 open bug 中，标记为 **cross-feat conflict**

**冲突解决**：

| 冲突类型 | 策略 |
|---------|------|
| 同一文件，不同 bug，同一根因 | 建议开发者先修复一个 feat 的 bug，另一个 feat 基于最新代码重新生成修复方案 |
| 同一文件，不同 bug，不同根因 | 强制拆分独立 phase，按合并顺序串行执行（先合并的先修复，后合并的基于最新代码重新生成修复方案） |
| 并发 remediate（同一 feat） | 乐观锁（registry version）+ 文件系统锁（phase 编号），第二个开发者收到 conflict 后重试 |

### 2.12 非功能性需求（NFR）

Mary 指出的 NFR 缺失在此补全：

#### 性能

| 指标 | 目标 | 说明 |
|------|------|------|
| Registry 写入延迟 | P99 < 100ms | 单条 bug 记录的 YAML 写入 + 乐观锁校验 |
| Registry 读取延迟 | P99 < 50ms | 单 feat 的 registry 加载（典型 < 50 条记录） |
| `--verify-bugs` targeted | < 直接关联测试数量的 2 倍时间 | 筛选 + 执行 overhead 可控 |
| `--verify-bugs` full-suite | 与常规 test-run 同量级 | 不引入额外等待 |

**批量写入策略**：test-run 完成后，所有 detected bug 先写入内存缓冲区，最后一次性 flush 到 YAML，减少 I/O。

#### 可审计性

- **审计日志**：每个状态变更写入 `artifacts/bugs/{feat_ref}/audit.log`
  ```yaml
  - timestamp: "2026-04-29T10:00:00Z"
    bug_id: BUG-xxx
    from: detected
    to: open
    actor: system:gate_remediation
    run_id: RUN-20260429-xxx
    reason: "gate FAIL verdict"
  ```
- **保留策略**：audit.log 保留 180 天；bug-registry.yaml 保留至 feat 发布后 90 天，然后归档到 `.archive/bugs/`。
- **不可篡改性**：依赖 git 版本控制（registry 和 audit.log 纳入 git 跟踪）。

#### 质量指标（v1.4 新增，v1.5 扩展）

| 指标 | 目标 | 说明 |
|------|------|------|
| `bug_reopen_rate_7d` | < 5% | 修复后 7 天内被重新打开的比例 |
| `regression_introduction_rate` | < 2% | 修复后 full-suite 中发现新失败的比例 |
| `fix_commit_revert_rate` | < 1% | 修复 commit 在 PR review 阶段被 revert 的比例 |
| `manual_close_rate`（v1.6 新增）| 追踪 | re_verify_passed 后走人工关闭（而非 2 条件自动提示）的比例 |
| `override_close_rate`（v1.6 新增）| < 5% | 使用 `--reason` 强制关闭的比例（过高说明 2 条件有系统性误判） |
| `auto_close_accuracy`（v1.5 新增，v1.6 不启用）| > 98% | auto-closed 后 7 天内未被 reopen 的比例（Mary 要求的补偿指标）。v1.6 无 auto-close，该指标冻结。 |

> **理由**：John 指出没有质量指标的 automation 必然导致 complacency。上述指标纳入 `metrics/` 目录，与 bug registry 同生命周期。`manual_close_rate` 测量开发者是否过度依赖人工关闭（忽略系统提示的 2 条件），`override_close_rate` 检测 2 条件是否存在系统性误判。v2 引入 autonomy 后，`auto_close_accuracy` 重新启用，补偿缺失的 random audit。

#### 可用性

- `ll-bug-remediate --preview`：先生成 phase 预览（不写入 `.planning/`），开发者确认后再执行。
- `ll-bug-review --feat-ref {ref}`：以表格形式列出该 feat 的所有 bug 状态、severity、gap_type，供开发者快速审阅。
- `ll-bug-review --diff-only`：终端展示修复 diff 供开发者快速审阅（v1.6 下不触发阻断，仅作为信息透明工具）。

### 2.13 架构风险与假设

Winston 指出的三个隐含假设在此显式说明：

#### 假设 A：Bug ID 的稳定性

`bug_id` 基于 `case_id` + hash 生成。若 spec 重构导致 `case_id` 变化，同一缺陷会被重复记录。

**缓解**：
- `case_id` 的变更必须通过 manifest 的 `version` 字段显式升级
- `sync_bugs_to_registry()` 在写入前执行模糊匹配：若 `coverage_id` 前缀相同且诊断信息相似度 > 80%，标记为 `potential_duplicate`，提示开发者合并

#### 假设 B：Settlement 与 Bug Registry 的一致性

Settlement 的 `gap_list` 和 bug-registry 的 `detected` 列表独立维护，可能出现 settlement 过滤了某 bug（认为是 flaky），但 registry 中它仍为 `detected` 的不一致。

**缓解**：
- `gate_remediation.py` 在 gate-evaluate 完成后执行一致性校验：遍历所有 `detected`/`archived` bug，若其 `case_id` 连续 2 次未出现在 gap_list 中，自动降级为 `archived`
- 不一致时以 settlement 为准（settlement 是验收层的权威输出）

#### 假设 C：并发修复的冲突

两个开发者可能同时运行 `ll-bug-remediate` 针对同一 feat 的不同 bug。

**缓解**：
- Bug registry：乐观锁（UUID version），冲突时第二个调用方收到 `ConflictError`，重试即可
- Phase 编号：文件系统锁（`.planning/phases/.lock`），确保并发时编号不重复
- 这些机制在 §2.8A Handoff 契约中已定义

### 2.14 MVP 边界与简化流程（v1.2 修订）

第三轮评审（John / Winston / Mary / Murat）后，对 MVP 范围达成以下共识：v1.2 仍然 over-specified，需要明确"没有它流程就转不起来"的最小集合。

#### MVP 核心原则：常规 1 个动作，无 critical 例外

v1.6 砍半 MVP 后，所有 bug（无论 severity）统一走同一流程。开发者修 bug 的 workflow 只插入 **1 个新动作**（确认修复计划），复用既有 PR review 和 CI。

**砍半变更（v1.6）**：
- Batch Mode → **恢复 mini-batch（max 2-3）**：Quinn 指出单 bug 单修复耗时是 batch 的 2-3 倍，且通知轰炸影响体验
- Autonomy Grant → **砍掉**：所有修复 `autonomous: false`，统一人工确认
- 6 条件 Auto-Close → **砍掉**：简化为 2 条件，关闭需人工确认或满足简化条件
- Break-Glass → **砍掉**：MVP 无 autonomy 门限可绕，人工 override 替代
- Diff Size Gate / Coverage Gate → **降级为提示**：计算并展示，不阻断 commit

---

**人类动作矩阵（v1.6）**：

| # | 动作 | 命令 | 平均耗时 | 触发条件 |
|---|------|------|---------|---------|
| 1 | **确认修复计划** | `ll-bug-remediate --feat-ref {ref}` | 30 秒 | gate FAIL 后始终需要 |

> **说明**：
> - MVP 阶段无 autonomy，所有修复都经过 `ll-bug-remediate` 确认后生成 GSD phase。
> - GSD auto task 自动 commit，安全网由既有 PR review + CI `--verify-bugs` 承担。
> - Diff size 和 coverage 变化作为终端提示展示，不阻断 commit（v2 引入 autonomy 后恢复为强制 gate）。

---

#### 修订后的 MVP 流程（端到端，v1.6）

```
[Stage 0] 测试执行（全自动）
test-run 发现 case failed
    ↓ 系统自动
case_id → bug_id 映射，自动推断 gap_type（3 种）
    ↓ 系统自动
写入 artifacts/bugs/{feat_ref}/bug-registry.yaml
    ↓ 系统自动
gate-evaluate 产出 FAIL verdict
    ↓ 系统自动
detected → open（确认真缺陷）
    ↓ 系统自动
（v1.6-final 默认单 bug 单修复，支持 --batch max 2-3）

─────────────────────────────────────────────
[Stage 1] 人类动作 #1：确认修复计划（30 秒）
─────────────────────────────────────────────
开发者运行 ll-bug-remediate --feat-ref {ref} --bug-id {id}
    ↓ 终端展示
Bug 预览：title、severity、gap_type、预估影响文件
    ↓ 开发者输入 y / n
系统生成 .planning/phases/{N}-bug-fix-{bug_id}/
    ↓ LLM 自动
生成 {N}-CONTEXT.md + {N}-01-PLAN.md（6 个标准 tasks）
    ↓ 开发者触发
/gsd-execute-phase {N}
    ↓ LLM 自动（auto tasks）
Task 1: Root Cause Analysis → Task 2: Implement Fix → 生成修复代码 diff
    ↓ GSD auto task 自动
Task 3: git commit + transition_bug_status(fixed)
    ↓ CI 自动触发
--verify-bugs targeted（默认）
    ↓ 系统自动
结果回写 bug-registry

─────────────────────────────────────────────
[Stage 2] 关闭（2 条件自动关闭 + 通知）
─────────────────────────────────────────────
满足以下 2 条件 → 系统自动 closed：
  ① re_verify 由 CI 自动触发且全部通过
  ② 修复 commit 与 re_verify 之间未引入新测试失败（在 affected scope 内）
    ↓ 系统自动
status: closed, closed_by: auto
    ↓ 系统通知
终端 + Slack 通知开发者："Bug {id} 已自动关闭。修复：{commit}。验证：{run_id}。"

不满足 2 条件 → 保持 re_verify_passed，开发者审阅后决定：
    ↓ 开发者运行
ll-bug-transition --bug-id {id} --to open（回退重新修复）
或 ll-bug-transition --bug-id {id} --to closed --reason "..."（人工覆盖关闭）
    ↓ 系统自动
status 更新
```

**Affected Component Specificity Floor（v1.5 新增，v1.6 降级）**：

v1.6 取消 6 条件 auto-close 后，specificity floor 从**强制规则**降级为**数据质量建议**。系统仍建议 `affected_component` 满足以下规范（用于人工审阅时参考），但不阻断任何流程：

| 建议模式 | 示例 | 原因 |
|---------|------|------|
| 避免 Root-level 通配 | `.`, `src/`, `app/` | 过于宽泛，失去定位价值 |
| 避免纯配置文件 | `config/*.yml`, `.env*` | 高频触摸，低特异性 |
| 避免纯测试文件（test_defect 除外）| `tests/**/*.spec.ts` | 测试变更可能不触及被测代码 |

v2 引入 autonomy 和 6 条件 auto-close 后，该 floor 恢复为强制规则。

---

#### MVP 保留 vs 延后清单

**MVP 必须保留（P0）—— 没有它闭环断裂**：

| 章节 | 内容 | 理由 |
|------|------|------|
| §2.1 | 三层分离 | 核心架构原则 |
| §2.2 | 状态机（open→fixing→fixed→re_verify_passed→closed） | 流转基础 |
| §2.2A | 终止状态（wont_fix, duplicate, not_reproducible） | 必须能终结 bug 生命周期 |
| §2.3 | Bug registry 格式 + 按 feat 隔离 | 数据层基础 |
| §2.3A | 引用持久化策略（持久/易失） | 避免重建后引用失效 |
| §2.4 | Pull model + forget-guard（T+4h 提醒） | 解决"开发者忘记"问题 |
| §2.5 | 修复 Phase 标准结构（6 tasks） | GSD 兼容性 |
| §2.6 | 再验证（targeted 默认） + severity 分层验证提示 | 闭环关键；v2 恢复为强制矩阵 |
| §2.9 | 执行主体矩阵 | 明确 LLM/脚本/人类分工 |
| §2.8 | 角色与职责 | 明确人机边界 |
| §2.8A | Handoff 契约（触发条件 + 乐观锁） | 消除责任真空 |
| §2.9 | 执行主体矩阵 | 明确 LLM/脚本/人类分工 |
| §2.10 | Shadow Fix Detection（commit hook + 轻量 reconciliation） | Mary 坚持 P0，数据质量不可妥协 |
| §2.12 | NFR（审计日志 + 保留策略） | 基础可审计性 |
| §2.13 | 架构风险与假设 | 显式列出隐含假设 |

**MVP 延后到 v2（P1/P2）—— 没有它流程能转**：

| 章节 | 内容 | 延后理由 | 替代方案 |
|------|------|---------|---------|
| §2.1 | Autonomy Grant + 撤销条件 | MVP 无数据校准阈值，且所有修复人工确认 | v2 根据实际数据评估 |
| §2.4 | forget-guard T+24h 升级 / T+48h team lead | MVP 用 Slack/人工跟进替代 | T+4h 提醒已足够 |
| §2.4A | Batch 硬约束（v1.5 max 4） | v1.6-final 恢复 mini-batch（max 2-3） | v2 评估是否恢复到 4 |
| §2.6 | full-suite 强制触发（critical/high） | MVP 阶段开发者手动选择即可 | v2 引入分层策略 |
| §2.6 | break-glass 覆盖通道 | MVP 无 autonomy 门限可绕 | 人工 override |
| §2.14 | 6 条件 Auto-Close + Causal Linkage 强制校验 | MVP 简化为 2 条件 + 人工关闭 | v2 引入 autonomy 后恢复 6 条件 |
| §2.10 | PR Check（shadow fix 第二层） | 可被 force push 绕过，ROI 低 | commit hook 已覆盖 80% |
| §2.11 | Multi-feat 并行冲突策略 | MVP 假设单 feat | "一次处理一个 feat"的约定 |
| §2.12 | 性能指标（P99<100ms 等） | 无用户量前指标是虚构的 | 预留接口，不设定阈值 |
| §5.1 | N 阈值按 test level 分层 | 归类准确性 infra 未就绪 | MVP 用统一 N=4 |
| §5.1 | severity 人工仲裁 UI | 初分规则已覆盖 80% | CLI `--severity` flag |
| §5.1 | auto-close 开关 | 默认人工确认足够 | 后续按需开启 |

**MVP 修改（简化）**：

| 原设计 | 修订后 | 理由 |
|--------|--------|------|
| 7 种 gap_type | **3 种**（code_defect / test_defect / env_issue） | John 指出 gap_type 决策成本过高 |
| gap_type 人工选择 | **自动推断 + 人工覆盖** | 降低决策成本至"一键确认"级别 |
| T+72h 自动 batch | **T+72h 强制 Tech Lead triage** | Winston 指出自动推进不可控 |
| re_verify_passed → 人工 closed | **2 条件自动关闭 + 通知开发者** | v1.6-final 砍掉 ll-bug-close，有异议时开发者 reopen |
| test_defect 走标准 GSD phase | **区分 simple（轻量 PR）/ complex（GSD phase）** | Murat 指出测试代码修复不能模糊 |
| v1.5 完整设计（autonomy + batch + 6 条件） | **v1.6 砍半 MVP**（人工确认 + 单 bug + 2 条件） | 多角色评审共识：先跑通最小闭环 |

---

#### MVP gap_type 自动推断规则（3 种）

```python
def infer_gap_type(case_result, run_history) -> str:
    """MVP 阶段自动推断，开发者只覆盖不选择"""
    
    # 条件 1：同一 commit 多次运行结果不一致 → env_issue
    if is_flaky(run_history, case_result["case_id"]):
        return "env_issue"
    
    # 条件 2：失败发生在测试代码（断言、fixture、setup）→ test_defect
    if failure_location_in_test_code(case_result["stack_trace"]):
        return "test_defect"
    
    # 默认：被测代码缺陷
    return "code_defect"
```

**人工覆盖方式**：
```bash
ll-bug-review --feat-ref {ref}          # 查看系统推断结果
ll-bug-transition --bug-id {id} --gap-type {type} --reason "..."
```

**test_defect 路径分流**：

| 子类 | 判定 | 路径 |
|------|------|------|
| `test_defect.simple` | 单文件修改、<10 行、非 framework | 轻量路径：直接 PR fix，reviewer 批准，不生成 GSD phase |
| `test_defect.complex` | 多文件、framework 变更、fixture 架构调整 | 标准路径：生成 GSD phase |

---

#### MVP 验收标准（替代原 §6）

| # | 标准 | 度量方式 | 目标 |
|---|------|---------|------|
| 1 | 统一路径手动动作 = 1 个（`ll-bug-remediate` 确认） | 统计所有 severity 的交互次数 | 平均 = 1 |
| 2 | 端到端时间缩短 30% | 对比当前纯手动流程（test report → fix → verify） | 缩短 30% |
| 3 | 影子修复检测率 > 80% | commit hook 拦截 + reconciliation 兜底 / 总 shadow fix 数 | > 80% |
| 4 | Bug registry 数据准确率 > 95% | 抽样审计：open bug 实际已修复的比例 | < 5% |
| 5 | Batch 生成后开发者确认率 > 90% | 运行 ll-bug-remediate 后输入 y（非 n 或 exclude）的比例 | > 90% |

---

### 2.15 人工 Override（v1.6 替代原 Break-Glass）

v1.6 取消 autonomy 和强制门限后，原 Break-Glass 协议无适用场景（无门限可绕）。保留**人工 override** 作为简化兜底机制。

**适用场景**：
- 简化关闭条件的 2 条件被 flaky test 误阻断（如无关测试偶发失败导致条件 ② 不满足）
- 开发者确认修复正确但 `--verify-bugs` 因环境原因失败
- 其他系统误判导致流程卡住

**流程**：

```bash
# 开发者运行 transition 命令并附加理由（v1.6-final：砍掉 ll-bug-close，统一用 ll-bug-transition）
ll-bug-transition --bug-id {id} --to closed --reason "verified manually: the fix is correct, test failure is env flake (see RUN-xxx logs)"
```

**系统要求**：
1. `--reason` 最少 20 字符，描述 override 原因
2. 强制要求 `--reason`，不可省略
3. 状态更新为 `closed_by: manual_override`
4. 写入 audit log：`actor: developer, action: manual_override_close, reason: ...`

**与 shadow fix detection 的关系**：
人工 override 是**显式**的人工决策（有理由、有审计）。Shadow fix 是**隐式**的绕过（无跟踪）。前者在流程上被允许，后者被检测和警示。

**v2 路线**：引入 autonomy 和强制门限后，人工 override 升级为 Break-Glass Protocol（§2.15 v2 设计见 v1.5 文档归档）。

---

### 2.16 安全审计意见与实施建议（v1.6-final-2 新增）

v1.6-final 定稿后，由 Winston（架构）、Murat（测试架构）、Quinn（QA 工程）进行最终安全审计。审计覆盖 6 个决策点，**全部采用最简单方案（维持当前设计）**，但将审计意见作为**已知风险**和**后续优化方向**记录在案。

#### 2.16.1 审计决策矩阵

| # | 决策点 | 审计推荐 | 最终选择 | 理由 |
|---|--------|----------|----------|------|
| 1 | Auto-close 后通知机制 | A. 自动关闭 + 终端/Slack 通知 | **A（最简单）** | 开发者有异议时可 reopen，不增加额外动作 |
| 2 | Coverage Gate 阻断策略 | A. 仅提示，不阻断 commit/close | **A（最简单）** | MVP 阶段数据不足，强制阻断可能产生过多摩擦 |
| 3 | Mini-batch 首周策略 | A. 维持 `--batch` max 2-3 | **A（最简单）** | 默认单 bug，需要时手动启用 batch |
| 4 | Auto-close 日度上限 | A. 不设上限 | **A（最简单）** | MVP 阶段 bug 量可控，上限可能人为卡住流程 |
| 5 | Post-close 抽样复核 | A. 不抽样 | **A（最简单）** | MVP 用 reopen rate 指标替代主动抽样 |
| 6 | Flaky test 黑名单机制 | A. 不维护黑名单 | **A（最简单）** | 用复现计数器（OQ-4）替代黑名单管理 |

#### 2.16.2 Winston（架构）审计意见

**核心发现**：

1. **Mini-batch 聚合逻辑位置错误**：当前设计将 batch 分组逻辑放在 Execution 层（`ll-bug-remediate`），但聚合决策应属于**验收层**（gate-evaluate）。Gate 拥有 settlement gap_list 的全局视角，能做出更准确的"同根因"判断。Execution 层只应执行 Gate 已批准的 batch 计划。
   - **已知风险**：Execution 层分组可能因信息不全导致"伪同质 batch"（表面同模块，实际根因不同）。
   - **后续优化**：v2 将 batch 准入规则迁移至 gate-evaluate，增加"disjoint region"校验（同一 batch 内 bug 的 affected_component 交集必须非空）。

2. **Auto-close 静默关闭风险**：2 条件自动关闭 + 仅通知机制，存在开发者忽略通知导致"静默关闭"的风险。一旦关闭的 bug 实际未修复，需等到下次回归测试才能发现。
   - **已知风险**：通知疲劳可能导致开发者对 auto-close 通知脱敏。
   - **后续优化**：增加 auto-close 速率监控（见 §2.12 NFR `auto_close_rate_7d`），若单日关闭数超过历史均值 2 倍，自动降级为人工确认。

3. **Affected Component 是最薄弱环节**：当前 `affected_component` 由 settlement 推断，质量不可控。它是 auto-close 条件 ②（无新失败）和 diff review 的基础，若特异性不足，整个关闭决策的可靠性下降。
   - **已知风险**：根级通配（`src/`）会导致条件 ② 几乎必然通过，失去保护作用。
   - **后续优化**：建立 file → test case 反向索引，使 affected_component 能从"代码变更文件"精确映射到"应运行的测试集合"。

#### 2.16.3 Murat（测试架构）审计意见

**核心发现**：

1. **2 条件关闭会遗漏未测试路径的回归**：条件 ② "affected scope 无新失败"只验证已测试路径，不保证未测试路径没有回归。一个修复可能破坏与 affected_component 间接关联的其他功能。
   - **已知风险**：回归缺陷可能穿透到下一次 feature phase 才暴露。
   - **后续优化**：v2 引入 `regression_detector`——在 auto-close 后，对最近一次 full-suite 结果做差异对比，若发现 affected_component 邻域（依赖图中 1-hop）出现新失败，自动 reopen。

2. **Batch 需要 "disjoint region" 准入规则**：当前 mini-batch 仅按 module 分组，未考虑 bug 间的耦合关系。同一 batch 中若两个 bug 的 affected_component 互相依赖，修复 A 可能导致 B 的验证环境变化，产生验证污染。
   - **已知风险**：batch 内 bug 互相干扰，导致 `re_verify_passed` 不能真实反映每个 bug 的修复状态。
   - **后续优化**：增加 batch 准入的"耦合度检查"——若两个 bug 的 affected_component 在依赖图中距离 ≤ 2，强制拆分为独立 phase。

3. **Reopen rate 红线机制**：若 reopen rate（关闭后 7 天内被重新打开的 bug 比例）超过 10%，说明 2 条件关闭过于宽松。
   - **已知风险**：MVP 阶段可能因样本量不足（bug 总数 < 20）导致 reopen rate 统计失真。
   - **后续优化**：当 reopen rate > 10% **且** 样本量 > 30 时，自动恢复 coverage gate 为**软阻断**（允许 `--force` 覆盖，但默认阻断并提示 diff review）。

#### 2.16.4 Quinn（QA 工程）审计意见

**核心发现**：

1. **Flaky test 误报是真实漏洞**：OQ-4 的复现计数器（N=3/4/5）在 E2E 层可能仍然过快标记 `not_reproducible`。一个真实但偶发的缺陷，在 E2E 95% 稳定性基线下，连续 5 次未复现的概率为 `0.05^5 = 3.1e-7`，看似安全；但如果缺陷触发条件是特定时序（如 race condition），可能只在高负载时出现，常规 test-run 根本不会触发。
   - **已知风险**：时序相关缺陷可能被系统误判为 flaky 并终结。
   - **后续优化**：E2E 层 `not_reproducible` 自动标记前，增加一次**stress run**（并发 3 倍负载，连续 10 次），仅当 stress run 也未复现才允许自动终结。

2. **CLI 需要 gate-run 分组视图**：当前 `ll-bug-review --feat-ref` 按 bug 列表展示，开发者难以看出"哪些 bug 来自同一次 gate FAIL"。这导致开发者可能分散处理本应关联修复的问题。
   - **已知风险**：同一 gate FAIL 产生的 bug 被分散处理，增加上下文切换成本。
   - **后续优化**：CLI 增加 `--group-by-run` 视图，将 bug 按 `run_id` 分组，显示每次 gate-evaluate 的批次上下文。

3. **首日灰度与每日站会 reopen review**：MVP 上线首周，建议每日站会花 2 分钟 review 前 24 小时 auto-close 的 bug 列表。这是发现系统性误判（如某个模块的测试全部 flaky 导致批量误关闭）的最快方式。
   - **已知风险**：缺乏人工复核机制时，系统性误判可能持续多天才发现。
   - **后续优化**：在 `ll-bug-review` 中增加 `--recently-closed` 子命令，自动输出最近 24 小时关闭的 bug 摘要（含 affected_component 分布、关闭原因统计），供站会快速审阅。

#### 2.16.5 审计共识与 v2 路线图

三位评审员共识：

1. **MVP 当前设计（6 个 A）是可接受的**，因为人工确认（`ll-bug-remediate`）和 reopen 机制提供了足够兜底。
2. **v2 必须优先解决的 3 项**：
   - 建立 file → test 反向索引（Winston + Murat 共同强调）
   - 引入 stress run 作为 E2E `not_reproducible` 的终结前提（Quinn）
   - 将 batch 聚合逻辑从 Execution 层迁移至 Gate 层（Winston）
3. **监控指标先行**：在实现上述优化前，必须先部署 §2.12 定义的 `reopen_rate_7d`、`auto_close_rate_7d`、`auto_close_accuracy` 监控。数据驱动决策，而非主观判断。

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

### 5.1 开放问题展开与推荐方案

#### OQ-2：`detected` 状态 bug 的自动清理策略

**问题背景**：`detected` 是 test-run 的原始观察，可能包含 flaky test、环境波动、spec 漂移等**假失败**。如果无限期保留，bug-registry 会持续膨胀，产生"幽灵 bug"噪音。

**可选策略对比**：

| 策略 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| A. 时间淘汰制 | 30 天无更新的 `detected` 自动删除 | 简单可预测 | 可能误删间歇性 bug；时间阈值任意 |
| B. Gate 结果联动 | Gate PASS 后，本次 run 的 `detected` 降级为 `archived` | 与验收层逻辑一致，只保留经 gate 确认的失败 | 需要 gate 明确关联到具体 run |
| C. 复现计数制 | 连续 N 次 test-run 未复现 → 自动标记 `not_reproducible` | 基于证据而非时间，更可靠 | 需要维护复现计数器 |
| D. 保留最近 K 次 | 只保留最近 3 次 test-run 的 `detected` | 控制 registry 大小 | 可能丢失历史上下文 |

**推荐方案：B + C 混合**

1. **主路径**：每次 gate-evaluate 产出 `PASS` 后，系统扫描本次关联的 `detected` bug。若某个 `detected` bug 的 case_id 在 gap_list 中**不存在**（即 settlement 认为它不构成阻塞），自动将其降级为 `archived`（软删除，保留记录但不再出现在活跃视图）。
2. **兜底路径**：若某个 `detected` bug 连续 **3 次** gate-evaluate 都未进入 gap_list（即 3 次都被 settlement 过滤），自动流转为 `not_reproducible`（终止状态），并保留 `auto_marked: true` 标记供审计。
3. **保护规则**：`archived`/`not_reproducible` 的 bug 若在新一轮 test-run 中再次失败，应**自动复活**为 `detected`（恢复跟踪），而非创建重复记录。

**理由**：`detected` 的价值在于等待 gate 的确认。如果 gate 已经多次否定它的严重性，继续保留只会增加噪音。3 次是一个经验平衡点——足以排除偶发 flaky，又不会过快丢弃间歇性问题。

---

#### OQ-4：`not_reproducible` 的"连续 N 次未复现"阈值

**问题背景**：`not_reproducible` 是终止状态，意味着"我们尝试复现但失败了，暂不考虑修复"。阈值 N 太小会导致 flaky test 被误标为终结，太大则 registry 清理不及时。

**可选阈值对比**：

| N 值 | 场景 | 风险 |
|------|------|------|
| N=2 | 敏捷清理 | 极易误标，很多间歇性 bug 2 次未复现很正常 |
| **N=3** | **平衡** | **3 次独立 test-run 都未触发，偶发概率已低于 12.5%（假设 flaky 率 50%）** |
| N=5 | 保守策略 | 清理慢，registry 堆积；适合高稳定性要求的金融/医疗场景 |
| 动态 N | smoke 用 3，full-suite 用 5 | 复杂度高，不同 mode 的 test-run 频次不同，难以对齐计数 |

**推荐方案：按测试层级设置动态阈值**

| 测试层级 | 稳定性基线 | N 阈值 | 说明 |
|---------|-----------|--------|------|
| Unit | > 99% | **3** | 执行快、稳定性高，3 次足够过滤偶发噪音 |
| Integration | 95–98% | **4** | 外部依赖引入一定波动，需要更多样本 |
| E2E | 85–95% | **5** | 浏览器时序、网络抖动导致天然高噪声，N=3 会大量误判 |

**补充规则**：
- E2E 层可采用 **统计置信度** 替代固定次数：连续 5 次未复现 **且** 最近 10 次执行中复现率 < 20%，才标 `not_reproducible`。
- `critical` severity 的 bug **永不自动标记为 `not_reproducible`**，必须由开发者人工判定。

**理由**：Murat 指出的"一刀切是懒政"成立。E2E 测试的噪声基线远高于单元测试，用同一阈值会导致大量真实但偶发的缺陷被埋葬。按层级设置只增加极小的复杂度，但显著提升准确性。

---

#### OQ-5：Severity 分级标准（谁定？）

**问题背景**：Severity 决定 bug 是否独立 phase（critical/high 默认独立）、修复优先级、以及是否受 `not_reproducible` 自动清理保护。分级必须有一致的标准，否则开发者会频繁手动调整。

**可选方案对比**：

| 方案 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| A. 全自动 | settlement/gate 根据断言失败类型、影响 API 数量自动定级 | 无人工摩擦，速度快 | 缺乏业务上下文，可能定级不准（如边缘功能但 contract violation 被标 critical） |
| B. 全人工 | test-run 后开发者逐个 review 并手动标记 | 最准确 | 高摩擦，开发者可能跳过或随意标记 |
| C. 系统初分 + 人工仲裁 | 系统根据规则给出初分，开发者在 `ll-bug-remediate` 前可调整 | 兼顾效率和准确性 | 需要实现仲裁 UI/CLI |

**推荐方案：C（系统初分 + 人工仲裁）**

**初分规则（v1）**：

| gap_type | 附加条件 | 初分 severity | 说明 |
|----------|----------|---------------|------|
| `contract_violation` | 任意 | **high** | API 契约被破坏（如 schema mismatch、required field missing）。 Murat 指出测试发现的 contract violation 不一定是代码缺陷（可能是消费者预期变化、mock 数据过时），直接标 critical 会导致 alarm fatigue |
| `contract_violation` | 生产环境真实流量 / canary 阶段确认 | **critical** | 仅当生产环境已确认影响时才升级为 critical，触发自动回滚条件 |
| `functional_failure` | core API / 主流程 | **high** | 阻断核心功能，用户体验严重受损 |
| `functional_failure` | 边缘功能 / 次要流程 | **medium** | 功能异常但不阻断主流程 |
| `coverage_gap` | 任意 | **low** | 测试覆盖不足，功能本身可能正常 |
| `performance_regression` | P95 延迟增加 > 50% | **high** | 显著性能劣化 |
| `performance_regression` | P95 延迟增加 20%~50% | **medium** | 可接受范围内但需关注 |
| `env_flake` | 任意 | **无** | 不赋值 severity，不作为修复对象 |

**仲裁机制**：
- 系统初分后写入 `bug-registry.yaml` 的 `severity` + `severity_source: auto`
- 开发者运行 `ll-bug-review --feat-ref {ref}` 查看初分列表
- 开发者可运行 `ll-bug-transition --bug-id {id} --severity {level} --reason "..."` 调整
- 人工调整后的 `severity_source` 变为 `manual`，优先于初分规则

**理由**：完全自动缺乏业务上下文（如一个边缘功能的 contract violation 可能实际影响很小），完全人工则高摩擦。初分规则覆盖了 80% 的常见场景，人工仲裁只处理 20% 的边界情况，是成本-收益最优解。

---

#### OQ-6（已解决，v1.4 更新）：`ll-bug-remediate` 是否支持 `--auto-close` 跳过人工确认？

**状态**：v1.3 已默认 auto-close（满足 2 条件后自动 `re_verify_passed → closed`）。本问题已解决，但保留历史记录供追溯。

**v1.6 更新**：auto-close 已砍掉，关闭由开发者人工确认。系统仅提示满足 2 条件的 bug 可关闭，不自动流转。

**v1.6-final 调整**：多角色评审后用户决策——砍掉 `ll-bug-close`，2 条件满足后**自动关闭 + 通知开发者**：
- 所有 severity 统一路径：满足 2 条件 → 系统自动 `closed`，终端 + Slack 通知开发者
- 开发者有异议时可手动 reopen

**回退机制**：v1.6-final 默认自动关闭。v2 引入 autonomy 后，若需全局禁用 auto-close，可通过环境变量 `BUG_AUTO_CLOSE=0` 恢复为人工确认。

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
- [ ] mini-batch phase 生成（max 2-3）：`.planning/phases/{N}-bug-fix-{batch_id}/` 目录结构正确
- [ ] 生成 `tests/defect/failure-cases/BUG-{id}.md`
- [ ] `/gsd-execute-phase {N}` 可直接执行生成的 phase
- [ ] Push model 验证：gate FAIL 后自动生成 draft phase 并通知开发者，开发者运行 `ll-bug-remediate` 确认后执行

### Phase 3 验收

- [ ] `--verify-bugs` 默认 targeted 模式，只运行 `status=fixed` 关联测试
- [ ] `--verify-mode=full-suite` 运行完整 suite 并检测回归
- [ ] 验证通过后 bug 自动流转为 `re_verify_passed`
- [ ] 验证失败后 bug 回退为 `open`
- [ ] 满足 2 条件后 bug 自动变为 `closed`，系统通知开发者
- [ ] 完整闭环：`qa-test-run` → `gate-evaluate` → draft phase 推送 → `ll-bug-remediate` 确认 → `gsd-execute-phase` → `--verify-bugs` → 自动 `closed` + 通知
- [ ] diff size / coverage 提示：终端展示统计信息，不阻断 commit

---

## 7. 修订记录

| 版本 | 日期 | 修订者 | 变更内容 |
|------|------|--------|----------|
| v1.0-draft | 2026-04-28 | 架构 / AI 代理 | 初始草案：三层分离、6 状态机、ssot/bugs/ 存储、自动 push 生成 phase |
| v1.1-draft | 2026-04-28 | 多角色评审后修订 | **架构**：明确 pull model，增加批量修复（--batch），迁移存储到 artifacts/bugs/；**状态机**：扩展终止状态（duplicate, not_reproducible），简化核心路径；**验收**：增加 full-suite 验证模式、gap_type 分类；**职责**：新增角色与 handoff 定义；**开放问题**：增加 severity 仲裁、auto-close 开关 |
| v1.2-draft | 2026-04-29 | 第二轮多角色评审后修订 | **Pull model**：增加遗忘防护机制（T+4h/T+24h/T+72h 提醒/升级/自动 batch）；**Batch**：硬约束 max 4 个 + 同质性要求；**状态机**：not_reproducible 复活改为创建新记录，保持终止状态纯粹性；**gap_type**：增加 test_defect、state_leak，contract_violation severity 降为 high；**N 阈值**：Unit=3, Integration=4, E2E=5；**引用**：增加持久/易失引用策略；**新增 §2.8A**：Handoff 契约（触发条件、并发控制）；**新增 §2.10**：影子修复检测（commit hook + PR check）；**新增 §2.11**：多 feat 并行冲突策略；**新增 §2.12**：NFR（性能、可审计性、可用性）；**新增 §2.13**：架构风险与假设（case_id 稳定性、settlement 一致性、并发冲突） |
| v1.3-draft | 2026-04-29 | 用户反馈修订 | **autonomous**：bug-fix phase 改为 `autonomous: true`，6 个 tasks 全部为 auto（含 Root Cause Analysis、Review & Close、Update Failure Case）；**人类动作**：从 2 个减为 1 个（仅保留 `ll-bug-remediate` 确认），取消"commit 前人类审阅"；**关闭**：`re_verify_passed` → `closed` 改为满足 4 条件后自动触发，不再依赖 `ll-bug-close`；**安全网**：PR review 与 `--verify-bugs` 承担修复质量兜底，不额外增加人类动作 |
| v1.4-draft | 2026-04-29 | 多角色评审后修订（Q1/Q2/Q3） | **Autonomy Grant Principle**：新增 §2.1，明确 autonomy 的 4 条件，声明不扩展至 feature phase；**Severity 分层**：新增 §2.6 分层验证矩阵，critical 强制人工 diff review，high/medium 按 diff size 门限动态阻断；**条件 #5**：auto-close 增加 Mary 的因果关联校验（diff 必须触及 affected_component）；**fix_hypothesis**：§2.3 registry 增加 `fix_hypothesis` 字段（信息透明，v2 扩展语义验证）；**质量指标**：§2.12 NFR 新增 `bug_reopen_rate_7d` 等 4 项 fix quality metrics；**CLI**：新增 `ll-bug-review --diff-only` 用于 diff size gate 阻断时的人工审阅 |
| v1.5-draft | 2026-04-29 | 多角色评审后修订（Q4/Q5/Q6） | **Autonomy 撤销条件**：§2.1 新增撤销条件表（reopen_rate>5% 连续2周、regression>2%、escalation>30%、break-glass>2次/月触发 autonomous:false 降级）；**fix_hypothesis 增强**：§2.3 增加 `confidence` 字段（high/medium/low），声明 schema stability 承诺（v1.6 语义验证）；**Forget-Guard 修订**：§2.4 T+72h 自动 batch 移除，改为 T+48h team lead 升级接管；**Coverage Gate**：§2.6 新增覆盖率不下降、净增测试数≥0 的关闭阻断条件，low severity 增加绝对 diff 上限（10 files/200 lines）；**NFR 扩展**：§2.12 新增 `y_key_reflex_rate`、`auto_close_accuracy`；**Auto-close 6 条件**：§2.14 从 5 条扩展为 6 条（新增 coverage non-decreasing），新增 Affected Component Specificity Floor（根级路径/纯配置/纯测试文件排除）；**Break-Glass**：§2.15 新增紧急覆盖协议（--break-glass CLI、第二审批人、[BREAK-GLASS] 前缀、审计日志、过度使用自动收紧） |
| v1.6-final | 2026-04-29 | 砍半 MVP 最终调整（用户决策） | **§2.14**：砍掉 `ll-bug-close`，2 条件满足后**自动关闭 + 通知开发者**，有异议时 reopen；**§2.4**：恢复 **mini-batch（max 2-3）**，解决单 bug 重复操作和通知轰炸问题；**§2.15**：人工 override 统一使用 `ll-bug-transition --to closed --reason`（砍掉 `ll-bug-close` 命令）；**Push Model**：维持自动创建 draft phase + 手动调用 `/gsd-execute-phase`；**Coverage Gate**：维持提示不阻断 |
| v1.6-final-2 | 2026-04-29 | 安全审计后修订 | **§2.16 新增**：安全审计意见与实施建议——记录 Winston（架构）、Murat（测试架构）、Quinn（QA 工程）对 6 个决策点的审计结论，全部采用最简单方案，但将风险与优化方向显式归档；更新 §7 修订记录；为 v2 路线图提供数据驱动的监控指标前提 |
