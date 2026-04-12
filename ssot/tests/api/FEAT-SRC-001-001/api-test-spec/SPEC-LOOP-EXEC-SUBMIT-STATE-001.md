# API Test Spec — LOOP-EXEC-SUBMIT-001: 执行循环提交 (状态约束)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.exec-submit.invalid-loop-state |
| coverage_id | api.loop.exec-submit.invalid-loop-state |
| capability | LOOP-EXEC-SUBMIT-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-001-001.Scope.execution-loop |

## Test Contract

### Preconditions

- execution loop 处于 completed 或 blocked 状态 (非 active)
- gate loop 处于 ready 状态

### Operation

```
POST /api/v1/loops/execution/submit
Content-Type: application/json

{
  "loop_id": "loop-exec-002",
  "object_type": "candidate_package",
  "object_ref": "pkg-exec-test-002",
  "target_gate": "gate-mainline-001",
  "transition_intent": "revision"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "LOOP_STATE_INVALID",
    "message": "Execution loop is not in active state. Current state: completed",
    "current_loop_state": "completed"
  }
}
```

### Response Assertions

- status_code == 409
- response.error.code == "LOOP_STATE_INVALID"
- response.data == null
- error message contains current loop state

### Side Effect Assertions

- 无新 submission 被创建
- gate 消费队列无变化
- execution loop 状态保持不变

### Anti-False-Pass Checks

- no new records in submission table
- loop state unchanged in persistence layer
- no side effects on gate queue

### Evidence Required

- request_snapshot
- response_snapshot
- loop_state_before_and_after
- submission_table_assertion

## Cleanup

- No cleanup needed (no side effects expected)
