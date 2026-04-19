---
phase: "10-change-grading"
plan: "03"
subsystem: "ll-frz-manage"
tags: ["frz", "revise", "circular-chain", "grade-03"]
dependency_graph:
  requires: ["GRADE-03", "frz_registry.py register_frz"]
  provides: ["FIXED column list output", "circular revision chain prevention", "revise tests", "validate_output.sh revise checks"]
  affects: ["ll-frz-manage", "frz_registry"]
tech-stack:
  added: ["circular chain detection algorithm", "FIXED column table formatting"]
  patterns: ["chain traversal with visited set for cycle detection"]
key-files:
  created: []
  modified:
    - "skills/ll-frz-manage/scripts/frz_manage_runtime.py"
    - "skills/ll-frz-manage/scripts/test_frz_manage_runtime.py"
    - "skills/ll-frz-manage/scripts/validate_output.sh"
decisions:
  - "FIXED columns chosen over conditional rendering to preserve downstream column-position parsing"
  - "_check_circular_revision uses set + ordered list to track visited FRZ IDs and return chain in traversal order"
  - "Circular check placed before register_frz but after duplicate check and revision arg extraction"
metrics:
  duration_minutes: ~15
  completed_date: "2026-04-19"
  tests_added: 6
  tests_total: 32
  all_tests_passing: true
---

# Phase 10 Plan 03: FRZ Revise Enhancement Summary

**One-liner:** Enhanced `ll-frz-manage` with FIXED-column list output showing revision metadata (REV_TYPE, PREV_FRZ), circular revision chain prevention, and 6 new tests covering revise flows.

## Objective

Verify and enhance the existing `--type revise` path in `ll-frz-manage`. The CLI plumbing was ~80% implemented; this plan enhanced list output, added circular chain prevention, and added dedicated tests.

## Tasks Executed

### Task 1: Verify existing --type revise, enhance list with FIXED columns, add circular chain prevention

- Verified `freeze_frz()` correctly reads and passes revise args (--type, --reason, --previous-frz)
- Enhanced `_format_frz_list()` from 4 columns to 6 FIXED columns: FRZ_ID, STATUS, REV_TYPE, PREV_FRZ, CREATED_AT, MSC_VALID
- Empty prev_frz shows '-' instead of empty string
- Added `_check_circular_revision()` function that walks the revision chain using a visited set + ordered list
- Added circular chain check to `freeze_frz()` before `register_frz()` — raises CIRCULAR_REVISION CommandError
- `register_frz()` unchanged — already stores revision metadata correctly
- Committed: `feat(10-03): enhance frz list with FIXED columns and add circular chain prevention`

### Task 2: Add dedicated revise tests + circular chain prevention tests + validate_output.sh revise check

- Added 6 new tests (32 total, up from 20+):
  - `test_circular_revision_chain`: Self-referencing revise rejected
  - `test_circular_revision_chain_back_reference`: Back-reference cycle detection + chain traversal order verification
  - `test_fixed_columns_always_shown`: List always shows REV_TYPE and PREV_FRZ columns
  - `test_empty_prev_frz_shows_dash`: Non-revision records show '-' for PREV_FRZ
  - `test_invalid_previous_frz_validation`: Revise with nonexistent previous_frz allowed (current behavior)
  - `test_revise_via_main_cli`: Full CLI path for revise with main() function
- Enhanced `validate_output.sh` to check revise-specific fields (previous_frz_ref, revision_reason) with yq/python fallback
- All 32 tests passing, no regressions
- Committed: `test(10-03): add revise tests and validate_output.sh revise checks`

## Key Decisions

1. **FIXED columns**: Chosen over conditional rendering to preserve downstream column-position parsing by scripts.
2. **Circular chain algorithm**: Uses a visited set for O(1) lookup + an ordered list to return the chain in traversal order. This avoids the `set` ordering issue discovered during testing.
3. **Circular check placement**: After duplicate check and revision arg extraction, before `register_frz()` call.

## Deviations from Plan

**None** — plan executed exactly as written. One bug was auto-fixed during testing (Rule 1): the circular revision check code was inserted before the `revision_type` variable extraction in `freeze_frz()`, causing `UnboundLocalError`. Fixed by moving arg extraction before the circular check.

## Known Stubs

None — all functionality is wired and tested.

## Threat Flags

None — circular chain prevention addresses the existing threat register (T-10-15).

## Self-Check

- [x] `_check_circular_revision` exists in frz_manage_runtime.py (line 164)
- [x] `CIRCULAR_REVISION` error exists in frz_manage_runtime.py (line 380)
- [x] `_format_frz_list()` uses FIXED columns with REV_TYPE and PREV_FRZ always present
- [x] `'-'` used as default for prev_frz in `_format_frz_list`
- [x] freeze_frz() still reads getattr(args, "type"), getattr(args, "reason"), getattr(args, "previous_frz")
- [x] register_frz call still passes previous_frz, revision_type, reason
- [x] 32 tests collected and passing
- [x] test_circular_revision_chain exists
- [x] test_fixed_columns_always_shown exists
- [x] test_empty_prev_frz_shows_dash exists
- [x] _check_circular_revision invoked in tests
- [x] validate_output.sh contains "revision_type" and "revise" check

## Self-Check: PASSED
