# v2.3 Requirements: ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成

**Source:** ADR-055 §3 实现计划 + §6 验收标准
**Milestone:** v2.3
**Created:** 2026-04-29
**Requirements gated by:** ADR-047 (双链测试), ADR-054 (实施轴桥接), ADR-053 (需求轴统一入口) — all delivered

---

## Milestone Requirements

### Phase A: Bug 注册表与状态机

- [ ] **BUG-REG-01**: Bug 注册表模块（`cli/lib/bug_registry.py`）能创建、读取、更新 `artifacts/bugs/{feat_ref}/bug-registry.yaml`，支持乐观锁（version 字段）
- [ ] **BUG-REG-02**: Bug 核心状态机完整流转：`detected → open → fixing → fixed → re_verify_passed → closed`，每个流转有明确触发条件和失败回退
- [ ] **BUG-REG-03**: Bug 终止状态可用：`wont_fix`（人工，需 resolution_reason）、`duplicate`（需 duplicate_of）、`not_reproducible`（系统自动，按层级 N=3/4/5）。终止状态复活策略：创建新记录，保留 `resurrected_from` 关联
- [ ] **BUG-PHASE-01**: Bug Phase 生成器（`cli/lib/bug_phase_generator.py`）生成 `.planning/phases/{N}-bug-fix-{bug_id}/` 目录，包含 CONTEXT.md + PLAN.md（6 个标准 tasks）+ DISCUSSION-LOG.md + SUMMARY.md
- [ ] **BUG-PHASE-02**: 支持单 bug 单 phase（默认）和 mini-batch 模式（`--batch`，max 2-3 个同 feat 同模块 bug 聚合）
- [ ] **BUG-INTEG-01**: test-run 集成：`build_bug_bundle()` 产出包含 `status: detected`、`gap_type`（code_defect / test_defect / env_issue）的 bug JSON，`gap_type` 自动推断 + 人工覆盖
- [ ] **BUG-INTEG-02**: `sync_bugs_to_registry()` 将 detected bug 持久化到 `artifacts/bugs/{feat_ref}/bug-registry.yaml`，内联关键诊断信息到 `diagnostics[]`

### Phase B: 验收层集成

- [ ] **GATE-REM-01**: Gate Remediation 模块（`cli/lib/gate_remediation.py`）在 gate FAIL 时读取 bug-registry 和 settlement gap_list，执行一致性校验（settlement 为准）
- [ ] **GATE-REM-02**: `detected → open` 自动提升 — gate FAIL 后，gap_list 中的 case_id 对应 bug 状态从 detected 提升为 open（确认为真缺陷）
- [ ] **GATE-INTEG-01**: gate-evaluate 输出契约更新：`release_gate_input.yaml` 包含 bug 关联信息（gap_list → bug_id 映射）
- [ ] **GATE-INTEG-02**: settlement 消费 bug 注册表：input contract 更新，支持读取活跃 bug 列表用于 gap 分析
- [ ] **PUSH-MODEL-01**: Push model 实现 — gate FAIL 后自动创建 draft phase 预览，终端高亮通知 + T+4h 提醒开发者运行 `ll-bug-remediate --feat-ref {ref}` 确认

### Phase C: GSD 闭环验证

- [ ] **VERIFY-01**: `--verify-bugs` targeted 模式（默认）：只运行 `status=fixed` bug 关联的 coverage_ids 对应测试，快速验证修复
- [ ] **VERIFY-02**: `--verify-mode=full-suite`：运行完整测试 suite，检测回归（新 bug 进入 `detected`，当前 bug 保持 `fixed` 或回退 `open`）
- [ ] **VERIFY-03**: 验证后状态流转：targeted 通过 → `re_verify_passed`；targeted 失败 → 回退 `open`；severity 分层提示（diff size、coverage 变化）展示但不阻断
- [ ] **VERIFY-04**: 2 条件自动关闭：① re_verify 通过 ② 修复 commit 与 re_verify 间无新测试失败 → 自动 `closed` + 终端/Slack 通知开发者；不满足则保持 `re_verify_passed`，开发者可 `ll-bug-transition --to closed --reason` 人工覆盖
- [ ] **CLI-01**: Bug transition CLI（`ll-bug-transition --bug-id {id} --to {state}`）：支持 `wont_fix`（需 `--reason` ≥20 字符）、`duplicate`（需 `--duplicate-of`）、人工关闭覆盖
- [ ] **CLI-02**: `ll-bug-remediate --feat-ref {ref} [--batch]`：开发者确认修复计划，展示 bug 预览（title、severity、gap_type、影响文件），输入 y/n 后生成 phase
- [ ] **SHADOW-01**: Shadow Fix Detection — commit hook 扫描 commit diff，若修改了 `status=open` bug 关联的源文件，终端输出警告提示
- [ ] **AUDIT-01**: 审计日志 — 每次状态变更写入 `artifacts/bugs/{feat_ref}/audit.log`（timestamp, bug_id, from, to, actor, run_id, reason）
- [ ] **INTEG-TEST-01**: 集成测试（`tests/integration/test_bug_closure.py`）：覆盖完整闭环 — test-run → gate FAIL → draft phase → remediate → execute-phase → verify-bugs → auto-close

