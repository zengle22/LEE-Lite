# E2E Journey Spec — JOURNEY-MAIN-001: 全状态监控

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.monitor.happy |
| coverage_id | e2e.journey.monitor.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-007.AcceptanceChecks.core-queue-states-visible |

## Test Contract

### Entry Point

`ll loop monitor`

### Preconditions

- Runner is active with jobs in various states
- At least one job exists in each of: ready, running, failed, deadletters, waiting-human
- Authoritative runner state is available

### User Steps

1. Operator executes `ll loop monitor`
2. System initializes monitor surface from authoritative runner state
3. System displays ready backlog count and list
4. System displays running jobs with ownership info
5. System displays failed jobs with failure reasons
6. System displays deadletter queue contents
7. System displays waiting-human jobs
8. Operator selects a specific job to view lineage details
9. System displays full lineage: job -> invocation -> outcome

### Expected CLI States

- Step 3: Output: "Ready Backlog: N jobs" followed by job listing
- Step 4: Output: "Running Jobs: N jobs" with owner info
- Step 5: Output: "Failed Jobs: N jobs" with failure reasons
- Step 6: Output: "Deadletters: N jobs"
- Step 7: Output: "Waiting-Human: N jobs"
- Step 9: JSON output with job_id, invocation_id, outcome_ref, lineage_chain

### Expected Network Events

- Authoritative state read: Read all runner state files
- Ready queue scan: List artifacts/jobs/ready
- Running state scan: List running job state files
- Failed state scan: List failed job state files
- Deadletter scan: List deadletter files
- Waiting-human scan: List waiting-human files
- Lineage resolution: Follow job -> invocation -> outcome refs

### Expected Persistence

- Monitor surface does NOT modify any state files (read-only)
- Monitor output log persists with timestamp
- No runner control state changes

### Anti-False-Pass Checks

- all_five_states_displayed (ready, running, failed, deadletters, waiting-human)
- authoritative_source_used (not directory guess)
- no_state_files_modified (monitor is read-only)
- lineage_chain_complete (job -> invocation -> outcome)
- no_console_error
- counts_accurate (displayed count matches actual files)

### Evidence Required

- cli_output_log (full monitor output)
- state_file_checksums_before_and_after (unchanged)
- lineage_resolution_output
- authoritative_source_verification
- count_accuracy_check
