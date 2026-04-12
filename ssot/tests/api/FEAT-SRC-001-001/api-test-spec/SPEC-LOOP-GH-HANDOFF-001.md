# API Test Spec — LOOP-GH-HANDOFF-001: Gate-Human 交接界面

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.gh-handoff.happy |
| coverage_id | api.loop.gh-handoff.happy |
| capability | LOOP-GH-HANDOFF-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-001.Scope.gate-human-interface |

## Test Contract

### Preconditions

- gate loop 处于 ready 消费状态
- 存在待消费的 proposal 对象
- human loop 处于可接收 decision 状态
- 交接界面已初始化

### Operation

```
POST /api/v1/loops/gate-human/handoff
Content-Type: application/json

{
  "handoff_id": "handoff-gh-001",
  "proposal_ref": "prop-test-001",
  "consumer_role": "human_reviewer",
  "decision_target": "approve|revise|retry"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "handoff_id": "handoff-gh-001",
    "proposal_consumed": true,
    "decision_pending": true,
    "consumer_role": "human_reviewer",
    "created_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.handoff_id == "handoff-gh-001"
- response.data.proposal_consumed == true
- response.data.decision_pending == true

### Side Effect Assertions

- proposal 状态标记为 "consumed"
- human loop 收到 decision request
- 交接记录持久化

### Anti-False-Pass Checks

- proposal_state_actually_changed_to_consumed (not just response claim)
- handoff_record_exists_in_database with correct proposal_ref
- human_loop_decision_queue_received_entry
- response.handoff_id matches persisted record id

### Evidence Required

- request_snapshot
- response_snapshot
- proposal_state_assertion
- handoff_record

## Cleanup

- 删除创建的 handoff 记录
- 恢复 proposal 状态
- 清理 human loop decision queue
