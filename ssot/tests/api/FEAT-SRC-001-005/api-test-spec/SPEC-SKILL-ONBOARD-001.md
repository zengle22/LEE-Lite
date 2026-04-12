# API Test Spec — SKILL-ONBOARD-001: 技能接入验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.skill-onboard.happy |
| coverage_id | api.skill-onboard.happy |
| capability | SKILL-ONBOARD-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-005.AC-01 |

## Test Contract

### Preconditions

- governed skill 定义已存在
- onboarding 矩阵已配置
- 系统中不存在相同 skill 的已有注册

### Operation

```
POST /api/v1/skills/onboard
Content-Type: application/json

{
  "skill_id": "skill-planner-001",
  "skill_type": "planner",
  "role": "producer",
  "onboarding_wave": 1,
  "integration_matrix_entry": {
    "produces": ["candidate_package"],
    "consumes": ["gate_decision"],
    "gate_consumer": true
  }
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "skill_id": "skill-planner-001",
    "onboarding_status": "registered",
    "wave": 1,
    "integration_matrix_validated": true,
    "registered_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.onboarding_status == "registered"
- response.data.integration_matrix_validated == true
- response.data.skill_id == "skill-planner-001"

### Side Effect Assertions

- skill 注册记录持久化
- onboarding 矩阵更新
- 注册事件记录到 audit log

### Evidence Required

- request_snapshot
- response_snapshot
- db_skill_registration_record
- onboarding_matrix_update_log
- audit_log_entry

## Cleanup

- 删除创建的 skill 注册记录
- 恢复 onboarding 矩阵
- 清理 audit log test entries
