# API Test Spec — LOOP-REFLOW-BOUNDS-001: 回流边界控制 (异常路径)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.reflow.missing-consumer |
| coverage_id | api.loop.reflow.missing-consumer |
| capability | LOOP-REFLOW-BOUNDS-001 |
| scenario_type | exception |
| priority | P0 |
| dimension | 异常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-02 |

## Test Contract

### Preconditions

- gate loop 返回 revise decision
- 指定的 target_loop 不存在或已被销毁

### Operation

```
POST /api/v1/loops/reflow/re-enter
Content-Type: application/json

{
  "reflow_id": "reflow-003",
  "source_gate_decision": "revise",
  "target_loop": "nonexistent_loop",
  "object_ref": "pkg-reflow-003",
  "reentry_reason": "gate_requested_revision"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "TARGET_LOOP_NOT_FOUND",
    "message": "Target loop 'nonexistent_loop' does not exist",
    "target_loop": "nonexistent_loop"
  }
}
```

### Response Assertions

- status_code == 404
- response.error.code == "TARGET_LOOP_NOT_FOUND"
- response.data == null

### Side Effect Assertions

- 无 reflow 记录被创建
- 无状态变更

### Anti-False-Pass Checks

- no_reflow_record_created in database
- target_loop_truly_does_not_exist (not just temporarily hidden)
- no_state_changes_to_any_loop

### Evidence Required

- request_snapshot
- response_snapshot
- loop_registry_assertion

## Cleanup

- No cleanup needed (no side effects expected)
