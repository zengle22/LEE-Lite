---
phase: "11"
plan: "02"
type: execute
wave: 2
depends_on:
  - "11-01"
requirements:
  - PACK-02
tags:
  - dependency-resolution
  - topological-sort
  - task-pack
  - graphlib
dependency_graph:
  requires:
    - "11-01 (task_pack_schema.py, test_task_pack_schema.py)"
  provides:
    - PACK-02: depends_on resolution via topological sort
    - Sample Task Pack for manual validation
  affects:
    - "ssot/tasks/ (new directory for Task Pack YAML files)"
tech_stack:
  added: []
  patterns:
    - "graphlib.TopologicalSorter for DAG resolution"
    - "yaml.safe_load for file parsing"
    - "Frozen dataclasses + _require() pattern (consistent with Plan 01)"
key_files:
  created:
    - "cli/lib/task_pack_resolver.py"
    - "ssot/tasks/PACK-SRC-001-001-feat001.yaml"
  modified:
    - "cli/lib/test_task_pack_resolver.py"
decisions:
  - "Used graphlib.TopologicalSorter (stdlib) instead of external library — zero new dependencies"
  - "Validated depends_on refs against known task_ids before graph construction — prevents confusing TopologicalSorter errors"
  - "Added CycleError wrapping with clear message — users see 'Circular dependency detected' instead of raw CycleError"
  - "13 tests total (7 required by plan) — added edge cases for 3-way cycles and self-dependency"
metrics:
  duration_minutes: ~5
  completed_date: "2026-04-20"
  tasks_completed: 2
  tests_added: 13
  total_tests_passing: 37
---

# Phase 11 Plan 02: Task Pack Dependency Resolution Summary

One-liner: `depends_on` dependency resolution via topological sort using `graphlib.TopologicalSorter`, with comprehensive test coverage and a sample Task Pack YAML for end-to-end validation.

## Tasks Executed

| # | Task | Type | Commit | Files |
|---|------|------|--------|-------|
| 1 | Create dependency resolver module with topological sort | auto | 5fec36b | `cli/lib/task_pack_resolver.py` |
| 2 | Implement resolver tests and sample Task Pack | auto | 37c259d | `cli/lib/test_task_pack_resolver.py`, `ssot/tasks/PACK-SRC-001-001-feat001.yaml` |

## Task Details

### Task 1: Create dependency resolver module

**File:** `cli/lib/task_pack_resolver.py` (107 lines)

**Exports:**
- `TaskPackResolverError(ValueError)` — error class for resolution failures
- `resolve_order(pack_yaml: dict) -> list[str]` — topological sort of task execution order
- `resolve_file(path: str | Path) -> list[str]` — loads YAML file and resolves order
- `main()` — CLI entry point for batch resolution

**Key implementation details:**
- Uses `graphlib.TopologicalSorter` (Python 3.9+ stdlib) — zero external dependencies
- Handles both wrapped (`task_pack: {...}`) and unwrapped YAML formats
- Validates all `depends_on` references against known `task_ids` BEFORE building the graph (prevents confusing TopologicalSorter errors on orphan refs)
- Uses `(t.get("depends_on") or [])` pattern to handle YAML `None` values
- Wraps `CycleError` into meaningful `TaskPackResolverError` with "Circular dependency detected" message

### Task 2: Implement resolver tests and sample Task Pack

**Test file:** `cli/lib/test_task_pack_resolver.py` (13 tests)

| Test | What it verifies |
|------|-----------------|
| `test_linear_chain` | A -> B -> C sequential ordering |
| `test_cycle_detection` | A -> B -> A cycle raises error |
| `test_diamond_dependency` | A -> B,C -> D diamond resolves with correct ordering |
| `test_orphan_depends_on_raises` | Reference to nonexistent task raises error |
| `test_no_deps_returns_as_is` | All tasks returned when no dependencies |
| `test_resolve_file` | File I/O with temp YAML file |
| `test_single_task` | Single task pack returns [task_id] |
| `test_resolve_file_not_found` | FileNotFoundError for missing file |
| `test_wrapped_format` | `task_pack: {...}` wrapper handled |
| `test_depends_on_none_handled` | YAML `depends_on: None` coerced to `[]` |
| `test_three_way_cycle` | A -> C -> B -> A 3-way cycle detected |
| `test_self_dependency` | Task depending on itself raises error |
| `test_sample_pack_e2e` | End-to-end: schema validate + resolve sample pack |

**Sample Task Pack:** `ssot/tasks/PACK-SRC-001-001-feat001.yaml`

4-task pack following ADR-051 §2.1 example exactly:
- TASK-001: impl (no deps)
- TASK-002: test-api (depends on TASK-001)
- TASK-003: test-e2e (depends on TASK-001)
- TASK-004: review (depends on TASK-002, TASK-003)

## Verification Results

```
pytest cli/lib/test_task_pack_schema.py cli/lib/test_task_resolver.py -v
37 passed in 0.09s
```

All acceptance criteria met:
- [x] `pytest cli/lib/test_task_pack_resolver.py -v` exits with code 0
- [x] 13 test functions defined (requirement: >= 7)
- [x] `test_cycle_detection` raises `TaskPackResolverError` with message containing "ircular"
- [x] `test_diamond_dependency` returns all 4 tasks with correct ordering
- [x] Sample pack exists with `task_pack:`, `pack_id:`, `feat_ref:`, `tasks:`, 4 task entries
- [x] `test_sample_pack_e2e` loads sample file, resolves, returns 4 task_ids

## Deviations from Plan

None — plan executed exactly as written.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag:yaml_parsing | `cli/lib/task_pack_resolver.py` | `yaml.safe_load()` used exclusively (mitigates T-11-04) |
| threat_flag:cycle_dos | `cli/lib/task_pack_resolver.py` | `CycleError` caught immediately, no infinite loop possible (mitigates T-11-05) |
| threat_flag:orphan_refs | `cli/lib/task_pack_resolver.py` | All depends_on validated against known task_ids before graph construction (mitigates T-11-06) |

## Self-Check: PASSED

- [x] `cli/lib/task_pack_resolver.py` exists
- [x] `cli/lib/test_task_pack_resolver.py` exists
- [x] `ssot/tasks/PACK-SRC-001-001-feat001.yaml` exists
- [x] Commit `5fec36b` exists
- [x] Commit `37c259d` exists
- [x] All 37 tests passing
