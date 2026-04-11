# API Test Spec — HANDOFF-CREATE-001: 创建交接对象

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.handoff.create.happy |
| coverage_id | api.handoff.create.happy |
| capability | HANDOFF-CREATE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-005-001.Scope.authoritative-handoff |

## Test Contract

### Preconditions

- candidate package 已通过校验
- 系统中不存在相同包的已有 handoff

### Request

```
POST /api/v1/handoffs
Content-Type: application/json

{
  "source_candidate_package_id": "pkg-test-001",
  "proposal_ref": "adr011-raw2src-fix-20260327-r1",
  "gate_decision_ref": "artifacts/active/gates/decisions/gate-decision.json",
  "handoff_type": "authoritative"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "handoff_id": "handoff-test-001",
    "type": "authoritative",
    "status": "pending-intake",
    "source_candidate_package_id": "pkg-test-001",
    "created_at": "<ISO8601 timestamp>",
    "frozen_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.type == "authoritative"
- response.data.status == "pending-intake"
- response.data.frozen_at is present (ISO8601)

### Side Effect Assertions

- handoff 记录已持久化
- frozen_at 时间戳已记录
- gate 消费队列可读取该 handoff

### Evidence Required

- request_snapshot
- response_snapshot
- db_assertion_result
- gate_queue_entry_log

## Cleanup

- 删除创建的 handoff 记录
