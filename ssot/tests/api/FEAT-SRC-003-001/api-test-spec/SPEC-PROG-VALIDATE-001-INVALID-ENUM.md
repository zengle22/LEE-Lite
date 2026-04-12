# API Test Spec — PROG-VALIDATE-001: 验证 Progression Mode

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.prog.validate.invalid |
| coverage_id | api.prog.validate.invalid-enum |
| capability | PROG-VALIDATE-001 |
| scenario_type | parameter_validation |
| priority | P0 |
| dimension | 参数校验 |
| source_feat_ref | FEAT-SRC-003-001.Constraints |

## Test Contract

### Preconditions

- Gate decision exists with status = "approved"
- `artifacts/jobs/ready` directory exists

### Request

```
POST /api/v1/jobs/generate
Content-Type: application/json

{
  "gate_decision_ref": "gate-decision-005",
  "progression_mode": "invalid-mode",
  "candidate_package_ref": "pkg-005",
  "next_skill_target": "skills/l3/ll-next-skill/",
  "authoritative_refs": {
    "proposal_ref": "adr011-proposal-v1",
    "evidence_refs": ["artifacts/evidence-001.md"]
  }
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_PROGRESSION_MODE",
    "message": "progression_mode must be one of: auto-continue, hold. Got: invalid-mode",
    "field": "progression_mode",
    "valid_values": ["auto-continue", "hold"],
    "received_value": "invalid-mode"
  }
}
```

### Response Assertions

- status_code == 400
- response.data is null
- response.error.code == "INVALID_PROGRESSION_MODE"
- response.error.field == "progression_mode"
- response.error.valid_values contains "auto-continue" and "hold"
- response.error.received_value == "invalid-mode"

### Side Effect Assertions

- No file created in `artifacts/jobs/ready` directory
- No file created in `artifacts/jobs/hold` directory
- Gate decision record unchanged

### Anti-False-Pass Checks

- Verify validation fails before any job generation logic executes
- Verify error message explicitly lists valid enumeration values

### Evidence Required

- request_snapshot
- response_snapshot
- empty_queues_assertion
- validation_order_log

## Source References
- FEAT-SRC-003-001.Constraints
- FEAT-SRC-003-001.AC-02 (progression_mode enumeration validation)

## Cleanup

- No file cleanup needed (no files created)
