---
phase: 10-change-grading
plan: 02
subsystem: ll-experience-patch-settle
tags: [settle, backwrite, minor-patch, grade-level, idempotency, yaml]

# Dependency graph
requires:
  - phase: 10-01
    provides: GradeLevel enum, derive_grade(), CHANGE_CLASS_TO_GRADE mapping in patch_schema.py
provides:
  - settle_runtime.py with Minor patch backwrite-as-records logic
  - Backwrite RECORDS in backwrites/ subdirectory for human review
  - Major patch rejection routing to ll-frz-manage
  - Idempotent settle behavior
  - --apply flag stub for future SSOT modification
affects:
  - skills/ll-experience-patch-settle (built from scratch)

# Tech tracking
tech-stack:
  added: [none - stdlib + PyYAML only]
  patterns:
    - "Backwrite-as-records: creates structured YAML summaries, NOT actual SSOT modifications"
    - "Idempotent settle: status=applied check returns early on second run"
    - "BACKWRITE_MAP: 12 change_class entries with per-target backwrite configuration"
    - "Workspace root resolution: walk-up from patch path looking for ssot/ directory"

key-files:
  created:
    - skills/ll-experience-patch-settle/SKILL.md
    - skills/ll-experience-patch-settle/ll.contract.yaml
    - skills/ll-experience-patch-settle/ll.lifecycle.yaml
    - skills/ll-experience-patch-settle/input/contract.yaml
    - skills/ll-experience-patch-settle/output/contract.yaml
    - skills/ll-experience-patch-settle/agents/executor.md
    - skills/ll-experience-patch-settle/scripts/settle_runtime.py
    - skills/ll-experience-patch-settle/scripts/test_settle_runtime.py
  modified:
    - skills/__init__.py (added for package structure)

key-decisions:
  - "Used direct import from scripts dir instead of package-based import (hyphenated skill dir incompatible with Python module naming)"
  - "BACKWRITE_MAP uses underscored target names (ui_spec, flow_spec, testset) instead of Chinese/English mixed names for file naming consistency"
  - "--apply flag implemented as visible stub with WARNING message, not hidden"

patterns-established:
  - "settle_minor_patch() returns dict with status, backwrite_targets, files_written"
  - "Backwrite records contain: patch_id, change_class, grade_level, changed_files, test_impact, created_at, note"
  - "Idempotency: status=applied early return prevents double-processing"

requirements-completed:
  - GRADE-02

# Metrics
duration: ~10min
completed: 2026-04-19
---

# Phase 10 Plan 02: Minor Patch Settle Skill Summary

**One-liner:** Built `ll-experience-patch-settle` skill from scratch with SKILL.md, contracts, executor agent, and `settle_runtime.py` implementing Minor patch backwrite-as-records logic with idempotency, Major rejection, and `--apply` flag stub.

## Objective

Build the `skills/ll-experience-patch-settle` skill from scratch (directory had only `__pycache__` compiled files). Purpose: GRADE-02 — Minor patches need settle logic that creates backwrite RECORDS in `backwrites/` subdirectory for human review. Major patches rejected and routed to FRZ revise.

## Tasks Executed

### Task 1: Create minimal skill skeleton

- Created SKILL.md with tri-classification reference table, BACKWRITE_MAP, execution protocol, non-negotiable rules
- SKILL.md references "grade_level", "minor", "major", "backwrite", "idempotent", and "ll-frz-manage --type revise"
- Clarified backwrite creates RECORDS not actual SSOT modifications (per ADR-049 §4.4)
- Created ll.contract.yaml, ll.lifecycle.yaml (draft→applied lifecycle), input/output contract definitions
- Created agents/executor.md with BACKWRITE_MAP reference and step-by-step execution instructions
- No supervisor.md created per review consensus
- Committed: `feat(10-02): create ll-experience-patch-settle skill skeleton`

### Task 2: Build settle_runtime.py with TDD

- **RED phase**: Wrote 8 failing tests covering all plan behaviors
- **GREEN phase**: Implemented settle_runtime.py (262 lines):
  - `BACKWRITE_MAP` with all 12 change_class entries
  - `settle_minor_patch()` function with:
    - Idempotency check (status=applied early return)
    - Grade derivation from patch_schema.py (no re-implementation)
    - Major patch rejection with CommandError referencing "ll-frz-manage"
    - Backwrite record creation to `backwrites/` subdirectory
    - Patch status update to "applied" with `settled_at` timestamp
  - CLI with `process` and `settle` subcommands
  - `--apply` flag stub with WARNING message
- All 8 tests passing:
  - Test 1: interaction → 3 backwrite records (ui_spec, flow_spec, testset)
  - Test 2: visual → 1 backwrite record (ui_spec_optional)
  - Test 3: copy_text → 0 backwrite records
  - Test 4: Major patch rejected with "ll-frz-manage" error
  - Test 5: Status updated to "applied"
  - Test 6: Idempotent — second run returns "already_applied"
  - Test 7: CLI process subcommand works end-to-end
  - Test 8: --apply flag shows stub warning
- Committed: `feat(10-02): build settle_runtime.py with Minor backwrite-as-records logic`

## Key Decisions

1. **Direct import over package import**: Hyphenated skill directory (`ll-experience-patch-settle`) is not a valid Python module name. Used direct `sys.path` insertion to import `settle_runtime` from the scripts directory.
2. **Underscored backwrite target names**: Used `ui_spec`, `flow_spec`, `testset` instead of mixed Chinese/English names for consistent file naming.
3. **Visible --apply stub**: Warning printed to stdout so users see it's reserved for future use.

## Deviations from Plan

**None** — plan executed exactly as written. All 8 acceptance criteria met, all 8 tests passing.

## Known Stubs

- `--apply` flag: Stub for future SSOT modification. Currently prints WARNING message and does nothing else. Planned for future milestone.

## Threat Flags

None — all threats from plan's threat register are mitigated:
- T-10-04: Grade validation at function entry (rejects Major)
- T-10-05: Backwrites to dedicated directory, never overwrite SSOT files
- T-10-06: settled_at timestamp recorded, idempotency prevents double-application
- T-10-14: derive_grade imported from patch_schema.py, not re-implemented

## Self-Check

- [x] All 6 skeleton files exist under skills/ll-experience-patch-settle/
- [x] settle_runtime.py exists with >= 100 lines (262 lines)
- [x] `def settle_minor_patch` exists (line 113)
- [x] BACKWRITE_MAP exists with 12 entries
- [x] `from cli.lib.patch_schema import GradeLevel, derive_grade` (line 24)
- [x] `--apply` flag exists (lines 198, 232-236)
- [x] Idempotency check (line 127: status == "applied" early return)
- [x] CLI shows process and settle subcommands
- [x] 8 tests passing
- [x] Commits: 702eb37, 3f4f011, 0b7b185

## Self-Check: PASSED
