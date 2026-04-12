# API Test Spec — ENTRY-START-001: 启动 Runner 入口

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.entry.start.happy |
| coverage_id | api.entry.start.happy |
| capability | ENTRY-START-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-002.AcceptanceChecks.named-skill-entry |

## Test Contract

### Preconditions

- Skill bundle exists at `skills/l3/ll-execution-loop-job-runner/`
- `artifacts/jobs/ready` directory exists and is accessible
- No active runner session exists

### Request

```
POST /api/v1/runner/start
Content-Type: application/json

{
  "skill_bundle_path": "skills/l3/ll-execution-loop-job-runner/",
  "ready_queue_path": "artifacts/jobs/ready",
  "mode": "start"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "session_id": "session-runner-001",
    "skill_bundle_path": "skills/l3/ll-execution-loop-job-runner/",
    "ready_queue_bound": "artifacts/jobs/ready",
    "run_context": {
      "started_at": "<ISO8601 timestamp>",
      "lineage_refs": [],
      "mode": "start"
    },
    "runner_status": "active"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.session_id is not null
- response.data.skill_bundle_path matches request input
- response.data.ready_queue_bound == "artifacts/jobs/ready"
- response.data.runner_status == "active"

### Side Effect Assertions

- Session file created with session_id
- Run context file persisted with started_at timestamp
- Ready queue bound to runner
- No stale session files from prior runs

### Anti-False-Pass Checks
- verify session file actually created on disk (not just in-memory response)
- verify run_context persisted with correct started_at timestamp (not stale data)
- verify no pre-existing stale session files conflict with new session

### Evidence Required

- request_snapshot
- response_snapshot
- session_file_assertion
- run_context_snapshot
- runner_process_status

## Source References
- FEAT-SRC-003-002.AcceptanceChecks.named-skill-entry
- FEAT-SRC-003-002.Scope.runner-entry
- FEAT-SRC-003-002.Constraints

## Cleanup

- Stop runner session
- Delete session file and run context file
- Clean up any created state files
