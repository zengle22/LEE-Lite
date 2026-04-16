---
phase: "02-patch-skill"
plan: "03"
subsystem: ll-patch-capture
tags: [python-runtime, cli-registration, shell-wrappers, registry-management, conflict-detection]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [REQ-PATCH-02]
  affects: [02-04]
tech-stack:
  added: []
  patterns: [thin-bash-wrapper, python-runtime-module, cli-protocol-invocation, sys-path-injection-cleanup]
key-files:
  created:
    - skills/ll-patch-capture/scripts/patch_capture_runtime.py
    - skills/ll-patch-capture/scripts/run.sh
    - skills/ll-patch-capture/scripts/validate_input.sh
    - skills/ll-patch-capture/scripts/validate_output.sh
  modified:
    - cli/ll.py
    - cli/commands/skill/command.py
decisions:
  - "Runtime is sole patch_registry.json writer — never trust AI-generated source fields (set actor/session/human_confirmed_class programmatically)"
  - "Conflict detection scans UXPATCH-*.yaml files for overlapping changed_files across active patches"
  - "Escalation triggers per D-09: first_patch_for_feat, semantic_patch_requires_src_decision, disputed_test_impact"
  - "Path traversal protection via Path.resolve().relative_to() for both feat_id and document inputs"
metrics:
  duration_minutes: 10
  completed_date: "2026-04-16T08:23:00Z"
  tasks_completed: 3
  files_created: 4
  files_modified: 2
  lines_added: 375
---

# Phase 02 Plan 03: Python Runtime, Shell Scripts & CLI Registration Summary

**One-liner:** Wires ll-patch-capture skill into CLI infrastructure via subparser registration, handler dispatch, Python runtime module (registry management + conflict detection), and thin bash wrapper scripts.

## Objective

Create the Python runtime module, shell wrapper scripts, and CLI registration for the ll-patch-capture skill. This plan wires the skill into the CLI infrastructure so it can be invoked via `python -m cli skill patch-capture`. The runtime handles registry read-modify-write, conflict detection, and dual-path routing logic that the Executor/Supervisor agents coordinate through.

## Tasks Completed

### Task 0: Register patch-capture CLI action in ll.py and command.py

**Commit:** `6433c74`
**Files:** `cli/ll.py`, `cli/commands/skill/command.py`

Two changes:
- **cli/ll.py** — Added "patch-capture" to the skill action tuple in `build_parser()`
- **cli/commands/skill/command.py** — Two changes:
  1. Added "patch-capture" to the `ensure()` action set in `_skill_handler()`
  2. Added explicit if/elif handler block for `ctx.action == "patch-capture"` with:
     - Payload validation (feat_id, input_type, input_value required)
     - Runtime dispatch via `resolve_skill_scripts_dir` and sys.path injection
     - Evidence collection and structured response return

### Task 1: Create Python runtime module (patch_capture_runtime.py)

