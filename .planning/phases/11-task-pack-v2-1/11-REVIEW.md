---
phase: 11-task-pack-v2-1
reviewed: 2026-04-20T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - cli/lib/task_pack_schema.py
  - cli/lib/task_pack_resolver.py
  - cli/lib/test_task_pack_schema.py
  - cli/lib/test_task_pack_resolver.py
findings:
  critical: 0
  warning: 5
  info: 3
  total: 8
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-04-20T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the Task Pack schema validation and dependency resolution modules along with their test suites. The code is well-structured with frozen dataclasses, proper enum usage, topological sort via `graphlib`, and comprehensive test coverage. Several type-safety gaps and edge-case handling issues were found that could cause crashes or accept malformed YAML. No critical security vulnerabilities were identified.

## Warnings

### WR-01: `_parse_task_dict` crashes on non-string `task_id`

**File:** `cli/lib/task_pack_schema.py:116`

**Issue:** If the YAML contains a non-string `task_id` (e.g., `task_id: 123` as an integer), `TASK_ID_PATTERN.match(task_id)` raises `TypeError` because `re.match()` expects a string or bytes. The None check on line 114 passes for integers, so this is an unhandled edge case.

**Fix:**
```python
task_id = data.get("task_id")
if task_id is None or not isinstance(task_id, str):
    raise TaskPackSchemaError("Task: required field 'task_id' is missing or invalid")
if not TASK_ID_PATTERN.match(task_id):
    raise TaskPackSchemaError(f"Invalid task_id format: {task_id}")
```

### WR-02: `depends_on` missing single-string-to-list coercion

**File:** `cli/lib/task_pack_schema.py:149`

**Issue:** The `verifies` field on line 153 coerces a single string to a list (`if isinstance(verifies, str): verifies = [verifies]`). The `depends_on` field on line 149 does not have the same coercion. If a user writes `depends_on: TASK-001` (string) instead of `depends_on: [TASK-001]` (list) in YAML, the Task dataclass receives a string where `list[str]` is expected, causing downstream failures.

**Fix:**
```python
depends_on = data.get("depends_on") or []
if isinstance(depends_on, str):
    depends_on = [depends_on]
verifies = data.get("verifies") or []
if isinstance(verifies, str):
    verifies = [verifies]
```

### WR-03: `resolve_order` raises bare `KeyError` on missing `task_id`

**File:** `cli/lib/task_pack_resolver.py:42`

**Issue:** The set comprehension `{t["task_id"] for t in tasks}` uses direct dict access. If `resolve_order` is called directly without prior schema validation and a task dict is missing `task_id`, a bare `KeyError` is raised instead of the documented `TaskPackResolverError`. This bypasses the expected error contract.

**Fix:**
```python
task_ids: set[str] = set()
for t in tasks:
    tid = t.get("task_id")
    if tid is None:
        raise TaskPackResolverError("Task is missing required field 'task_id'")
    task_ids.add(tid)
```

### WR-04: `resolve_file` bypasses schema validation

**File:** `cli/lib/task_pack_resolver.py:79-82`

**Issue:** `resolve_file` loads YAML and calls `resolve_order` directly without invoking `validate()` from `task_pack_schema`. This means packs with missing required fields, invalid enum values, duplicate task_ids, or orphan dependencies can slip through and cause unpredictable errors (KeyError, TypeError) rather than clean `TaskPackResolverError` or `TaskPackSchemaError`.

**Fix:**
```python
with open(p, encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}

# Validate schema before resolving
validate(data)
return resolve_order(data)
```

### WR-05: `validate()` redundant loop re-checks already-validated fields

**File:** `cli/lib/task_pack_schema.py:266-279`

**Issue:** Lines 248-262 already iterate over `tasks_raw` to collect `task_ids`, verify each entry is a dict, and check for missing `task_id`. Lines 266-279 loop over the same list again and re-call `_require(t, "task_id", ...)` for every task, plus re-check `type` and `status`. The `task_id` check at line 271 is dead code -- it can never fail because the same condition was already enforced on lines 252-255. This is not a bug, but it indicates a logic error in the validation flow and wastes cycles.

**Fix:** Remove the redundant `_require(t, "task_id", t_label)` on line 271, since task_id presence is already guaranteed by lines 252-255:
```python
for i, t in enumerate(tasks_raw):
    t_label = f"{label}.tasks[{i}]"
    tid = t["task_id"]  # Already validated; safe to access directly

    # Only validate fields not yet checked
    _require(t, "type", t_label)
    _require(t, "title", t_label)
    _enum_check(t["type"], TaskType, t_label, "type")
    # ... rest unchanged
```

## Info

### IN-01: `test_task_pack_frozen` and `test_task_frozen` use overly broad exception catch

**File:** `cli/lib/test_task_pack_schema.py:50, 57`

**Issue:** Both tests use `pytest.raises(Exception)` to catch `FrozenInstanceError`. This is too broad and could mask unrelated exceptions (e.g., `AttributeError`). Use the specific exception type.

**Fix:**
```python
from dataclasses import FrozenInstanceError
# ...
with pytest.raises(FrozenInstanceError):
    pkg.pack_id = "new-id"
```

### IN-02: `pack_id` format validation is overly permissive

**File:** `cli/lib/task_pack_schema.py:50`

**Issue:** `PACK_ID_PATTERN = re.compile(r"^PACK-")` only checks that `pack_id` starts with "PACK-" but does not validate any suffix. A `pack_id` of just `"PACK-"` or `"PACK- "` would pass. The test file confirms this -- `test_rejects_invalid_pack_id_format` only checks for `"bad-pack-id"`. Consider tightening the pattern to require a non-empty suffix.

**Fix:**
```python
PACK_ID_PATTERN = re.compile(r"^PACK-.+$")
```

### IN-03: `_VALIDATORS` dict uses unused tuple element in loop

**File:** `cli/lib/task_pack_schema.py:300-302`

**Issue:** In `_detect_schema_type`, the loop `for stype, (top_key, _) in _VALIDATORS.items():` unpacks but discards the parser function with `_`. This is fine stylistically, but the parser function is never used in this method. Consider storing just the top key in a simpler structure if the parser is not needed for detection:
```python
_SCHEMA_TOP_KEYS = {"task_pack": "task_pack"}

def _detect_schema_type(data: dict) -> str | None:
    for stype, top_key in _SCHEMA_TOP_KEYS.items():
        if top_key in data:
            return stype
    return None
```

---

_Reviewed: 2026-04-20T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
