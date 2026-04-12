# API Test Spec — WRITE-ENFORCEMENT-001: 写入模式强制

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.write-enforcement.happy |
| coverage_id | api.write-enforcement.happy |
| capability | WRITE-ENFORCEMENT-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-004.AC-03 |

## Test Contract

### Preconditions

- 写入模式配置已初始化
- path/mode 边界已定义
- 待执行写入操作符合正式写入模式

### Operation

```
POST /api/v1/write-enforcement/validate
Content-Type: application/json

{
  "path": "ssot/handoff/mainline/handoff-001.md",
  "write_mode": "formal",
  "content_type": "handoff_material",
  "author_skill_id": "skill-planner-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "path": "ssot/handoff/mainline/handoff-001.md",
    "write_mode_enforced": true,
    "mode_match": true,
    "silent_fallback_detected": false,
    "validated_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.write_mode_enforced == true
- response.data.mode_match == true
- response.data.silent_fallback_detected == false

### Side Effect Assertions

- 写入验证记录到 write enforcement audit log
- 无写入模式配置变更

### Anti-False-Pass Checks

- write_mode matches the configured mode for this path (no silent fallback to free write)
- no_fallback_record in enforcement logs
- content_type is consistent with the declared write_mode

### Evidence Required

- request_snapshot
- response_snapshot
- write_enforcement_audit_log

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-004.Scope.write-enforcement
- FEAT-SRC-001-004.AC-03
