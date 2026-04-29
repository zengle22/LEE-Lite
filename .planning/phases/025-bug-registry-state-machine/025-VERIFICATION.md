---
phase: 025-bug-registry-state-machine
verified: 2026-04-29T14:30:00Z
status: gaps_found
score: 6/7 must-haves verified
overrides_applied: 0
gaps:
  - truth: "gap_type auto-inference returns test_defect when stack trace points to test code"
    status: partial
    reason: "_infer_gap_type() in bug_registry.py (line 128-135) and test_exec_reporting.py (line 174-180) only handle env_issue (keyword match) and code_defect (default). The test_defect path described in D-12 ('stack trace in test code -> test_defect') is not implemented. The function never returns test_defect."
    artifacts:
      - path: "cli/lib/bug_registry.py"
        issue: "_infer_gap_type() has no test_defect detection logic (lines 128-135)"
      - path: "cli/lib/test_exec_reporting.py"
        issue: "_infer_gap_type() has no test_defect detection logic (lines 174-180)"
    missing:
      - "Add test_defect detection: check if stderr_ref or diagnostics contain paths in tests/ directory"
      - "Add test case verifying _infer_gap_type returns 'test_defect' for test-code stack traces"
deferred:  # Items addressed in later phases -- not actionable gaps
  - truth: "detected bugs downgrade to archived after gate PASS and auto-transition to not_reproducible after N strikes"
    addressed_in: "Phase 26"
    evidence: "GATE-REM-01/02 in Phase 26 success criteria handle detected->archived and strike counting"
  - truth: "Severity auto-classification per ADR-055 §5.1 with manual override via CLI"
    addressed_in: "Phase 27"
    evidence: "CLI-01 in Phase 27 includes --severity override; D-10 says '人工覆盖' is Phase 27 scope"
---

# Phase 025: Bug Registry & State Machine Verification Report

**Phase Goal:** Bug registry with YAML-backed state machine, CRUD operations, phase generation, and test-orchestrator integration via callback injection.
**Verified:** 2026-04-29T14:30:00Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | bug_registry.py exists as a module with YAML-backed CRUD and state machine | VERIFIED | 306 lines, exports all required symbols, YAML persistence with atomic write |
| 2 | State machine enforces 10 valid states with correct transition rules | VERIFIED | BUG_STATE_TRANSITIONS has 10 states, tests verify happy path (detected->closed), invalid transitions raise CommandError, wont_fix/duplicate from any non-terminal |
| 3 | Terminal states (wont_fix, duplicate, not_reproducible) enforce field requirements | VERIFIED | wont_fix requires reason (test_wont_fix_requires_reason passes), duplicate requires duplicate_of (test_duplicate_requires_duplicate_of passes), not_reproducible thresholds: unit=3/integration=4/e2e=5 |
| 4 | YAML persistence uses atomic write (tempfile + os.replace) from frz_registry pattern | VERIFIED | _save_registry at line 85-105 uses tempfile.mkstemp + os.replace, verbatim pattern from frz_registry.py |
| 5 | Generator creates .planning/phases/{N}-bug-fix-{bug_id}/ directory with 4 files, PLAN.md has 6 tasks and autonomous: false | VERIFIED | test_phase_dir_structure passes, test_plan_md_contains_6_tasks passes, autonomous: false in PLAN.md frontmatter |
| 6 | run_spec_test() accepts on_complete callback without importing bug_registry; command.py wires sync_bugs_to_registry at all 3 call sites | VERIFIED | on_complete parameter present with default None, 0 grep hits for bug_registry in test_orchestrator.py, 3 occurrences of on_complete=sync_bugs_to_registry in command.py |
| 7 | gap_type auto-inference returns test_defect when stack trace points to test code | FAILED | _infer_gap_type() only handles env_issue (keyword match) and code_defect (default). test_defect path from D-12 is not implemented in either bug_registry.py or test_exec_reporting.py |

