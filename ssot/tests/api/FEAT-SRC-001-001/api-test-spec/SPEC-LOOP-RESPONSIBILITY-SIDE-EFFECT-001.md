# API Test Spec — LOOP-RESPONSIBILITY-001: Loop 责任分离 (数据副作用)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.responsibility.data-side-effect |
| coverage_id | api.loop.responsibility.data-side-effect |
| capability | LOOP-RESPONSIBILITY-001 |
| scenario_type | data_side_effect |
| priority | P0 |
| dimension | 数据副作用 |
| source_feat_ref | FEAT-SRC-001-001.Scope.loop-responsibility |

## Test Contract

### Preconditions

- 主链中三种 loop 均已正确初始化
- 数据库可写

### Operation

```
GET /api/v1/loops/responsibility/verify
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "loop_responsibilities": {
      "execution": {
        "owns": ["object_submission", "state_transition_to_gate"],
        "transition_owner": "execution_loop"
      },
      "gate": {
        "owns": ["proposal_evaluation", "decision_generation"],
        "transition_owner": "gate_loop"
      },
      "human": {
        "owns": ["decision_review", "progression_trigger"],
        "transition_owner": "human_loop"
      }
    },
    "overlap_detected": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Side Effect Assertions

- 验证结果持久化到 responsibility audit table
- 验证时间戳被记录
- 无责任矩阵变更 (read-only)

### Anti-False-Pass Checks

- audit_record_created_with_verification_timestamp
- responsibility_matrix_unchanged (read-only operation)
- verified_at_timestamp_is_recent (within test window)

### Evidence Required

- request_snapshot
- response_snapshot
- responsibility_audit_record
- timestamp_verification

## Cleanup

- 删除验证 audit 记录
