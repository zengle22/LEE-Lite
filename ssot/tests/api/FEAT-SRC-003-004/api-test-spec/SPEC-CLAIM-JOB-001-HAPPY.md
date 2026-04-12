# API Test Spec — CLAIM-JOB-001: 抢占式 Claim Job

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.claim.job.happy |
| coverage_id | api.claim.job.happy |
| capability | CLAIM-JOB-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-004.AcceptanceChecks.single-owner |

## Test Contract

### Preconditions

- Job `job-ready-001` exists in ready queue
- No existing ownership record for this job
- Runner is authorized to claim jobs

### Request

```
POST /api/v1/runner/claim
Content-Type: application/json

{
  "job_id": "job-ready-001",
  "runner_id": "runner-001",
  "claim_evidence": {
    "claim_method": "atomic_file_rename",
    "timestamp": "<ISO8601 timestamp>"
  }
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
    "state_transition": "ready -> running",
    "claim_evidence": {
      "method": "atomic_file_rename",
      "verified": true
    }
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.owner_id == "runner-001"
- response.data.state_transition == "ready -> running"
- response.data.claim_evidence.verified == true

### Side Effect Assertions

- Job state file atomically transitioned from ready to running
- Ownership record file created
- No other runner can claim the same job (single-owner)

### Anti-False-Pass Checks
- verify job state actually transitioned from "ready" to "running" atomically (not just 200 response)
- verify ownership record file exists and contains correct owner_id (not stale data)
- verify concurrent claim attempt from another runner would be rejected (single-owner enforced)

### Evidence Required

- request_snapshot
- response_snapshot
- job_state_transition_proof
- ownership_file_assertion
- single_owner_verification

## Source References
- FEAT-SRC-003-004.AcceptanceChecks.single-owner
- FEAT-SRC-003-004.Scope.preemptive-claim
- FEAT-SRC-003-004.Constraints.atomic-claim

## Cleanup

- Release job ownership
- Reset job state to ready
- Delete ownership record
