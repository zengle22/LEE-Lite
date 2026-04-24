---
phase: 18
slug: execution-axis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-24
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/cli/lib/ -x -q` |
| **Full suite command** | `pytest tests/ -x -q --ignore=tests/e2e` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/cli/lib/test_run_manifest_gen.py -x -q`
- **After every plan wave:** Run `pytest tests/cli/lib/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | EXEC-01 | T-18-01 | Validate run_id format | unit | `pytest tests/cli/lib/test_run_manifest_gen.py -x -q` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | EXEC-01 | T-18-02 | Wrap YAML load in try/except | unit | `pytest tests/cli/lib/test_run_manifest_gen.py -x -q` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 1 | EXEC-02 | T-18-03 | C_MISSING intentional design | unit | `pytest tests/cli/lib/test_scenario_spec_compile.py -x -q` | ❌ W0 | ⬜ pending |
| 18-02-02 | 02 | 1 | EXEC-02 | — | N/A | unit | `pytest tests/cli/lib/test_scenario_spec_compile.py -x -q` | ❌ W0 | ⬜ pending |
| 18-03-01 | 03 | 2 | EXEC-03 | T-18-04 | Validate run_id in state loading | unit | `pytest tests/cli/lib/test_state_machine_executor.py -x -q` | ❌ W0 | ⬜ pending |
| 18-03-02 | 03 | 2 | EXEC-03 | T-18-05 | Wrap YAML load in try/except | unit | `pytest tests/cli/lib/test_state_machine_executor.py -x -q` | ❌ W0 | ⬜ pending |
| 18-04-01 | 04 | 2 | TEST-02 | T-18-06 | Tests use localhost only | integration | `pytest tests/integration/test_e2e_chain.py -x -q` | ❌ W0 | ⬜ pending |
| 18-04-02 | 04 | 2 | TEST-03 | — | N/A | integration | `pytest tests/integration/test_resume.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/cli/lib/test_run_manifest_gen.py` — stubs for EXEC-01
- [ ] `tests/cli/lib/test_scenario_spec_compile.py` — stubs for EXEC-02
- [ ] `tests/cli/lib/test_state_machine_executor.py` — stubs for EXEC-03
- [ ] `tests/integration/test_e2e_chain.py` — stubs for TEST-02
- [ ] `tests/integration/test_resume.py` — stubs for TEST-03
- [ ] `tests/conftest.py` — shared fixtures (if not already exists)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| E2E chain with --app-url/--api-url | TEST-02 | Requires running frontend/backend | Start servers, run `python -m cli skill qa-test-run --proto-ref XXX --app-url http://localhost:3000 --api-url http://localhost:8000` |
| --resume from failed state | TEST-03 | Requires failed run state | After E2E chain failure, run `python -m cli skill qa-test-run --resume` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending