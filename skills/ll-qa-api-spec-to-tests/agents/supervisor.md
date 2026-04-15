skill: ll-qa-api-spec-to-tests
version: "1.0"

## Supervisor Validation Checklist

Validate each generated pytest test script against the following checklist:

1. Generated `.py` file exists at expected output path
2. File passes `py_compile` (no syntax errors) — run `python -m py_compile <file>`
3. File contains `import pytest`
4. File contains `import yaml`
5. File contains `from pathlib import Path`
6. File contains `EVIDENCE_DIR` constant pointing to `ssot/tests/.artifacts/evidence`
7. File contains test class with correct `case_id` and `coverage_id` in docstring
8. File contains `evidence_record` dict construction matching ADR-047 Section 6.3 structure
9. File contains `yaml.safe_dump` for writing evidence YAML
10. File contains evidence output path with `run_id` for collision avoidance
11. File contains all `evidence_required` items from the input spec
12. File does NOT contain any code that modifies the input spec file (specs are frozen)
13. File has `try/except` error handling that writes evidence on failure
14. File asserts `response.status_code` against `spec.expected.status_code`
15. File iterates and asserts `spec.expected.response_assertions`
16. File iterates and asserts `spec.expected.side_effect_assertions`
17. Evidence writing is inside the test method (not in fixture or conftest)

## Reporting
For each file, report:
- Number of checks passed / total checks
- List of any failed checks with line references
- Overall pass/fail verdict
