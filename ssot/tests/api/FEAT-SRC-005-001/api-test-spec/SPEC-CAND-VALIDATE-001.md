# API Test Spec — CAND-VALIDATE-001: 校验候选包

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.cand.validate.happy |
| coverage_id | api.cand.validate.happy |
| capability | CAND-VALIDATE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-005-001.Scope.candidate-package |

## Test Contract

### Preconditions

- 存在格式完整、内容合规的 candidate package

### Request

```
POST /api/v1/candidate-packages/validate
Content-Type: application/json

{
  "candidate_package_id": "pkg-valid-001",
  "proposal_ref": "adr011-raw2src-fix-20260327-r1",
  "evidence_refs": [
    "artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1/proposal.md"
  ]
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "valid": true,
    "validation_details": {
      "proposal_present": true,
      "evidence_present": true,
      "format_valid": true,
      "gate_decision_ref_present": true
    }
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.valid == true
- response.data.validation_details.proposal_present == true
- response.data.validation_details.evidence_present == true

### Evidence Required

- request_snapshot
- response_snapshot
- validation_result_log

## Cleanup

- 无持久化副作用，无需清理
