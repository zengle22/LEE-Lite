---
phase: 025-bug-registry-state-machine
plan: "01"
subsystem: bug-registry
tags: [state-machine, yaml-persistence, bug-lifecycle, tdd]
dependency_graph:
  requires: [frz_registry.py, errors.py, fs.py]
  provides: [bug_registry.py, BUG_STATE_TRANSITIONS, transition_bug_status, sync_bugs_to_registry]
  affects: [test_orchestrator.py, test_exec_reporting.py, command.py]
tech_stack:
  added: []
  patterns:
    - yaml-atomic-write (tempfile + os.replace from frz_registry.py)
    - dict-based-state-machine (BUG_STATE_TRANSITIONS)
    - optimistic-lock (UUID version field)
    - callback-injection (on_complete for test_orchestrator)
key_files:
  created:
    - cli/lib/bug_registry.py (306 lines)
    - cli/lib/test_bug_registry.py (335 lines)
  modified: []
decisions: []
metrics:
  duration: "TBD"
  completed: "2026-04-29"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 2
  tests_added: 15
  tests_passing: 15
---

# Phase 25 Plan 01: Bug Registry State Machine Summary

Implement bug_registry.py core module with independent state machine, YAML persistence, and CRUD operations.

## Deviations from Plan

**1. [Rule 1 - Bug] Fixed test_bug_id_format assertion**
- **Found during:** GREEN phase test run
- **Issue:** Test asserted `parts[1] == "api"` but case_id `"api.job.gen.fail"` is a single dash-separated segment: `parts[1]` is `"api.job.gen.fail"`, not `"api"`
- **Fix:** Changed assertion to `bug_id.startswith("BUG-api.job.gen.fail-")` and `rsplit("-", 1)[-1]` for hash extraction
- **Files modified:** `cli/lib/test_bug_registry.py`
- **Commit:** part of 4719a0d

**2. [Plan deviation] Combined RED commit includes stub**
- The plan specified creating the test file for RED commit. Since the test file imports from bug_registry.py, a stub module was created alongside to make the import succeed. This is standard TDD practice.

## Deviations from Plan

None beyond the test assertion fix above. The plan executed as designed — TDD cycle completed with all 15 tests passing.

## Auth Gates

None encountered.

## Known Stubs

None — all functions are fully implemented.

## Threat Flags

No new threat surface introduced beyond what the plan's threat_model documents. Module reads/writes only to `artifacts/bugs/{feat_ref}/bug-registry.yaml` within the workspace.

## Self-Check: PASSED

- [x] `cli/lib/bug_registry.py` exists (306 lines, min 180)
- [x] `cli/lib/test_bug_registry.py` exists (335 lines, min 200)
- [x] Commit 4719a0d exists (RED)
- [x] Commit 288953e exists (GREEN)
- [x] All 15 tests pass
- [x] `tempfile.mkstemp` present in bug_registry.py
- [x] `os.replace` present in bug_registry.py
- [x] `state_machine_executor` NOT present in bug_registry.py
- [x] `CommandError` raised on invalid transitions
- [x] `from cli.lib.errors import CommandError` present
- [x] `@pytest.mark.unit` on all test functions
- [x] 10 states in BUG_STATE_TRANSITIONS
- [x] Exports: BUG_STATE_TRANSITIONS, transition_bug_status, load_or_create_registry, sync_bugs_to_registry, check_not_reproducible, _infer_gap_type
