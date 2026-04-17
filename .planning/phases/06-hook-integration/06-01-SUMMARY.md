---
phase: 06
plan: 01
plan_title: "Patch Context Injector & Auto-Register"
subsystem: "experience-patch-layer"
tags:
  - adr-049
  - patch-awareness
  - context-injection
  - auto-register
requires:
  - "patch_schema.py (ChangeClass, PatchStatus enums)"
  - "ssot/experience-patches directory structure"
provides:
  - "find_related_patches(workspace_root, target_file, feat_ref)"
  - "summarize_patch_for_context(patch, max_tokens)"
  - "inject_context(workspace_root, target_files)"
  - "detect_changes(workspace_root, feat_ref)"
  - "draft_patch_yaml(changes, workspace_root)"
  - "register_patch(patch, output_dir)"
affects:
  - "cli/lib/patch_context_injector.py"
  - "cli/lib/patch_auto_register.py"
  - "cli/lib/patch_schema.py"
tech_stack:
  added:
    - "PyYAML for patch YAML serialization"
  patterns:
    - "Immutable data via frozen dataclass-ready patterns"
    - "Type-annotated Python (PEP 484)"
key_files:
  created:
    - "cli/lib/patch_context_injector.py"
    - "cli/lib/patch_auto_register.py"
    - "cli/lib/patch_schema.py"
decisions:
  - "patch_schema.py created inline (Rule 3): was referenced but missing from worktree"
  - "resolve_patch_context NOT imported from test_exec_artifacts: function does not exist there; scanning implemented inline"
  - "No auto-commit of patches per ADR-049 section 12.2"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-17T12:55Z"
  tasks_completed: 2
  files_created: 3
  commits:
    - "0fa2854 feat(06-01): implement patch context injector with schema"
    - "3dc74ab feat(06-01): implement patch auto-register from git changes"
---

# Phase 06 Plan 01: Patch Context Injector & Auto-Register Summary

## One-Liner

Experience patch context injection and auto-registration modules: scan patches for AI awareness, detect git changes to draft patches, with budget protection and user confirmation gates per ADR-049.

## Tasks Executed

| # | Name | Status | Commit |
|---|------|--------|--------|
| 1 | `patch_context_injector.py` | Done | `0fa2854` |
| 2 | `patch_auto_register.py` | Done | `3dc74ab` |

## Key Decisions

### Rule 3 Deviation: Created missing `patch_schema.py`

The plan referenced `ChangeClass` and `PatchStatus` from `cli/lib/patch_schema.py` which did not exist in the worktree. Created the module with enum definitions for patch lifecycle states and change classifications as a blocking fix.

### Rule 3 Deviation: `resolve_patch_context` not available

The plan specified importing `resolve_patch_context` from `test_exec_artifacts.py`, but this function does not exist in that module. Implemented the patch scanning logic directly in `patch_context_injector.py` via `_discover_patch_dirs`, `_load_patch_yaml`, and `_is_terminal` internal helpers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created `patch_schema.py` (missing dependency)**
- **Found during:** Task 1
- **Issue:** `patch_context_injector.py` imports `ChangeClass` and `PatchStatus` from `patch_schema.py` which did not exist
- **Fix:** Created `cli/lib/patch_schema.py` with `PatchStatus` (draft, proposed, approved, applied, rejected, superseded) and `ChangeClass` (ui_flow, copy_text, validation, navigation, layout, interaction, performance, accessibility, error_handling, data_display, other) enums
- **Files modified:** `cli/lib/patch_schema.py` (created)
- **Commit:** `0fa2854`

**2. [Rule 3 - Blocking] Inline scanning instead of imported `resolve_patch_context`**
- **Found during:** Task 1
- **Issue:** Plan specified importing `resolve_patch_context` from `test_exec_artifacts.py` but the function does not exist in that module
- **Fix:** Implemented scanning logic directly in `patch_context_injector.py` using `_discover_patch_dirs`, `_load_patch_yaml`, `_is_terminal` helpers
- **Files modified:** `cli/lib/patch_context_injector.py`
- **Commit:** `0fa2854`

## Design Notes

- **Context Budget Protection:** `inject_context` enforces 3000 token global budget and 10 patch maximum (ADR-049 section 12.1)
- **No Auto-Finalization:** `register_patch` writes YAML but does NOT auto-commit or auto-approve patches. User confirmation required per ADR-049 section 12.2.
- **test_impact Required:** `register_patch` validates that `test_impact` is filled and not left as a TODO placeholder
- **Git-Based Detection:** `detect_changes` uses `git diff --name-status` for both staged and unstaged changes

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: file_write | cli/lib/patch_auto_register.py | `register_patch` writes YAML to `ssot/experience-patches/` directory; validate output_dir parameter to prevent path traversal |
| threat_flag: subprocess | cli/lib/patch_auto_register.py | `_run_git_diff` executes git subprocess with fixed arguments; workspace_root should be validated as trusted path |

## Self-Check

### File Existence
- [x] `cli/lib/patch_context_injector.py` — EXISTS
- [x] `cli/lib/patch_auto_register.py` — EXISTS
- [x] `cli/lib/patch_schema.py` — EXISTS

### Commits
- [x] `0fa2854` — patch context injector + schema
- [x] `3dc74ab` — patch auto register

## Self-Check: PASSED