---

## Future Requirements (v2)

- Autonomy Grant 机制（基于 reopen_rate、regression_rate 数据校准阈值）
- 多 feat 并行冲突策略（跨 feat 文件冲突检测 + 串行合并）
- full-suite 强制触发矩阵（critical 强制 full-suite + 性能基线）
- Break-Glass Protocol（紧急覆盖通道 + 第二审批人）
- 6 条件 Auto-Close（含 coverage non-decreasing + causal linkage）
- Affected Component Specificity Floor（强制规则）
- File → Test 反向索引（精确 affected scope 计算）
- Stress run 作为 E2E `not_reproducible` 终结前提
- Batch 聚合逻辑从 Execution 层迁移至 Gate 层

## Out of Scope

| Item | Reason |
|------|--------|
| Autonomy Grant | MVP 无数据校准阈值，所有修复人工确认 |
| 多 feat 并行冲突 | MVP 假设单 feat，"一次处理一个 feat" |
| full-suite 强制触发 | MVP 开发者手动选择，v2 引入分层策略 |
| Break-Glass | MVP 无 autonomy 门限可绕 |
| ADR-048 Mission Compiler | 继续延期 |

---

## Traceability

| Requirement | Phase | ADR Section | Acceptance Criteria |
|-------------|-------|-------------|---------------------|
| BUG-REG-01 | 25 | §2.3, §3 Phase 1 | §6 Phase 1: registry CRUD |
| BUG-REG-02 | 25 | §2.2, §3 Phase 1 | §6 Phase 1: state machine |
| BUG-REG-03 | 25 | §2.2, §2.2A | §6 Phase 1: terminal states |
| BUG-PHASE-01 | 25 | §2.4, §2.5 | §6 Phase 2: phase generation |
| BUG-PHASE-02 | 25 | §2.4 | §6 Phase 2: mini-batch |
| BUG-INTEG-01 | 25 | §3 Phase 1 | §6 Phase 1: build_bug_bundle |
| BUG-INTEG-02 | 25 | §2.3, §3 Phase 1 | §6 Phase 1: sync_bugs |
| GATE-REM-01 | 26 | §2.4, §3 Phase 2 | §6 Phase 2: gate FAIL handling |
| GATE-REM-02 | 26 | §2.2, §2.8A | §6 Phase 2: detected→open |
| GATE-INTEG-01 | 26 | §3 Phase 2 | §6 Phase 2: contract update |
| GATE-INTEG-02 | 26 | §3 Phase 2 | §6 Phase 2: settlement reads registry |
| PUSH-MODEL-01 | 26 | §2.4 | §6 Phase 2: push notification |
| VERIFY-01 | 27 | §2.6 | §6 Phase 3: targeted verify |
| VERIFY-02 | 27 | §2.6 | §6 Phase 3: full-suite verify |
| VERIFY-03 | 27 | §2.6 | §6 Phase 3: state transitions |
| VERIFY-04 | 27 | §2.14, §2.16 | §6 Phase 3: 2-condition close |
| CLI-01 | 27 | §2.15 | §6 Phase 3: transition CLI |
| CLI-02 | 27 | §2.4 | §6 Phase 3: remediate CLI |
| SHADOW-01 | 27 | §2.10 | §6 Phase 3: shadow detection |
| AUDIT-01 | 27 | §2.12 | §6 Phase 3: audit log |
| INTEG-TEST-01 | 27 | §6 Phase 3 | §6 Phase 3: E2E closure |

---

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total requirements | 19 |
| Phase A (Bug 注册表与状态机) | 7 |
| Phase B (验收层集成) | 5 |
| Phase C (GSD 闭环验证) | 7 |
| Mapped to phases | 19/19 (100%) |
| Unmapped | 0 |

---

*Requirements defined: 2026-04-29*
