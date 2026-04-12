# API Test Spec — ANTI-REENTRY-001: 防重入保护

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.anti.reentry.duplicate |
| coverage_id | api.anti.reentry.duplicate-claim |
| capability | ANTI-REENTRY-001 |
| scenario_type | idempotent |
| priority | P0 |
| dimension | 幂等/重试/并发 |
| source_feat_ref | FEAT-SRC-003-004.Constraints.anti-reentry |

## Test Contract

### Preconditions

- Job `job-ready-001` has already been claimed by runner-001
- Ownership record exists for runner-001

### Request

```
POST /api/v1/runner/claim
Content-Type: application/json

{
  "job_id": "job-ready-001",
  "runner_id": "runner-002",
  "claim_evidence": {
    "claim_method": "atomic_file_rename",
    "timestamp": "<ISO8601 timestamp>"
  }
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ALREADY_CLAIMED",
    "message": "Job job-ready-001 has already been claimed by runner-001",
    "job_id": "job-ready-001",
    "current_owner": "runner-001"
  }
}
```

### Response Assertions

- status_code == 409
- response.data is null
- response.error.code == "ALREADY_CLAIMED"
- response.error.current_owner == "runner-001"

### Side Effect Assertions

- No state change occurs
- Original ownership record unchanged
- Audit log records the rejected duplicate attempt

### Anti-False-Pass Checks

- ownership_record_unchanged
- job_state_unchanged
- rejected_attempt_logged
- no_new_ownership_created

### Evidence Required

- request_snapshot
- response_snapshot
- ownership_file_unchanged
- audit_log_entry

## Source References
- FEAT-SRC-003-004.Constraints.anti-reentry
- FEAT-SRC-003-004.AC-06 (idempotent claim protection)
- FEAT-SRC-003-004.Constraints

## Cleanup

- No cleanup needed (no state changes)
- Clear audit log test entry
