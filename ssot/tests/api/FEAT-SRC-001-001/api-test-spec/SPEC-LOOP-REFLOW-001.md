# API Test Spec — LOOP-REFLOW-BOUNDS-001: 回流边界控制

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.reflow.happy |
| coverage_id | api.loop.reflow.happy |
| capability | LOOP-REFLOW-BOUNDS-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-02 |

## Test Contract

### Preconditions

- gate loop 返回 revise/retry decision
- execution loop 处于允许重入的状态
- 回流对象已准备

### Operation

```
POST /api/v1/loops/reflow/re-enter
Content-Type: application/json

{
  "reflow_id": "reflow-001",
  "source_gate_decision": "revise",
  "target_loop": "execution",
  "object_ref": "pkg-reflow-001",
  "reentry_reason": "gate_requested_revision"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "reflow_id": "reflow-001",
    "reentry_allowed": true,
    "target_loop": "execution",
    "object_ref": "pkg-reflow-001",
    "reentered_at": "<ISO8601 timestamp>",
    "loop_state_after_reentry": "active"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.reentry_allowed == true
- response.data.loop_state_after_reentry == "active"
- response.data.target_loop == "execution"

### Side Effect Assertions

- execution loop 状态更新为 "active"
- reflow 记录持久化
- gate decision 标记为 "consumed_by_reflow"

### Anti-False-Pass Checks

- loop_state_actually_changed_to_active in persistence layer
- reflow_record_exists with correct source_gate_decision
- gate_decision_marked_as_consumed_by_reflow
- object_rebinding_confirmed in object registry

### Evidence Required

- request_snapshot
- response_snapshot
- loop_state_change_log
- reflow_record
- gate_decision_state

## Cleanup

- 删除创建的 reflow 记录
- 恢复 execution loop 状态
- 恢复 gate decision 状态
