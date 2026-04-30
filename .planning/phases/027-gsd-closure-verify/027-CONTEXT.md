# Phase 27: GSD 闭环验证 (GSD Closure Verification)

## Goal

Complete the bug lifecycle loop: verify fixes, auto-close bugs with 2 conditions, provide CLI tools, detect shadow fixes, audit all transitions, and end-to-end integration test.

**Depends on**: Phase 25 (Bug Registry), Phase 26 (Gate Integration) - both already completed!

## Requirements Traceability

| Req ID | Description | Status |
|--------|-------------|--------|
| VERIFY-01 | `--verify-bugs` targeted mode (default: run only status=fixed bug tests | Planned |
| VERIFY-02 | `--verify-mode=full-suite` for regression detection | Planned |
| VERIFY-03 | Post-verify state transitions: targeted pass → re_verify_passed, fail → open | Planned |
| VERIFY-04 | 2-condition auto-close + notifications | Planned |
| CLI-01 | `ll-bug-transition` command | Planned |
| CLI-02 | `ll-bug-remediate` command | Planned |
| SHADOW-01 | Shadow Fix Detection (CLI + auto-check) | Planned |
| AUDIT-01 | Audit log for ALL state changes | Planned |
| INTEG-TEST-01 | Integration test for full loop | Planned |

## Decisions Made & Locked

### 1. **VERIFY: Flag to qa-test-run**
* Decision: Add `--verify-bugs` (boolean) and `--verify-mode` (targeted|full-suite) flags to existing `qa-test-run` action in `command.py`
* Rationale: Reuses existing test orchestration infrastructure, keeps all test execution in one place
* Implementation: Extend `run_spec_test()` in `test_orchestrator.py` to accept and handle these flags

### 2. **AUDIT: Centralized in transition_bug_status()**
* Decision: Move audit logging to `transition_bug_status()` in `bug_registry.py`
* Rationale: Single source of truth for all state transitions, ensures no audit log is complete
* Implementation:
  - Move `_write_audit_log()` from `gate_remediation.py` to `bug_registry.py`
  - Call it automatically from `transition_bug_status()`
  - Update gate_remediation.py to remove duplicate audit calls

### 3. **SHADOW: CLI + auto-check**
* Decision: Implement both CLI command and automatic checks in existing commands
* Rationale: Flexible - users can run manually, and automatic checks provide safety net
* Implementation:
  - Add `ll-bug-check-shadow` action in `command.py`
  - Auto-check in relevant places (like before gate-evaluate)

## Implementation Plan (Modules to Create/Update)

### Part 1: `bug_registry.py Enhancements
* **Update `transition_bug_status()`**:
  - Call audit logging automatically
  - Add optional `run_id` and `actor` parameters
  - Update `fixed_at`, `verified_at`, `closed_at` timestamps when entering those states

* **Add helper functions**:
  - `get_fixed_bugs(workspace_root, feat_ref)`: Get all `status=fixed` bugs
  - `get_bugs_by_coverage_ids(bugs, coverage_ids)`: Map coverage_ids → bugs
  - `transition_after_verify(bug, passed, run_id)`: Handle fixed → re_verify_passed|open

* **Add `fix_commit` field setter helper**:
  - When setting `fixed` status, allow setting `fix_commit`

### Part 2: `test_orchestrator.py` Enhancements (VERIFY-01, VERIFY-02, VERIFY-03)
* **Add to `run_spec_test()` parameters**:
  - `verify_bugs: bool = False`
  - `verify_mode: str = "targeted"`

* **Add helper**:
  - `_filter_test_units_by_fixed_bugs(workspace_root, feat_ref, proto_ref, test_units)`: Filter to only coverage_ids for fixed bugs

* **Post-execution handling**:
  - After test execution completes, if `verify_bugs=True`, trigger bug state transitions based on results

### Part 3: `command.py` Additions
* **Add `ll-bug-transition` action (CLI-01)**:
  - `--bug-id`: Required
  - `--to`: Target state (wont_fix|duplicate|closed|open|fixing|fixed|re_verify_passed)
  - `--reason`: Required for wont_fix/closed
  - `--duplicate-of`: Required for duplicate
  - Calls `transition_bug_status()` internally

* **Add `ll-bug-remediate` action (CLI-02)**:
  - `--feat-ref`: Required
  - `--bug-id`: Optional (single bug)
  - `--batch`: Optional (mini-batch max 3)
  - Loads registry, shows preview, asks confirmation, calls `bug_phase_generator.py`

* **Add `ll-bug-check-shadow` action (SHADOW-01)**:
  - `--feat-ref`: Required
  - Loads registry, checks git diff against `status=open` bugs' `affected_files`
  - Warns if files modified but bug not in fixing/fixed status

* **Update `qa-test-run` action**:
  - Add `--verify-bugs` flag
  - Add `--verify-mode` flag (targeted|full-suite)

### Part 4: `gate_remediation.py` Cleanup
* Remove duplicate `_write_audit_log()` (moved to bug_registry)
* Simplify `promote_detected_to_open()` and `archive_detected_not_in_gap_list()` to not call audit log directly

### Part 5: `verify_closure.py` (NEW Module? Or part of bug_registry/gate_remediation?)
Wait, better as part of bug_registry or a new `bug_verify.py`?
Actually, let's create `bug_verify.py`:
* `check_auto_close_conditions(bug, test_results_since_fix)`: Checks 2 conditions
* `auto_close_bug(bug, run_id)`: Calls transition + sends notification

### Part 6: `shadow_detect.py` (NEW Module for SHADOW-01)
* `scan_git_diff(workspace_root, since_commit=None)`: Gets modified files from git
* `check_shadow_fixes(workspace_root, feat_ref)`: Compares modified files vs open bugs
* Returns list of potential shadow fixes with warnings

### Part 7: Tests (ALL of the above
* `test_bug_registry_verify.py: Tests for VERIFY functions
* `test_bug_transition_cli.py`: Tests for CLI commands
* `test_shadow_detect.py`: Tests for shadow detection
* `tests/integration/test_bug_closure.py`: End-to-end integration test

## Key Design Patterns to Follow (From Phases 25-26)

1. **Immutability**: Always return new dicts from transition functions, never mutate in place
2. **Atomic Writes**: Use temp file + os.replace for YAML files
3. **Optimistic Locking**: Always increment `version` field with UUID on every change
4. **Decoupling**: Use callbacks where possible; test_orchestrator doesn't import bug_registry directly
5. **Backward Compatibility**: Add optional parameters with defaults
6. **Robustness**: Wrap non-critical operations (notifications, etc.) in try/except
7. **Composability**: Each module has single responsibility

## What's Already Done (From Previous Phases)

✅ `bug_registry.py`: State machine, CRUD, YAML persistence, sync_bugs_to_registry
✅ `bug_phase_generator.py`: Single/batch phase generation
✅ `gate_remediation.py`: promote/archive functions
✅ `push_notifier.py`: Terminal notifications, draft previews, reminders
✅ `test_orchestrator.py`: on_complete callback infrastructure
✅ Contracts: gate-evaluate and settlement contracts already updated
✅ Tests: bug_registry, gate_remediation, push_notifier tests written

## Open Questions Already Resolved (Locked Decisions)

1. **✅ Verify mode: Flag to qa-test-run (not separate command)**
2. **✅ Audit log: Centralized in transition_bug_status()**
3. **✅ Shadow detection: CLI + auto-check**
4. **✅ Auto-close: 2 conditions, notifications**
5. **✅ All transitions already defined in state machine**

## Audit Log Schema

```yaml
# artifacts/bugs/{feat_ref}/audit.log
- timestamp: "2026-04-28T10:00:00Z"
  bug_id: BUG-xxx
  from: detected
  to: open
  actor: system:gate-remediation
  run_id: RUN-xxx
  reason: gate FAIL verdict
```

## Shadow Fix Detection Logic

1. Get list of `status=open` bugs from registry
2. Get list of modified files from git diff (default: since last commit)
3. For each open bug, check if `fix_hypothesis.affected_files` overlap with modified files
4. If overlap exists, warn user:
   "⚠️ Shadow Fix Detected: You modified file X but bug Y is still open. Consider running ll-bug-remediate to track the fix properly."

## 2-Condition Auto-Close Logic

Conditions both need to be true:
1. ✅ `bug.status == re_verify_passed`
2. ✅ No new test failures in affected scope since fix commit was made

If both true:
- Transition bug to `closed`
- Set `closed_at` timestamp
- Show terminal notification
- Optional: Send Slack notification if configured
- Log to audit log with `actor:system:auto-close`

If not, keep `re_verify_passed` status

## CLI Command Structure (command.py)

```python
# New actions added to _skill_handler:
"bug-transition", "bug-remediate", "bug-check-shadow"
```

## Success Criteria (ADR-055 §6 Phase 3)

- [ ] `--verify-bugs` targeted mode works: only runs fixed bug tests
- [ ] `--verify-mode=full-suite` works: runs all tests
- [ ] Post-verify state transitions work correctly
- [ ] Auto-close triggers when 2 conditions met
- [ ] `ll-bug-transition` works for all valid state changes
- [ ] `ll-bug-remediate` creates phases correctly
- [ ] Shadow fix detection finds modified files vs open bugs
- [ ] All state changes are audited
- [ ] End-to-end integration test passes
