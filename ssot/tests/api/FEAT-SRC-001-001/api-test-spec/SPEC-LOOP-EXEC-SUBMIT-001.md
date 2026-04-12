# API Test Spec — LOOP-EXEC-SUBMIT-001: 执行循环提交

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.exec-submit.happy |
| coverage_id | api.loop.exec-submit.happy |
| capability | LOOP-EXEC-SUBMIT-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-001.Scope.execution-loop |

## Test Contract

### Preconditions

- execution loop 处于 active 状态
- 存在有效的待提交对象 (candidate package 或 equivalent artifact)
- gate loop 处于 ready 消费状态
- 无已有并行 handoff 规则

### Operation

```
POST /api/v1/loops/execution/submit
Content-Type: application/json

{
  "loop_id": "loop-exec-001",
  "object_type": "candidate_package",
  "object_ref": "pkg-exec-test-001",
  "target_gate": "gate-mainline-001",
  "transition_intent": "revision|retry"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "submission_id": "sub-exec-001",
    "object_ref": "pkg-exec-test-001",
    "target_gate": "gate-mainline-001",
    "submitted_at": "<ISO8601 timestamp>",
    "gate_status": "pending-intake"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.submission_id is not null
- response.data.gate_status == "pending-intake"
- response.data.object_ref == "pkg-exec-test-001"
- response.data.target_gate == "gate-mainline-001"

### Side Effect Assertions

- execution loop 状态记录中标记该对象为 "submitted"
- gate loop 消费队列中新增该对象的引用
- 无并行 handoff 规则被创建

### Anti-False-Pass Checks

- submission_record_exists in database (not just response claim)
- gate_queue_entry_created with matching submission_id
- no_parallel_handoff_rule_created
- response.submission_id matches persisted record id

### Evidence Required

- request_snapshot
- response_snapshot
- loop_state_assertion_result
- gate_queue_entry_log

## Cleanup

- 删除创建的 submission 记录
- 清理 gate 消费队列中的测试条目
- 恢复 execution loop 状态为 pre-test state
