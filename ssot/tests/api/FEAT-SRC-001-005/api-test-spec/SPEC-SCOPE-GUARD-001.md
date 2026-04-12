# API Test Spec — SCOPE-GUARD-001: 作用域防护

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.scope-guard.happy |
| coverage_id | api.scope-guard.happy |
| capability | SCOPE-GUARD-001 |
| scenario_type | happy_path |
| priority | P1 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-005.AC-03 |

## Test Contract

### Preconditions

- governed skill adoption scope 已定义
- 存在受治理的 file set
- 仓库级文件治理改造尝试被触发

### Operation

```
POST /api/v1/scope-guard/verify
Content-Type: application/json

{
  "adoption_scope": "governed-skills-only",
  "target_files": [
    "skills/planner/config.yaml",
    "skills/reviewer/config.yaml"
  ],
  "excluded_patterns": [
    "**/*.md",
    "docs/**",
    "src/**"
  ]
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "scope_guard_active": true,
    "adoption_scope": "governed-skills-only",
    "files_in_scope": 2,
    "files_out_of_scope": 0,
    "scope_expansion_blocked": true,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.scope_guard_active == true
- response.data.files_out_of_scope == 0
- response.data.scope_expansion_blocked == true

### Side Effect Assertions

- 作用域防护验证记录到 scope guard audit log
- 无 scope 配置变更

### Anti-False-Pass Checks

- files_in_scope count matches actual governed skill files only
- no_repository_wide_governance_triggered

### Evidence Required

- request_snapshot
- response_snapshot
- scope_guard_audit_log

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-005.Scope.scope-guard
- FEAT-SRC-001-005.AC-03
