---
phase: 11
plan: "01"
subsystem: task-pack-v2-1
tags: [PACK-01, schema, validation, yaml]
dependency_graph:
  requires: []
  provides: [PACK-01]
  affects: [PACK-02]
tech-stack:
  added: []
  patterns:
    - frozen dataclasses
    - enum validation
    - _require() helper
    - yaml.safe_load (not yaml.load)
key-files:
  created:
    - ssot/schemas/qa/task_pack.yaml
    - cli/lib/task_pack_schema.py
    - cli/lib/test_task_pack_schema.py
  modified: []
decisions:
  - Used graphlib.TopologicalSorter pattern for resolver (PACK-02, not this plan)
  - Followed frz_schema.py / patch_schema.py patterns exactly
  - ID format validation via regex: PACK_ID_PATTERN, TASK_ID_PATTERN
  - depends_on orphan detection at schema level (not deferred to resolver)
metrics:
  duration_minutes: ~10
  tasks_completed: 3
  tests_added: 24
  files_created: 3
---

# Phase 11 Plan 01: Task Pack Schema (PACK-01) Summary

**One-liner:** YAML schema definition + Python validator module with frozen dataclasses, enums, and 24 unit tests for Task Pack validation (PACK-01).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create test scaffolds (Wave 0) | 047b566 | test_task_pack_schema.py, test_task_pack_resolver.py, task_pack_schema.py (stub), task_pack_resolver.py (stub) |
| 2 | Create Task Pack YAML schema and Python validator | 91ea6c6 | ssot/schemas/qa/task_pack.yaml, cli/lib/task_pack_schema.py |
| 3 | Implement schema validation tests | fa281b7 | cli/lib/test_task_pack_schema.py |

## One-liner

Task Pack YAML schema and Python validator following project's established frozen-dataclass + `_require()` pattern, with 24 unit tests covering acceptance, rejection, file I/O, and ID format validation.

## Key Decisions Made

1. **Followed frz_schema.py pattern exactly** — frozen dataclasses, `_require()`, `_enum_check()`, `_parse_task_dict()`, `_parse_task_pack_dict()`, custom error class inheriting from `ValueError`.
2. **Orphan depends_on detection at schema level** — `validate()` checks that all `depends_on` refs exist in the same pack, raising `TaskPackSchemaError` before reaching the resolver.
3. **ID format validation** — `PACK_ID_PATTERN = re.compile(r"^PACK-")` and `TASK_ID_PATTERN = re.compile(r"^TASK-\d{3,}$")` enforced in `_parse_task_pack_dict` and `_parse_task_dict`.
4. **`yaml.safe_load` exclusively** — per threat model T-11-01, never using `yaml.load()` without SafeLoader.
5. **Single string `verifies` coercion** — `if isinstance(verifies, str): verifies = [verifies]` handles users who write `verifies: AC-001` instead of `verifies: [AC-001]`.
6. **None `depends_on` handling** — `(t.get("depends_on") or [])` pattern handles YAML parsing quirks where `depends_on:` yields `None`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Stubs needed for pytest discovery**
- **Found during:** Task 1
- **Issue:** Test files imported `task_pack_schema.py` and `task_pack_resolver.py` which did not exist yet, causing pytest collection errors.
- **Fix:** Created minimal stub modules with empty implementations (enums, dataclasses, stub functions) so pytest could discover test functions. Task 2 replaced the stub with full implementation.
- **Files modified:** `cli/lib/task_pack_schema.py`, `cli/lib/task_pack_resolver.py`

### Auto-added Issues

**2. [Rule 2 - Missing functionality] Title validation**
- **Found during:** Task 2
- **Issue:** Plan specified `title` as required but the stub did not validate it.
- **Fix:** Added `if not title: raise TaskPackSchemaError(...)` check in `_parse_task_dict`.

**3. [Rule 2 - Missing functionality] Empty tasks list validation**
- **Found during:** Task 2
- **Issue:** Plan required non-empty tasks list but initial validation only checked `isinstance(tasks_raw, list)`.
- **Fix:** Added `len(tasks_raw) == 0` check.

## Test Results

```
24 passed in 0.10s
```

All 24 tests pass:
- 7 dataclass/enum construction tests
- 2 valid pack acceptance tests
- 9 rejection tests (missing fields, invalid types, orphans, duplicates, bad formats)
- 2 file I/O tests
- 4 `_parse_*_dict` tests

## Known Stubs

None. All functionality specified in the plan is implemented and tested.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag:yaml_parsing | cli/lib/task_pack_schema.py | Uses `yaml.safe_load()` exclusively per T-11-01 mitigation |

## Verification

```bash
# Schema validation tests
pytest cli/lib/test_task_pack_schema.py -v    # 24 passed

# Full suite
pytest cli/lib/ -q                            # all green

# Import check
python -c "from cli.lib.task_pack_schema import TaskPack, Task, TaskType, TaskStatus, validate, validate_file, TaskPackSchemaError; print('imports OK')"
```

## Self-Check: PASSED

All created files exist and all commits verified:
- `ssot/schemas/qa/task_pack.yaml` — FOUND
- `cli/lib/task_pack_schema.py` — FOUND
- `cli/lib/test_task_pack_schema.py` — FOUND
- Commits: 047b566, 91ea6c6, fa281b7 — all FOUND in git log
