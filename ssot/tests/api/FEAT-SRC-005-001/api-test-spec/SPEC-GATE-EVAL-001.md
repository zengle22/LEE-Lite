# API Test Spec — GATE-EVAL-001: Gate 评估

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.gate.eval.happy |
| coverage_id | api.gate.eval.happy |
| capability | GATE-EVAL-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-005-001.AcceptanceChecks.submission-visible |

## Test Contract

### Preconditions

- 存在 status = "pending-intake" 的 handoff
- handoff 包含完整的 candidate package 引用

### Request

```
POST /api/v1/gate/evaluate
Content-Type: application/json

{
  "handoff_id": "handoff-test-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "evaluation_id": "eval-001",
    "handoff_id": "handoff-test-001",
    "decision": "approved",
    "evaluation_criteria": [
      {
        "criterion": "proposal_present",
        "result": "pass"
      },
      {
        "criterion": "evidence_present",
        "result": "pass"
      },
      {
        "criterion": "format_valid",
        "result": "pass"
      }
    ],
    "evaluated_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.decision == "approved"
- response.data.evaluation_criteria 中所有 result == "pass"
- response.data.evaluated_at is present

### Side Effect Assertions

- gate decision 已持久化
- handoff 状态已更新为 "approved"

### Evidence Required

- request_snapshot
- response_snapshot
- db_assertion_result
- gate_evaluation_log

## Cleanup

- 删除 gate evaluation 记录
- 还原 handoff 状态
