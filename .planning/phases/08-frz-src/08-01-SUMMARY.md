---
phase: "08"
plan: "01"
type: execute
subsystem: drift-detection
tags:
  - drift-detection
  - projection-guard
  - semantic-integrity
  - tdd
dependency_graph:
  requires:
    - anchor_registry (Phase 7)
    - frz_schema (Phase 7)
    - errors (Phase 7)
  provides:
    - check_drift() - anchor-level semantic drift detection
    - check_derived_allowed() - field whitelist enforcement
    - check_constraints() - constraint validation
    - check_known_unknowns() - expired unknown detection
    - guard_projection() - projection invariance guard
  affects:
    - 08-02 (extract_frz uses drift detection)
    - 08-03 (skill scripts call guard)
    - 08-04 (cascade mode chains guard)
tech_stack:
  added: []
  patterns:
    - frozen dataclass DTOs
    - TDD (RED→GREEN)
    - pure library modules
    - INTRINSIC_KEYS whitelist
    - ANCHOR_ID_PATTERN validation
key_files:
  created:
    - cli/lib/drift_detector.py (304 lines)
    - cli/lib/test_drift_detector.py (244 lines)
    - cli/lib/projection_guard.py (122 lines)
    - cli/lib/test_projection_guard.py (121 lines)
  modified: []
decisions:
  - "guard_projection uses GUARD_INTRINSIC_KEYS (9 keys) instead of drift_detector INTRINSIC_KEYS (5 keys) — guard operates at broader projection context"
  - "guard_projection returns early with pass for empty output_data — no content to violate constraints"
  - "check_drift detects new_field drift type for extra keys in target_data not in FRZ anchor content"
  - "check_drift validates anchor_id against ANCHOR_ID_PATTERN per threat T-08-01"
metrics:
  duration: ~15min
  completed: "2026-04-18"
  tests_created: 27
  tests_passed: 27
  files_created: 4
---

# Phase 08 Plan 01: Drift Detection and Projection Guard Summary

**One-liner:** Semantic drift detection library with 5-scenario anchor-level checks and projection invariance guard enforcing derived_allowed whitelist, TDD-developed with 27 passing unit tests.

## Completed Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Create drift_detector.py with 5-scenario detection | `fa80e1b`, `2573255` |
| 2 | Create projection_guard.py with derived_allowed enforcement | `b7c7bd4` |
| 3 | Write unit tests for drift_detector (18 tests) | `fa80e1b` |
| 4 | Write unit tests for projection_guard (9 tests) | `b7c7bd4` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Security] Added anchor_id format validation**
- **Found during:** Threat surface scan (T-08-01 in plan threat model)
- **Issue:** `check_drift()` did not validate anchor_id format before processing, violating threat T-08-01 which assigns `mitigate` disposition
- **Fix:** Added `ensure(isinstance(anchor_id, str) and ANCHOR_ID_PATTERN.match(anchor_id), ...)` at start of `check_drift()`, importing `ANCHOR_ID_PATTERN` from `cli.lib.anchor_registry`
- **Files modified:** `cli/lib/drift_detector.py`
- **Commit:** `2573255`

**2. [Rule 1 - Bug] Guard intrinsic keys mismatch**
- **Found during:** Task 2 implementation
- **Issue:** Plan specified `guard_projection` should call `check_derived_allowed` from drift_detector, but drift_detector uses `INTRINSIC_KEYS` (5 keys) while guard needs `GUARD_INTRINSIC_KEYS` (9 keys including metadata, created_at, status, version)
- **Fix:** `guard_projection` directly checks against `GUARD_INTRINSIC_KEYS` rather than delegating to `check_derived_allowed`, ensuring the broader guard context keys are respected
- **Files modified:** `cli/lib/projection_guard.py`

**3. [Rule 1 - Bug] Empty output constraint violation**
- **Found during:** Task 4 test execution
- **Issue:** Plan specifies empty output_data should pass guard, but `check_constraints` flags all constraints as violated when output is empty
- **Fix:** Added early return in `guard_projection` — if `output_data` is empty dict, return `GuardResult(passed=True, violations=[], verdict="pass")` immediately
- **Files modified:** `cli/lib/projection_guard.py`

## Known Stubs

None. All functions are fully implemented with data sources wired.

## Threat Flags

None remaining. Threat T-08-01 was auto-fixed during execution.

## Verification Evidence

```
python -m pytest cli/lib/test_drift_detector.py cli/lib/test_projection_guard.py -v
============================= 27 passed in 0.07s ==============================
```

All success criteria met:
1. `cli/lib/drift_detector.py` exists with check_drift, check_derived_allowed, check_constraints, check_known_unknowns functions
2. `cli/lib/projection_guard.py` exists with guard_projection returning GuardResult(passed/violations/verdict)
3. 18+ passing tests covering all D-12 scenarios including none/no-drift, new_field, combined violations, empty output
4. 9+ passing tests for whitelist enforcement including combined violations, empty output
5. DriftResult drift_type values include: "none", "missing", "tampered", "new_field", "constraint_violation", "unknown_expired"
6. check_drift's target_data parameter is documented as a dict keyed by anchor_id

## Self-Check: PASSED

All 4 created files verified. All 3 commits present in git log.
