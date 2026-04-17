---
phase: 04-test-integration
reviewed: 2026-04-17T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - cli/lib/patch_schema.py
  - cli/lib/qa_schemas.py
  - cli/lib/test_exec_artifacts.py
  - cli/lib/test_exec_execution.py
  - cli/lib/test_exec_runtime.py
  - skills/ll-experience-patch-settle/scripts/settle_runtime.py
  - skills/ll-patch-capture/scripts/patch_capture_runtime.py
  - ssot/schemas/qa/manifest.yaml
  - ssot/schemas/qa/patch.yaml
  - tests/qa_schema/fixtures/valid_patch.yaml
  - tests/qa_schema/test_patch_schema.py
  - tests/unit/test_test_exec_patch_context.py
  - tests/unit/test_test_exec_patch_execution.py
  - tests/unit/test_test_exec_runtime_patch_gate.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-17
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed 14 files spanning the test-integration phase: patch schema definitions, runtime execution logic, settlement/capture skills, YAML schemas, and their test suites. The code is generally well-structured with good separation of concerns and proper use of `yaml.safe_load`. No critical security vulnerabilities or logic errors were found. Four warnings and four info-level items were identified, primarily around mutation of input arguments, type annotation inconsistencies, and edge-case behavior in slug generation.

---

## Warnings

### WR-01: `create_manifest_items_for_new_scenarios` mutates its input list in-place

**File:** `cli/lib/test_exec_artifacts.py:298`
**Issue:** `manifest_items.extend(new_items)` mutates the caller's list object in-place rather than returning a new list. This violates the immutability principle stated in project coding standards (create new objects, never mutate existing ones). While the function returns `manifest_items`, the caller may hold a reference to the same list and observe unexpected mutations.

**Fix:**
```python
# Line 298: change extend to return a new list
# Current (mutates):
manifest_items.extend(new_items)
return manifest_items

# Fixed (immutable):
result = list(manifest_items)
result.extend(new_items)
return result
```

---

### WR-02: `settle_patch` uses `yaml.dump` which loses YAML formatting and comments

**File:** `skills/ll-experience-patch-settle/scripts/settle_runtime.py:106`
**Issue:** `yaml.dump(data, f, default_flow_style=False, allow_unicode=True)` writes the full YAML document back. This loses original formatting (comments, blank lines, anchor/alias nodes, document ordering) since PyYAML re-serializes the in-memory dict. For files that may have hand-written content, this is a data-loss risk.

**Fix:**
```python
# Write back using safe_dump with explicit settings, or use ruamel.yaml
# if preserving formatting is required:
yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

If preserving comments/formatting is required, consider switching to `ruamel.yaml` with `YAML(typ='rt')`.

---

### WR-03: `build_conflict_resolution_map` route-to-coverage_id mapping is lossy

**File:** `cli/lib/test_exec_artifacts.py:90`
**Issue:** Coverage IDs are derived from routes by replacing `/` with `.` (`route.replace("/", ".")`). This means `/users/{id}` and `/users_/id` both map to `users.id`, creating collisions in the conflict resolution map. A route with multiple path segments containing dots will also collide.

**Fix:**
```python
# Add a delimiter when joining segments to avoid collisions:
# Instead of: route.replace("/", ".")
# Use: ".".join(route.split("/"))  # preserves structure
# Or use the route as-is and normalize consistently in both places
```

---

### WR-04: `slugify` truncates to 50 chars, risking patch file collisions

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:22`
**Issue:** `slugify` limits output to 50 characters. Two patches with titles differing only after the 50th character (e.g., `"Patch for very long feature name — alternative approach"` vs `"Patch for very long feature name — different approach"`) could produce the same slug, causing `feat_dir.glob(f"{patch_id}__*.yaml")` to return multiple files. The first match wins, silently skipping validation of the second.

**Fix:**
```python
# Include a hash suffix when slug would be ambiguous, or use the full title
# if length is not a hard constraint:
slug = slugify(p.get("title", p["id"]))
# Append a short content hash to guarantee uniqueness:
import hashlib
slug = f"{slugify(p.get('title', p['id']))}-{hashlib.md5(p['id'].encode()).hexdigest()[:6]}"
```

---

## Info

### IN-01: `execute_test_exec_skill` comment about in-memory modification is misleading

**File:** `cli/lib/test_exec_runtime.py:237`
**Issue:** The comment "manifest_items modification happens in-memory within the execution context" suggests `manifest_items` are modified, but the current implementation only imports `mark_manifest_patch_affected` and `create_manifest_items_for_new_scenarios` without actually calling them. The functions are imported but not invoked in this phase. The comment should reflect that these are wired for future use, not active in this phase.

**Fix:**
```python
# Update comment to clarify wiring intent:
# Note: manifest_items modification is wired for future use (D-07/D-09).
# The functions above are imported and available but not yet called
# in this phase's execution flow.
```

---

### IN-02: `test_build_conflict_resolution_map_returns_warn_for_visual` assertion uses ambiguous key lookup

**File:** `tests/unit/test_test_exec_patch_context.py:288`
**Issue:** The test `assert result.get("route.one") == "warn"` works but relies on the string-coverage-id mapping behavior. If the mapping algorithm changes (e.g., delimiter changes from `.` to `-`), this test breaks silently without indicating the fragility.

**Fix:**
```python
# Add a comment documenting the expected mapping:
# Route "route.one" -> coverage_id = "route.one" (dots are preserved)
assert result.get("route.one") == "warn", "visual routes use '.' as separator"
```

---

### IN-03: `get_next_patch_id` file locking is Unix-only, silently skipped on Windows

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:31-43`
**Issue:** `fcntl.flock` calls are wrapped in `try/except ImportError`, so on Windows the file lock is silently not acquired. The registry read still succeeds, and writes go to separate patch YAML files (not the registry), so correctness is not affected. However, if a future change routes writes through the registry with concurrent Windows processes, this could cause silent data loss.

**Fix:**
```python
# Add a warning comment or log statement:
try:
    import fcntl
    fcntl.flock(f, fcntl.LOCK_SH)
except ImportError:
    # Warning: file locking not available on Windows.
    # Concurrent registry writes may cause race conditions.
    pass
```

---

### IN-04: `test_unmatched_items_keep_patch_affected_false` assertion is ambiguous

**File:** `tests/unit/test_test_exec_patch_execution.py:231`
**Issue:** The assertion `assert val is None or val is False` is ambiguous about whether `None` is a legitimate "unmodified" sentinel or indicates the field was never set. Combined with `WR-01` (the underlying mutation issue), this suggests the function should consistently return either `True` or `False`, not `None`.

**Fix:**
Ensure `mark_manifest_patch_affected` always sets `patch_affected` to `False` (not `None`) for unmatched items, making the boolean explicit:
```python
if not matching_patches:
    item_copy["patch_affected"] = False
```

---

_Reviewed: 2026-04-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
