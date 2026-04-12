# API Test Spec — JOB-GEN-001: 批准后生成 Job

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.job.gen.happy |
| coverage_id | api.job.gen.happy |
| capability | JOB-GEN-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-001.Scope.ready-job-generation |

## Test Contract

### Preconditions

- Gate decision exists with status = "approved"
- `progression_mode = auto-continue` is set on the gate decision
- `artifacts/jobs/ready` directory exists and is writable
- No existing ready job with the same gate_decision_ref

### Request

```
POST /api/v1/jobs/generate
Content-Type: application/json

{
  "gate_decision_ref": "gate-decision-001",
  "progression_mode": "auto-continue",
  "candidate_package_ref": "pkg-001",
  "next_skill_target": "skills/l3/ll-next-skill/",
  "authoritative_refs": {
    "proposal_ref": "adr011-raw2src-fix-20260327-r1",
    "evidence_refs": [
      "artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1/proposal.md",
      "artifacts/epic-to-feat/adr011-raw2src-fix-20260327-r1/evidence.md"
    ]
  }
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-ready-001",
    "job_type": "ready_execution",
    "status": "ready",
    "progression_mode": "auto-continue",
    "created_at": "<ISO8601 timestamp>",
    "gate_decision_ref": "gate-decision-001",
    "next_skill_target": "skills/l3/ll-next-skill/",
    "queue_path": "artifacts/jobs/ready/job-ready-001.json"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.job_id is not null
- response.data.job_type == "ready_execution"
- response.data.status == "ready"
- response.data.progression_mode == "auto-continue"
- response.data.queue_path contains "artifacts/jobs/ready"

### Side Effect Assertions

- File exists at response.data.queue_path
- File content matches the request payload with authoritative_refs preserved
- Gate decision record is updated with job_generation_status = "emitted"
- No file created in hold/waiting-human queue path

### Evidence Required

- request_snapshot
- response_snapshot
- file_system_assertion (job file exists in ready path)
- gate_decision_update_log

## Cleanup

- Delete the created job file from `artifacts/jobs/ready`
- Reset gate decision job_generation_status to prior state
