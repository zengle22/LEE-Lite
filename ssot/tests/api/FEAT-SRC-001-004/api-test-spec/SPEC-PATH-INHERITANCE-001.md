# API Test Spec — PATH-INHERITANCE-001: 路径规则继承

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.path-inheritance.happy |
| coverage_id | api.path-inheritance.happy |
| capability | PATH-INHERITANCE-001 |
| scenario_type | happy_path |
| priority | P1 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-004.Constraints |

## Test Contract

### Preconditions

- 上游路径治理规则已配置
- 下游 skill 目录继承上游治理 scope
- 无自定义路径规则冲突

### Operation

```
GET /api/v1/path-inheritance/verify?downstream_skill=skill-reviewer-001&parent_scope=mainline-handoff
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "downstream_skill": "skill-reviewer-001",
    "parent_scope": "mainline-handoff",
    "inheritance_valid": true,
    "inherited_rules": [
      "path_scope_restriction",
      "write_mode_enforcement",
      "governance_boundary"
    ],
    "custom_rules_detected": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.inheritance_valid == true
- response.data.inherited_rules 包含至少 2 条规则
- response.data.custom_rules_detected == false

### Side Effect Assertions

- 验证结果记录到 path inheritance audit log
- 无继承配置变更

### Anti-False-Pass Checks

- downstream_skill actually inherits from the declared parent_scope (not independent)
- inherited_rules match the parent scope configuration

### Evidence Required

- request_snapshot
- response_snapshot
- path_inheritance_audit_record

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-004.Scope.path-inheritance
- FEAT-SRC-001-004.Constraints