**Score:** 6/7 must-haves verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | detected bugs downgrade to archived after gate PASS, auto-transition to not_reproducible after N strikes | Phase 26 | GATE-REM-01/02 success criteria: gate FAIL handling, detected->open promotion |
| 2 | Severity auto-classification per ADR-055 §5.1 with CLI override | Phase 27 | CLI-01 includes `--severity` override; D-10 says manual override is Phase 27 scope |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cli/lib/bug_registry.py` | Bug registry CRUD + state machine + YAML persistence, min 180 lines | VERIFIED | 306 lines, exports: BUG_STATE_TRANSITIONS, transition_bug_status, load_or_create_registry, sync_bugs_to_registry, check_not_reproducible, _infer_gap_type |
| `cli/lib/test_bug_registry.py` | Unit tests for bug_registry state machine and persistence, min 200 lines | VERIFIED | 335 lines, 15 test functions, all @pytest.mark.unit, all passing |
| `cli/lib/bug_phase_generator.py` | Phase directory generation for bug fix workflows, min 100 lines | VERIFIED | 190 lines, exports: generate_bug_phase, generate_batch_phase |
| `cli/lib/test_bug_phase_generator.py` | Unit tests for phase generator, min 60 lines | VERIFIED | 105 lines, 5 test functions, all @pytest.mark.unit, all passing |
| `cli/lib/test_orchestrator.py` | on_complete callback parameter in run_spec_test() | VERIFIED | on_complete: Callable[..., None] | None = None at line 165, invoked at line 302-303 |
| `cli/lib/test_exec_reporting.py` | Upgraded build_bug_bundle() with gap_type and MD5 hash | VERIFIED | _infer_gap_type() at line 174, gap_type in bug JSON at line 205, MD5 hash at line 190, run_id parameter at line 183 |
| `cli/commands/skill/command.py` | Wired sync_bugs_to_registry as on_complete callback | VERIFIED | Import at line 143, 3 call sites at lines 168, 181, 217 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli/lib/bug_registry.py` | `cli/lib/frz_registry.py` | copies atomic write pattern | VERIFIED | tempfile.mkstemp at line 95, os.replace at line 99, yaml.dump wrapping {"bug_registry": registry} at line 88 |
| `cli/lib/bug_registry.py` | `cli/lib/errors.py` | raises CommandError on invalid transitions | VERIFIED | from cli.lib.errors import CommandError at line 18, raise CommandError at lines 211, 218, 223 |
| `cli/lib/test_orchestrator.py` | `on_complete` callback | if on_complete is not None: on_complete(...) | VERIFIED | Guard at line 302, invocation at line 303 with (workspace_root, feat_ref, proto_ref, run_id, case_results) |
| `cli/commands/skill/command.py` | `cli/lib/bug_registry.py` | imports sync_bugs_to_registry and passes as callback | VERIFIED | from cli.lib.bug_registry import sync_bugs_to_registry at line 143, 3 callback injections |
| `cli/lib/test_orchestrator.py` | `cli/lib/bug_registry.py` | NO direct import -- decoupled per D-05 | VERIFIED | grep for "bug_registry" in test_orchestrator.py returns 0 hits |
| `cli/lib/bug_phase_generator.py` | `.planning/phases/` | mkdir + write_text to create phase directories | VERIFIED | mkdir at line 141/175, write_text calls at lines 143-146/177-180 |
| `cli/lib/bug_phase_generator.py` | `cli/lib/fs.py` | uses write_text for file creation | VERIFIED | from cli.lib.fs import write_text at line 10 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `cli/lib/bug_registry.py` | registry["bugs"] | sync_bugs_to_registry builds from case_results | Yes -- _build_bug_record creates full schema dicts from real case data | FLOWING |
| `cli/lib/test_exec_reporting.py` | bug JSON | build_bug_bundle iterates case_results | Yes -- filters failed cases, builds real bug dicts with gap_type, diagnostics | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| bug_registry exports all required symbols | `python -c "from cli.lib.bug_registry import BUG_STATE_TRANSITIONS, transition_bug_status, load_or_create_registry, sync_bugs_to_registry, check_not_reproducible, _infer_gap_type"` | "States: 10, All exports OK" | PASS |
| bug_phase_generator exports | `python -c "from cli.lib.bug_phase_generator import generate_bug_phase, generate_batch_phase"` | "Phase generator exports OK" | PASS |
| on_complete parameter present | `python -c "import inspect; from cli.lib.test_orchestrator import run_spec_test; ..."` | "on_complete default: None, on_complete param: PRESENT" | PASS |
| test_orchestrator decoupled from bug_registry | `grep -c "bug_registry" cli/lib/test_orchestrator.py` | 0 | PASS |
| command.py has 3 callback wirings | `grep -c "on_complete=sync_bugs_to_registry" cli/commands/skill/command.py` | 3 | PASS |
| bug_registry independent from state_machine_executor | `grep -c "state_machine_executor" cli/lib/bug_registry.py` | 0 | PASS |
| All 20 unit tests pass | `pytest cli/lib/test_bug_registry.py cli/lib/test_bug_phase_generator.py -x -v` | 20 passed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| BUG-REG-01 | 025-01 | Bug registry CRUD with optimistic locking | SATISFIED | load_or_create_registry, _load_registry, _save_registry implemented; version UUID field present; YAML at artifacts/bugs/{feat_ref}/bug-registry.yaml |
| BUG-REG-02 | 025-01 | State machine: detected->open->fixing->fixed->re_verify_passed->closed | SATISFIED | BUG_STATE_TRANSITIONS has 10 states; test_happy_path_transitions covers full happy path; invalid transitions raise CommandError |
| BUG-REG-03 | 025-01 | Terminal states with field requirements + resurrection | SATISFIED | wont_fix needs reason, duplicate needs duplicate_of, not_reproducible thresholds (3/4/5); test_resurrection_new_record passes |
| BUG-PHASE-01 | 025-02 | Phase generator creates directory with 4 files + 6-task PLAN.md | SATISFIED | generate_bug_phase creates CONTEXT.md, PLAN.md, DISCUSSION-LOG.md, SUMMARY.md; PLAN.md has all 6 task names |
| BUG-PHASE-02 | 025-02 | Mini-batch mode (max 3 same-feat same-module bugs) | SATISFIED | generate_batch_phase enforces max 3 bugs, raises CommandError on overflow; test_batch_max_3 and test_batch_creates_single_dir pass |
| BUG-INTEG-01 | 025-03 | build_bug_bundle() with gap_type, status, MD5-based bug_id | SATISFIED | build_bug_bundle has gap_type field, status:"detected", MD5-6char hash, diagnostics capped at 5; _infer_gap_type helper present |
| BUG-INTEG-02 | 025-03 | sync_bugs_to_registry() persists to YAML | SATISFIED | sync_bugs_to_registry implemented at line 264; called as on_complete callback; test_sync_persists and test_resurrection_new_record pass |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `cli/lib/bug_phase_generator.py` | 116, 121 | "placeholder" in docstrings | INFO | Intentional -- DISCUSSION-LOG.md and SUMMARY.md are empty placeholders per ADR-055 design. Not functional stubs. |

