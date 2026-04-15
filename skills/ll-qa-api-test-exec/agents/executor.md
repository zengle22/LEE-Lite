skill: ll-qa-api-test-exec
version: "1.0"

## Role
Supervisory executor for API test execution. The actual execution is handled by code (api_test_exec.py), not by this LLM prompt.

## Instructions
1. Verify input files exist: spec_path, test_dir, manifest_path
2. Confirm test_dir contains at least one .py test file
3. Run the execution pipeline via run.sh which:
   a. Validates inputs (validate_input.sh)
   b. Invokes api_test_exec.run_api_test_exec() which:
      - Runs pytest on test_dir
      - Parses junitxml results
      - Validates evidence files against spec.evidence_required
      - Atomically updates manifest
   c. Validates outputs (validate_output.sh)
4. Report execution summary: total cases, passed, failed, evidence files created

## Note
This skill is CODE-DRIVEN. The LLM executor does NOT generate or run tests directly.
All test execution happens through api_test_exec.py via subprocess.
