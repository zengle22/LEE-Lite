---
phase: "09"
slug: impl-spec-test
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-04-18"
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs test files |
| **Quick run command** | `python -m pytest cli/lib/test_silent_override.py -x` |
| **Full suite command** | `python -m pytest cli/lib/test_silent_override.py skills/ll-qa-impl-spec-test/tests/ -x` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest cli/lib/test_silent_override.py -x`
- **After every plan wave:** Run `python -m pytest cli/lib/test_silent_override.py skills/ll-qa-impl-spec-test/tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | STAB-01, STAB-03, STAB-04 | T-09-01 (FRZ tampering) | classify_change correctly distinguishes clarification from semantic_change | unit | `pytest cli/lib/test_silent_override.py -k classification -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | STAB-01, STAB-03, STAB-04 | T-09-01 (FRZ tampering) | silent_override blocks tampered/missing/constraint-violation FRZ output | unit | `pytest cli/lib/test_silent_override.py -k block -x` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | STAB-02, STAB-04 | — | semantic_stability dimension produces verdict with semantic_drift field | unit | `pytest skills/ll-qa-impl-spec-test/tests/test_semantic_stability_dimension.py -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | STAB-02, STAB-04 | — | impl-spec-test returns block verdict on semantic drift | unit | `pytest skills/ll-qa-impl-spec-test/tests/test_semantic_stability_dimension.py -x` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | STAB-03 | — | validate_output.sh invokes silent_override.py and exits non-zero on block | integration | `bash skills/ll-dev-*/validate_output.sh` (manual smoke test) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cli/lib/test_silent_override.py` — stubs for STAB-01, STAB-03, STAB-04
- [ ] `skills/ll-qa-impl-spec-test/tests/test_semantic_stability_dimension.py` — stubs for STAB-02
- [ ] Test data fixtures: FRZ packages with known anchors for drift comparison scenarios

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| validate_output.sh integration across all 6 dev skills | STAB-03 | Shell scripts call external Python; full integration requires running each skill end-to-end | Run each `ll-dev-*/validate_output.sh` against a known-clean artifact dir and a known-tampered artifact dir, verify exit codes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-04-18
