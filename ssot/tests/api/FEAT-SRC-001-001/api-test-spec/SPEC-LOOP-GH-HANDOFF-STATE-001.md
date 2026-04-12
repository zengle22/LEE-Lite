# API Test Spec — LOOP-GH-HANDOFF-001: Gate-Human 交接界面 (状态约束)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.gh-handoff.invalid-transition |
| coverage_id | api.loop.gh-handoff.invalid-transition |
| capability | LOOP-GH-HANDOFF-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-001-001.Constraints |

## Test Contract

### Preconditions

- gate loop 处于 completed 状态 (非 ready)
- 尝试发起交接

### Operation

```
POST /api/v1/loops/gate-human/handoff
Content-Type: application/json

{
  "handoff_id": "handoff-gh-003",
  "proposal_ref": "prop-test-003",
  "consumer_role": "human_reviewer",
  "decision_target": "approve"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_GATE_STATE",
    "message": "Gate loop is not in ready state. Current state: completed",
    "current_gate_state": "completed"
  }
}
```

### Response Assertions

- status_code == 409
- response.error.code == "INVALID_GATE_STATE"
- response.data == null

### Side Effect Assertions

- 无 handoff 被创建
- proposal 状态不变
- gate loop 状态不变

### Anti-False-Pass Checks

- no_handoff_record_created in database
- gate_state_unchanged_in_persistence_layer
- proposal_state_unchanged

### Evidence Required

- request_snapshot
- response_snapshot
- gate_state_before_and_after
- handoff_table_assertion

## Cleanup

- No cleanup needed (no side effects expected)
