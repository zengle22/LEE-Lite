# E2E Journey Spec — JOURNEY-EXCEPTION-001: 运行未 Claim 的 Job

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.unclaimed-run |
| coverage_id | e2e.journey.exception.unclaimed-run |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-003.Constraints.lifecycle-mapping |

## Test Contract

### Entry Point

`ll job run --job-id job-ready-003`

### Preconditions

- Runner is active
- Job `job-ready-003` exists in ready queue but has NOT been claimed
- No existing ownership record for this job

### User Steps

1. Operator executes `ll job run --job-id job-ready-003` without prior claim
2. System detects job has not been claimed
3. System returns JOB_NOT_CLAIMED error
4. System does not execute the job
5. Operator sees guidance to claim first

### Expected CLI States

- Step 3: CLI outputs "Error: JOB_NOT_CLAIMED - Job job-ready-003 has not been claimed. Run 'll job claim --job-id job-ready-003' first."
- Step 3: Exit code != 0
- Step 5: Error message includes correct claim command

### Expected Network Events

- Job state read: GET job-ready-003 state (shows "ready", not "claimed")
- No skill invocation
- No state change

### Expected Persistence

- Job state unchanged (still "ready")
- No ownership record created
- No execution result written
- Audit log records the rejected attempt

### Anti-False-Pass Checks

- job_state_unchanged
- no_skill_invocation_occurred
- no_ownership_record
- error_message_contains_claim_command
- exit_code_nonzero
- audit_log_entry_exists

### Evidence Required

- cli_output_log
- exit_code_capture
- job_state_file_before_and_after
- no_ownership_check
- audit_log_entry
