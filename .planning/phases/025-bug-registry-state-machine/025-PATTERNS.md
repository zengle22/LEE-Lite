# Phase 25: Bug Registry & State Machine - Pattern Map

**Mapped:** 2026-04-29
**Files analyzed:** 7 (3 new, 4 modified)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `cli/lib/bug_registry.py` (NEW) | registry | CRUD + state-machine | `cli/lib/frz_registry.py` | exact |
| `cli/lib/bug_phase_generator.py` (NEW) | generator | file-I/O | `cli/lib/test_exec_reporting.py` (build_execution_refs) | partial |
| `cli/lib/test_orchestrator.py` (MOD) | orchestrator | request-response | self (existing) | exact |
| `cli/lib/test_exec_reporting.py` (MOD) | reporter | transform | self (existing) | exact |
| `cli/commands/skill/command.py` (MOD) | controller | request-response | self (existing) | exact |
| `cli/lib/test_bug_registry.py` (NEW) | test | -- | `cli/lib/test_frz_registry.py` | exact |
| `cli/lib/test_bug_phase_generator.py` (NEW) | test | -- | `cli/lib/test_frz_registry.py` | exact |

## Pattern Assignments

### `cli/lib/bug_registry.py` (registry, CRUD + state-machine)

**Analog:** `cli/lib/frz_registry.py`

**Imports pattern** (lines 1-20 of frz_registry.py):
```python
from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent, read_text, write_text
```

Additional imports for bug_registry (from RESEARCH.md):
```python
import hashlib
import uuid
```

**YAML atomic write pattern** (frz_registry.py lines 45-66 -- copy verbatim):
```python
def _save_registry(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to YAML using atomic write (temp file + os.replace)."""
    ensure_parent(path)
    content = yaml.dump(
        {"frz_registry": records},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    dir_name = path.parent
    fd, temp_path = tempfile.mkstemp(dir=str(dir_name), suffix=".yaml.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, str(path))
    except BaseException:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
```

**Adaptation for bug_registry:** Replace `{"frz_registry": records}` with `{"bug_registry": registry_dict}` where registry_dict contains schema_version, feat_ref, bugs list, version field.

**Registry load pattern** (frz_registry.py lines 31-42):
```python
def _load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = read_text(path)
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return []
    return data.get("frz_registry", [])
```

**Adaptation for bug_registry:** Returns full registry dict (not list), keyed by `"bug_registry"`. Returns `_empty_registry()` when file missing.

**Error pattern** (frz_registry.py lines 96-101):
```python
raise CommandError(
    "INVALID_REQUEST",
    f"Invalid FRZ ID format: {frz_id}. Must match FRZ-xxx",
)
```

**State machine transition matrix** (from RESEARCH.md, design ref: state_machine_executor.py lines 318-337):
```python
BUG_STATE_TRANSITIONS: dict[str, set[str]] = {
    "detected":         {"open", "wont_fix", "duplicate"},
    "open":             {"fixing", "wont_fix", "duplicate"},
    "fixing":           {"fixed", "wont_fix", "duplicate"},
    "fixed":            {"re_verify_passed", "open", "wont_fix", "duplicate"},
    "re_verify_passed": {"closed", "wont_fix", "duplicate"},
    "archived":         {"wont_fix", "duplicate", "not_reproducible"},
    "closed":           set(),
    "wont_fix":         set(),
    "duplicate":        set(),
    "not_reproducible": set(),
}
```

**State transition function** (from RESEARCH.md):
- Validate: `if new_status not in valid` + special case for wont_fix/duplicate from any non-terminal
- Terminal field requirements: wont_fix requires reason, duplicate requires duplicate_of
- Immutable return: `new_bug = {**bug, "status": new_status}`
- Trace append: `new_bug["trace"] = [*bug.get("trace", []), {"event": "status_changed", ...}]`

**Optimistic lock pattern** (test_orchestrator.py lines 116-148):
```python
expected_version = manifest_root.get("_version", manifest.get("_version", "0"))
# ... perform updates ...
manifest_root["_version"] = str(uuid.uuid4())
manifest_root["_last_updated"] = _timestamp()
```

**Adaptation:** Registry root gets `version` field (UUID). Read-modify-write as single atomic operation. On version mismatch, raise `CommandError("CONFLICT", "Registry version conflict")`.

**Timestamp helper** (test_orchestrator.py line 27-29):
```python
def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

---

### `cli/lib/bug_phase_generator.py` (generator, file-I/O)

**Analog:** `cli/lib/test_exec_reporting.py` (build_execution_refs pattern -- lines 326-348)

**Imports pattern:**
```python
from __future__ import annotations

