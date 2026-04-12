# E2E Journey Spec — JOURNEY-EXCEPTION-001: Hold Job 被阻止自动派发

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.hold-blocked |
| coverage_id | e2e.journey.exception.hold-blocked |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-005.Constraints.no-auto-dispatch-hold |

## Test Contract

### Entry Point

Automatic: Runner attempting to process a job with progression_mode=hold

### Preconditions

- Job `job-hold-001` exists with progression_mode = "hold"
- Job is in running state (claimed by runner)
- Target next skill exists and is accessible

### User Steps

1. Runner attempts to process job-hold-001
2. System detects progression_mode = "hold"
3. System blocks auto-dispatch
4. System returns HOLD_NOT_DISPATCHABLE message
5. Job remains in current state (not dispatched, not removed from queue)
6. Operator verifies no invocation was created

### Expected CLI States

- Step 2: Runner log: "Progression mode: hold -> auto-dispatch BLOCKED"
- Step 4: Runner log: "Job job-hold-001: HOLD_NOT_DISPATCHABLE - waiting for operator precondition"
- Step 5: Job state unchanged
- Step 6: No invocation file for this job

### Expected Network Events

- Job state read: Read job-hold-001 to check progression_mode
- No skill invocation
- No invocation record write
- Audit log: Record of blocked dispatch attempt

### Expected Persistence

- Job state unchanged (still in its prior state)
- No invocation file created
- Audit log records the blocked attempt with reason

### Anti-False-Pass Checks

- no_invocation_file
- job_state_unchanged
- block_reason_logged
- no_skill_invocation_occurred
- audit_log_has_blocked_attempt

### Evidence Required

- runner_log (showing block detection)
- no_invocation_check
- job_state_file_unchanged
- audit_log_entry
