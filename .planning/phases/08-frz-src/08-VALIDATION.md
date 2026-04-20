---
phase: 08
slug: frz-src
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `cli/lib/conftest.py` (Phase 7 established) |
| **Quick run command** | `pytest cli/lib/ skills/ -k "frz or drift or extract" --tb=short -q` |
| **Full suite command** | `pytest cli/lib/ skills/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest cli/lib/ skills/ -k "frz or drift or extract" --tb=short -q`
- **After every plan wave:** Run `pytest cli/lib/ skills/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | EXTR-04 | — | Drift detection catches anchor missing | unit | `pytest cli/lib/test_drift_detector.py -v` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | EXTR-04 | — | Drift detection catches semantic tampering | unit | `pytest cli/lib/test_drift_detector.py -v` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | EXTR-04 | — | Drift detection catches non-derived_allowed field | unit | `pytest cli/lib/test_drift_detector.py -v` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | EXTR-04 | — | Drift detection catches constraint violation | unit | `pytest cli/lib/test_drift_detector.py -v` | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 1 | EXTR-04 | — | Drift detection catches expired known_unknowns | unit | `pytest cli/lib/test_drift_detector.py -v` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | EXTR-01, EXTR-05 | — | Extract produces SRC within derived_allowed | unit | `pytest cli/lib/test_frz_extractor.py -v` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | EXTR-03 | — | Anchor registered with correct projection_path | unit | `pytest cli/lib/test_frz_extractor.py -v` | ❌ W0 | ⬜ pending |
| 08-02-03 | 02 | 2 | EXTR-05 | — | Projection guard rejects out-of-scope field | unit | `pytest cli/lib/test_frz_extractor.py -v` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 3 | EXTR-02 | — | SRC→EPIC extract with anchor inheritance | integration | `pytest skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py -v` | ❌ W0 | ⬜ pending |
| 08-04-01 | 04 | 3 | EXTR-02 | — | EPIC→FEAT extract with anchor inheritance | integration | `pytest skills/ll-product-epic-to-feat/scripts/test_epic_to_feat_extract.py -v` | ❌ W0 | ⬜ pending |
| 08-02-04 | 02 | 2 | EXTR-01~05 | — | Full cascade FRZ→SRC→EPIC→FEAT passes | e2e | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py -v -k cascade` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cli/lib/test_drift_detector.py` — 5 drift detection test cases (D-12)
- [ ] `cli/lib/test_projection_guard.py` — projection guard unit tests
- [ ] `cli/lib/test_frz_extractor.py` — FRZ→SRC extract unit tests with FRZ fixtures
- [ ] `cli/lib/test_anchor_registry.py` — extended tests for register_projection (from Plan 08-02 Task 1)
- [ ] `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py` — extract + cascade tests (existing file, extended)
- [ ] `skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py` — SRC→EPIC integration tests
- [ ] `skills/ll-product-epic-to-feat/scripts/test_epic_to_feat_extract.py` — EPIC→FEAT integration tests
- [ ] `cli/lib/conftest.py` — shared fixtures (FRZ fixtures, anchor registry mock)
- [ ] Framework already installed (Phase 7 pytest setup)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cascade gate审核 flow | EXTR-02 | Gate requires human judgment for block verdicts | Run `ll frz-manage extract --cascade --frz FRZ-xxx`, verify gate prompts appear between each step |
| FRZ missing content warnings | EXTR-01 | Depends on actual FRZ content completeness | Create FRZ with missing TECH/UI layers, run extract, verify warning output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-04-18
