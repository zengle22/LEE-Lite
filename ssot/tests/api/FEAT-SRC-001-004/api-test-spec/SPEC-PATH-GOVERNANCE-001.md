# API Test Spec — PATH-GOVERNANCE-001: 路径治理边界

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.path-governance.happy |
| coverage_id | api.path-governance.happy |
| capability | PATH-GOVERNANCE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-004.AC-02 |

## Test Contract

### Preconditions

- 路径治理 scope 已初始化
- 受治理路径规则已配置
- 待验证路径在受治理 scope 内

### Operation

```
POST /api/v1/path-governance/verify
Content-Type: application/json

{
  "path": "ssot/handoff/mainline/handoff-001.md",
  "operation": "write",
  "governance_scope": "mainline-handoff"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "path": "ssot/handoff/mainline/handoff-001.md",
    "in_governed_scope": true,
    "governance_scope": "mainline-handoff",
    "operation_allowed": true,
    "scope_expansion_detected": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.in_governed_scope == true
- response.data.operation_allowed == true
- response.data.scope_expansion_detected == false

### Side Effect Assertions

- 验证结果记录到 path governance audit log
- 无治理 scope 配置变更

### Anti-False-Pass Checks

- path is within the declared governance scope (not outside but falsely reported)
- no_governance_scope_expansion occurred during verification
- audit_log_entry_created for this verification

### Evidence Required

- request_snapshot
- response_snapshot
- path_governance_audit_log

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-004.Scope.path-governance
- FEAT-SRC-001-004.AC-02
