# API Test Spec — LOOP-INHERITANCE-001: 下游协作规则继承

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.loop.inheritance.happy |
| coverage_id | api.loop.inheritance.happy |
| capability | LOOP-INHERITANCE-001 |
| scenario_type | happy_path |
| priority | P1 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-001-001.AC-03 |

## Test Contract

### Preconditions

- 下游 workflow 已注册并声明继承本 FEAT 的协作规则
- 不存在平行 handoff/queue 规则

### Operation

```
GET /api/v1/loops/inheritance/verify?downstream=workflow-dev-feat-to-tech
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "downstream": "workflow-dev-feat-to-tech",
    "inherits_from": "FEAT-SRC-001-001",
    "rules_inherited": [
      "execution_loop_submission",
      "gate_human_handoff",
      "loop_responsibility_split",
      "reflow_boundary"
    ],
    "parallel_rules_detected": false,
    "verified_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.inherits_from == "FEAT-SRC-001-001"
- response.data.rules_inherited 包含至少 4 条规则
- response.data.parallel_rules_detected == false

### Side Effect Assertions

- 验证结果记录到 inheritance audit log
- 无下游规则变更

### Anti-False-Pass Checks

- downstream_workflow_actually_inherits_from_declared_parent (not independent)
- rules_inherited_list_matches_parent_configuration

### Evidence Required

- request_snapshot
- response_snapshot
- inheritance_audit_record

## Cleanup

- 删除验证 audit 记录
