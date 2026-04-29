---
phase: 025-bug-registry-state-machine
plan: "02"
subsystem: cli
tags: [bug-workflow, phase-generator, adr-055]
dependency_graph:
  requires:
    - cli/lib/fs.py (write_text, ensure_parent)
    - cli/lib/errors.py (CommandError)
  provides:
    - cli/lib/bug_phase_generator.py (generate_bug_phase, generate_batch_phase)
  affects:
    - .planning/phases/ (generated phase directories)
tech_stack:
  added:
    - cli/lib/bug_phase_generator.py (~190 lines)
    - cli/lib/test_bug_phase_generator.py (~105 lines)
  patterns:
    - Immutable file generation via write_text
    - Hash-based batch directory naming (MD5, 8 chars)
    - 6-task PLAN.md template per ADR-055 §2.5
key_files:
  created:
    - cli/lib/bug_phase_generator.py
    - cli/lib/test_bug_phase_generator.py
  modified: []
decisions:
  - "autonomous: false in all generated PLAN.md frontmatter (locked D-15)"
  - "Max 3 bugs per batch phase (locked D-13)"
  - "Batch directory name uses MD5 hash of joined bug_ids (8 hex chars)"
  - "No imports from bug_registry — generators are independent"
metrics:
  duration: ~10 minutes
  completed: 2026-04-29
  tasks: 2
  files: 2
  tests: 5 (all passing)
---

# Phase 025 Plan 02: Bug Phase Generator Summary

## One-liner

Phase directory generator that creates GSD fix-phase directories (.planning/phases/) for single or batched bug workflows with 4-file structure and 6-task PLAN.md template.

## What was built

### cli/lib/bug_phase_generator.py (~190 lines)

Exports:
- `generate_bug_phase(workspace_root, bug, phase_number)` — creates single-bug phase directory
- `generate_batch_phase(workspace_root, bugs, phase_number)` — creates batch phase (max 3 bugs)

Internal helpers:
- `_build_context_md(bug)` — renders CONTEXT.md from bug record fields
- `_build_plan_md(bugs, is_batch)` — renders PLAN.md with frontmatter + 6-task template
- `_build_discussion_log_md()` — empty placeholder
- `_build_summary_md()` — empty placeholder
- `_build_batch_context_md(bugs)` — concatenates multiple bug contexts

Directory structure generated:
```
.planning/phases/{N:03d}-bug-fix-{bug_id}/
  CONTEXT.md       — bug evidence, case_id, actual/expected, diagnostics
  PLAN.md          — 6 standard tasks, autonomous: false
  DISCUSSION-LOG.md — empty placeholder
  SUMMARY.md        — empty placeholder
```

### cli/lib/test_bug_phase_generator.py (5 tests, all passing)

| Test | Coverage |
|------|----------|
| test_phase_dir_structure | 4 files exist, CONTEXT.md has bug_id, PLAN.md has tasks + autonomous: false |
| test_plan_md_contains_6_tasks | All 6 task names present |
| test_batch_creates_single_dir | "batch" in dir name, both bug IDs in PLAN.md |
| test_batch_max_3 | CommandError("INVALID_REQUEST") on 4 bugs |
| test_batch_single_file_set | Exactly 4 files in batch dir |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

DISCUSSION-LOG.md and SUMMARY.md are intentionally empty placeholders per ADR-055 §2.5. They will be populated during fix-phase execution. Not functional stubs.

## Threat Flags

None. Generated files go to controlled .planning/phases/ directory. No path traversal risk — bug_id used as-is in directory name (no user-supplied paths).

## Verification

- `python -c "from cli.lib.bug_phase_generator import generate_bug_phase, generate_batch_phase"` — imports OK
- `pytest cli/lib/test_bug_phase_generator.py -x -v` — 5/5 passed
- `grep "write_text" bug_phase_generator.py` — present
- `grep "autonomous: false"` — present in generated PLAN.md (verified by test)
- Both single-bug and batch modes verified programmatically with full file content checks

## Self-Check: PASSED

- cli/lib/bug_phase_generator.py: EXISTS
- cli/lib/test_bug_phase_generator.py: EXISTS
- Commit 93fa4ae: feat(025-02): implement bug phase generator — EXISTS
- Commit fcef13f: test(025-02): add bug phase generator unit tests — EXISTS
- 5 unit tests: ALL PASSING