**Commit:** `6d4a5e9`
**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py` (256 lines)

Created with:
- **run_skill()** — Main entry point with full input validation, security checks, and orchestration
- **get_next_patch_id()** — Sequential UXPATCH-NNNN ID generation from registry or filesystem
- **detect_conflicts()** — Scans active patches for overlapping changed_files
- **register_patch_in_registry()** — JSON registry read-modify-write with slug-based filenames
- **Security**: Path traversal protection for feat_id and document inputs, input size limits, regex validation
- **Escalation logic**: First-patch-for-FEAT, semantic-patch-requires-SRC-decision, disputed-test-impact
- **Trust boundary**: Programmatically sets source.actor/session/human_confirmed_class (never trusts AI-generated values)

### Task 2: Create shell wrapper scripts (run.sh, validate_input.sh, validate_output.sh)

**Commit:** `6d88c82`
**Files:** `skills/ll-patch-capture/scripts/run.sh` (85 lines), `skills/ll-patch-capture/scripts/validate_input.sh` (23 lines), `skills/ll-patch-capture/scripts/validate_output.sh` (11 lines)

- **run.sh**: Thin bash wrapper with argument parsing (--feat-id, --input-type, --input-value), JSON construction via Python (injection-safe), CLI protocol invocation, pre/post validation calls
- **validate_input.sh**: Validates document input is parseable YAML via sys.argv (no string interpolation)
- **validate_output.sh**: Validates output patch YAML via `python -m cli.lib.patch_schema --type patch`

## Decisions Made

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Runtime is sole registry writer | Prevents double-write corruption | Implemented |
| Conflict detection via file scanning | MVP approach — no DB needed | Implemented |
| Escalation triggers per D-09 | Human review for high-risk patches | Implemented |
| Path traversal via relative_to() | Authoritative check for containment | Implemented |
| JSON construction in Python (not bash) | Prevents injection from special chars | Implemented |

## Deviations from Plan

**1. [Rule 2 - Security] Added input size limits**
- **Found during:** Task 1
- **Issue:** Plan did not specify input size limits for input_value — potential DoS vector
- **Fix:** Added `ensure(len(input_value) <= 50000, ...)` and `ensure(len(feat_id) <= 128, ...)`
- **Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
- **Commit:** `6d4a5e9`

**2. [Rule 1 - Bug] Fixed registry_entry parameter**
- **Found during:** Task 1
- **Issue:** Plan passed `patch_data` (nested dict) to `register_patch_in_registry()` but function expected unwrapped patch dict for timestamp assignment
- **Fix:** Changed call from `register_patch_in_registry(feat_dir, patch_data)` to `register_patch_in_registry(feat_dir, patch)` (unwrapped dict)
- **Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
- **Commit:** `6d4a5e9`

**3. [Rule 2 - Security] Added feat_id regex validation**
- **Found during:** Task 1
- **Issue:** Plan relied on path containment check only — missing format validation for feat_id
- **Fix:** Added regex check `^[a-zA-Z0-9][\w.\-]*$` to reject special characters early
- **Files modified:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py`
- **Commit:** `6d4a5e9`

## Known Stubs

None. All runtime files are fully implemented with no placeholder values.

## Threat Flags

All threats from the plan's threat_model are mitigated in implementation:

| Threat ID | Category | Component | Mitigation |
|-----------|----------|-----------|------------|
| T-02-08 | Injection | CLI payload values | `ensure()` validates required fields; input_value stripped and size-limited |
| T-02-09 | Spoofing | Document path | `Path.resolve().relative_to(workspace_root.resolve())` — raises INVALID_REQUEST if escapes workspace |
| T-02-10 | Tampering | Registry R-M-W | Accepted per threat model (single-threaded via Claude Code sessions) |
| T-02-11 | Tampering | Patch YAML | `validate_file()` called BEFORE registry update — invalid patches never registered |

## Commits

- `6433c74`: feat(02-03): register patch-capture CLI action in ll.py and command.py
- `6d4a5e9`: feat(02-03): create Python runtime module for ll-patch-capture skill
- `6d88c82`: feat(02-03): create shell wrapper scripts for ll-patch-capture

## Self-Check

### Created files
- FOUND: cli/ll.py (modified — added "patch-capture" to action tuple)
- FOUND: cli/commands/skill/command.py (modified — added handler dispatch)
- FOUND: skills/ll-patch-capture/scripts/patch_capture_runtime.py (256 lines)
- FOUND: skills/ll-patch-capture/scripts/run.sh (85 lines, executable)
- FOUND: skills/ll-patch-capture/scripts/validate_input.sh (23 lines, executable)
- FOUND: skills/ll-patch-capture/scripts/validate_output.sh (11 lines, executable)

### Commits
- FOUND: 6433c74 (CLI registration)
- FOUND: 6d4a5e9 (Python runtime)
- FOUND: 6d88c82 (Shell scripts)

### Acceptance criteria
- PASS: cli/ll.py contains "patch-capture" in skill action tuple
- PASS: cli/commands/skill/command.py contains "patch-capture" in ensure() action set
- PASS: cli/commands/skill/command.py contains explicit if/elif block for patch-capture
- PASS: All Python files pass syntax check (ast.parse)
- PASS: patch_capture_runtime.py has run_skill, get_next_patch_id, detect_conflicts, register_patch_in_registry
- PASS: patch_capture_runtime.py imports validate_file from cli.lib.patch_schema
- PASS: patch_capture_runtime.py imports ensure from cli.lib.errors
- PASS: run.sh invokes CLI protocol via python -m cli skill patch-capture
- PASS: validate_output.sh calls python -m cli.lib.patch_schema --type patch
- PASS: All shell scripts are executable

### Self-Check: PASSED
