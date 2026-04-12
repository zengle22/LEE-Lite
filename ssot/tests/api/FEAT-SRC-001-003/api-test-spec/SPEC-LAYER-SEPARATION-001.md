# API Test Spec — LAYER-SEPARATION-001: 对象分层验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.layer.separation.happy |
| coverage_id | api.layer.separation.happy |
| capability | LAYER-SEPARATION-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-003.AC-01 |

## Test Contract

### Preconditions

- 系统中同时存在 candidate 和 formal-stage 对象
- 分层配置已初始化

### Operation

```
POST /api/v1/layers/verify
Content-Type: application/json

{
  "candidate_layer_ref": "cand-layer-001",
  "formal_layer_ref": "formal-layer-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "separation_valid": true,
    "candidate_layer": {
      "ref": "cand-layer-001",
      "objects": ["pkg-001", "pkg-002"],
      "authority_level": "pending-gate"
    },
    "formal_layer": {
      "ref": "formal-layer-001",
      "objects": ["formal-001"],
      "authority_level": "authoritative"
    },
    "layer_mixing_detected": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.separation_valid == true
- response.data.layer_mixing_detected == false
- formal_layer.authority_level == "authoritative"

### Side Effect Assertions

- 验证结果记录到 layer audit log
- 无分层配置变更

### Evidence Required

- request_snapshot
- response_snapshot
- layer_audit_log_entry

## Cleanup

- 删除验证 audit 记录
