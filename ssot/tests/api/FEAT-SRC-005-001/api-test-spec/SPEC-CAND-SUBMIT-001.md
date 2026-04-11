# API Test Spec — CAND-SUBMIT-001: 提交候选包

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.cand.submit.happy |
| coverage_id | api.cand.submit.happy |
| capability | CAND-SUBMIT-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-005-001.Scope.candidate-package |

## Test Contract

### Preconditions

- 存在有效的 candidate package（包含 proposal + evidence）
- 用户已通过身份验证（试点阶段简化为 mock user）
- 系统中不存在相同 candidate package 的已有 handoff

### Request

```
POST /api/v1/candidate-packages/submit
Content-Type: application/json

{
  "candidate_package_id": "pkg-test-001",
  "proposal_ref": "adr011-raw2src-fix-20260327-r1",
  "evidence_refs": [
    "artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1/proposal.md",
    "artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1/evidence.md"
  ],
  "submitter_id": "user-test-001"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "handoff_id": "handoff-001",
    "status": "pending-intake",
    "created_at": "<ISO8601 timestamp>",
    "candidate_package_id": "pkg-test-001"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.handoff_id is not null
- response.data.status == "pending-intake"
- response.data.candidate_package_id == "pkg-test-001"

### Side Effect Assertions

- 数据库中存在 handoff 记录，status = "pending-intake"
- handoff 记录的 candidate_package_id == "pkg-test-001"
- gate 消费队列中新增该 handoff 的引用

### Evidence Required

- request_snapshot
- response_snapshot
- db_assertion_result
- gate_queue_entry_log

## Cleanup

- 删除创建的 handoff 记录
- 清理 gate 消费队列中的测试条目
