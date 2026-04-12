# API Test Spec — HANDOFF-UPGRADE-001: 正式升级路径

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.handoff.upgrade.happy |
| coverage_id | api.handoff.upgrade.happy |
| capability | HANDOFF-UPGRADE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-002.AC-01 |

## Test Contract

### Preconditions

- handoff 对象存在且状态为 gate-approved
- gate decision 已生成且为 approve
- 无已有 formal materialization 对于该 handoff

### Operation

```
POST /api/v1/handoff/upgrade
Content-Type: application/json

{
  "handoff_id": "handoff-test-001",
  "gate_decision_ref": "gd-test-001",
  "upgrade_intent": "formal_materialization"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "formal_materialization_id": "formal-001",
    "handoff_id": "handoff-test-001",
    "gate_decision_ref": "gd-test-001",
    "upgrade_path": ["handoff", "gate_decision", "formal_materialization"],
    "upgraded_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.formal_materialization_id is not null
- response.data.upgrade_path 包含且仅包含 3 个元素
- response.data.handoff_id == "handoff-test-001"

### Side Effect Assertions

- handoff 状态标记为 "upgraded"
- formal materialization 记录持久化
- 升级链路被记录到 audit log

### Evidence Required

- request_snapshot
- response_snapshot
- db_formal_materialization_record
- handoff_state_change_log
- upgrade_path_audit_log

## Cleanup

- 删除创建的 formal materialization 记录
- 恢复 handoff 状态
- 清理 audit log test entries
