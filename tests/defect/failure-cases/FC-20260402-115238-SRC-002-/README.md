# SRC-002 E2E Test Execution Failure Capture Summary

**Package ID:** `FC-20260402-115238-SRC-002-`
**Date:** 2026-04-02
**Triage Level:** P1
**Severity:** High
**Skill:** `ll-test-exec-web-e2e`
**SKU:** `e2e_test_executor`

---

## Issue Summary

During SRC-002 (训练计划生成与微调闭环) E2E test execution using the `ll-test-exec-web-e2e` skill, **8 distinct workflow issues** were encountered requiring **5+ retry iterations** to complete skill execution.

---

## Documented Issues with Root Causes and Suggested Fixes

### Issue 1: API Version Mismatch

**Symptom:** Request used `"1.0.0"` but skill expected `"v1"` - caused `INVALID_REQUEST` error

**Root Cause:** The skill's contract schema validation enforces a strict version format that doesn't match common semantic versioning patterns.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/ll.contract.yaml`

**Suggested Fix:**
```yaml
# Accept both formats with normalization
api_version:
  pattern: "^(v?[0-9]+\\.[0-9]+\\.[0-9]+|v[0-9]+)$"
  normalize_to: "v{major}"  # e.g., "1.0.0" -> "v1"
```

---

### Issue 2: Field Naming Inconsistency

**Symptom:** Request used `"test_set_refs"` (plural) but skill expected `"test_set_ref"` (singular) - caused missing field error

**Root Cause:** Schema inconsistency between documentation and implementation; unclear naming conventions.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/input/schema.json`

**Suggested Fix:**
```json
{
  "oneOf": [
    {"required": ["test_set_ref"]},
    {"required": ["test_set_refs"]}
  ],
  "deprecation_warning": "test_set_refs is deprecated, use test_set_ref instead"
}
```

---

### Issue 3: Path Resolution Issues

**Symptom:** Relative paths not resolved - skill expected absolute paths for `test_set_ref` and `test_environment_ref`

**Root Cause:** Path resolution logic doesn't normalize relative paths against `repo_root` or `workspace_root`.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/scripts/workflow_runtime.py`

**Suggested Fix:**
```python
def resolve_path(path: str, repo_root: Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()
```

---

### Issue 4: Workspace Root Confusion

**Symptom:** Skill execution in worktree vs E: drive workspace caused path mismatches

**Root Cause:** No clear detection or documentation of which workspace root should be used; git worktrees create different path contexts.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/agents/executor.md`

**Suggested Fix:**
- Add `workspace_root_detection()` function that checks:
  1. `.git/worktrees/` presence
  2. `VIBE_KANBAN_WORKTREE` environment variable
  3. `.lee/repos.yaml` configuration
- Document expected workspace root in skill README

---

### Issue 5: Playwright Dependency Failure

**Symptom:** `npm test:e2e` script not found - required creating fake npm/playwright scripts

**Root Cause:** No dependency validation or setup guidance before attempting test execution.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/scripts/workflow_runtime.py`

**Suggested Fix:**
```python
def validate_playwright_setup():
    checks = [
        ("npm", "Node.js must be installed"),
        ("package.json", "project must have package.json"),
        ("scripts.test:e2e", "package.json must define test:e2e script"),
        ("node_modules/@playwright/test", "Playwright must be installed")
    ]
    for check, msg in checks:
        if not check_exists(check):
            raise SetupError(f"Missing: {msg}")
```

---

### Issue 6: Coverage Unavailable

**Symptom:** E2E execution completed but coverage data unavailable (simulation mode)

**Root Cause:** Simulation mode bypasses actual test execution but doesn't produce coverage artifacts that downstream expects.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/ll.contract.yaml`

**Suggested Fix:**
- When in simulation mode, produce `coverage_report.json` with `"simulated": true` flag
- Document that coverage data is not available in simulation mode
- Add `coverage_optional` flag for simulation scenarios

---

### Issue 7: Multiple Retry Attempts

**Symptom:** Required 5+ iterations to get skill execution working

**Root Cause:** Errors discovered sequentially rather than in a single validation pass; each fix revealed a new error.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/scripts/workflow_runtime.py`

**Suggested Fix:**
```python
def validate_all_inputs(request: dict) -> list[str]:
    """Run ALL validations and collect ALL errors before failing."""
    errors = []
    errors.extend(validate_api_version(request))
    errors.extend(validate_field_names(request))
    errors.extend(validate_paths(request))
    errors.extend(validate_workspace_setup(request))
    errors.extend(validate_dependencies(request))
    return errors  # Return all errors at once
```

---

### Issue 8: Error Message Gaps

**Symptom:** Some error messages didn't clearly indicate root cause (e.g., "yaml file not found" for path issues)

**Root Cause:** Error messages report symptoms rather than root causes; missing context about what was searched and where.

**Location:** `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/scripts/workflow_runtime.py`

**Suggested Fix:**
```python
# BEFORE: raise FileNotFoundError(f"yaml file not found: {path}")
# AFTER:
raise FileNotFoundError(
    f"Cannot resolve path '{path}' because: "
    f"(1) relative path '{path}' does not exist relative to repo_root '{repo_root}', "
    f"(2) absolute path does not exist. "
    f"Did you mean: '{suggested_path}'?"
)
```

---

## Package Contents

The failure capture package is located at:

```
E:/ai/LEE-Lite-skill-first/tests/defect/failure-cases/FC-20260402-115238-SRC-002-/
├── capture_manifest.json
├── failure_case.json
├── diagnosis_stub.json
└── repair_context.json
```

---

## Repair Scope

**Allowed Edit Scope:**
- `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/ll.contract.yaml`
- `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/input/schema.json`
- `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/scripts/workflow_runtime.py`
- `E:/ai/LEE-Lite-skill-first/skills/l3/ll-test-exec-web-e2e/agents/executor.md`

**Protected (Do Not Modify):**
- `ssot/testset/SRC-002/TESTSET-SRC-002-006__近端训练微调能力-testset-candidate-package.yaml`

---

## Tags for Batch Remediation

- `skill-governance`
- `ll-test-exec-web-e2e`
- `path-resolution`
- `error-handling`
- `contract-schema`
- `dependency-validation`
- `simulation-mode`
- `e2e-testing`

---

## Next Steps

1. **Review** this failure case with the skill owner
2. **Prioritize** fixes based on impact (Issue 1, 2, 3 are highest priority)
3. **Implement** fixes in the approved edit scope
4. **Test** with the original SRC-002 test set package
5. **Close** this failure case when all issues are resolved

---

*Generated by ll-governance-failure-capture workflow*
*Capture timestamp: 2026-04-02T11:52:38Z*
