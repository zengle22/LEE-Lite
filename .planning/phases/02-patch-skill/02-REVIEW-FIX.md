---
phase: 02-patch-skill
fixed_at: 2026-04-16T00:30:00Z
review_path: .planning/phases/02-patch-skill/02-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-04-16T00:30:00Z
**Source review:** .planning/phases/02-patch-skill/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9
- Fixed: 9
- Skipped: 0

## Fixed Issues

### CR-01: Dead error-handling in validate_output.sh

**Files modified:** `skills/ll-patch-capture/scripts/validate_output.sh`
**Commit:** 06ab833
**Applied fix:** Replaced the unreachable `$?` check with `if !` wrapper around the `python -m cli.lib.patch_schema` command. Under `set -euo pipefail`, the original check was dead code because a non-zero exit would terminate the script immediately. Now the error message is properly displayed.

### CR-02: Missing FEAT_ID validation in run.sh

**Files modified:** `skills/ll-patch-capture/scripts/run.sh`
**Commit:** 578c6fd
**Applied fix:** Added regex validation (`^[a-zA-Z0-9][a-zA-Z0-9._-]*$`) before FEAT_ID is used in filesystem operations. Prevents path traversal attacks (e.g., `../../../tmp/evil`) when run.sh is called directly, bypassing the Python CLI.

### WR-01: test_impact escalation check compares dict to strings

**Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
**Commit:** 62d8bd2
**Applied fix:** Changed the escalation check from comparing `test_impact` (a dict) against string literals to checking `is not None and not isinstance(ti, dict)`. The original check always triggered because a dict never equals any of the string values.

### WR-02: Race condition in get_next_patch_id

**Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
**Commit:** 0216e17 (updated from 62d8bd2)
**Applied fix:** Added `fcntl.flock()` shared/exclusive locking around the registry read in `get_next_patch_id`. Wrapped in try/except `ImportError` for Windows compatibility where `fcntl` is unavailable.

### WR-03: sys.path manipulation not thread-safe

**Files modified:** `cli/commands/skill/command.py`
**Commit:** 02a73d7
**Applied fix:** Replaced `sys.path.insert` / `from ... import` / `sys.path.remove` pattern with `importlib.util.spec_from_file_location()` for isolated dynamic module loading. Eliminates thread-safety issues from global `sys.path` mutation.

### WR-04: Unhandled JSONDecodeError

**Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
**Commit:** 62d8bd2
**Applied fix:** Wrapped `json.load()` in `register_patch_in_registry` with try/except `json.JSONDecodeError`, calling `ensure(False, "INVALID_REQUEST", ...)` for graceful error handling instead of crashing mid-operation.

### WR-05: Executor writes "active" but escalation expects "draft"

**Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
**Commit:** 62d8bd2
**Applied fix:** When escalation is triggered, the runtime now sets `patch["status"] = "draft"` and writes the updated YAML file before setting `registered = False`. This prevents inconsistent state where the file says "active" but the registry has no entry.

### WR-06: Missing conflict-triggered escalation test coverage

**Files modified:** `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py`
**Commit:** 2237f64
**Applied fix:** Added `test_escalation_conflicting_files` test that pre-seeds an active patch with overlapping `changed_files`, creates a new patch with conflicting files, and asserts that `run_skill` returns `escalation_needed: True`, `registered: False`, and populates the `conflicts` array. All 25 tests pass.

### WR-07: Redundant conditional import

**Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
**Commit:** 62d8bd2
**Applied fix:** Removed the redundant `from cli.lib.errors import ensure as _ensure` inside the `except ValueError` block and replaced `_ensure(...)` with the top-level `ensure(...)` which was already imported at module level.

## Skipped Issues

None — all findings were fixed.

---

_Fixed: 2026-04-16T00:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
