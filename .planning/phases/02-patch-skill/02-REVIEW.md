---
phase: 02-patch-skill
reviewed: 2026-04-16T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - cli/commands/skill/command.py
  - cli/ll.py
  - skills/ll-patch-capture/SKILL.md
  - skills/ll-patch-capture/agents/executor.md
  - skills/ll-patch-capture/agents/supervisor.md
  - skills/ll-patch-capture/input/contract.yaml
  - skills/ll-patch-capture/input/semantic-checklist.md
  - skills/ll-patch-capture/ll.contract.yaml
  - skills/ll-patch-capture/ll.lifecycle.yaml
  - skills/ll-patch-capture/output/contract.yaml
  - skills/ll-patch-capture/output/semantic-checklist.md
  - skills/ll-patch-capture/scripts/patch_capture_runtime.py
  - skills/ll-patch-capture/scripts/run.sh
  - skills/ll-patch-capture/scripts/test_patch_capture_runtime.py
  - skills/ll-patch-capture/scripts/validate_input.sh
  - skills/ll-patch-capture/scripts/validate_output.sh
findings:
  critical: 2
  warning: 7
  info: 7
  total: 16
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the ll-patch-capture skill implementation across CLI routing, Python runtime, shell scripts, agent prompts, and test suite. The codebase demonstrates good security practices (path traversal checks, regex validation on feat_id, JSON construction via Python rather than shell interpolation). However, there are two critical issues (a shell validation dead-code path that suppresses error output, and missing FEAT_ID validation in the shell entry point), several warnings around race conditions, incorrect field access logic, and unsafe sys.path manipulation, plus minor quality issues in tests and code organization.

## Critical Issues

### CR-01: Dead error-handling code in validate_output.sh suppresses failure messages

**File:** `skills/ll-patch-capture/scripts/validate_output.sh:9-10`
**Issue:** The script has `set -euo pipefail` on line 3, which causes immediate exit on any non-zero command. When `python -m cli.lib.patch_schema` on line 9 returns non-zero (schema validation failure), the script exits immediately -- the `if [[ $? -ne 0 ]]` check on line 10 is unreachable dead code. The user never sees the "FAIL: invalid patch output" message, making failures silent from the perspective of whoever called this script.
**Fix:**
```bash
# Option 1: Use if/then to catch the error
if ! python -m cli.lib.patch_schema --type patch "${OUTPUT_PATH}"; then
    echo "FAIL: invalid patch output"
    exit 1
fi
echo "OK: output validated"
```

### CR-02: No FEAT_ID validation in run.sh before filesystem operations

**File:** `skills/ll-patch-capture/scripts/run.sh:46`
**Issue:** The `FEAT_ID` variable is used directly in the OUTPUT_DIR path without any validation in the shell script:
```bash
OUTPUT_DIR="${WORKSPACE}/ssot/experience-patches/${FEAT_ID}"
mkdir -p "${OUTPUT_DIR}"
```
If `run.sh` is called directly (bypassing the Python CLI), a crafted FEAT_ID like `../../../tmp/evil` creates directories outside the intended tree. The Python runtime validates FEAT_ID with a regex (patch_capture_runtime.py line 127-131), but the shell entry point has no equivalent check.
**Fix:** Add FEAT_ID validation in run.sh before use:
```bash
if ! echo "${FEAT_ID}" | grep -qE '^[a-zA-Z0-9][a-zA-Z0-9._-]*$'; then
    echo "Error: --feat-id contains invalid characters"
    exit 1
fi
```

## Warnings

### WR-01: test_impact escalation check always triggers when test_impact is populated

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:218`
**Issue:** `test_impact` in the schema is a nested dict (`{impacts_user_path: bool, impacts_acceptance: bool, ...}`), not a string. The check `patch.get("test_impact", "none") not in ("none", "path_change", "assertion_change", "new_case_needed")` compares a dict against string values. A dict will never equal any of those strings, so this condition is ALWAYS true whenever test_impact is present, causing unintended escalation on every patch that has test_impact populated.
**Fix:** Redesign the check to examine a specific sub-field or remove this escalation trigger:
```python
ti = patch.get("test_impact")
if ti is not None and not isinstance(ti, dict):
    escalation_reasons.append("disputed_test_impact")
```

### WR-02: Race condition in get_next_patch_id under concurrent access

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:25-39`
**Issue:** `get_next_patch_id` reads the registry, computes `max + 1`, and returns -- all without any locking. Two concurrent calls for the same feat_dir can read the same max ID and both generate the same next ID, resulting in duplicate patch IDs.
**Fix:** Add file-based locking around the read-compute cycle:
```python
import fcntl
with open(registry_path, "r") as f:
    fcntl.flock(f, fcntl.LOCK_SH)
    registry = json.load(f)
    fcntl.flock(f, fcntl.LOCK_UN)
```

### WR-03: sys.path manipulation in command.py is not thread-safe

