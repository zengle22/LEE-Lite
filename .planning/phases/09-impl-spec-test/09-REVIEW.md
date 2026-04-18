---
phase: 09-impl-spec-test
reviewed: 2026-04-18T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - cli/lib/silent_override.py
  - cli/lib/test_silent_override.py
  - skills/ll-dev-feat-to-proto/scripts/validate_output.sh
  - skills/ll-dev-feat-to-surface-map/scripts/validate_output.sh
  - skills/ll-dev-feat-to-tech/scripts/validate_output.sh
  - skills/ll-dev-feat-to-ui/scripts/validate_output.sh
  - skills/ll-dev-proto-to-ui/scripts/validate_output.sh
  - skills/ll-dev-tech-to-impl/scripts/validate_output.sh
  - skills/ll-qa-impl-spec-test/scripts/impl_spec_test_skill_guard.py
  - skills/ll-qa-impl-spec-test/tests/test_semantic_stability_dimension.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-04-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Reviewed 10 files implementing semantic stability checking for the frozen-registry (FRZ) based code generation system. The core silent_override.py module is well-structured with a clear data flow: load FRZ, extract anchors, check drift, classify changes, return verdict. The validate_output.sh scripts correctly integrate silent_override checks with appropriate mode selection (full, journey_sm, product_boundary). The impl_spec_test_skill_guard.py properly validates the 9th dimension (semantic_stability) with correct structural and consistency checks. However, several issues were found around error handling robustness, shell script environment variable validation, and test fragility.

## Warnings

### WR-01: Unhandled JSON/YAML parse errors in silent_override.py CLI

**File:** `E:\ai\LEE-Lite-skill-first\cli\lib\silent_override.py:358-375`
**Issue:** When iterating over artifact files in the output directory, `json.loads()` and `yaml.safe_load()` are called without try/except blocks. If any artifact file contains malformed JSON or YAML, the entire CLI command crashes with an unhandled exception rather than returning a structured `CommandError`. This makes it difficult for callers to distinguish between "bad input" and "system error."

**Fix:**
```python
# Around line 361-367, wrap parse operations:
for f in sorted(output_dir.iterdir()):
    if f.suffix in (".json", ".yaml", ".yml"):
        try:
            content = f.read_text(encoding="utf-8")
            if f.suffix == ".json":
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except (json.JSONDecodeError, yaml.YAMLError) as exc:
            return _fail(f"Failed to parse artifact {f.name}: {exc}")
        if isinstance(data, dict):
            output_data.update(data)
```

Apply the same pattern for the single-file branch (lines 368-375).

### WR-02: Empty `$FRZ_ID` environment variable not validated in validate_output.sh scripts

**File:** `E:\ai\LEE-Lite-skill-first\skills\ll-dev-feat-to-proto\scripts\validate_output.sh:14` (and 5 other validate_output.sh scripts with same pattern)
**Issue:** All six validate_output.sh scripts pass `--frz "$FRZ_ID"` to `silent_override.py check` without first validating that `FRZ_ID` is set and non-empty. While `set -u` will catch an entirely unset variable, it will NOT catch `FRZ_ID=""` (explicitly set to empty string). This results in the script proceeding with `--frz ""`, which then fails deeper in the Python code with a less helpful error. The validation should fail fast with a clear message at the shell level.

**Fix:** Add this guard before the `silent_override.py check` call in each script:
```bash
if [ -z "${FRZ_ID:-}" ]; then
  echo "ERROR: FRZ_ID environment variable is not set"
  exit 2
fi
```

Affected files:
- `skills/ll-dev-feat-to-proto/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-surface-map/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-tech/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-ui/scripts/validate_output.sh`
- `skills/ll-dev-proto-to-ui/scripts/validate_output.sh`
- `skills/ll-dev-tech-to-impl/scripts/validate_output.sh`

### WR-03: Recovery handling validation bypassed (warnings logged but not blocking)

**File:** `E:\ai\LEE-Lite-skill-first\skills\ll-qa-impl-spec-test\scripts\impl_spec_test_skill_guard.py:320-326`
**Issue:** The `_validate_recovery_handling` function detects missing recovery handling fields for features that involve state changes, database operations, API calls, etc. (line 148-167 defines patterns like "migration", "rollback", "state_change"). However, when recovery errors are found, they are only printed as warnings to stderr and do not cause validation to fail (lines 321-326). The comment says "In strict mode, this could be made into a blocking error." If recovery handling is genuinely required for these feature types, silently bypassing the check undermines the safety guarantee.

