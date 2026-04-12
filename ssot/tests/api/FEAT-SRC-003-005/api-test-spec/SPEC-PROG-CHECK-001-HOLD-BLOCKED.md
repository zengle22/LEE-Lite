# API Test Spec — PROG-CHECK-001: Progression Mode 检查

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.prog.check.hold-blocked |
| coverage_id | api.prog.check.hold-blocked |
| capability | PROG-CHECK-001 |
| scenario_type: | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-003-005.Constraints.no-auto-dispatch-hold |

## Test Contract

### Preconditions

- Job `job-hold-001` is in running state with progression_mode = "hold"
- Target next skill exists

### Request

```
POST /api/v1/skills/dispatch
Content-Type: application/json

{
  "job_id": "job-hold-001",
  "target_skill": "skills/l3/ll-next-skill/",
  "input_package": {
    "refs": ["artifacts/jobs/running/job-hold-001.json"]
  }
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "HOLD_NOT_DISPATCHABLE",
    "message": "Job job-hold-001 has progression_mode=hold and cannot be auto-dispatched",
    "job_id": "job-hold-001",
    "progression_mode": "hold",
    "required_mode": "auto-continue"
  }
}
```

### Response Assertions

- status_code == 403
- response.data is null
- response.error.code == "HOLD_NOT_DISPATCHABLE"
- response.error.progression_mode == "hold"
- response.error.required_mode == "auto-continue"

### Side Effect Assertions

- No invocation created
- No lineage record created
- Job state unchanged
- Audit log records blocked dispatch attempt

### Anti-False-Pass Checks
- verify no invocation or lineage files created anywhere in artifacts (not just checked directories)
- verify job state and progression_mode remain completely unchanged after request
- verify audit log entry exists recording the blocked dispatch attempt with correct job_id

### Evidence Required

- request_snapshot
- response_snapshot
- no_invocation_created
- job_state_unchanged
- audit_log_entry

## Source References
- FEAT-SRC-003-005.Constraints.no-auto-dispatch-hold
- FEAT-SRC-003-005.AC-07 (progression mode enforcement)
- FEAT-SRC-003-005.Constraints

## Cleanup

- No cleanup needed (no state changes)
- Clear audit log test entry
