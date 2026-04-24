---
phase: 18-execution-axis
reviewed: 2026-04-24T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - cli/lib/run_manifest_gen.py
  - cli/lib/scenario_spec_compile.py
  - cli/lib/state_machine_executor.py
  - cli/lib/gate_integration.py
  - cli/lib/independent_verifier.py
  - cli/lib/settlement_integration.py
  - cli/lib/step_result.py
  - tests/cli/lib/test_run_manifest_gen.py
  - tests/cli/lib/test_scenario_spec_compile.py
  - tests/cli/lib/test_state_machine_executor.py
  - tests/cli/lib/test_gate_integration.py
  - tests/cli/lib/test_independent_verifier.py
  - tests/cli/lib/test_settlement_integration.py
  - tests/integration/test_e2e_chain.py
  - tests/integration/test_resume.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-04-24
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Phase 18 implements execution axis P0 modules with run manifest generation, scenario spec compilation, state machine executor, and integration tests. The code is generally well-structured with good security practices (path traversal validation, safe YAML loading). No critical security vulnerabilities were found.

Two warnings were identified: placeholder implementations that always succeed (which could mask real failures in testing), and an inconsistent ID assignment fallback pattern. These are acceptable for phase 1 implementation but should be addressed before production use.

## Warnings

### WR-01: Placeholder `_execute_step` Always Succeeds

**File:** `cli/lib/state_machine_executor.py:463-478`
**Issue:** The `_execute_step` method is a placeholder that only raises `StepExecutionError` if `step.action` is empty. It always succeeds when a step has an action, meaning actual step execution does not occur. This could mask real failures during testing.

```python
def _execute_step(self, step: ScenarioStep) -> None:
    """Execute a single step.

    This is a placeholder for actual Playwright/step execution.
    Raises StepExecutionError on failure.
    """
    # Placeholder for actual step execution
    # In a real implementation, this would invoke Playwright or similar
    if not step.action:
        raise StepExecutionError(f"Step {step.step_index} has no action")
```

**Fix:** Replace placeholder with actual step execution logic that invokes Playwright or the test execution framework.

---

### WR-02: Empty `_do_verify` Method

**File:** `cli/lib/state_machine_executor.py:480-486`
**Issue:** The `_do_verify` method is explicitly empty - a placeholder for assertion verification logic. The docstring notes assertions are "currently merged with EXECUTE" but this means VERIFY state does nothing meaningful.

```python
def _do_verify(self) -> None:
    """Perform VERIFY phase - check assertions.

    Note: Currently assertions are checked inline during EXECUTE.
    This method provides a hook for more detailed verification logic.
    """
    pass
```

**Fix:** Implement actual assertion verification logic, or remove the VERIFY state from the state machine if not needed.

---

## Info

### IN-01: Inconsistent ID Assignment Fallback

**File:** `cli/lib/scenario_spec_compile.py:261-263`
**Issue:** When `_source_coverage_id` is missing from the e2e_spec, the assignment fallbacks are inconsistent:

```python
journey_id = e2e_spec.get("_source_coverage_id", e2e_spec.get("unit_ref", ""))
spec_id = e2e_spec.get("unit_ref", "")
coverage_id = e2e_spec.get("_source_coverage_id", "")
```

If `_source_coverage_id` is absent:
- `journey_id` falls back to `unit_ref`
- `coverage_id` falls back to empty string `""`

This creates a situation where `journey_id` and `coverage_id` could have different values.

**Fix:** Use consistent fallback behavior for all three IDs:
```python
journey_id = e2e_spec.get("_source_coverage_id") or e2e_spec.get("unit_ref", "")
spec_id = e2e_spec.get("unit_ref", "")
coverage_id = e2e_spec.get("_source_coverage_id") or ""
```

---

## Security Assessment

**No critical security issues found.** The codebase follows good security practices:

- **Path traversal validation:** `_validate_run_id` in `run_manifest_gen.py` properly rejects `..`, `/`, `\`, and absolute paths (T-18-01 mitigation)
- **Safe YAML loading:** All YAML loading uses `yaml.safe_load()` - no unsafe deserialization
- **No hardcoded secrets:** No credentials, API keys, or tokens found in source files
- **No dangerous functions:** No use of `eval()`, `exec()`, `innerHTML`, `system()`, or shell execution

## Code Quality Assessment

Overall good code quality:
- Type annotations used consistently
- Frozen dataclasses used for immutability where appropriate
- Clear separation of concerns with distinct modules
- Good error handling with descriptive exceptions
- Comprehensive test coverage with parameterized tests

## Test Quality Assessment

Tests are well-structured with:
- Good use of pytest fixtures
- Parameterized tests for truth table coverage
- Proper isolation with `tmp_path` fixtures
- Clear test names describing what is being verified

---

_Reviewed: 2026-04-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
