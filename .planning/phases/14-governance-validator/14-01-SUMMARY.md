---
phase: "14"
plan: "01"
status: "complete"
completed: "2026-04-23"
wave: 1
autonomous: true
requirements:
  - "GOV-01"
  - "GOV-02"
  - "GOV-03"
files_created:
  - "cli/lib/governance_validator.py"
  - "tests/cli/lib/test_governance_validator.py"
files_modified:
  - "cli/lib/enum_guard.py"
key_links_verified:
  - "validate_enums() call in governance_validator.py → enum_guard.py"
---

## Plan 14-01 Summary

**Objective:** Implement governance_validator.py covering all 11 SRC-009 governance objects with required/optional/forbidden field validation, collect-all violation reporting, and enum_guard integration.

**Status:** Complete

## Deliverables

### cli/lib/governance_validator.py (688 lines)
- `GovernanceViolation` frozen dataclass with 5 fields (field, value, expected, label, violation_type)
- `ViolationType` enum (required_missing, forbidden_field, extra_field)
- 11 validator classes (all frozen dataclasses):
  - SkillValidator
  - ModuleValidator
  - AssertionLayerValidator
  - FailureClassValidator
  - GoldenPathValidator
  - GateValidator
  - StateMachineValidator
  - RunManifestValidator
  - EnvironmentValidator
  - AccidentValidator
  - VerifierValidator
- `validate()` — public API function
- `validate_file()` — YAML file validation
- `main()` CLI entry point with --object, --check, --list-types flags
- VALIDATORS map with all 11 object types
- OBJECT_TOP_KEYS for auto-detection

### tests/cli/lib/test_governance_validator.py (1355 lines, 99 tests)
- TestGovernanceViolation (5 tests)
- TestSkillValidator (8 tests)
- TestModuleValidator (6 tests)
- TestAssertionLayerValidator (6 tests)
- TestFailureClassValidator (6 tests)
- TestGoldenPathValidator (8 tests)
- TestGateValidator (11 tests)
- TestStateMachineValidator (6 tests)
- TestRunManifestValidator (7 tests)
- TestEnvironmentValidator (6 tests)
- TestAccidentValidator (10 tests)
- TestVerifierValidator (7 tests)
- TestCollectAllViolations (3 tests)
- TestValidatorsMap (3 tests)
- TestCLI (2 tests)

### cli/lib/enum_guard.py (modified)
- Added field name aliases for SRC-009 compatibility:
  - `verdict` → GateVerdict (for Gate and Verifier objects)
  - `failure_classification` → FailureClass (for Accident object)

## Decisions Implemented

| Decision | Implementation |
|----------|---------------|
| D-01: Single file | governance_validator.py contains all validators |
| D-02: Collect-all violations | validate() returns list, not fail-fast |
| D-03: Frozen dataclass | All validators @dataclass(frozen=True) |
| D-04: --object CLI flag | main() uses --object for type specification |
| D-05: enum_guard integration | validate_enums() called for objects with enum fields |
| D-06: Consistent error format | Violation __str__() matches enum_guard format |
| D-07: All violations before raising | Returns complete list of violations |

## Success Criteria Verification

| # | Criteria | Status |
|---|---------|--------|
| 1 | --object flag works for validation | PASS |
| 2 | Missing required → violation_type=required_missing | PASS |
| 3 | Forbidden field → violation_type=forbidden_field | PASS |
| 4 | Extra field → violation_type=extra_field | PASS |
| 5 | Enum field objects call validate_enums() | PASS |
| 6 | --list-types shows all 11 types | PASS |
| 7 | --check mode validates inline JSON | PASS |
| 8 | validate_file() loads YAML and validates | PASS |
| 9 | All 11 validators are frozen dataclasses | PASS |
| 10 | Tests pass (99/99) | PASS |

## Key Links

| From | To | Via | Status |
|------|----|-----|--------|
| governance_validator.py | enum_guard.py | validate_enums() call | VERIFIED |

## Notes

- All 99 tests pass
- Line counts exceed minimums (688 > 300 required, 1355 > 200 required)
- enum_guard.py extended with aliases to support SRC-009 field names
