# API Test Spec — STATE-TRANSITION-001: 状态转移

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.state.transition.running-to-done |
| coverage_id | api.state.transition.running-to-done |
| capability | STATE-TRANSITION-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-003-006.Scope.state-boundary |

## Test Contract

### Preconditions

- Job `job-running-001` is in running state
- Valid state transition: running -> done

### Request

```
PUT /api/v1/jobs/job-running-001/state
Content-Type: application/json

{
  "job_id": "job-running-001",
  "from_state": "running",
  "to_state": "done"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-running-001",
    "from_state": "running",
    "to_state": "done",
    "transition_valid": true,
    "transitioned_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.from_state == "running"
- response.data.to_state == "done"
- response.data.transition_valid == true

### Side Effect Assertions

- Job state file updated
- Transition log recorded
- Prior state archived for audit

### Anti-False-Pass Checks
- verify job state file actually reflects "done" state after transition (not just response says valid)
- verify transition log entry persisted with correct from_state and to_state
- verify prior state properly archived for audit trail (not overwritten/lost)

### Evidence Required

- request_snapshot
- response_snapshot
- job_state_before_and_after
- transition_log_entry

## Source References
- FEAT-SRC-003-006.Scope.state-boundary
- FEAT-SRC-003-006.Constraints.valid-transitions
- FEAT-SRC-003-006.AC-08 (state transition audit trail)

## Cleanup

- Reset job state to "running"
- Clear transition log entry
