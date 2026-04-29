# Roadmap

## Milestones

- **v2.3 ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成** — In Progress
- **v2.2.1 Failure Case Resolution** — SHIPPED 2026-04-28
- [v2.2 双链执行闭环](.planning/milestones/v2.2-ROADMAP.md) SHIPPED 2026-04-24
- v2.1 双链双轴测试强化 SHIPPED 2026-04-23
- v2.0 ADR-050/051 SSOT 语义治理升级 SHIPPED 2026-04-22
- v1.1 ADR-049 体验修正层 SHIPPED 2026-04-21
- v1.0 ADR-047 双链测试 SHIPPED 2026-04-17

---

## v2.3: ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成 — Phase Summary

| Phase | Name | Target Requirements | Plans | Status |
|-------|------|-------------------|-------|--------|
| 25 | Bug 注册表与状态机 | BUG-REG-01, BUG-REG-02, BUG-REG-03, BUG-PHASE-01, BUG-PHASE-02, BUG-INTEG-01, BUG-INTEG-02 | 3 plans | **Pending** |
| 26 | 验收层集成 | GATE-REM-01, GATE-REM-02, GATE-INTEG-01, GATE-INTEG-02, PUSH-MODEL-01 | 3 plans | **Pending** |
| 27 | GSD 闭环验证 | VERIFY-01, VERIFY-02, VERIFY-03, VERIFY-04, CLI-01, CLI-02, SHADOW-01, AUDIT-01, INTEG-TEST-01 | 4-5 plans | **Pending** |

**Total:** 3 phases, ~10-11 plans

---

## v2.3 Phase Details

### Phase 25: Bug 注册表与状态机

**Goal:** Bug 发现的原始观察能被持久化追踪，状态机支持完整流转和终止处理，与现有 test-run 执行链集成。

**Depends on:** Nothing (v2.3 first phase, depends on v2.2 delivered ADR-054 test_orchestrator.py)

**Requirements:** BUG-REG-01, BUG-REG-02, BUG-REG-03, BUG-PHASE-01, BUG-PHASE-02, BUG-INTEG-01, BUG-INTEG-02

**Success Criteria** (what must be TRUE):
1. Bug registry module (bug_registry.py) can create/read/update artifacts/bugs/{feat_ref}/bug-registry.yaml with optimistic locking (version field)
2. Bug state machine complete flow: detected -> open -> fixing -> fixed -> re_verify_passed -> closed, each transition has clear trigger conditions with fallback to open
3. Terminal states available: wont_fix (requires resolution_reason), duplicate (requires duplicate_of), not_reproducible (per-level N=3/4/5). Resurrection creates new record with resurrected_from linkage
4. Bug Phase generator (bug_phase_generator.py) generates .planning/phases/{N}-bug-fix-{bug_id}/ directory structure with CONTEXT.md + PLAN.md (6 standard tasks) + DISCUSSION-LOG.md + SUMMARY.md, supports --batch mini-batch mode (max 2-3 same-feat same-module bugs)
5. test-run integration: build_bug_bundle() outputs bug JSON with status:detected and gap_type (code_defect/test_defect/env_issue, auto-inferred + manual override), sync_bugs_to_registry() persists detected bugs to artifacts/bugs/{feat_ref}/bug-registry.yaml with inline diagnostics[]

**Plans:**
- [ ] 025-01-PLAN.md — bug_registry.py core module (TDD: CRUD + state machine + YAML persistence + unit tests)
- [ ] 025-02-PLAN.md — bug_phase_generator.py (single bug + mini-batch directory generation + unit tests)
- [ ] 025-03-PLAN.md — Integration (on_complete callback + build_bug_bundle upgrade + command.py wiring)

---

### Phase 26: 验收层集成

**Goal:** Gate FAIL 后系统自动将 detected bug 提升为 open 真缺陷，gate/settlement 输出契约包含 bug 关联信息，开发者通过 push model 收到修复任务通知。

