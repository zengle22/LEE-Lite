# API Test Spec — FILTER-APPROVE-001: 过滤非 approve 决策

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.filter.approve.happy |
| coverage_id | api.filter.approve.happy |
| capability | FILTER-APPROVE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-001.AcceptanceChecks.non-approve-excluded |

## Test Contract

### Preconditions

- Gate decision exists with status = "revise" (non-approve)
- `artifacts/jobs/ready` directory exists

### Request

```
POST /api/v1/jobs/generate
Content-Type: application/json

{
  "gate_decision_ref": "gate-decision-revise-001",
  "progression_mode": "auto-continue",
  "candidate_package_ref": "pkg-004",
  "next_skill_target": "skills/l3/ll-next-skill/",
  "authoritative_refs": {
    "proposal_ref": "adr011-proposal-v1",
    "evidence_refs": []
  }
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "DECISION_NOT_APPROVED",
    "message": "Job generation is only permitted for approved gate decisions. Decision status: revise",
    "gate_decision_ref": "gate-decision-revise-001",
    "decision_status": "revise"
  }
}
```

### Response Assertions

- status_code == 403
- response.data is null
- response.error.code == "DECISION_NOT_APPROVED"
- response.error.gate_decision_ref == "gate-decision-revise-001"
- response.error.decision_status == "revise"

### Side Effect Assertions

- No file created in `artifacts/jobs/ready` directory
- No file created in `artifacts/jobs/hold` directory
- Gate decision record NOT updated with job generation status
- Audit log records the rejected attempt with decision status

### Anti-False-Pass Checks

- Scan entire artifacts/jobs/ directory for any file referencing gate-decision-revise-001
- Verify no side-channel job creation occurred

### Evidence Required

- request_snapshot
- response_snapshot
- empty_ready_queue_assertion
- empty_hold_queue_assertion
- audit_log_entry

## Source References
- FEAT-SRC-003-001.AcceptanceChecks.non-approve-excluded
- FEAT-SRC-003-001.Constraints
- FEAT-SRC-003-001.AC-01 (approve-only gate enforcement)

## Cleanup

- No file cleanup needed (no files created)
- Clear audit log test entry
