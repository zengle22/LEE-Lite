# API Test Spec — MIGRATION-CUTOVER-001: 迁移切换控制

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.migration-cutover.happy |
| coverage_id | api.migration-cutover.happy |
| capability | MIGRATION-CUTOVER-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-005.AC-01 |

## Test Contract

### Preconditions

- governed skill 已完成 onboarding 并处于 ready 状态
- 迁移波次已配置
- cutover rule 与 fallback rule 已定义
- 当前处于波次 1，目标 skill 属于该波次

### Operation

```
POST /api/v1/migration/cutover
Content-Type: application/json

{
  "migration_wave": 1,
  "skill_id": "skill-planner-001",
  "cutover_rule": "gradual_rollout",
  "fallback_rule": "revert_to_previous",
  "target_state": "active_governed"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "migration_id": "mig-001",
    "wave": 1,
    "skill_id": "skill-planner-001",
    "cutover_status": "in_progress",
    "previous_state": "onboarded",
    "target_state": "active_governed",
    "cutover_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.cutover_status == "in_progress"
- response.data.wave == 1
- response.data.skill_id == "skill-planner-001"

### Side Effect Assertions

- skill 状态从 "onboarded" 更新为 "active_governed"
- 迁移记录持久化
- 切换事件记录到 migration audit log

### Anti-False-Pass Checks

- skill state actually transitions (not just response claim)
- migration_record exists with correct wave and skill_id
- no_other_skills outside current wave are affected
- audit_log_entry_created for this cutover event

### Evidence Required

- request_snapshot
- response_snapshot
- db_migration_record
- skill_state_change_log
- migration_audit_log

## Cleanup

- 删除创建的迁移记录
- 恢复 skill 状态为 pre-cutover state
- 清理 audit log test entries

### Source References

- FEAT-SRC-001-005.Scope.migration-management
- FEAT-SRC-001-005.AC-01
