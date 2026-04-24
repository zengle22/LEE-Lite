---
phase: "17-chain-entrypoint"
plan: "02"
subsystem: "testing"
tags: ["spec-adapter", "spec-to-testset", "environment-provision", "bridge-layer"]

# Dependency graph
requires: []
provides:
  - "StepResult dataclass for test_orchestrator step data transfer"
  - "EnvConfig dataclass for test execution environment config"
  - "spec_adapter.py converting API/E2E specs to SPEC_ADAPTER_COMPAT YAML"
  - "environment_provision.py generating ENV YAML files"
affects: ["18-execution-axis", "test_orchestrator", "test_exec_runtime"]

# Tech tracking
tech-stack:
  added: []
  patterns: ["SPEC_ADAPTER_COMPAT bridge format", "target_format selector resolution"]

key-files:
  created:
    - "cli/lib/contracts.py"
    - "cli/lib/spec_adapter.py"
    - "cli/lib/environment_provision.py"
  modified: []

key-decisions:
  - "SPEC_ADAPTER_COMPAT is the bridge format between ADR-047 spec files and test_exec_runtime"
  - "target_format resolution supports css_selector/xpath/semantic/text per ADR-054 R-2"
  - "Environment provision supports app_url/api_url separation per ADR-054 R-3"

patterns-established:
  - "StepResult dataclass: internal DTO for test_orchestrator step data transfer (not exposed to AI agents)"
  - "EnvConfig dataclass: environment configuration consumed by test_exec_runtime"

requirements-completed: [BRIDGE-01, BRIDGE-02, BRIDGE-03, BRIDGE-04, BRIDGE-06, ENV-01, ENV-02]

# Metrics
duration: 5min
completed: 2026-04-24
---

# Phase 17-chain-entrypoint Plan 02 Summary

**StepResult and EnvConfig dataclasses define test orchestrator contracts; spec_adapter.py bridges ADR-047 specs to SPEC_ADAPTER_COMPAT; environment_provision.py generates ENV YAML files with app-url/api-url separation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-24T11:32:39Z
- **Completed:** 2026-04-24T11:37:00Z
- **Tasks:** 3
- **Files created:** 3

## Accomplishments
- StepResult dataclass with run_id, execution_refs, candidate_path, case_results, manifest_items, execution_output_dir for test_orchestrator step data transfer
- EnvConfig dataclass with feat_ref, proto_ref, modality, base_url, app_url, api_url, browser, timeout, feat_assumptions
- spec_adapter.py parses api-test-spec/*.md and e2e-journey-spec/*.md, adds _source_coverage_id and _api_extension/_e2e_extension, outputs SPEC_ADAPTER_COMPAT YAML
- target_format resolution (css_selector/xpath/semantic/text) implemented
- environment_provision.py generates ssot/environments/ENV-{id}.yaml with app_base_url/api_base_url separation
- Creates ssot/environments/ directory with .gitkeep (ENV-02)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create cli/lib/contracts.py with StepResult dataclass** - `8984d30` (feat)
2. **Task 2: Create cli/lib/spec_adapter.py** - `670b9d5` (feat)
3. **Task 3: Create cli/lib/environment_provision.py** - `4461471` (feat)

## Files Created/Modified

- `cli/lib/contracts.py` - StepResult and EnvConfig dataclasses for test orchestration data transfer
- `cli/lib/spec_adapter.py` - SPEC_ADAPTER_COMPAT bridge: parses API/E2E spec markdown files, maps to TESTSET unit format, adds traceability extensions
- `cli/lib/environment_provision.py` - ENV YAML generator with app-url/api-url separation support

## Decisions Made

- SPEC_ADAPTER_COMPAT format uses ssot_type field to trigger test_exec_runtime compatibility branch
- API spec units carry _source_coverage_id and _api_extension for manifest traceability (ADR-054 R-1, R-6)
- E2E spec units carry _source_coverage_id and _e2e_extension with ui_step_metadata (ADR-054 R-1, R-8)
- feat_assumptions parsing uses '=' delimiter first to handle URLs with ports correctly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. [Bug] _merge_assumptions URL parsing failure**
- **Found during:** Task 3 (environment_provision.py functional test)
- **Issue:** feat_assumptions with URLs like 'base_url=http://localhost:8000' were incorrectly parsed because partition(":") split on the port colon
- **Fix:** Changed delimiter check order to test "=" first (since URLs contain ":" but not "="), then use ":" only for simple key:value pairs
- **Files modified:** cli/lib/environment_provision.py (_merge_assumptions function)
- **Verification:** Re-ran functional test confirming URL values parsed correctly
- **Committed in:** `4461471` (same commit as Task 3)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Bug fix necessary for correct URL parsing in feat_assumptions. No scope impact.

## Next Phase Readiness

- spec_adapter.py ready for integration with test_orchestrator (Phase 18)
- environment_provision.py ready for integration with test_orchestrator (Phase 18)
- contracts.py StepResult/EnvConfig ready for test_orchestrator consumption
- test_exec_runtime.py SPEC_ADAPTER_COMPAT compatibility branch still needs implementation (ADR-054 §2.4)

---
*Phase: 17-chain-entrypoint-02*
*Completed: 2026-04-24*

## Self-Check: PASSED

- All Python imports successful (contracts, spec_adapter, environment_provision)
- All files exist on disk
- All commits verified in git history
