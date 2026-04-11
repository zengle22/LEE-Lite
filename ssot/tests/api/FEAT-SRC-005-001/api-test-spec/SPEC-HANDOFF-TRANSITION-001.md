# API Test Spec — HANDOFF-TRANSITION-001: 交接流转

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.handoff.transition.happy |
| coverage_id | api.handoff.transition.happy |
| capability | HANDOFF-TRANSITION-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-005-001.Scope.gate-consumption |

## Test Contract

### Preconditions

- 存在 status = "pending-intake" 的 handoff
- handoff 已通过 gate evaluation 获得 approved

### Request

```
POST /api/v1/handoffs/handoff-test-001/transition
Content-Type: application/json

{
  "target_status": "gate-queued",
  "transition_reason": "approved_and_ready_for_gate"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "handoff_id": "handoff-test-001",
    "previous_status": "pending-intake",
    "current_status": "gate-queued",
    "transitioned_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.previous_status == "pending-intake"
- response.data.current_status == "gate-queued"

### Side Effect Assertions

- handoff 状态在数据库中已更新为 "gate-queued"
- gate 消费链可以读取该 handoff

### Evidence Required

- request_snapshot
- response_snapshot
- db_assertion_result

## Cleanup

- 还原 handoff 状态

---

# API Test Spec — HANDOFF-TRANSITION-001: 非法状态迁移

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.handoff.transition.invalid-state |
| coverage_id | api.handoff.transition.invalid-state |
| capability | HANDOFF-TRANSITION-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-005-001.Constraints.loop-semantics |

## Test Contract

### Preconditions

- 存在 status = "rejected" 的 handoff（不可直接流转为 gate-queued）

### Request

```
POST /api/v1/handoffs/handoff-rejected-001/transition
Content-Type: application/json

{
  "target_status": "gate-queued",
  "transition_reason": "force_transition"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot transition from 'rejected' to 'gate-queued'. Must resolve rejections first.",
    "current_status": "rejected",
    "allowed_transitions": ["pending-revision"]
  }
}
```

### Response Assertions

- status_code == 400
- response.error.code == "INVALID_STATE_TRANSITION"
- response.error.allowed_transitions contains "pending-revision"

### Side Effect Assertions

- handoff 状态未发生变化

### Evidence Required

- request_snapshot
- response_snapshot

## Cleanup

- 无状态变更，无需清理
