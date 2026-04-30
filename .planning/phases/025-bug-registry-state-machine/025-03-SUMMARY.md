---
phase: 025-bug-registry-state-machine
plan: "03"
subsystem: cli/lib
tags: [bug-registry, integration, callback-injection, test-orchestrator]
dependency_graph:
  requires:
    - "01 (bug_registry.py with sync_bugs_to_registry)"
    - "02 (bug_phase_generator.py)"
  provides:
    - on_complete callback in run_spec_test()
    - upgraded build_bug_bundle() with gap_type and MD5 hash
    - wired sync_bugs_to_registry in command.py
  affects:
    - cli/lib/test_orchestrator.py
    - cli/lib/test_exec_reporting.py
    - cli/commands/skill/command.py
tech_stack:
  added: []
  patterns:
    - callback-injection
    - immutable-return
    - atomic-write
key_files:
  created: []
  modified:
    - cli/lib/test_orchestrator.py
    - cli/lib/test_exec_reporting.py
    - cli/commands/skill/command.py
decisions:
  - "D-05 verified: test_orchestrator.py has zero imports from bug_registry"
  - "D-06 verified: MD5-6char hash with case_id+run_id+title as input"
  - "D-04 verified: on_complete callback parameter with default None (backward compatible)"
metrics:
  duration: "manual execution"
  completed: "2026-04-29"
  tasks: 3
  files_modified: 3
---

# Phase 025 Plan 03: Wire Bug Registry into Test Execution Chain

## One-Liner

Callback injection wiring: `on_complete` parameter added to `run_spec_test()`, `build_bug_bundle()` upgraded with gap_type and MD5 hash, `sync_bugs_to_registry` passed as callback in all 3 `run_spec_test` call sites in command.py.

## Tasks Executed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add on_complete callback to run_spec_test() | 6936565 | cli/lib/test_orchestrator.py |
| 2 | Upgrade build_bug_bundle() for gap_type and MD5 hash | adb0cec | cli/lib/test_exec_reporting.py |
| 3 | Wire sync_bugs_to_registry as callback in command.py | f218d2e | cli/commands/skill/command.py |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

- `python -c "from cli.lib.test_orchestrator import run_spec_test"` -- PASS
- `python -c "from cli.lib.test_exec_reporting import build_bug_bundle"` -- PASS
- `grep -c "on_complete=sync_bugs_to_registry" command.py` -- returns 3 (all call sites)
- `grep bug_registry test_orchestrator.py` -- returns 0 (D-05 decoupling verified)
- `on_complete` parameter present in `run_spec_test()` signature
- Callback invoked after `update_manifest()`, before `StepResult` return

## Key Design Decisions Implemented

### Callback Injection Pattern (D-04, D-05)
- `run_spec_test()` accepts optional `on_complete: Callable[..., None] | None = None`
- Callback invoked after `update_manifest()` with `(workspace_root, feat_ref, proto_ref, run_id, case_results)`
- `test_orchestrator.py` has zero imports from `bug_registry` -- dependency inverted
- `command.py` imports `sync_bugs_to_registry` and passes it as callback at all 3 call sites

### build_bug_bundle() Upgrade (D-06)
- Added optional `run_id` parameter (default None, backward compatible)
- Hash switched from SHA1-10char to MD5-6char uppercase
- Hash input includes `case_id + run_id + title` for diversification
- Bug JSON now includes: `status: "detected"`, `gap_type`, `diagnostics` (capped at 5), `run_id`

### gap_type Inference (D-11, D-12)
- New `_infer_gap_type()` private helper in test_exec_reporting.py
- Keywords: timeout, connection reset, flaky, intermittent -> `env_issue`
- Default: `code_defect`
- No direct import of bug_registry keeps test_exec_reporting decoupled

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: Tampering | test_orchestrator.py | case_results passed to callback could be mitigated by sync_bugs_to_registry building NEW dicts (immutable pattern) |
| threat_flag: Information Disclosure | test_orchestrator.py | case_results contain execution evidence paths -- same trust boundary as existing test execution |

## Self-Check: PASSED
