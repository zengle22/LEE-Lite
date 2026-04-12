# API Test Spec — LOOP-REFLOW-BOUNDS-001: 回流边界控制 (数据副作用)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.reflow.data-side-effect |
| coverage_id | api.loop.reflow.data-side-effect |
| capability | LOOP-REFLOW-BOUNDS-001 |
| scenario_type | data_side_effect |
| priority | P0 |
| dimension | 数据副作用 |
| source_feat_ref | FEAT-SRC-001-001.AC-02 |

## Test Contract

### Preconditions

- gate loop 返回 revise decision
- execution loop 处于允许重入的状态
- 数据库可写

### Operation

```
POST /api/v1/loops/reflow/re-enter
Content-Type: application/json

{
  "reflow_id": "reflow-004",
  "source_gate_decision": "revise",
  "target_loop": "execution",
  "object_ref": "pkg-reflow-004",
  "reentry_reason": "gate_requested_revision"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "reflow_id": "reflow-004",
    "reentry_allowed": true,
    "target_loop": "execution",
    "object_ref": "pkg-reflow-004",
    "reentered_at": "<ISO8601 timestamp>",
    "loop_state_after_reentry": "active"
  },
  "error": null
}
```

### Side Effect Assertions

- reflow 记录持久化，包含完整溯源链
- execution loop 状态更新为 "active"
- gate decision 状态更新为 "consumed_by_reflow"
- object_ref 重新绑定到 execution loop

### Anti-False-Pass Checks

- reflow_record_persisted_with_complete_provenance_chain
- loop_state_actually_updated_in_database (not cached)
- gate_decision_state_consistent_across_all_records
- object_rebinding_atomic (all or none)

### Evidence Required

- request_snapshot
- response_snapshot
- db_reflow_record
- loop_state_change_log
- gate_decision_state_change
- object_rebinding_assertion

## Cleanup

- 删除创建的 reflow 记录
- 恢复 execution loop 状态
- 恢复 gate decision 状态
- 恢复 object binding
