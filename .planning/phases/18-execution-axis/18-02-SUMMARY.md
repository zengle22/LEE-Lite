---
phase: "18"
plan: "02"
subsystem: execution-axis
tags:
  - scenario-compilation
  - e2e-journey-spec
  - A/B/C-layer
  - C_MISSING
dependency-graph:
  requires: []
  provides:
    - cli/lib/scenario_spec_compile.py
  affects:
    - tests/cli/lib/test_scenario_spec_compile.py
tech-stack:
  added:
    - dataclasses
    - yaml
  patterns:
    - A/B/C layer separation
    - keyword-based extraction
    - evidence collection
key-files:
  created:
    - path: cli/lib/scenario_spec_compile.py
      lines: 304
      purpose: E2E spec to scenario spec compiler with A/B/C layer separation
    - path: tests/cli/lib/test_scenario_spec_compile.py
      lines: 320
      purpose: Unit tests for scenario_spec_compile.py (30 tests)
decisions:
  - id: D-03
    description: C-layer assertions MUST be marked C_MISSING
  - id: D-04
    description: C_MISSING placeholders MUST collect HAR + screenshot evidence
metrics:
  duration: "00:03:00"
  completed: "2026-04-24T00:00:00Z"
  tasks: 2
  files: 2
  tests: 30
  commits: 1
---

# Phase 18 Plan 02: Scenario Spec Compile Summary

## One-liner

Scenario spec compiler with A/B/C layer separation, C_MISSING placeholders with HAR + screenshot evidence collection.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create scenario_spec_compile.py with A/B/C layer separation | 92e7f48 | cli/lib/scenario_spec_compile.py |
| 2 | Create unit tests for scenario_spec_compile.py | 92e7f48 | tests/cli/lib/test_scenario_spec_compile.py |

## Success Criteria

- [x] A-layer assertions extracted from Expected UI States section
- [x] B-layer assertions extracted with fallback handling
- [x] C-layer assertions marked C_MISSING with HAR + screenshot evidence
- [x] scenario_spec_to_yaml() produces valid YAML
- [x] All unit tests pass (30/30)
- [x] C_MISSING placeholders have evidence_required=["har", "screenshot"]

## Key Implementation Details

### Dataclasses Created

- `ALayerAssertion`: UI state assertions with description and source_step
- `BLayerAssertion`: Network/API assertions with fallback handling
- `CLayerAssertion`: Business state assertions marked C_MISSING
- `ScenarioStep`: Single step in a scenario
- `ScenarioAssertions`: Container for A/B/C layer assertions
- `ScenarioSpec`: Compiled scenario spec with all layers

### Layer Extraction Logic

**A-Layer (UI State)**:
- Keywords: "visible", "显示", "show", "display", "text", "contain", "have", "element"

**B-Layer (Network/API)**:
- Keywords: "api", "network", "request", "response", "http", "/api/"
- Fallback assertion added when no explicit network assertion found

**C-Layer (Business State)**:
- Keywords: "persistence", "persist", "database", "db", "backend", "server"
- Marked as `C_MISSING` with evidence_required=["har", "screenshot"]

### Functions Implemented

- `compile_scenario_spec()`: Main compilation function
- `compile_e2e_spec_file()`: Compile single e2e spec file
- `compile_scenario_spec_batch()`: Batch compilation
- `scenario_spec_to_yaml()`: YAML serialization
- `write_scenario_spec()`: Write to file

## Deviations from Plan

None - plan executed exactly as written.

## Commits

- **92e7f48**: feat(18-02): add scenario_spec_compile.py with A/B/C layer separation

## Self-Check: PASSED

- [x] cli/lib/scenario_spec_compile.py exists (304 lines)
- [x] tests/cli/lib/test_scenario_spec_compile.py exists (320 lines)
- [x] Commit 92e7f48 found
- [x] 30 unit tests pass
- [x] C_MISSING structure verified
