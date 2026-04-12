# API Test Spec — LOOP-INHERITANCE-001: 下游协作规则继承 (异常路径)

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.inheritance.parallel-rule-detection |
| coverage_id | api.loop.inheritance.parallel-rule-detection |
| capability | LOOP-INHERITANCE-001 |
| scenario_type | exception |
| priority | P1 |
| dimension | 异常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-03 |

## Test Contract

### Preconditions

- 下游 workflow 注册了平行 handoff 规则 (违反继承约束)

### Operation

```
GET /api/v1/loops/inheritance/verify?downstream=workflow-dev-feat-to-tech-violation
```

### Expected Response

```json
{
  "status": "error",
  "data": {
    "downstream": "workflow-dev-feat-to-tech-violation",
    "inherits_from": "FEAT-SRC-001-001",
    "rules_inherited": [
      "execution_loop_submission",
      "gate_human_handoff"
    ],
    "parallel_rules_detected": true,
    "parallel_rules": [
      {
        "rule_name": "custom_handoff_protocol",
        "conflicts_with": "gate_human_handoff",
        "severity": "critical"
      }
    ],
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": {
    "code": "PARALLEL_RULE_VIOLATION",
    "message": "Downstream workflow defines parallel handoff rule 'custom_handoff_protocol' that conflicts with inherited rule 'gate_human_handoff'"
  }
}
```

### Response Assertions

- status_code == 409
- response.data.parallel_rules_detected == true
- response.data.parallel_rules 数组非空
- response.error.code == "PARALLEL_RULE_VIOLATION"

### Side Effect Assertions

- 违规记录到 inheritance audit log
- 下游 workflow 被标记为 non-compliant

### Anti-False-Pass Checks

- parallel_rules_actually_detected (not pre-existing state)
- downstream_workflow_marked_non-compliant_in_persistence
- violation_severity_correctly_classified_as_critical

### Evidence Required

- request_snapshot
- response_snapshot
- violation_audit_record
- downstream_compliance_status

## Cleanup

- 删除违规 audit 记录
- 恢复下游 workflow compliance 状态
