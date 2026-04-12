# API Test Spec — LINEAGE-REF-001: Lineage 引用验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.lineage.ref.happy |
| coverage_id | api.lineage.ref.happy |
| capability | LINEAGE-REF-001 |
| scenario_type | happy_path |
| priority | P1 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-003.Scope |

## Test Contract

### Preconditions

- formal 对象已存在并具有完整 lineage 链
- 下游 consumer 已注册
- lineage 链从 producer 到 formal 完整可追溯

### Operation

```
GET /api/v1/lineage/verify?formal_ref=formal-layer-001/formal-001&consumer=skill-reviewer-001
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "formal_ref": "formal-layer-001/formal-001",
    "consumer": "skill-reviewer-001",
    "lineage_chain": ["pkg-001", "formal-001"],
    "lineage_valid": true,
    "chain_complete": true,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.lineage_valid == true
- response.data.chain_complete == true
- response.data.lineage_chain 包含至少一个 producer 对象

### Side Effect Assertions

- 验证结果记录到 lineage audit log
- 无 lineage 配置变更

### Anti-False-Pass Checks

- lineage_chain is traversable end-to-end (not truncated)
- formal_ref matches the terminal node of the lineage chain

### Evidence Required

- request_snapshot
- response_snapshot
- lineage_audit_record

## Cleanup

- 删除验证 audit 记录

### Source References

- FEAT-SRC-001-003.Scope.lineage-ref
- FEAT-SRC-001-003.AC-02
