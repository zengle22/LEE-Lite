# E2E Journey Spec — JOURNEY-EXCEPTION-001: 并发 Claim 竞争

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.concurrent-claim |
| coverage_id | e2e.journey.exception.concurrent-claim |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-004.Constraints.single-owner |

## Test Contract

### Entry Point

Automatic: Two Runner instances simultaneously scanning and claiming the same job

### Preconditions

- Two Runner instances (Runner-A and Runner-B) are active
- Job file `job-ready-001.json` exists in `artifacts/jobs/ready/`
- No existing ownership record
- Both runners are configured to scan the same ready queue

### User Steps

1. Both Runner instances simultaneously discover job-ready-001
2. Runner-A executes claim first (by minimal time difference)
3. System accepts Runner-A's claim, marks owner=Runner-A
4. Runner-B executes claim immediately after
5. System rejects Runner-B's claim with ALREADY_CLAIMED error
6. Operator verifies only Runner-A has ownership record
7. Operator verifies Runner-B did not create any ownership record

### Expected CLI States

- Step 3: Runner-A log output: "Claimed job job-ready-001 (owner: runner-a)"
- Step 5: Runner-B log output: "Claim rejected for job-ready-001: ALREADY_CLAIMED by runner-a"
- Runner-B continues scanning for other available jobs

### Expected Network Events

- Runner-A: Successful claim -> state update + ownership write
- Runner-B: Failed claim -> state read shows already claimed, no write
- Both runners: State read to check current job status

### Expected Persistence

- Single ownership record for Runner-A
- No ownership record for Runner-B
- Job state file shows "running" with owner=runner-a
- Audit log records both claim attempts

### Anti-False-Pass Checks

- exactly_one_ownership_record
- owner_is_runner_a
- no_runner_b_ownership
- job_state_shows_correct_owner
- audit_log_shows_both_attempts
- no_console_error

### Evidence Required

- runner_a_claim_log
- runner_b_rejection_log
- ownership_file_snapshot (single file)
- job_state_file
- audit_log_both_attempts
- directory_listing (no duplicate ownership)
