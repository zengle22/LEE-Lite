# API Test Spec — LOOP-GH-HANDOFF-001: Gate-Human 交接界面 (异常路径)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.gh-handoff.decision-failure |
| coverage_id | api.loop.gh-handoff.decision-failure |
| capability | LOOP-GH-HANDOFF-001 |
| scenario_type | exception |
| priority | P0 |
| dimension | 异常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-01 |

## Test Contract

### Preconditions

- gate loop 处于 ready 状态
- human loop 不可用或返回失败

### Operation

```
POST /api/v1/loops/gate-human/handoff
Content-Type: application/json

{
  "handoff_id": "handoff-gh-004",
  "proposal_ref": "prop-test-004",
  "consumer_role": "human_reviewer",
  "decision_target": "approve"
}
```

### Expected Response

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "DECISION_CONSUMER_UNAVAILABLE",
    "message": "Human reviewer consumer is not available to accept decision",
    "consumer_role": "human_reviewer"
  }
}
```

### Response Assertions

- status_code == 503
- response.error.code == "DECISION_CONSUMER_UNAVAILABLE"
- response.data == null

### Side Effect Assertions

- handoff 可能被创建但标记为 failed
- 或无 handoff 被创建 (取决于实现)
- 无 decision 被下发到下游

### Anti-False-Pass Checks

- no_decision_propagated_to_downstream
- handoff_state_consistent (either not created or marked failed)
- consumer_availability_state_truly_unavailable

### Evidence Required

- request_snapshot
- response_snapshot
- handoff_state_if_created
- consumer_availability_log

## Cleanup

- 如创建 failed handoff，则清理
- 恢复 consumer availability state
