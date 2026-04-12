# API Test Spec — LOOP-RESPONSIBILITY-001: Loop 责任分离 (异常路径)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.responsibility.overlap-detection |
| coverage_id | api.loop.responsibility.overlap-detection |
| capability | LOOP-RESPONSIBILITY-001 |
| scenario_type | exception |
| priority | P0 |
| dimension | 异常路径 |
| source_feat_ref | FEAT-SRC-001-001.Constraints |

## Test Contract

### Preconditions

- 人为制造责任重叠: execution 和 gate 都声明拥有 proposal_evaluation 职责

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
        "owns": ["object_submission", "state_transition_to_gate", "proposal_evaluation"],
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
    "overlap_detected": true,
    "overlaps": [
      {
        "capability": "proposal_evaluation",
        "claimed_by": ["execution", "gate"]
      }
    ],
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": {
    "code": "RESPONSIBILITY_OVERLAP",
    "message": "Detected overlapping responsibility: proposal_evaluation claimed by execution, gate"
  }
}
```

### Response Assertions

- status_code == 409
- response.data.overlap_detected == true
- response.data.overlaps 数组非空
- response.error.code == "RESPONSIBILITY_OVERLAP"

### Side Effect Assertions

- 重叠检测被记录到 audit log
- 无状态变更

### Anti-False-Pass Checks

- overlap_actually_exists (not manufactured by test setup error)
- both_loops_claim_the_overlapping_capability
- no_state_changed_during_read_only_verification

### Evidence Required

- request_snapshot
- response_snapshot
- overlap_audit_log_entry

## Cleanup

- No cleanup needed (read-only verification)
