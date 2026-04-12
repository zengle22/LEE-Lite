# API Test Spec — CONSUMER-ADMISSION-001: Consumer 准入验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.consumer.admission.happy |
| coverage_id | api.consumer.admission.happy |
| capability | CONSUMER-ADMISSION-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-003.AC-02 |

## Test Contract

### Preconditions

- formal layer 对象已存在且状态为 authoritative
- consumer skill 已注册并处于 active 状态
- 存在有效的 formal ref 与 lineage 链

### Operation

```
POST /api/v1/consumer/admission/verify
Content-Type: application/json

{
  "consumer_skill_id": "skill-reviewer-001",
  "formal_ref": "formal-layer-001/formal-001",
  "lineage_chain": ["pkg-001", "formal-001"],
  "access_intent": "consume_formal_artifact"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "admission_granted": true,
    "consumer_skill_id": "skill-reviewer-001",
    "formal_ref": "formal-layer-001/formal-001",
    "lineage_verified": true,
    "authority_level": "authoritative",
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.admission_granted == true
- response.data.lineage_verified == true
- response.data.authority_level == "authoritative"

### Side Effect Assertions

- 准入验证记录到 consumer admission audit log
- 无准入配置变更

### Anti-False-Pass Checks

- formal_ref resolves to an existing authoritative object (not a path-guessed reference)
- lineage_chain is traversable from consumer to formal (not fabricated)
- no_admission_record_without_verification (system does not grant access without completing lineage check)
- audit_log_entry_created for this specific verification

### Evidence Required

- request_snapshot
- response_snapshot
- consumer_admission_audit_log
- lineage_traversal_record

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-003.Scope.consumer-admission
- FEAT-SRC-001-003.AC-02
