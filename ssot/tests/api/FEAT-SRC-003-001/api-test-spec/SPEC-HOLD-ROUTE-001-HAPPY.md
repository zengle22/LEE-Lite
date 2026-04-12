# API Test Spec — HOLD-ROUTE-001: Hold Job 路由

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.hold.route.happy |
| coverage_id | api.hold.route.happy |
| capability | HOLD-ROUTE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-001.Constraints.hold-queue |

## Test Contract

### Preconditions

- Gate decision exists with status = "approved"
- `progression_mode = hold` is set on the gate decision
- `artifacts/jobs/hold` directory exists and is writable
- No existing hold job with the same gate_decision_ref

### Request

```
POST /api/v1/jobs/route-hold
Content-Type: application/json

{
  "gate_decision_ref": "gate-decision-003",
  "progression_mode": "hold",
  "candidate_package_ref": "pkg-003",
  "next_skill_target": "skills/l3/ll-next-skill/",
  "hold_reason": "awaiting_additional_context"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-hold-001",
    "job_type": "hold_job",
    "status": "waiting-human",
    "progression_mode": "hold",
    "created_at": "<ISO8601 timestamp>",
    "queue_path": "artifacts/jobs/hold/job-hold-001.json",
    "hold_reason": "awaiting_additional_context"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.job_type == "hold_job"
- response.data.status == "waiting-human"
- response.data.progression_mode == "hold"
- response.data.queue_path contains "artifacts/jobs/hold" (NOT "artifacts/jobs/ready")
- response.data.queue_path does NOT contain "ready"

### Side Effect Assertions

- File exists at response.data.queue_path in hold directory
- No file created in `artifacts/jobs/ready` directory
- File contains hold_reason field
- Gate decision record updated with hold_job_generation_status = "emitted"

### Anti-False-Pass Checks

- Verify file NOT in artifacts/jobs/ready (no queue leak)
- Verify job_id is unique and not reused from prior hold jobs
- Verify hold_reason is explicitly set (not null/empty)

### Evidence Required

- request_snapshot
- response_snapshot
- file_system_assertion (hold path only)
- no_ready_queue_leak_assertion
- gate_decision_update_log

## Source References
- FEAT-SRC-003-001.Constraints.hold-queue
- FEAT-SRC-003-001.Scope.hold-routing
- FEAT-SRC-003-001.AcceptanceChecks.hold-job-isolation

## Cleanup

- Delete the created hold job file
- Reset gate decision hold status