**Fix:** Either make this a blocking validation failure, or add an explicit `--strict` CLI flag that controls whether recovery handling is enforced. At minimum, the current behavior should be documented in the function docstring and the guard should return a non-zero exit code when recovery errors exist.

```python
# Option: Make it blocking
if recovery_errors:
    for error in recovery_errors:
        print(f"[ERROR] Recovery handling: {error}", file=sys.stderr)
    return _fail("Recovery handling validation failed")
```

### WR-04: Variable shadowing of `payload` in impl_spec_test_skill_guard.py

**File:** `E:\ai\LEE-Lite-skill-first\skills\ll-qa-impl-spec-test\scripts\impl_spec_test_skill_guard.py:208, 337`
**Issue:** The variable name `payload` is assigned at line 208 to hold the main response JSON object. Then inside the deep review validation loop at line 337, the same variable name `payload` is reassigned to hold individual ref file contents (`payload = _load_json_any(ref_path)`). While the outer `payload` is not used again after line 337 (so no runtime bug occurs), this shadowing makes the code harder to reason about and could cause issues if future maintainers reference `payload` expecting the outer value.

**Fix:** Rename the inner variable to `ref_payload` or `ref_content`:
```python
ref_content = _load_json_any(ref_path)
if not isinstance(ref_content, (dict, list)):
    raise ValueError(f"response.data.{ref_field} must be JSON object or array")
```

## Info

### IN-01: Fragile sys.path manipulation in test_semantic_stability_dimension.py

**File:** `E:\ai\LEE-Lite-skill-first\skills\ll-qa-impl-spec-test\tests\test_semantic_stability_dimension.py:13-22`
**Issue:** The test file uses `Path(__file__).resolve().parents[6]` to compute the project root. This `parents[6]` offset is fragile -- if the test file is moved even one directory level, or if the project structure changes, the path calculation breaks silently and the imports fail. Similarly, `parents[1] / "scripts"` assumes a fixed directory layout.

**Fix:** Use a more robust approach, such as a conftest.py at the project root that adds to sys.path, or use a marker file (like `pyproject.toml` or `setup.py`) to locate the project root:
```python
def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Cannot find project root")

PROJECT_ROOT = _find_project_root()
```

### IN-02: Missing `anchors_checked` field validation in semantic_stability dimension

**File:** `E:\ai\LEE-Lite-skill-first\skills\ll-qa-impl-spec-test\scripts\impl_spec_test_skill_guard.py:299`
**Issue:** The test file (`test_semantic_stability_dimension.py` line 125) includes `anchors_checked` as part of the valid semantic_stability dimension data, but the guard's required fields list at line 299 only requires `["checked", "frz_refs", "semantic_drift", "verdict"]`. The `anchors_checked` field is not validated, meaning a caller could omit it and still pass validation. If `anchors_checked` is part of the semantic_stability contract, it should be in the required fields list.

**Fix:** Add `"anchors_checked"` to `_semantic_stability_required_fields` if it is a required part of the dimension schema:
```python
_semantic_stability_required_fields = ["checked", "frz_refs", "anchors_checked", "semantic_drift", "verdict"]
```

### IN-03: Brittle string parsing for extra field extraction

**File:** `E:\ai\LEE-Lite-skill-first\cli\lib\silent_override.py:285-293`
**Issue:** The `_parse_extra_fields` function extracts field names by splitting on the literal string `"extra fields:"` in the detail string. This couples `silent_override.py` to the exact format produced by `check_drift` in `drift_detector.py` (line 193: `f"Anchor {anchor_id} has extra fields: {', '.join(sorted(extra_keys))}"`). If the detail format in `drift_detector.py` ever changes, `_parse_extra_fields` will silently return an empty list, causing new fields to go undetected.

**Fix:** Consider having `check_drift` return extra field names as a structured field on `DriftResult` (e.g., `extra_fields: list[str] | None = None`) rather than embedding them in a human-readable detail string. This eliminates the string parsing dependency:
```python
@dataclass(frozen=True)
class DriftResult:
    anchor_id: str
    frz_ref: str
    has_drift: bool
    drift_type: str
    detail: str
    extra_fields: list[str] | None = None  # Populated when drift_type == "new_field"
```

---

_Reviewed: 2026-04-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
