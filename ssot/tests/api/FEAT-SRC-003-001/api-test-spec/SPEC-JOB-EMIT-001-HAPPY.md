# API Test Spec — JOB-EMIT-001: 发射 Ready Job

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.job.emit.happy |
| coverage_id | api.job.emit.happy |
| capability | JOB-EMIT-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-001.Scope.authoritative-refs |

## Test Contract

### Preconditions

- Gate decision with `approved` status and `progression_mode = auto-continue` exists
- Authoritative refs (proposal + evidence) are valid and accessible
- `artifacts/jobs/ready` directory exists

### Request

```
POST /api/v1/jobs/emit-ready
Content-Type: application/json

{
  "job_id": "job-ready-002",
  "authoritative_refs": {
    "gate_decision_ref": "gate-decision-002",
    "proposal_ref": "adr018-epic2feat-restart-20260326-r1",
    "evidence_refs": [
      "artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1/evidence.md"
    ],
    "lineage_refs": [
      "artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1/candidate-package.md"
    ]
  },
  "next_skill_target": "skills/l3/ll-execution-loop-job-runner/",
  "progression_mode": "auto-continue"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-ready-002",
    "emitted_path": "artifacts/jobs/ready/job-ready-002.json",
    "authoritative_refs": {
      "gate_decision_ref": "gate-decision-002",
      "proposal_ref": "adr018-epic2feat-restart-20260326-r1",
      "evidence_refs": ["artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1/evidence.md"],
      "lineage_refs": ["artifacts/epic-to-feat/adr018-epic2feat-restart-20260326-r1/candidate-package.md"]
    },
    "next_skill_target": "skills/l3/ll-execution-loop-job-runner/",
    "emitted_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.emitted_path starts with "artifacts/jobs/ready/"
- response.data.authoritative_refs matches request input exactly
- response.data.next_skill_target matches request input

### Side Effect Assertions

- Job file exists at emitted_path with complete content
- File is readable by downstream runner
- File contains all authoritative_refs from request
- File contains a unique job_id that is traceable back to gate_decision_ref

### Anti-False-Pass Checks
- verify emitted job file actually exists at the returned emitted_path (not just 201 response)
- verify job file content contains all authoritative_refs from request (not generic placeholder)
- verify no duplicate job files created in artifacts/jobs/ready for the same gate_decision_ref
- verify gate decision record updated with job_generation_status = "emitted"

### Evidence Required

- request_snapshot
- response_snapshot
- file_system_assertion
- content_integrity_check

## Source References
- FEAT-SRC-003-001.Scope.authoritative-refs
- FEAT-SRC-003-001.Constraints
- FEAT-SRC-003-001.AcceptanceChecks.job-emission

## Cleanup

- Delete job file from `artifacts/jobs/ready/job-ready-002.json`
- Verify no orphaned references remain
