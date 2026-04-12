# E2E Journey Spec — JOURNEY-MAIN-001: 完整生命周期 (Happy Path)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.lifecycle.happy |
| coverage_id | e2e.journey.lifecycle.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-003.AcceptanceChecks.explicit-cli-controls |

## Test Contract

### Entry Point

`ll loop run-execution` (start control command)

### Preconditions

- Runner skill bundle is installed and active
- Job `job-ready-001` exists in ready queue
- No existing active runner session

### User Steps

1. Operator executes `ll loop run-execution`
2. System starts runner and outputs structured start state
3. Operator executes `ll job claim --job-id job-ready-001`
4. System outputs claim confirmation with ownership info
5. Operator executes `ll job run --job-id job-ready-001`
6. System executes job and outputs execution progress
7. System completes job execution and returns execution result
8. Operator executes `ll job complete --job-id job-ready-001`
9. System outputs completion confirmation with structured state
10. Operator verifies output is structured JSON format

### Expected CLI States

- Step 2: JSON output with runner_id, started_at, status="running"
- Step 4: JSON output with job_id, owner=runner_id, claimed_at, status="claimed"
- Step 6: Progress output during execution
- Step 7: JSON output with job_id, execution_result, completed_at
- Step 9: JSON output with job_id, status="completed", state_evidence_ref

### Expected Network Events

- Runner start: Session creation and state persistence
- Job claim: Job state updated from "ready" to "claimed", ownership recorded
- Job run: Skill invocation triggered, execution state tracked
- Job complete: Job state updated to "completed", outcome written

### Expected Persistence

- Runner session file exists
- Job state file shows "completed"
- Ownership record exists
- Command evidence recorded for each control action
- Structured output logged to control surface log

### Anti-False-Pass Checks

- all_control_commands_succeeded (exit code 0 for each)
- structured_output_valid_json (each command produces parseable JSON)
- job_state_completed (not just stdout confirmation)
- command_evidence_exists (one per control action)
- no_console_error
- ownership_record_matches_runner

### Evidence Required

- cli_output_log (all commands)
- json_output_validation
- job_state_file_snapshot
- command_evidence_log
- runner_session_file
- process_status_check