**File:** `cli/commands/skill/command.py:111-125`
**Issue:** Modifying `sys.path` at request-handling time is not thread-safe. If two concurrent requests for different skills manipulate `sys.path`, the `finally` block removing the path could break a concurrent request that imported from it. Additionally, `from patch_capture_runtime import run_skill` could import the wrong module if another skill's scripts directory was inserted first.
**Fix:** Use `importlib.util` for isolated dynamic imports:
```python
import importlib.util
mod_path = scripts_dir / "patch_capture_runtime.py"
spec = importlib.util.spec_from_file_location("patch_capture_runtime", mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.run_skill(...)
```

### WR-04: Unhandled JSONDecodeError in register_patch_in_registry

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:78-79`
**Issue:** If `patch_registry.json` contains malformed JSON, `json.load(f)` raises `json.JSONDecodeError` which crashes the skill mid-operation, potentially leaving partial state.
**Fix:**
```python
try:
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
except json.JSONDecodeError as e:
    ensure(False, "INVALID_REQUEST", f"corrupt registry: {e}")
```

### WR-05: Executor writes "active" status but escalation leaves file inconsistent

**File:** `skills/ll-patch-capture/agents/executor.md:59`
**Issue:** The executor agent is instructed to set `status: "active"` for all patches. When escalation is triggered, the supervisor expects status `"draft"`, but the Python runtime does not update the file's status field. The YAML file says `"active"` while the registry does not contain the entry, creating an inconsistent state.
**Fix:** The runtime should update the patch file status to `"draft"` when escalation is triggered:
```python
if escalation_reasons:
    patch["status"] = "draft"
    with open(patch_path, "w", encoding="utf-8") as f:
        yaml.dump(patch_data, f, default_flow_style=False, allow_unicode=True)
```

### WR-06: Missing conflict-triggered escalation test coverage

**File:** `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py`
**Issue:** The test suite covers escalation for `first_patch_for_feat` and `semantic_patch_requires_src_decision`, but has no test verifying that `detect_conflicts` findings cause `run_skill` to set `escalation_needed: True` and `registered: False`. This is a critical path with no integration test.
**Fix:** Add a test that pre-seeds an active patch with overlapping files, then runs `run_skill` and asserts escalation.

### WR-07: Redundant conditional import of ensure inside except block

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:157-158`
**Issue:** `ensure` is already imported at module level (line 14). The code re-imports it as `_ensure` inside the `except ValueError` block, which is unnecessary and confusing:
```python
except ValueError:
    from cli.lib.errors import ensure as _ensure
    _ensure(False, "INVALID_REQUEST", f"document path outside workspace: {input_value}")
```
**Fix:** Use the top-level `ensure` directly:
```python
except ValueError:
    ensure(False, "INVALID_REQUEST", f"document path outside workspace: {input_value}")
```

## Info

### IN-01: Unused Path import in command.py handlers

**File:** `cli/commands/skill/command.py:68, 103`
**Issue:** `from pathlib import Path` is imported in both the `tech-to-impl` and `patch-capture` handlers but never used in either block.

### IN-02: Magic number 50000 for input_value length limit

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:133`
**Issue:** The value `50000` should be a named constant with documentation explaining the rationale.
**Fix:**
```python
MAX_INPUT_VALUE_LENGTH = 50000  # Max prompt/document size per ADR-049
ensure(len(input_value) <= MAX_INPUT_VALUE_LENGTH, "INVALID_REQUEST", f"input_value too long (max {MAX_INPUT_VALUE_LENGTH} chars)")
```

### IN-03: Test helper uses incorrect source.from value

**File:** `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py:47`
**Issue:** `_make_complete_patch` sets `"from": "prompt"` but the input contract and executor.md specify `source.from` should be `"product_experience"`. The schema validator only checks presence, not value correctness, so this masks regressions.
**Fix:** Change `"from": "prompt"` to `"from": "product_experience"` in the test helper.

### IN-04: validate_input.sh performs only syntactic validation

**File:** `skills/ll-patch-capture/scripts/validate_input.sh:11-23`
**Issue:** The script checks that the file is parseable YAML but does not verify semantic content (required fields per input/contract.yaml). For document-type input, it should at minimum check that expected keys exist.

### IN-05: Supervisor agent prompt mixes CLI and function-call references

**File:** `skills/ll-patch-capture/agents/supervisor.md:17-19`
**Issue:** The prompt tells the agent to run `python -m cli.lib.patch_schema --type patch` (CLI invocation) but also references `validate_file()` (Python function). This dual reference could confuse the LLM about which mechanism to use.
**Fix:** Standardize on one invocation method in the prompt.

### IN-06: run_skill validates document path but never reads document content

**File:** `skills/ll-patch-capture/scripts/patch_capture_runtime.py:150-158`
**Issue:** For `input_type == "document"`, the runtime validates the file exists and is within the workspace, but never reads the file content. Content processing is fully delegated to external LLM agents, meaning the runtime has no verification the document was actually consumed. This is by design but worth noting as a gap in the runtime's responsibility boundary.

### IN-07: Missing test for feat_id too long

**File:** `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py`
**Issue:** The runtime enforces `len(feat_id) <= 128` (line 132) but no test verifies this constraint. Add a test with a feat_id exceeding 128 characters.

---

_Reviewed: 2026-04-16T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
