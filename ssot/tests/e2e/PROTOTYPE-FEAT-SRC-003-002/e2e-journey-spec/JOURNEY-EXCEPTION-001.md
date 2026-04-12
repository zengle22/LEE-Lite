# E2E Journey Spec — JOURNEY-EXCEPTION-001: Skill Bundle 不存在

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.bundle-missing |
| coverage_id | e2e.journey.exception.bundle-missing |
| journey_id | JOURNEY-EXCEPTION-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-002.Scope.canonical-bundle |

## Test Contract

### Entry Point

`ll loop run-execution --start`

### Preconditions

- `skills/l3/ll-execution-loop-job-runner/` directory does NOT exist
- No existing active runner session

### User Steps

1. Operator executes `ll loop run-execution --start`
2. System attempts to verify skill bundle at canonical path
3. System finds bundle does not exist
4. System returns BUNDLE_NOT_FOUND error
5. Operator sees explicit error with bundle path and installation guidance
6. Operator confirms no runner process started

### Expected CLI States

- Step 2: CLI outputs "Verifying skill bundle: skills/l3/ll-execution-loop-job-runner/"
- Step 4: CLI outputs "Error: BUNDLE_NOT_FOUND - Canonical skill bundle not found at skills/l3/ll-execution-loop-job-runner/. Install the bundle before starting the runner."
- Step 4: Exit code != 0
- Step 6: No runner process running

### Expected Network Events

- Skill bundle check: Attempt to read canonical bundle path (fails)
- No session creation
- No ready queue binding

### Expected Persistence

- No session file created
- No run context file created
- No runner process spawned

### Anti-False-Pass Checks

- no_runner_process
- no_session_file
- error_message_contains_bundle_path
- error_message_contains_installation_guidance
- exit_code_nonzero

### Evidence Required

- cli_output_log
- exit_code_capture
- process_list_check (no runner)
- directory_listing (no session files)