from pathlib import Path
from typing import Any
```

Uses `cli/lib/fs.py` helpers: `ensure_parent`, `write_text`, `write_json`.

**Directory creation pattern** (test_exec_reporting.py lines 184-185):
```python
bug_path.parent.mkdir(parents=True, exist_ok=True)
```

**File generation pattern** (test_exec_reporting.py -- write_text usage):
```python
write_text(workspace_root / refs["test_report_ref"], render_report(...))
write_json(workspace_root / refs["results_summary_ref"], summary)
```

**PLAN.md 6-task template** (from RESEARCH.md lines 600-635):
- Task 1: Root Cause Analysis (auto)
- Task 2: Implement Fix (auto)
- Task 3: Update Bug Status (auto, fixing -> fixed)
- Task 4: Verify Fix (auto, fixed -> re_verify_passed)
- Task 5: Review & Close (auto, re_verify_passed -> closed)
- Task 6: Update Failure Case (auto)

**Directory structure to generate:**
```
.planning/phases/{N}-bug-fix-{bug_id}/
  CONTEXT.md
  PLAN.md
  DISCUSSION-LOG.md
  SUMMARY.md
```

---

### `cli/lib/test_orchestrator.py` (MODIFIED -- add on_complete callback)

**Current signature** (lines 152-164):
```python
def run_spec_test(
    workspace_root: Path,
    *,
    feat_ref: str | None = None,
    proto_ref: str | None = None,
    base_url: str = "http://localhost:8000",
    app_url: str = "http://localhost:3000",
    api_url: str | None = None,
    modality: str = "api",
    coverage_mode: str = "smoke",
    resume: bool = False,
    resume_from: str | None = None,
) -> StepResult:
```

**Modification:** Add `on_complete` parameter:
```python
from typing import Any, Callable

def run_spec_test(
    ...existing params...,
    on_complete: Callable[..., None] | None = None,  # NEW
) -> StepResult:
```

**Callback invocation point** -- insert after line 295 (`update_manifest` call), before Step Result return (line 300):
```python
    # -------------------------------------------------------------------------
    # Step 4.5: on_complete callback (Phase 25 integration point)
    # -------------------------------------------------------------------------
    if on_complete is not None:
        on_complete(workspace_root, feat_ref, proto_ref, run_id, case_results)
```

**Critical:** test_orchestrator.py must NOT import bug_registry. The callback injection pattern keeps the dependency inverted (D-05).

---

### `cli/commands/skill/command.py` (MODIFIED -- wire callback)

**Current pattern** (lines 141-156, qa-test-run handler):
```python
if ctx.action == "qa-test-run":
    from cli.lib.test_orchestrator import run_spec_test

    feat_ref = ctx.payload.get("feat_ref")
    ...
    result = run_spec_test(
        workspace_root=ctx.workspace_root,
        feat_ref=feat_ref,
        ...
    )
```

**Modification:** Import sync_bugs_to_registry and pass as callback:
```python
if ctx.action == "qa-test-run":
    from cli.lib.test_orchestrator import run_spec_test
    from cli.lib.bug_registry import sync_bugs_to_registry

    ...
    result = run_spec_test(
        workspace_root=ctx.workspace_root,
        feat_ref=feat_ref,
        ...,
        on_complete=sync_bugs_to_registry,  # NEW
    )
```

Same for the "both" chain branch (lines 156-167, 168-178) -- pass on_complete to both API and E2E calls.

---

### `cli/lib/test_exec_reporting.py` (MODIFIED -- upgrade build_bug_bundle)

**Current implementation** (lines 174-201):
```python
def build_bug_bundle(case_results: list[dict[str, Any]], output_root: Path, workspace_root: Path) -> str:
    bug_root = output_root / "bugs"
    bugs = []
    for item in case_results:
        if item["status"] != "failed":
            continue
        digest = hashlib.sha1(str(item["case_id"]).encode("utf-8")).hexdigest()[:10]
        bug_id = f"BUG-{slugify(item['case_id'])[:48]}-{digest}"
        ...
        write_json(bug_path, {
            "bug_id": bug_id,
            "case_id": item["case_id"],
            "title": item["title"],
            "actual": item["actual"],
            "expected": item["expected"],
            "evidence_ref": item["evidence_ref"],
        })
```

**Required changes (minimal diff):**
1. Add optional `run_id` parameter (default None for backward compat)
2. Add `status: "detected"` and `gap_type` fields to each bug JSON
3. Switch hash from SHA1 to MD5 (D-06): `hashlib.md5(...).hexdigest()[:6].upper()`
4. Include `run_id` in hash input when available
5. Add `diagnostics` array: `item.get("diagnostics", [])[:5]`

**gap_type inference** (from RESEARCH.md):
```python
def _infer_gap_type(case_result: dict[str, Any]) -> str:
    diagnostics = case_result.get("diagnostics", [])
    for d in diagnostics:
        dl = str(d).lower()
        if any(kw in dl for kw in ("timeout", "connection reset", "flaky", "intermittent")):
            return "env_issue"
    return "code_defect"
