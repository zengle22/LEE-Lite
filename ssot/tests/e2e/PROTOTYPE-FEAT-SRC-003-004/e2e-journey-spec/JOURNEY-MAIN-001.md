# E2E Journey Spec — JOURNEY-MAIN-001: 自动取件

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.consume.happy |
| coverage_id | e2e.journey.consume.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-004.AcceptanceChecks.auto-consume |

## Test Contract

### Entry Point

Automatic: Runner scanning `artifacts/jobs/ready` (no manual trigger)

### Preconditions

- Runner is active and scanning ready queue
- Job file `job-ready-001.json` exists in `artifacts/jobs/ready/`
- No existing ownership record for this job
- No other runner instance competing for this job

### User Steps

1. Operator places job file in `artifacts/jobs/ready/job-ready-001.json`
2. Runner automatically scans ready queue and discovers the job
3. Runner executes claim on the job
4. System transfers job state from ready to running
5. System records ownership with runner ID and claim timestamp
6. Operator verifies ownership record exists
7. Operator verifies job file is no longer in ready queue (or marked as claimed)

### Expected CLI States

- Step 2: Runner log output: "Scanning ready queue: found 1 job(s)"
- Step 3: Runner log output: "Claiming job: job-ready-001"
- Step 4: Runner log output: "Job job-ready-001 state: ready -> running"
- Step 5: Runner log output: "Ownership recorded: runner-{id}"
- Step 6-7: Operator verifies via `cat` and `ls` commands

### Expected Network Events

- Ready queue scan: Read directory listing of artifacts/jobs/ready
- Job read: Read job-ready-001.json content
- State update: Rename/move job from ready to running state
- Ownership write: Write ownership record file
- Claim evidence write: Write claim timestamp and runner ID

### Expected Persistence

- Job state file updated (ready -> running)
- Ownership record file exists with runner_id and claimed_at
- Claim evidence file exists
- Original job file removed from ready queue or marked as claimed

### Anti-False-Pass Checks

- job_no_longer_in_ready (file moved or marked)
- job_in_running (state file exists)
- ownership_file_exists (with correct runner_id)
- claim_timestamp_recorded
- no_human_relay_involved
- no_console_error

### Evidence Required

- runner_scan_log
- job_state_before_and_after
- ownership_file_snapshot
- claim_evidence_file
- directory_listing_ready_queue
- directory_listing_running_state
