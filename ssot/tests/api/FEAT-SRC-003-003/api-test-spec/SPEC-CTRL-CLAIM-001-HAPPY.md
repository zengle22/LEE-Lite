# API Test Spec — CTRL-CLAIM-001: Claim 控制命令

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.ctrl.claim.happy |
| coverage_id | api.ctrl.claim.happy |
| capability | CTRL-CLAIM-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-003.Scope.job-claim |

## Test Contract

### Preconditions

- Job `job-ready-001` exists in ready state
- Runner session is active
- No existing ownership record for this job

### Request

```
POST /api/v1/jobs/claim
Content-Type: application/json

{
  "job_id": "job-ready-001",
  "runner_id": "runner-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-ready-001",
    "owner_id": "runner-001",
    "claimed_at": "<ISO8601 timestamp>",
    "previous_state": "ready",
    "new_state": "claimed"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.owner_id == "runner-001"
- response.data.previous_state == "ready"
- response.data.new_state == "claimed"
- response.data.claimed_at is not null

### Side Effect Assertions

- Job state file updated from "ready" to "claimed"
- Ownership record file created with runner_id and claimed_at
- Command evidence recorded for the claim action

### Anti-False-Pass Checks
- verify job state file actually transitioned from "ready" to "claimed" on disk
- verify ownership record file created with correct runner_id (not default or null)
- verify no other runner can simultaneously claim the same job (single-owner enforced)

### Evidence Required

- request_snapshot
- response_snapshot
- job_state_before_and_after
- ownership_file_assertion
- command_evidence_log

## Source References
- FEAT-SRC-003-003.Scope.job-claim
- FEAT-SRC-003-003.Constraints.no-tampering
- FEAT-SRC-003-003.AC-04 (single-owner enforcement)

## Cleanup

- Release job ownership
- Reset job state to "ready"
- Delete ownership record file
- Clear command evidence log entry