**No TODO, FIXME, HACK, or stub patterns found** in any implementation file.

### Decisions Honored (D-01 through D-15)

| Decision | Description | Status | Evidence |
|----------|-------------|--------|----------|
| D-01 | Independent state machine, not reusing state_machine_executor.py | HONORED | 0 grep hits for state_machine_executor in bug_registry.py |
| D-02 | BUG_STATE_TRANSITIONS dict + transition_bug_status() | HONORED | Dict at line 24, function at line 192 |
| D-03 | YAML persistence reusing frz_registry.py atomic write | HONORED | tempfile.mkstemp + os.replace at lines 95-99 |
| D-04 | run_spec_test() gets on_complete=None callback | HONORED | Parameter at line 165 of test_orchestrator.py |
| D-05 | sync_bugs_to_registry() as callback, test_orchestrator doesn't import bug_registry | HONORED | 0 bug_registry imports in test_orchestrator.py |
| D-06 | bug_id format: BUG-{case_id}-{md5_hash_6char} | HONORED | MD5[:6].upper() at line 151, format at line 152 |
| D-07 | Same case different failure = new bug_id with resurrected_from | HONORED | test_resurrection_new_record passes; sync logic at lines 283-298 |
| D-08 | not_reproducible thresholds: Unit=3, Integration=4, E2E=5 | HONORED | NOT_REPRODUCIBLE_THRESHOLDS at line 37-41, verified by test_not_reproducible_thresholds |
| D-09 | Gate PASS -> archived, 3-strike -> not_reproducible | DEFERRED | Logic belongs to Phase 26 (GATE-REM-01/02). Terminal states and thresholds exist, gate integration is Phase 26. |
| D-10 | Severity auto-inference + manual CLI override | PARTIAL | Default "medium" in _build_bug_record (line 163). CLI override deferred to Phase 27 (CLI-01). |
| D-11 | gap_type: code_defect / test_defect / env_issue | PARTIAL | _infer_gap_type returns env_issue or code_defect only. test_defect path not implemented. |
| D-12 | Inference rules: flaky->env_issue, test stack->test_defect, default->code_defect | PARTIAL | env_issue and code_defect paths implemented. test_defect path (stack trace in test code) missing. |
| D-13 | Single bug single phase, --batch max 2-3 | HONORED | generate_batch_phase enforces max 3; test_batch_max_3 passes |
| D-14 | Generated dir: CONTEXT.md + PLAN.md (6 tasks) + DISCUSSION-LOG.md + SUMMARY.md | HONORED | All 4 files generated; PLAN.md has 6 task names; verified by test_phase_dir_structure and test_plan_md_contains_6_tasks |
| D-15 | All generated PLAN.md marked autonomous: false | HONORED | autonomous: false in _build_plan_md frontmatter at line 107 |

### Human Verification Required

None. All checks are programmatically verifiable.

### Gaps Summary

**1 gap found:**

The `_infer_gap_type()` function in both `bug_registry.py` and `test_exec_reporting.py` is missing the `test_defect` detection path. Per D-12, the inference rules should be:
- flaky/timeout/connection reset/intermittent keywords -> `env_issue` (IMPLEMENTED)
- stack trace in test code -> `test_defect` (NOT IMPLEMENTED)
- default -> `code_defect` (IMPLEMENTED)

The function never returns `test_defect`. The test assertion at `test_bug_registry.py:256` lists `test_defect` as a valid gap_type, but no test exercises this path. To close this gap:
1. Add test file path detection to `_infer_gap_type()` -- check if `stderr_ref` or `diagnostics` contain paths under `tests/` or `test_` prefixed files
2. Add a unit test case verifying `test_defect` is returned when diagnostics reference a test file path

---

_Verified: 2026-04-29T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
