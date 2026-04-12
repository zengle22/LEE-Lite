# API Test Spec — LOOP-RESPONSIBILITY-001: Loop 责任分离

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.responsibility.happy |
| coverage_id | api.loop.responsibility.happy |
| capability | LOOP-RESPONSIBILITY-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-01 |

## Test Contract

### Preconditions

- 主链中 execution、gate、human 三种 loop 均已初始化
- 无重叠的责任分配

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

### Response Assertions

- status_code == 200
- response.data.overlap_detected == false
- 三种 loop 各有一个 transition_owner
- 每个 loop 的 owns 数组非空且无重叠

### Side Effect Assertions

- 无状态变更 (纯验证操作)
- 验证结果被记录到 audit log

### Anti-False-Pass Checks

- each_loop_has_exactly_one_transition_owner (no duplicates)
- no_overlap_in_owns_arrays_between_any_two_loops
- response.overlap_detected consistent with actual responsibility matrix

### Evidence Required

- request_snapshot
- response_snapshot
- responsibility_matrix_audit_log

## Cleanup

- No cleanup needed (read-only verification)
