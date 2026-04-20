---
phase: 7
slug: frz
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | None detected at project root — Wave 0 creates stubs |
| **Quick run command** | `pytest cli/lib/test_frz_schema.py -x` |
| **Full suite command** | `pytest cli/lib/test_frz_schema.py cli/lib/test_anchor_registry.py cli/lib/test_frz_registry.py skills/ll-frz-manage/scripts/test_frz_manage_runtime.py -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest <relevant_test_file> -x`
- **After every plan wave:** Run full suite command above
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | FRZ-01 | — | FRZPackage dataclass with 5 MSC fields | unit | `pytest cli/lib/test_frz_schema.py::test_frz_package_structure -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | FRZ-02 | — | MSCValidator rejects incomplete packages | unit | `pytest cli/lib/test_frz_schema.py::test_msc_validator_missing_dims -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | EXTR-03 | — | AnchorRegistry registers and resolves anchor IDs | unit | `pytest cli/lib/test_anchor_registry.py::test_register_anchor -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 2 | FRZ-03 | — | FRZ registry records version, status, created_at | unit | `pytest cli/lib/test_frz_registry.py::test_register_frz -x` | ❌ W0 | ⬜ pending |
| 07-04-01 | 04 | 2 | FRZ-04 | — | `ll frz-manage validate` outputs MSC report | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_validate -x` | ❌ W0 | ⬜ pending |
| 07-04-02 | 04 | 2 | FRZ-05 | — | `ll frz-manage freeze` writes FRZ to registry | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_freeze -x` | ❌ W0 | ⬜ pending |
| 07-04-03 | 04 | 2 | FRZ-06 | — | `ll frz-manage list` shows registered FRZ packages | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_list -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cli/lib/test_frz_schema.py` — stubs for FRZ-01, FRZ-02
- [ ] `cli/lib/test_frz_registry.py` — stubs for FRZ-03
- [ ] `cli/lib/test_anchor_registry.py` — stubs for anchor registry
- [ ] `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py` — stubs for FRZ-04, FRZ-05, FRZ-06
- [ ] `pytest` — already installed (verify at project root)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| FRZ package MSC report readability | FRZ-02 | Output formatting is subjective | Run `ll frz-manage validate --input <doc-dir>`, verify report is human-readable |
| FRZ registry file structure | FRZ-03 | YAML structure needs human review | Open `ssot/registry/frz-registry.yaml`, verify version/status/created_at fields |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
