# API Test Spec — LOOP-GH-HANDOFF-001: Gate-Human 交接界面 (参数校验)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.gh-handoff.missing-consumer |
| coverage_id | api.loop.gh-handoff.missing-consumer |
| capability | LOOP-GH-HANDOFF-001 |
| scenario_type | parameter_validation |
| priority | P0 |
| dimension | 参数校验 |
| source_feat_ref | FEAT-SRC-001-001.AC-01 |

## Test Contract

### Preconditions

- gate loop 处于 ready 消费状态
- 交接请求缺少必填 consumer_role 字段

### Operation

```
POST /api/v1/loops/gate-human/handoff
Content-Type: application/json

{
  "handoff_id": "handoff-gh-002",
  "proposal_ref": "prop-test-002",
  "decision_target": "approve"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Field 'consumer_role' is required",
    "missing_fields": ["consumer_role"]
  }
}
```

### Response Assertions

- status_code == 400
- response.error.code == "MISSING_REQUIRED_FIELD"
- response.data == null
- error identifies the missing consumer_role field

### Side Effect Assertions

- 无 handoff 被创建
- proposal 状态不变

### Anti-False-Pass Checks

- no_handoff_record_created in database
- proposal_state_unchanged
- error_response_identifies_correct_missing_field

### Evidence Required

- request_snapshot
- response_snapshot
- handoff_table_assertion (no new record)

## Cleanup

- No cleanup needed (no side effects expected)
