# API Test Spec — GATE-AUTHORITY-001: Gate 权限防护

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.gate.authority.happy |
| coverage_id | api.gate.authority.happy |
| capability | GATE-AUTHORITY-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-003.AC-03 |

## Test Contract

### Preconditions

- gate loop 已初始化并拥有 gate authority
- 业务 skill (非 gate) 存在但未授权 gate 权限
- 存在待审批的 candidate 对象

### Operation

```
POST /api/v1/gate/authority/verify
Content-Type: application/json

{
  "gate_id": "gate-mainline-001",
  "candidate_ref": "cand-layer-001/pkg-001",
  "approver_skill_id": "skill-planner-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "gate_authority_valid": true,
    "gate_id": "gate-mainline-001",
    "approver_skill_id": "skill-planner-001",
    "silent_inheritance_detected": false,
    "unauthorized_approval_blocked": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.gate_authority_valid == true
- response.data.silent_inheritance_detected == false

### Side Effect Assertions

- 权限验证记录到 gate authority audit log
- 无权限配置变更

### Anti-False-Pass Checks

- approver_skill_id is NOT a registered gate authority (business skill cannot act as gate)
- no_silent_inheritance_chain from gate to business skill
- gate_authority_record_exists with correct permission scope

### Evidence Required

- request_snapshot
- response_snapshot
- gate_authority_audit_log

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-003.Scope.gate-authority
- FEAT-SRC-001-003.AC-03
