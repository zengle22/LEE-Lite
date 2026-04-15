skill: ll-qa-api-spec-to-tests
version: "1.0"

## Role
Convert frozen api-test-spec YAML into executable pytest test scripts with embedded evidence collection per ADR-047 Section 6.3.

## Instructions
1. Read the api-test-spec YAML from `{spec_path}`
2. Validate it has all required fields: case_id, coverage_id, endpoint, capability, expected, evidence_required
3. Generate a pytest test file at `{output_dir}/test_{case_id}.py` containing:

   a. **Imports**: pytest, yaml, pathlib, datetime, and requests (or the provided api_client fixture)

   b. **EVIDENCE_DIR constant**:
   ```python
   EVIDENCE_DIR = Path("ssot/tests/.artifacts/evidence")
   ```

   c. **Test class**: `Test{Capability}Case` with docstring showing case_id and coverage_id:
   ```python
   class TestTrainingPlanCase:
       """Test: api_case.plan.create.happy | Coverage: api.training_plan.create.happy"""
   ```

   d. **Test method**: `test_{capability}_{scenario}` that:
      - Sets up preconditions from `spec.preconditions`
      - Builds request from `spec.request` (method, path_params, query_params, headers, body)
      - Captures request snapshot before execution
      - Executes request using the `requests` library or provided `api_client` fixture
      - Asserts `response.status_code == spec.expected.status_code`
      - Iterates `spec.expected.response_assertions` and asserts each
      - Iterates `spec.expected.side_effect_assertions` and asserts each
      - Collects evidence as a YAML dict matching ADR-047 Section 6.3:
        ```python
        evidence = {
            "evidence_record": {
                "case_id": "{case_id}",
                "coverage_id": "{coverage_id}",
                "executed_at": datetime.datetime.utcnow().isoformat() + "Z",
                "run_id": os.environ.get("RUN_ID", "run-unknown"),
                "evidence": {
                    "request_snapshot": {"method": "...", "url": "...", "body": {...}},
                    "response_snapshot": {"status_code": ..., "body": {...}},
                    "assertion_results": [{"assertion": "...", "result": "pass"}],
                },
                "side_effects": [...],
                "execution_status": "success",
            }
        }
        ```
      - Writes evidence to `EVIDENCE_DIR / {run_id} / {coverage_id}.evidence.yaml`:
        ```python
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text(yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True))
        ```

   e. **Error handling**: wrap the entire test body in `try/except`:
      - On exception, write an evidence_record dict with `execution_status: "error"` and include the error message
      - The error evidence_record must still include case_id, coverage_id, executed_at, and run_id
      - Re-raise the exception so pytest marks the test as failed

4. The generated script MUST NOT modify the spec file (specs are frozen contracts)
5. The generated script MUST write evidence YAML for every item in `spec.evidence_required`
6. Each `evidence_required` item must have a corresponding code block that collects and records that evidence type

## Output Format
Write the generated `.py` file to `{output_path}`. The file must be syntactically valid Python and importable by pytest.

## Evidence Collection Requirements
The generated test must collect these evidence types (as specified in `evidence_required`):
- `request_snapshot`: HTTP method, URL, request body before sending
- `response_snapshot`: HTTP status code and response body
- `assertion_result`: result of each response assertion
- `side_effect_assertion`: result of each side-effect assertion
- `db_assertion_result`: database state verification (if applicable)

## Anti-False-Pass Guarantees
- The test must verify the response is NOT a generic error page
- The test must check that the response body contains expected fields, not just status code
- The test must fail if evidence collection fails (do not silently skip evidence writing)
