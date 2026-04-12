# API Test Spec — IO-SCOPE-001: 主链 IO 边界验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.io-scope.happy |
| coverage_id | api.io-scope.happy |
| capability | IO-SCOPE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-004.AC-01 |

## Test Contract

### Preconditions

- 主链 IO 路径配置已初始化
- 存在待验证的 IO 操作

### Operation

```
POST /api/v1/io-scope/validate
Content-Type: application/json

{
  "operation": "write",
  "path": "ssot/handoff/mainline/handoff-001.md",
  "mode": "create",
  "io_type": "mainline_handoff"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "in_scope": true,
    "io_type": "mainline_handoff",
    "governed_path": true,
    "path": "ssot/handoff/mainline/handoff-001.md",
    "mode_allowed": true,
    "validated_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.in_scope == true
- response.data.governed_path == true
- response.data.mode_allowed == true

### Side Effect Assertions

- 验证结果记录到 IO governance audit log
- 无 IO 配置变更

### Evidence Required

- request_snapshot
- response_snapshot
- io_governance_audit_log

## Cleanup

- 删除验证 audit 记录
