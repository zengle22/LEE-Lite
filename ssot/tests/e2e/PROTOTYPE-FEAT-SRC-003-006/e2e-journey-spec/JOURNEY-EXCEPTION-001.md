# E2E Journey Spec — JOURNEY-EXCEPTION-001: Retry/Reentry 结果

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.retry-reentry |
| coverage_id | e2e.journey.exception.retry-reentry |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-006.Scope.retry-reentry |

## Test Contract

### Entry Point

Automatic: Runner receiving retry-reentry signal from downstream skill

### Preconditions

- Job `job-ready-002` is in running state
- Downstream skill has returned retry-reentry directive
- Retry directive contains reentry parameters

### User Steps

1. Downstream skill sends retry-reentry signal to runner
2. Runner receives and validates retry directive
3. Runner writes retry-reentry outcome file
4. Job returns to execution semantics (not publish-only)
5. Operator verifies retry outcome file exists with directive details
6. Operator confirms job is ready for re-execution, not published

### Expected CLI States

- Step 2: Runner log: "Received retry-reentry signal for job-ready-002"
- Step 3: Runner log: "Writing retry-reentry outcome for job-ready-002"
- Step 4: Runner log: "Job job-ready-002: returned to execution semantics (retry)"
- Step 5: `cat outcome-job-ready-002.json` shows retry-reentry status with directive
- Step 6: Job state does NOT show "published" or "complete"

### Expected Network Events

- Retry signal receive: Read retry directive from skill output
- Retry outcome file write: Write retry-reentry outcome
- Job state update: Transition to retry_return state
- Audit log: Record retry outcome writeback

### Expected Persistence

- Retry outcome file exists with retry directive details
- Job state file shows retry_return (not published, not done)
- No publish-only state transition occurred

### Anti-False-Pass Checks

- retry_outcome_file_exists
- job_state_is_retry_return (not published)
- no_publish_state_transition
- retry_directive_recorded
- execution_semantics_preserved

### Evidence Required

- runner_retry_log
- retry_outcome_file_snapshot
- job_state_file_after
- retry_directive_content
- no_publish_verification