```

---

### `cli/lib/test_bug_registry.py` (NEW -- unit tests)

**Analog:** `cli/lib/test_frz_registry.py`

**Test fixture pattern** (test_frz_registry.py lines 22-25):
```python
@pytest.fixture
def tmp_workspace() -> Path:
    """Create a temporary workspace directory."""
    return Path(tempfile.mkdtemp())
```

**Test style** (test_frz_registry.py -- one test per behavior):
```python
@pytest.mark.unit
def test_register_frz_success(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True, "present": ["product_boundary"]}
    record, frz_id = register_frz(tmp_workspace, ...)
    assert record["frz_id"] == "FRZ-001"
    assert record["status"] == "frozen"
```

**Error assertion pattern** (test_frz_registry.py lines 47-53):
```python
with pytest.raises(CommandError) as exc_info:
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg2")
assert exc_info.value.status_code == "INVALID_REQUEST"
assert "already registered" in exc_info.value.message
```

**Persistence verification pattern** (test_frz_registry.py lines 157-166):
```python
updated = update_frz_status(tmp_workspace, "FRZ-001", "superseded")
assert updated["status"] == "superseded"
result = get_frz(tmp_workspace, "FRZ-001")
assert result is not None
assert result["status"] == "superseded"
```

**Required test cases** (from RESEARCH.md Wave 0):
- test_load_or_create -- registry creation on first use
- test_optimistic_lock -- version field write
- test_happy_path_transitions -- detected->open->fixing->fixed->re_verify_passed->closed
- test_invalid_transition -- raises CommandError
- test_wont_fix_requires_reason -- terminal state validation
- test_duplicate_requires_ref -- terminal state validation
- test_not_reproducible_thresholds -- auto-mark logic
- test_resurrection_new_record -- new bug_id with resurrected_from
- test_gap_type_inference -- env_issue vs code_defect
- test_sync_persists -- sync_bugs_to_registry writes YAML

---

### `cli/lib/test_bug_phase_generator.py` (NEW -- unit tests)

**Analog:** `cli/lib/test_frz_registry.py` (same fixture pattern)

**Required test cases:**
- test_phase_dir_structure -- generated dir contains CONTEXT.md + PLAN.md + DISCUSSION-LOG.md + SUMMARY.md
- test_mini_batch -- --batch mode groups 2-3 same-module bugs

---

## Shared Patterns

### YAML Atomic Write
**Source:** `cli/lib/frz_registry.py` lines 45-66
**Apply to:** `cli/lib/bug_registry.py` (_save_registry function)
**Pattern:** `tempfile.mkstemp(dir=...)` -> `yaml.dump()` -> `os.replace()` with cleanup on failure

### CommandError for Validation
**Source:** `cli/lib/errors.py` lines 33-49
**Apply to:** `cli/lib/bug_registry.py` (invalid transitions, missing fields), `cli/lib/bug_phase_generator.py`
```python
raise CommandError("INVALID_REQUEST", "descriptive message")
raise CommandError("REGISTRY_MISS", "not found message")
```

### StepResult Contract
**Source:** `cli/lib/contracts.py` lines 14-36
**Apply to:** `cli/lib/bug_registry.py` (sync_bugs_to_registry returns None but callers use StepResult)

### _timestamp() Helper
**Source:** `cli/lib/test_orchestrator.py` lines 27-29
**Apply to:** `cli/lib/bug_registry.py` (copy verbatim)
```python
def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

### Immutability (No Mutation)
**Source:** `rules/python/coding-style.md`
**Apply to:** All new files -- return new dicts instead of modifying in place
```python
# CORRECT: immutable transition
new_bug = {**bug, "status": new_status}
new_bug["trace"] = [*bug.get("trace", []), trace_entry]
```

### Test Organization
**Source:** `cli/lib/test_frz_registry.py`
**Apply to:** `cli/lib/test_bug_registry.py`, `cli/lib/test_bug_phase_generator.py`
- `@pytest.mark.unit` on all tests
- `tmp_workspace` fixture using `tempfile.mkdtemp()`
- Import from `cli.lib.errors import CommandError` for error assertions
- One assertion group per test function

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| (none) | -- | -- | All files have at least partial analogs |

## Metadata

**Analog search scope:** `cli/lib/`, `cli/commands/skill/`
**Files scanned:** 8 (frz_registry.py, test_frz_registry.py, test_orchestrator.py, state_machine_executor.py, test_exec_reporting.py, errors.py, contracts.py, command.py)
**Pattern extraction date:** 2026-04-29
