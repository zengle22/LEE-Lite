# E2E Journey Spec — JOURNEY-EXCEPTION-001: 非 Approve 决策被拒绝

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.not-approved |
| coverage_id | e2e.journey.exception.not-approved |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-001.AcceptanceChecks.non-approve-excluded |

## Test Contract

### Entry Point

`POST /api/v1/jobs/generate` (attempted with non-approve decision)

### Preconditions

- Gate decision exists with status = "revise"
- `artifacts/jobs/ready` directory exists
- No existing job files from this gate decision

### User Steps

1. Operator attempts to generate job from "revise" gate decision
2. System rejects the request with DECISION_NOT_APPROVED error
3. Operator sees explicit error message with decision status
4. Operator confirms no files were created in artifacts/jobs/ready or hold

### Expected CLI States

- Step 2: CLI outputs "Error: DECISION_NOT_APPROVED - Job generation is only permitted for approved gate decisions. Decision status: revise"
- Step 2: Exit code != 0
- Step 4: `ls artifacts/jobs/ready/` shows no new files

### Expected Network Events

- Gate decision read: GET gate decision record (to check status)
- No job file write operations
- Audit log entry recording the rejected attempt

### Expected Persistence

- No new files in artifacts/jobs/ready/
- No new files in artifacts/jobs/hold/
- Audit log contains rejected attempt record

### Anti-False-Pass Checks

- no_new_files_in_artifacts_jobs (scan entire directory tree)
- exit_code_nonzero
- error_message_explicit (contains DECISION_NOT_APPROVED and decision status)
- audit_log_entry_exists
- gate_decision_unchanged

### Evidence Required

- cli_output_log (including error message)
- exit_code_capture
- directory_listing (no new files)
- audit_log_entry
- gate_decision_unchanged_proof