**Depends on:** Phase 25

**Requirements:** GATE-REM-01, GATE-REM-02, GATE-INTEG-01, GATE-INTEG-02, PUSH-MODEL-01

**Success Criteria** (what must be TRUE):
1. Gate Remediation module (gate_remediation.py) reads bug-registry and settlement gap_list on gate FAIL, performs consistency check (settlement is source of truth), detected -> open auto-promotion
2. release_gate_input.yaml output contract updated with bug association info (gap_list -> bug_id mapping); settlement input contract updated for reading active bug list
3. Push model: gate FAIL auto-creates draft phase preview, terminal highlight notification + T+4h reminder to run ll-bug-remediate --feat-ref {ref}
4. Developer runs ll-bug-remediate --feat-ref {ref}, sees bug preview (title, severity, gap_type, affected files), y/n input generates phase directory

**Plans:**
- 26-01: gate_remediation.py core module
- 26-02: gate-evaluate output contract update
- 26-03: settlement input contract + push model

---

### Phase 27: GSD 闭环验证

**Goal:** Fixed bugs can be auto-verified and closed, developers have complete CLI tools for bug lifecycle management, shadow fixes detected and warned, audit log records all state changes, integration tests verify end-to-end closure.

**Depends on:** Phase 26

**Requirements:** VERIFY-01, VERIFY-02, VERIFY-03, VERIFY-04, CLI-01, CLI-02, SHADOW-01, AUDIT-01, INTEG-TEST-01

**Success Criteria** (what must be TRUE):
1. --verify-bugs targeted mode (default): only runs tests for coverage_ids of status=fixed bugs; --verify-mode=full-suite runs complete suite for regression detection
2. Post-verification state transitions: targeted pass -> re_verify_passed; targeted fail -> fallback open; severity hints displayed
3. 2-condition auto-close: re_verify pass AND no new test failures between fix commit and re_verify -> auto closed + notification
4. Bug transition CLI (ll-bug-transition --bug-id {id} --to {state}): supports wont_fix (--reason >=20 chars), duplicate (--duplicate-of), manual close override
5. Shadow Fix Detection: commit hook scans diff, warns if status=open bug source files modified
6. Audit log: every state change written to artifacts/bugs/{feat_ref}/audit.log
7. Integration test (test_bug_closure.py) covers complete loop

**Plans:**
- 27-01: --verify-bugs mode (targeted + full-suite)
- 27-02: Post-verification state transitions + 2-condition auto-close
- 27-03: Bug transition CLI + Shadow Fix Detection
- 27-04: Audit log module
- 27-05: Integration test (test_bug_closure.py)

---

<details>
<summary>v2.2.1 Failure Case Resolution (Phases 20-24) — SHIPPED 2026-04-28</summary>

- [x] Phase 20: P0 defect emergency fix (3/3 plans) — 2026-04-28
- [x] Phase 21: PROTO defect fix (3/3 plans) — 2026-04-28
- [x] Phase 22: TECH and IMPL defect fix (3/3 plans) — 2026-04-28
- [x] Phase 23: TESTSET and governance fix (3/3 plans) — 2026-04-28
- [x] Phase 24: impl-spec-test enhance and verify (4/4 plans) — 2026-04-28

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
     |
     v
Phase 25 --> Phase 26 --> Phase 27
(Bug Registry   (Gate       (GSD Closure
 + State Machine) Integration) Verification)
```

---

## Risk Notes

| Phase | Risk | Mitigation |
|-------|------|------------|
| 25 | Optimistic lock concurrency may miss edge cases | Unit tests cover concurrent write conflict scenarios |
| 26 | gate/settlement contract updates may affect existing consumers | Backward compatible: add fields, don't delete/rename existing |
| 27 | Integration test covering full loop is complex | Step-by-step: per-module tests first, then assemble E2E |

---

*Last updated: 2026-04-29 — Phase 25 plans created (3 plans), ready for execution*
