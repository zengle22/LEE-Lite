# API Test Spec — OUTCOME-DONE-001: 记录 Done 结果

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.outcome.done.happy |
| coverage_id | api.outcome.done.happy |
| capability | OUTCOME-DONE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-006.AcceptanceChecks.explicit-outcomes |

## Test Contract

### Preconditions

- Job `job-running-001` is in running state
- Downstream skill has completed execution successfully
- Completion result data is available

### Request

```
POST /api/v1/jobs/outcome
Content-Type: application/json

{
  "job_id": "job-running-001",
  "outcome_type": "done",
  "execution_result": {
    "status": "completed",
    "output_refs": ["artifacts/output/job-running-001-output.md"],
    "completed_at": "<ISO8601 timestamp>"
  },
  "attempt_id": "attempt-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-running-001",
    "outcome_type": "done",
    "previous_state": "running",
    "new_state": "done",
    "outcome_ref": "artifacts/jobs/outcomes/outcome-job-running-001.json",
    "recorded_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.outcome_type == "done"
- response.data.previous_state == "running"
- response.data.new_state == "done"
- response.data.outcome_ref is not null

### Side Effect Assertions

- Outcome file written to artifacts/jobs/outcomes/
- Job state file updated to "done"
- Execution result data persisted

### Anti-False-Pass Checks
- verify outcome file actually written to artifacts/jobs/outcomes/ with correct content
- verify job state file actually updated to "done" (not just response says done)
- verify no duplicate outcome records created for the same job_id

### Evidence Required

- request_snapshot
- response_snapshot
- outcome_file_assertion
- job_state_transition_proof
- execution_result_content_check

## Source References
- FEAT-SRC-003-006.AcceptanceChecks.explicit-outcomes
- FEAT-SRC-003-006.Scope.outcome-recording
- FEAT-SRC-003-006.Constraints

## Cleanup

- Delete outcome file
- Reset job state to "running"
- Clean up execution result references
