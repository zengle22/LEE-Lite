---
phase: "08"
plan: "03"
type: execute
subsystem: src-to-epic-extract
tags:
  - frz-to-epic
  - extract-subcommand
  - anchor-registry
  - projection-invariance
  - tdd
dependency_graph:
  requires:
    - anchor_registry (Phase 7 + multi-projection from 08-02)
    - frz_schema (Phase 7)
    - frz_registry (Phase 7)
    - drift_detector (Phase 8, Plan 01)
    - projection_guard (Phase 8, Plan 01)
    - frz_extractor (Phase 8, Plan 02)
  provides:
    - extract subcommand for ll src-to-epic CLI
    - extract_epic_from_frz() workflow function
    - build_epic_from_frz() rule-template mapping
    - extract_epic_from_frz_logic() full extraction pipeline
  affects:
    - 08-04 (epic-to-feat extract follows same pattern)
tech_stack:
  added: []
  patterns:
    - frozen dataclass DTOs (EpicExtractResult)
    - rule-template projection (deterministic, D-01)
    - TDD (RED->GREEN for test suite)
    - compound key (anchor_id + projection_path) for anchor registry
key_files:
  created:
    - skills/ll-product-src-to-epic/scripts/src_to_epic_extract.py (~220 lines)
    - skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py (~250 lines)
  modified:
    - skills/ll-product-src-to-epic/scripts/src_to_epic.py (+19 lines)
    - skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py (+130 lines)
decisions:
  - "EpicExtractResult dataclass separates extraction logic from runtime for testability"
  - "Acceptance contract anchors use derived FC-xxx IDs since FRZ acceptance_contract lacks explicit IDs"
  - "FRZ YAML loaded via _parse_frz_dict() from frz_schema, not via validate_file() (status check done separately)"
metrics:
  duration: ~20min
  completed: "2026-04-18"
  tests_created: 14
  tests_passed: 14
  files_created: 2
  files_modified: 2
---

# Phase 08 Plan 03: SRC-to-EPIC FRZ Extract Summary

**One-liner:** FRZ-based EPIC extraction via rule-template projection with anchor inheritance, projection guard, and drift detection — 14 passing tests.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add extract subcommand + extract_epic_from_frz | `6b80f7d` | src_to_epic.py, src_to_epic_runtime.py, src_to_epic_extract.py |
| 2 | Create src_to_epic_extract.py with FRZ->EPIC logic | `6b80f7d` | src_to_epic_extract.py (new) |
| 3 | Write integration tests (14 tests) | `27771ce` | test_src_to_epic_extract.py |

## Deviations from Plan

None - plan executed exactly as written. All tasks completed with acceptance criteria met.

## Known Stubs

None. All functions are fully implemented with data sources wired:
- `build_epic_from_frz()` maps all FRZ MSC dimensions to EPIC sections
- `extract_epic_from_frz_logic()` registers anchors, runs guard/drift, returns result
- `extract_epic_from_frz()` loads FRZ from registry, validates, writes output

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag:input_validation | src_to_epic_runtime.py | Validates FRZ ID format (FRZ_ID_PATTERN) and frozen status before extraction (T-08-10, T-08-13 mitigated) |
| threat_flag:anchor_validation | src_to_epic_extract.py | Anchor IDs validated via AnchorRegistry.register_projection which checks ANCHOR_ID_PATTERN (T-08-11 mitigated) |
| threat_flag:guard_enforcement | src_to_epic_extract.py | guard_projection runs after extraction; block verdict prevents successful extraction (T-08-12 mitigated) |

All 4 threats from the plan's threat model are mitigated in implementation. No new threat surface introduced.

## Verification Evidence

```
python -m pytest skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py -v
============================= 14 passed in 0.09s ==============================
```

All success criteria met:
1. `src_to_epic.py` has `extract` subcommand with --frz, --src, --output arguments
2. `src_to_epic_runtime.py` has `extract_epic_from_frz()` function
3. `src_to_epic_extract.py` has `build_epic_from_frz()` and `extract_epic_from_frz_logic()`
4. Existing run/executor-run commands are unmodified (added only extract subcommand)
5. Anchor IDs from FRZ registered with projection_path="EPIC" via AnchorRegistry.register_projection
6. 14 passing tests covering mapping correctness, anchor inheritance, guard blocking, non-frozen rejection, empty FRZ dimensions, CLI parsing

## Self-Check: PASSED

All created/modified files verified. Both commits present in git log. All 14 tests passing.