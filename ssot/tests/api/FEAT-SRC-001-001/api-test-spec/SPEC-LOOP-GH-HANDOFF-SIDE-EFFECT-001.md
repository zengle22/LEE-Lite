# API Test Spec — LOOP-GH-HANDOFF-001: Gate-Human 交接界面 (数据副作用)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.gh-handoff.data-side-effect |
| coverage_id | api.loop.gh-handoff.data-side-effect |
| capability | LOOP-GH-HANDOFF-001 |
| scenario_type | data_side_effect |
| priority | P0 |
| dimension | 数据副作用 |
| source_feat_ref | FEAT-SRC-001-001.Scope.gate-human-interface |

## Test Contract

### Preconditions

- gate loop 处于 ready 消费状态
- human loop 可接收 decision
- 数据库可写

### Operation

```
POST /api/v1/loops/gate-human/handoff
Content-Type: application/json

{
  "handoff_id": "handoff-gh-005",
  "proposal_ref": "prop-test-005",
  "consumer_role": "human_reviewer",
  "decision_target": "approve"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "handoff_id": "handoff-gh-005",
    "proposal_consumed": true,
    "decision_pending": true,
    "consumer_role": "human_reviewer",
    "created_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Side Effect Assertions

- handoff 记录持久化
- proposal 状态更新为 "consumed"
- human loop decision queue 新增 entry
- 交接时间戳被记录

### Anti-False-Pass Checks

- handoff_record_persisted_with_correct_timestamp
- proposal_state_actually_updated_to_consumed in database
- decision_queue_entry_exists_with_matching_handoff_id
- all_side_effects_are_atomic (all or none)

### Evidence Required

- request_snapshot
- response_snapshot
- db_handoff_record
- proposal_state_change_log
- decision_queue_entry

## Cleanup

- 删除创建的 handoff 记录
- 恢复 proposal 状态
- 清理 decision queue
