# API Test Spec — LOOP-EXEC-SUBMIT-001: 执行循环提交 (异常路径)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.exec-submit.missing-object |
| coverage_id | api.loop.exec-submit.missing-object |
| capability | LOOP-EXEC-SUBMIT-001 |
| scenario_type | exception |
| priority | P0 |
| dimension | 异常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-01 |

## Test Contract

### Preconditions

- execution loop 处于 active 状态
- 指定的 object_ref 不存在或已被删除

### Operation

```
POST /api/v1/loops/execution/submit
Content-Type: application/json

{
  "loop_id": "loop-exec-003",
  "object_type": "candidate_package",
  "object_ref": "pkg-nonexistent-999",
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
    "code": "OBJECT_NOT_FOUND",
    "message": "Referenced object pkg-nonexistent-999 does not exist",
    "object_ref": "pkg-nonexistent-999"
  }
}
```

### Response Assertions

- status_code == 404
- response.error.code == "OBJECT_NOT_FOUND"
- response.data == null
- error message references the missing object

### Side Effect Assertions

- 无新 submission 被创建
- gate 消费队列无变化

### Anti-False-Pass Checks

- no_submission_record_created in database
- object truly does not exist (not hidden by caching)
- no_side_effects_on_gate_queue
- error_response_contains_OBJECT_NOT_FOUND_code

### Evidence Required

- request_snapshot
- response_snapshot
- object_existence_check
- submission_table_assertion

## Cleanup

- No cleanup needed (no side effects expected)
