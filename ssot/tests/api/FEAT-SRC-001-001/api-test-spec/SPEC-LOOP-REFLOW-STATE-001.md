# API Test Spec — LOOP-REFLOW-BOUNDS-001: 回流边界控制 (状态约束)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.reflow.invalid-reentry |
| coverage_id | api.loop.reflow.invalid-reentry |
| capability | LOOP-REFLOW-BOUNDS-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-001-001.AC-02 |

## Test Contract

### Preconditions

- gate loop 返回 revise decision
- 但 execution loop 处于不允许重入的状态 (例如 completed)

### Operation

```
POST /api/v1/loops/reflow/re-enter
Content-Type: application/json

{
  "reflow_id": "reflow-002",
  "source_gate_decision": "revise",
  "target_loop": "execution",
  "object_ref": "pkg-reflow-002",
  "reentry_reason": "gate_requested_revision"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "REENTRY_NOT_ALLOWED",
    "message": "Execution loop is in completed state and does not allow reentry",
    "target_loop_state": "completed",
    "allowed_reentry_states": ["active", "paused"]
  }
}
```

### Response Assertions

- status_code == 409
- response.error.code == "REENTRY_NOT_ALLOWED"
- response.data == null

### Side Effect Assertions

- 无 reflow 记录被创建
- execution loop 状态不变
- gate decision 状态不变

### Anti-False-Pass Checks

- no_reflow_record_created in database
- loop_state_unchanged_in_persistence_layer
- gate_decision_state_unchanged

### Evidence Required

- request_snapshot
- response_snapshot
- loop_state_before_and_after
- reflow_table_assertion (no new record)

## Cleanup

- No cleanup needed (no side effects expected)
