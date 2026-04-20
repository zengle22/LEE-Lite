---
phase: 10
slug: change-grading
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | None detected — tests run directly |
| **Quick run command** | `pytest skills/ll-patch-capture/scripts/ -x` |
| **Full suite command** | `pytest skills/ -x --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest <affected_test_file> -x`
- **After every plan wave:** Run `pytest skills/ -x --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | GRADE-01 | T-10-01/T-10-02 | GradeLevel enum, derive_grade, ChangeClass extension work correctly | unit | `python -c "from cli.lib.patch_schema import GradeLevel, derive_grade; assert derive_grade('semantic') == GradeLevel.MAJOR"` | ✅ | ⬜ pending |
| 10-01-02 | 01 | 1 | GRADE-01 | T-10-01/T-10-02 | classify_change returns correct (change_class, grade_level, confidence, dimensions_detected) for visual/interaction/semantic/mixed/negation inputs | unit | `pytest skills/ll-patch-capture/scripts/test_patch_capture_runtime.py -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | GRADE-01 | — | SKILL.md updated with tri-classification references | docs | `grep -c "grade_level" skills/ll-patch-capture/SKILL.md` | ✅ | ⬜ pending |
| 10-02-01 | 02 | 2 | GRADE-02 | T-10-04 | Skill skeleton files exist with correct content (grade_level, backwrite, Major rejection) | docs | `test -f skills/ll-experience-patch-settle/SKILL.md && grep -q "grade_level" skills/ll-experience-patch-settle/SKILL.md` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | GRADE-02 | T-10-04/T-10-05 | settle_minor_patch backwrites correctly by change_class, rejects Major, idempotent | unit | `pytest skills/ll-experience-patch-settle/scripts/test_settle_runtime.py -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 1 | GRADE-03 | T-10-07 | _format_frz_list shows fixed columns with REV_TYPE/PREV_FRZ; circular detection works | unit | `python -c "from skills.ll-frz-manage.scripts.frz_manage_runtime import _format_frz_list; ..."` | ✅ | ⬜ pending |
| 10-03-02 | 03 | 1 | GRADE-03 | T-10-08 | Revise tests pass, validate_output.sh checks revise fields | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py -x -k "revise or list"` | ✅ | ⬜ pending |
| 10-04-01 | 04 | 2 | GRADE-04 | T-10-10/T-10-11 | summarize_patch_for_context outputs grade_level, Major WARNING, auto-derive works | unit | `python -c "from cli.lib.patch_context_injector import summarize_patch_for_context; assert 'grade_level' in ..."` | ✅ | ⬜ pending |
| 10-04-02 | 04 | 2 | GRADE-04 | T-10-16 | patch_aware_context.py summarize_patch includes grade_level, cross-caller consistency | unit | `python -c "from patch_aware_context import summarize_patch; ..."` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py` — tests for tri-classification, mixed inputs, negations, no-indicator fallback
- [ ] `skills/ll-experience-patch-settle/scripts/test_settle_runtime.py` — tests for backwrite by change_class, Major rejection, idempotency
- [ ] `skills/ll-experience-patch-settle/SKILL.md` + skeleton files — skill definition for Minor settle workflow

*Framework (pytest 9.0.2) already installed — no Wave 0 framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `ll frz-manage freeze --type revise` end-to-end | GRADE-03 | Requires FRZ package input files + MSC validation flow | 1. Create FRZ-001 with freeze.yaml → freeze. 2. Create FRZ-002 with revise args → verify registry shows revision chain |
| Full FRZ → SRC → EPIC → FEAT extraction after revise | GRADE-03 | End-to-end workflow spanning multiple skills | 1. Create revised FRZ. 2. Run extract chain. 3. Verify anchor IDs and no semantic drift |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (all tasks have automated verify)
- [x] Wave 0 covers all MISSING references (3 test files to create during execution)
- [x] No watch-mode flags
- [x] Feedback latency < 30s

**Approval: approved 2026-04-19**
