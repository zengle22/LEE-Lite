# Roadmap

## Milestones

- **v2.3 ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成** — In Progress
- **v2.2.1 Failure Case Resolution** — ✓ SHIPPED 2026-04-28
- [v2.2 双链执行闭环](.planning/milestones/v2.2-ROADMAP.md) ✓ SHIPPED 2026-04-24
- v2.1 双链双轴测试强化 ✓ SHIPPED 2026-04-23
- v2.0 ADR-050/051 SSOT 语义治理升级 ✓ SHIPPED 2026-04-22
- v1.1 ADR-049 体验修正层 ✓ SHIPPED 2026-04-21
- v1.0 ADR-047 双链测试 ✓ SHIPPED 2026-04-17

---

## v2.3: ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成 — Phase Summary

| Phase | Name | Target Requirements | Estimated Plans | Status |
|-------|------|-------------------|----------------|--------|
| 25 | Bug 注册表与状态机 | BUG-REG-01, BUG-REG-02, BUG-REG-03, BUG-PHASE-01, BUG-PHASE-02, BUG-INTEG-01, BUG-INTEG-02 | 3-4 plans | **Pending** |
| 26 | 验收层集成 | GATE-REM-01, GATE-REM-02, GATE-INTEG-01, GATE-INTEG-02, PUSH-MODEL-01 | 3 plans | **Pending** |
| 27 | GSD 闭环验证 | VERIFY-01, VERIFY-02, VERIFY-03, VERIFY-04, CLI-01, CLI-02, SHADOW-01, AUDIT-01, INTEG-TEST-01 | 4-5 plans | **Pending** |

**Total:** 3 phases, ~10-12 plans

---

## v2.3 Phase Details

### Phase 25: Bug 注册表与状态机

**Goal:** Bug 发现的原始观察能被持久化追踪，状态机支持完整流转和终止处理，与现有 test-run 执行链集成。

**Depends on:** Nothing (v2.3 首个 phase，依赖 v2.2 已交付的 ADR-054 test_orchestrator.py)

**Requirements:** BUG-REG-01, BUG-REG-02, BUG-REG-03, BUG-PHASE-01, BUG-PHASE-02, BUG-INTEG-01, BUG-INTEG-02

**Success Criteria** (what must be TRUE):
1. Bug 注册表模块（bug_registry.py）能创建、读取、更新 artifacts/bugs/{feat_ref}/bug-registry.yaml，支持乐观锁（version 字段）防止并发写入冲突
2. Bug 核心状态机完整流转：detected -> open -> fixing -> fixed -> re_verify_passed -> closed，每个流转有明确触发条件和失败回退到 open
3. 终止状态可用：wont_fix（需 resolution_reason）、duplicate（需 duplicate_of）、not_reproducible（按层级 N=3/4/5），终止状态复活时创建新记录保留 resurrected_from 关联
4. Bug Phase 生成器（bug_phase_generator.py）能生成 .planning/phases/{N}-bug-fix-{bug_id}/ 目录结构，包含 CONTEXT.md + PLAN.md（6 个标准 tasks）+ DISCUSSION-LOG.md + SUMMARY.md，支持 --batch mini-batch 模式（max 2-3 同 feat 同模块 bug 聚合）
5. test-run 集成：build_bug_bundle() 产出含 status:detected 和 gap_type（code_defect/test_defect/env_issue，自动推断+人工覆盖）的 bug JSON，sync_bugs_to_registry() 将 detected bug 持久化到 artifacts/bugs/{feat_ref}/bug-registry.yaml 并内联关键诊断信息到 diagnostics[]

**Planned Work:**
- 25-01: bug_registry.py 核心模块（CRUD + 乐观锁 + 状态机）
- 25-02: bug_phase_generator.py（单 bug + mini-batch 目录生成）
- 25-03: test_orchestrator.py 集成（build_bug_bundle + sync_bugs_to_registry）
- 25-04: 单元测试 + 状态机流转验证

---

### Phase 26: 验收层集成

**Goal:** Gate FAIL 后系统自动将 detected bug 提升为 open 真缺陷，gate/settlement 输出契约包含 bug 关联信息，开发者通过 push model 收到修复任务通知。

**Depends on:** Phase 25

**Requirements:** GATE-REM-01, GATE-REM-02, GATE-INTEG-01, GATE-INTEG-02, PUSH-MODEL-01

**Success Criteria** (what must be TRUE):
1. Gate Remediation 模块（gate_remediation.py）在 gate FAIL 时读取 bug-registry 和 settlement gap_list，执行一致性校验（settlement 为准），detected -> open 自动提升（gap_list 中的 case_id 对应 bug 状态确认为真缺陷）
2. release_gate_input.yaml 输出契约更新，包含 bug 关联信息（gap_list -> bug_id 映射）；settlement input contract 更新，支持读取活跃 bug 列表用于 gap 分析
3. Push model 实现：gate FAIL 后自动创建 draft phase 预览，终端高亮通知 + T+4h 提醒开发者运行 ll-bug-remediate --feat-ref {ref} 确认
4. 开发者运行 ll-bug-remediate --feat-ref {ref} 后，展示 bug 预览（title、severity、gap_type、影响文件），输入 y/n 后生成 phase 目录，/gsd-execute-phase {N} 可直接执行生成的 phase

**Planned Work:**
- 26-01: gate_remediation.py 核心模块（gap_list 校验 + detected->open 提升）
- 26-02: gate-evaluate 输出契约更新（release_gate_input.yaml + bug 关联）
- 26-03: settlement input contract 更新 + push model 通知机制

---

### Phase 27: GSD 闭环验证

