---
phase: 03-skill
plan: 02
type: tdd
wave: 2
autonomous: true
subsystem: settle_runtime
tags: [tdd, settlement, backwrite, runtime]
dependency_graph:
  requires:
    - "03-01 (skill skeleton + patch schema)"
  provides:
    - REQ-PATCH-03 (settlement runtime)
  affects:
    - cli/lib/patch_schema.py (import)
    - ssot/experience-patches/*/patch_registry.json (read/write)
tech_stack:
  added: []
  patterns:
    - "data.get('experience_patch', data) YAML unwrapping"
    - "yaml.safe_load() for security"
    - "json.dump atomic write pattern"
    - "Path.resolve().startswith() path traversal prevention"
key_files:
  created:
    - skills/ll-experience-patch-settle/scripts/settle_runtime.py
    - skills/ll-experience-patch-settle/scripts/test_settle_runtime.py
  modified: []
decisions:
  - "Used dict with id/status keys for update_registry_statuses (matches run_skill usage)"
  - "Delta files written to feat_dir (same level as patches) per RESEARCH.md decision"
  - "settle_patch returns dict with patch_id/new_status/file_path for chaining"
metrics:
  duration: "TBD"
  completed_date: "2026-04-16"
---

# Phase 3 Plan 02: Settle Runtime TDD Summary

Batch settlement runtime for experience patches -- scans pending_backwrite patches, groups by change_class, generates delta/SRC files per D-02/D-03/D-04, updates patch statuses and registry, generates resolved_patches.yaml report.

## One-liner

Settlement runtime with 8 functions (scan, group, settle, registry update, delta generation, report, conflict detection, entry point) and 31 passing unit tests across 9 test classes.

## Tasks Completed

| # | Task | Status |
|---|------|--------|
| 0 | Test scaffold with 9 test classes, _make_complete_patch, _make_feat_dir helpers | DONE |
| 1 | scan_pending_patches, group_by_class, settle_patch, update_registry_statuses | DONE |
| 2 | generate_delta_files, generate_settlement_report, detect_settlement_conflicts, run_skill | DONE |

## Key Decisions

### YAML Unwrapping Consistency
Used `data.get("experience_patch", data)` pattern matching patch_capture_runtime.py exactly (lines 69, 200, 212). settle_patch additionally handles root_key detection for write-back.

### update_registry_statuses Input Format
Function expects list of dicts with `id` and `status` fields (matching the format of patch dicts returned by scan_pending_patches after settlement). run_skill updates patch["status"] before passing to this function.

### Delta File Location
Per RESEARCH.md Open Question 1 resolution, delta files written directly to feat_dir (same level as UXPATCH-*.yaml patches), not in a separate deltas/ subdirectory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] run_skill registry update parameter mismatch**
- **Found during:** Task 2 implementation
- **Issue:** update_registry_statuses() expects dicts with `id`/`status` fields, but `run_skill` was passing result dicts with `patch_id`/`new_status` fields
- **Fix:** Added `all_updated_patches` list that tracks patch dicts with updated status, separate from `all_results` (which has flattened result format)
- **Files modified:** settle_runtime.py

## Self-Check

- [x] settle_runtime.py has all 8 required functions with type annotations
- [x] test_settle_runtime.py has all 9 required test classes
- [x] pytest -x -v passes with 31 tests (exceeds 25 minimum)
- [x] YAML unwrapping uses data.get("experience_patch", data) consistently
- [x] yaml.safe_load() used (never yaml.load())
- [x] json.dump uses indent=2, ensure_ascii=False
- [x] Path traversal prevention (regex + resolve().startswith())
- [x] Zero new external dependencies
- [x] Delta files contain original_text field (D-06 compliance)
- [x] Visual patches generate no delta files (D-02)
- [x] run_skill entry point matches patch_capture_runtime.py CLI protocol

## Self-Check: PASSED
