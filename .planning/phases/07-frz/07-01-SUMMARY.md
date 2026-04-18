---
phase: 07
plan: 01
type: execute
wave: 1
subsystem: frz-schema
tags: [frz, msc, schema, validation]
dependency_graph:
  requires: []
  provides:
    - FRZ-01: FRZ package structure with MSC 5-dim fields
    - FRZ-02: MSC validator minimum semantic completeness
  affects:
    - "cli/lib/qa_schemas.py (follows same pattern)"
    - "ssot/adr/ADR-050 (implements MSC dimensions)"
tech-stack:
  added:
    - Python dataclasses (frozen)
    - PyYAML (safe_load)
    - pytest
  patterns:
    - frozen dataclass hierarchy
    - manual validation (no Pydantic)
    - CLI entry point with --type flag
key-files:
  created:
    - path: cli/lib/frz_schema.py
      lines: ~565
      purpose: FRZPackage dataclass, MSCValidator, YAML parser, CLI
    - path: cli/lib/test_frz_schema.py
      lines: ~370
      purpose: 21 unit tests for FRZ schema and MSC validation
  modified:
    - path: cli/lib/frz_schema.py
      reason: "Fix: MSCValidator.validate_file extracts frz_package inner dict"
decisions:
  - "Used frozen dataclasses (not Pydantic) to match qa_schemas.py pattern"
  - "ID format validation uses regex patterns for FRZ, JRN, ENT, SM, UNK IDs"
  - "MSC minimum content rules enforce real semantics, not just key presence"
  - "MSCValidator.validate_file handles both top-level frz_package key and bare dict"
metrics:
  duration: "executed in single wave"
  completed_date: "2026-04-18"
  tasks_completed: 2
  tests_added: 21
  tests_passed: 21
  tests_failed: 0
---

# Phase 07 Plan 01: FRZ Schema + MSC Validator Summary

**One-liner:** FRZPackage frozen dataclass hierarchy with all 5 MSC dimension sub-types, MSCValidator with minimum-content semantic validation, YAML parser with ID format validation, and CLI entry point — all following qa_schemas.py patterns.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create FRZ schema module | 181f41e | cli/lib/frz_schema.py |
| 2 | Create unit tests | b3ca62f | cli/lib/test_frz_schema.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MSCValidator.validate_file passed wrong dict to _parse_frz_dict**
- **Found during:** Task 2 (test_validate_file_valid_yaml failed)
- **Issue:** `validate_file()` passed the entire YAML dict (with top-level `frz_package` key) to `_parse_frz_dict()`, which expected the inner FRZ package data. This caused all fields to be empty/default, making validation always fail.
- **Fix:** Added `inner = data.get("frz_package", data)` to extract the inner dict before parsing, matching the pattern used by `validate_file()` in the file-level validation entry point.
- **Files modified:** cli/lib/frz_schema.py (line 440)
- **Commit:** b3ca62f

None - all other plan items executed exactly as written.

## Verification Evidence

- `from cli.lib.frz_schema import FRZPackage, MSCValidator, FRZStatus, FRZSchemaError` — imports OK
- `pytest cli/lib/test_frz_schema.py -v` — 21 passed, 0 failed
- File `cli/lib/frz_schema.py` exists with ~565 lines (>150 minimum)
- File `cli/lib/test_frz_schema.py` exists with ~370 lines, 21 test functions (>12 minimum)
- All acceptance criteria met (see below)

### Acceptance Criteria — Task 1 (frz_schema.py)

- [x] Contains `@dataclass(frozen=True)` on FRZPackage and all 7 sub-entity dataclasses
- [x] Contains `class FRZStatus(str, Enum)` with values: draft, freeze_ready, frozen, blocked, revised, superseded
- [x] Contains `class MSCValidator` with static methods `validate` and `validate_file`
- [x] Contains function `_parse_frz_dict` that converts dict to FRZPackage
- [x] Contains `class FRZSchemaError(ValueError)`
- [x] Contains `def main()` CLI entry point with `if __name__ == "__main__"` block
- [x] Uses `yaml.safe_load` (no `yaml.load(` without `safe`)
- [x] Imports `CommandError` from `cli.lib.errors`
- [x] All sub-entity dataclasses are frozen: ProductBoundary, CoreJourney, DomainEntity, StateMachine, AcceptanceContract, KnownUnknown, FRZEvidence
- [x] FRZ ID format validation with `FRZ_ID_PATTERN`
- [x] Sub-entity ID format validation (JRN, ENT, SM, UNK patterns)
- [x] Recursive dict-to-dataclass conversion in `_parse_frz_dict`

### Acceptance Criteria — Task 2 (test_frz_schema.py)

- [x] 21 test functions (minimum 12 required)
- [x] `test_frz_package_structure` — construction + frozen enforcement
- [x] `test_msc_validator_valid_package` — all 5 dims pass
- [x] `test_msc_validator_missing_all_dims` — empty pkg fails
- [x] `test_validate_file_not_found` — FileNotFoundError
- [x] `test_frz_schema_error` — ValueError subclass
- [x] `test_parse_frz_dict_full` — complete dict parsing
- [x] Imports `from cli.lib.frz_schema import FRZPackage, MSCValidator, FRZSchemaError, FRZStatus`
- [x] Imports `pytest`

## Success Criteria

- [x] FRZ-01 delivered: FRZPackage dataclass with all 5 MSC dimension fields
- [x] FRZ-02 delivered: MSCValidator.validate() returns msc_valid=False when dimensions missing, msc_valid=True when all 5 have minimum content
- [x] All 21 unit tests pass with 0 failures
- [x] File follows existing pattern from qa_schemas.py

## Self-Check: PASSED
