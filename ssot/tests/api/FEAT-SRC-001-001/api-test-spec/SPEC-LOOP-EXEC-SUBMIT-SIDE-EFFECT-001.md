# API Test Spec — LOOP-EXEC-SUBMIT-001: 执行循环提交 (数据副作用)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.exec-submit.data-side-effect |
| coverage_id | api.loop.exec-submit.data-side-effect |
| capability | LOOP-EXEC-SUBMIT-001 |
| scenario_type | data_side_effect |
| priority | P0 |
| dimension | 数据副作用 |
| source_feat_ref | FEAT-SRC-001-001.Scope.execution-loop |

## Test Contract

### Preconditions

- execution loop 处于 active 状态
- 存在有效的待提交对象
- 数据库可写

### Operation

```
POST /api/v1/loops/execution/submit
Content-Type: application/json

{
  "loop_id": "loop-exec-004",
  "object_type": "candidate_package",
  "object_ref": "pkg-exec-test-004",
  "target_gate": "gate-mainline-001",
  "transition_intent": "revision"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "submission_id": "sub-exec-004",
    "object_ref": "pkg-exec-test-004",
    "target_gate": "gate-mainline-001",
    "submitted_at": "<ISO8601 timestamp>",
    "gate_status": "pending-intake"
  },
  "error": null
}
```

### Side Effect Assertions

- submission 记录持久化到数据库，包含完整 audit trail
- execution loop 状态更新为 "submitted"，记录时间戳
- gate 消费队列中新增 entry，指向同一 submission_id
- lineage chain 记录: object_ref -> submission_id -> gate_entry

### Anti-False-Pass Checks

- submission_record_persisted_with_complete_audit_trail
- loop_state_actually_updated_in_database (not cached)
- gate_queue_entry_points_to_same_submission_id
- lineage_chain_links_are_consistent_across_all_records

### Evidence Required

- request_snapshot
- response_snapshot
- db_submission_record
- loop_state_change_log
- gate_queue_entry_verification
- lineage_chain_assertion

## Cleanup

- 删除创建的 submission 记录
- 清理 gate 消费队列中的测试条目
- 恢复 execution loop 状态
- 删除 lineage chain test records