**Goal:** 修复后的 bug 能被自动再验证并流转关闭，开发者有完整的 CLI 工具管理 bug 生命周期，影子修复被检测并警告，审计日志记录所有状态变更，集成测试验证端到端闭环。

**Depends on:** Phase 26

**Requirements:** VERIFY-01, VERIFY-02, VERIFY-03, VERIFY-04, CLI-01, CLI-02, SHADOW-01, AUDIT-01, INTEG-TEST-01

**Success Criteria** (what must be TRUE):
1. --verify-bugs targeted 模式（默认）只运行 status=fixed bug 关联的 coverage_ids 对应测试，快速验证修复；--verify-mode=full-suite 运行完整 suite 检测回归（新 bug 进入 detected，当前 bug 保持 fixed 或回退 open）
2. 验证后状态流转正确：targeted 通过 -> re_verify_passed；targeted 失败 -> 回退 open；severity 分层提示（diff size、coverage 变化）展示但不阻断
3. 2 条件自动关闭：re_verify 通过且修复 commit 与 re_verify 间无新测试失败 -> 自动 closed + 终端通知开发者；不满足则保持 re_verify_passed，开发者可 ll-bug-transition --to closed --reason 人工覆盖
4. Bug transition CLI（ll-bug-transition --bug-id {id} --to {state}）：支持 wont_fix（需 --reason >=20 字符）、duplicate（需 --duplicate-of）、人工关闭覆盖
5. Shadow Fix Detection：commit hook 扫描 commit diff，若修改了 status=open bug 关联的源文件，终端输出警告提示
6. 审计日志：每次状态变更写入 artifacts/bugs/{feat_ref}/audit.log（timestamp, bug_id, from, to, actor, run_id, reason）
7. 集成测试（tests/integration/test_bug_closure.py）覆盖完整闭环：test-run -> gate FAIL -> draft phase -> remediate -> execute-phase -> verify-bugs -> auto-close

**Planned Work:**
- 27-01: --verify-bugs 模式实现（targeted + full-suite）
- 27-02: 验证后状态流转 + 2 条件自动关闭
- 27-03: Bug transition CLI + Shadow Fix Detection（commit hook）
- 27-04: 审计日志模块
- 27-05: 集成测试（test_bug_closure.py）端到端闭环验证

---

<details>
<summary>✅ v2.2.1 Failure Case Resolution (Phases 20-24) — SHIPPED 2026-04-28</summary>

- [x] Phase 20: P0 缺陷紧急修复 (3/3 plans) — 2026-04-28
- [x] Phase 21: PROTO 相关缺陷修复 (3/3 plans) — 2026-04-28
- [x] Phase 22: TECH 和 IMPL 缺陷修复 (3/3 plans) — 2026-04-28
- [x] Phase 23: TESTSET 和治理技能修复 (3/3 plans) — 2026-04-28
- [x] Phase 24: impl-spec-test 增强和验证 (4/4 plans) — 2026-04-28

Full details: [milestones/v2.2.1-ROADMAP.md](milestones/v2.2.1-ROADMAP.md)

</details>

---

## Requirement Traceability

### v2.3

| Requirement | Phase | ADR Section | Status |
|-------------|-------|-------------|--------|
| BUG-REG-01 | 25 | §2.3, §3 Phase 1 | Pending |
| BUG-REG-02 | 25 | §2.2, §3 Phase 1 | Pending |
| BUG-REG-03 | 25 | §2.2, §2.2A | Pending |
| BUG-PHASE-01 | 25 | §2.4, §2.5 | Pending |
| BUG-PHASE-02 | 25 | §2.4 | Pending |
| BUG-INTEG-01 | 25 | §3 Phase 1 | Pending |
| BUG-INTEG-02 | 25 | §2.3, §3 Phase 1 | Pending |
| GATE-REM-01 | 26 | §2.4, §3 Phase 2 | Pending |
| GATE-REM-02 | 26 | §2.2, §2.8A | Pending |
| GATE-INTEG-01 | 26 | §3 Phase 2 | Pending |
| GATE-INTEG-02 | 26 | §3 Phase 2 | Pending |
| PUSH-MODEL-01 | 26 | §2.4 | Pending |
| VERIFY-01 | 27 | §2.6 | Pending |
| VERIFY-02 | 27 | §2.6 | Pending |
| VERIFY-03 | 27 | §2.6 | Pending |
| VERIFY-04 | 27 | §2.14, §2.16 | Pending |
| CLI-01 | 27 | §2.15 | Pending |
| CLI-02 | 27 | §2.4 | Pending |
| SHADOW-01 | 27 | §2.10 | Pending |
| AUDIT-01 | 27 | §2.12 | Pending |
| INTEG-TEST-01 | 27 | §6 Phase 3 | Pending |

**Coverage:** 19/19 requirements mapped (100%)

---

## Phase Dependency Map

```
Phase 24 (v2.2.1 done)
     │
     ▼
Phase 25 ──> Phase 26 ──> Phase 27
(Bug 注册表   (验收层集成)  (GSD 闭环验证)
 与状态机)
```

---

## Risk Notes

| Phase | Risk | Mitigation |
|-------|------|------------|
| 25 | 乐观锁并发场景可能遗漏 edge case | 单元测试覆盖并发写入冲突场景 |
| 26 | gate/settlement 契约更新可能影响现有消费者 | 向后兼容：新增字段，不删除/重命名现有字段 |
| 27 | 集成测试覆盖完整闭环复杂度高 | 分步构建：先单模块测试，再组装端到端 |

---

*Last updated: 2026-04-29 — v2.3 roadmap created, Phase 25-27 defined*
