# API Test Spec — CTRL-FAIL-001: Fail 控制命令

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.ctrl.fail.happy |
| coverage_id | api.ctrl.fail.happy |
| capability | CTRL-FAIL-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-003.Scope.job-fail |

## Test Contract

### Preconditions

- Job `job-running-001` exists in running state
- Runner session is active and owns this job

### Request

```
POST /api/v1/jobs/fail
Content-Type: application/json

{
  "job_id": "job-running-001",
  "reason": "skill_execution_timeout",
  "details": {
    "timeout_seconds": 300,
    "last_progress_at": "<ISO8601 timestamp>"
  }
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-running-001",
    "previous_state": "running",
    "new_state": "failed",
    "failure_reason": "skill_execution_timeout",
    "failed_at": "<ISO8601 timestamp>",
    "evidence_ref": "evidence-fail-job-running-001"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.previous_state == "running"
- response.data.new_state == "failed"
- response.data.failure_reason == "skill_execution_timeout"
- response.data.evidence_ref is not null

### Side Effect Assertions

- Job state file updated from "running" to "failed"
- Failure evidence file created with reason and details
- Command evidence recorded for the fail action

### Anti-False-Pass Checks
- verify job state file actually transitioned from "running" to "failed" on disk
- verify failure evidence file created with actual reason and details (not empty)
- verify no additional jobs or invocations were created as side effects

### Evidence Required

- request_snapshot
- response_snapshot
- job_state_before_and_after
- failure_evidence_file
- command_evidence_log

## Source References
- FEAT-SRC-003-003.Scope.job-fail
- FEAT-SRC-003-003.Constraints.command-evidence
- FEAT-SRC-003-003.AC-05 (failure evidence recording)

## Cleanup

- Reset job state to "running" (or original state)
- Delete failure evidence file
- Clear command evidence log entry
