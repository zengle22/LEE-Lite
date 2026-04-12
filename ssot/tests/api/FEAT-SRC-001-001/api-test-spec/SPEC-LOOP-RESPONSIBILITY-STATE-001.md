# API Test Spec — LOOP-RESPONSIBILITY-001: Loop 责任分离 (状态约束)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.responsibility.state-enforcement |
| coverage_id | api.loop.responsibility.state-enforcement |
| capability | LOOP-RESPONSIBILITY-001 |
| scenario_type | state_constraint |
| priority | P0 |
| dimension | 状态约束 |
| source_feat_ref | FEAT-SRC-001-001.Constraints |

## Test Contract

### Preconditions

- 某一 loop (例如 gate) 处于 inactive 状态
- 该 loop 仍声称拥有 transition 责任

### Operation

```
GET /api/v1/loops/responsibility/verify
```

### Expected Response

```json
{
  "status": "error",
  "data": {
    "loop_responsibilities": {
      "execution": {
        "owns": ["object_submission", "state_transition_to_gate"],
        "transition_owner": "execution_loop",
        "loop_state": "active"
      },
      "gate": {
        "owns": ["proposal_evaluation", "decision_generation"],
        "transition_owner": "gate_loop",
        "loop_state": "inactive"
      },
      "human": {
        "owns": ["decision_review", "progression_trigger"],
        "transition_owner": "human_loop",
        "loop_state": "active"
      }
    },
    "overlap_detected": false,
    "state_violations": [
      {
        "loop": "gate",
        "state": "inactive",
        "issue": "Inactive loop claims transition ownership"
      }
    ],
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": {
    "code": "LOOP_STATE_VIOLATION",
    "message": "Gate loop is inactive but still claims transition ownership"
  }
}
```

### Response Assertions

- status_code == 409
- response.data.state_violations 数组非空
- response.error.code == "LOOP_STATE_VIOLATION"

### Side Effect Assertions

- 状态违规被记录到 audit log
- 无状态变更

### Anti-False-Pass Checks

- state_violations_actually_exist (gate loop truly inactive)
- no_state_changed_during_read_only_verification
- error_response_contains_LOOP_STATE_VIOLATION_code

### Evidence Required

- request_snapshot
- response_snapshot
- state_violation_audit_log

## Cleanup

- No cleanup needed (read-only verification)
