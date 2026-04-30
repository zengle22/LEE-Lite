---
phase: 25
slug: bug-registry-state-machine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest cli/lib/test_bug_registry.py -x -v` |
| **Full suite command** | `pytest cli/lib/test_bug_registry.py cli/lib/test_bug_phase_generator.py -x -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest cli/lib/test_bug_registry.py -x -v`
- **After every plan wave:** Run `pytest cli/lib/test_bug_registry.py cli/lib/test_bug_phase_generator.py -x -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| bug-registry-core | 01 | 1 | BUG-REG-01 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_load_or_create -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-01 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_optimistic_lock -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-02 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_happy_path_transitions -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-02 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_invalid_transition -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-03 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_wont_fix_requires_reason -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-03 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_duplicate_requires_ref -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-03 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_not_reproducible_thresholds -x` | ❌ W0 | ⬜ pending |
| bug-registry-core | 01 | 1 | BUG-REG-03 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_resurrection_new_record -x` | ❌ W0 | ⬜ pending |
| bug-phase-gen | 02 | 1 | BUG-PHASE-01 | — | N/A | unit | `pytest cli/lib/test_bug_phase_generator.py::test_phase_dir_structure -x` | ❌ W0 | ⬜ pending |
| bug-phase-gen | 02 | 1 | BUG-PHASE-02 | — | N/A | unit | `pytest cli/lib/test_bug_phase_generator.py::test_mini_batch -x` | ❌ W0 | ⬜ pending |
| orchestrator-integration | 03 | 2 | BUG-INTEG-01 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_gap_type_inference -x` | ❌ W0 | ⬜ pending |
| orchestrator-integration | 03 | 2 | BUG-INTEG-02 | — | N/A | unit | `pytest cli/lib/test_bug_registry.py::test_sync_persists -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cli/lib/test_bug_registry.py` — stubs for BUG-REG-01/02/03, BUG-INTEG-01/02
- [ ] `cli/lib/test_bug_phase_generator.py` — stubs for BUG-PHASE-01/02

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Terminal output during ll-bug-transition | BUG-REG-02 | CLI output formatting not testable in unit tests | Run transition command, verify human-readable output |
| bug-registry.yaml file on disk | BUG-REG-01 | File content verified by tests but manual spot-check for formatting | Inspect `artifacts/bugs/{feat_ref}/bug-registry.yaml` after a test run |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
