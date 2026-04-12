# E2E Journey Spec — JOURNEY-MAIN-001: Done 结果回写

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.done-writeback.happy |
| coverage_id | e2e.journey.done-writeback.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-006.AcceptanceChecks.explicit-outcomes |

## Test Contract

### Entry Point

Automatic: Runner receiving completion signal from downstream skill

### Preconditions

- Job `job-ready-001` is in running state
- Downstream skill has completed execution successfully
- Completion signal with result data is available
- Output directory for execution outcomes is writable

### User Steps

1. Downstream skill sends completion signal to runner
2. Runner receives and validates completion signal
3. Runner writes done outcome file with evidence
4. Job state transitions from running to done
5. Operator verifies outcome file exists with completion timestamp and evidence refs
6. Operator verifies job state file shows "done"

### Expected CLI States

- Step 2: Runner log: "Received completion signal for job-ready-001: status=done"
- Step 3: Runner log: "Writing done outcome for job-ready-001"
- Step 4: Runner log: "Job state: running -> done"
- Step 5: `cat outcome-job-ready-001.json` shows done status with evidence
- Step 6: `cat job-ready-001-state.json` shows status="done"

### Expected Network Events

- Completion signal receive: Read from skill output
- Outcome file write: Write done outcome with evidence refs
- Job state update: Rename/update state file to "done"
- Audit log: Record outcome writeback

### Expected Persistence

- Outcome file exists at `artifacts/jobs/outcomes/outcome-job-ready-001.json`
- Outcome file contains: status="done", completed_at, evidence_refs, attempt_id
- Job state file shows "done"
- No stale running state

### Anti-False-Pass Checks

- outcome_file_exists
- outcome_status_is_done
- job_state_is_done
- no_stale_running_state
- evidence_refs_valid
- no_console_error

### Evidence Required

- runner_outcome_log
- outcome_file_snapshot
- job_state_file_after
- completion_signal_source
- directory_listing_outcomes
