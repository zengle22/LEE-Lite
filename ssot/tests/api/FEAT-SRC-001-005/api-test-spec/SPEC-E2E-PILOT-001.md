# API Test Spec — E2E-PILOT-001: 跨 skill E2E 闭环

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.e2e-pilot.happy |
| coverage_id | api.e2e-pilot.happy |
| capability | E2E-PILOT-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-005.AC-02 |

## Test Contract

### Preconditions

- producer skill (skill-planner-001) 已 onboarded 并处于 active_governed 状态
- consumer skill (skill-reviewer-001) 已 onboarded 并处于 active_governed 状态
- gate skill (skill-gate-001) 已 onboarded 并拥有 gate authority
- audit pipeline 已配置并可接收证据

### Operation

```
POST /api/v1/e2e-pilot/execute
Content-Type: application/json

{
  "pilot_id": "pilot-001",
  "chain": {
    "producer": "skill-planner-001",
    "consumer": "skill-reviewer-001",
    "audit": "audit-pipeline-001",
    "gate": "skill-gate-001"
  },
  "test_artifact": {
    "type": "candidate_package",
    "ref": "pkg-pilot-001"
  }
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "pilot_id": "pilot-001",
    "chain_status": "completed",
    "steps": [
      {"step": "produce", "skill": "skill-planner-001", "status": "success"},
      {"step": "consume", "skill": "skill-reviewer-001", "status": "success"},
      {"step": "audit", "skill": "audit-pipeline-001", "status": "success"},
      {"step": "gate", "skill": "skill-gate-001", "status": "success"}
    ],
    "evidence_generated": true,
    "completed_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.chain_status == "completed"
- response.data.steps 包含 4 个步骤且全部 status == "success"
- response.data.evidence_generated == true

### Side Effect Assertions

- 完整的 pilot chain 执行记录持久化
- E2E 证据生成并存储
- 每个 skill 的执行状态被记录

### Anti-False-Pass Checks

- all 4 chain steps actually executed (not skipped)
- evidence_artifacts exist for each step
- chain_execution_record exists with complete step sequence
- no_step_short_circuited (each step has real input from previous)

### Evidence Required

- request_snapshot
- response_snapshot
- e2e_pilot_execution_record
- chain_step_evidence (per step)
- generated_evidence_artifacts

## Cleanup

- 删除 pilot 执行记录
- 清理生成的证据文件
- 重置各 skill 的执行状态

### Source References

- FEAT-SRC-001-005.Scope.e2e-pilot
- FEAT-SRC-001-005.AC-02
