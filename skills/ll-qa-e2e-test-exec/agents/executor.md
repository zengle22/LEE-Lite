# Executor: ll-qa-e2e-test-exec

## Role
Supervisory executor for E2E test execution. The actual execution is handled by code (e2e_test_exec.py), not by this LLM prompt.

## Instructions
1. Verify input files exist: spec_path, test_dir, manifest_path
2. Confirm test_dir contains at least one .spec.ts Playwright test file
3. Run the execution pipeline via run.sh which:
   a. Validates inputs (validate_input.sh)
   b. Ensures Playwright installed (npm install, npx playwright install chromium)
   c. Invokes e2e_test_exec.run_e2e_test_exec() which:
      - Copies .spec.ts files into Playwright project
      - Runs npx playwright test with JSON reporter
      - Parses Playwright JSON results
      - Validates evidence files against e2e_spec.evidence_required
      - Atomically updates manifest
   d. Validates outputs (validate_output.sh)
4. Report execution summary: total cases, passed, failed, evidence files created

## Note
This skill is CODE-DRIVEN. The LLM executor does NOT generate or run tests directly.
All test execution happens through e2e_test_exec.py via subprocess.
