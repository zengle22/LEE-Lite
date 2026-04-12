# API Test Spec — MON-BACKLOG-001: 查看 Ready Backlog

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.mon.backlog.happy |
| coverage_id | api.mon.backlog.happy |
| capability | MON-BACKLOG-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-007.Scope.ready-backlog |

## Test Contract

### Preconditions

- At least 2 jobs exist in artifacts/jobs/ready
- Runner is active and reading from authoritative state

### Request

```
GET /api/v1/monitor/backlog
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "backlog_count": 2,
    "jobs": [
      {
        "job_id": "job-ready-001",
        "created_at": "<ISO8601 timestamp>",
        "next_skill_target": "skills/l3/ll-next-skill/",
        "progression_mode": "auto-continue"
      },
      {
        "job_id": "job-ready-002",
        "created_at": "<ISO8601 timestamp>",
        "next_skill_target": "skills/l3/ll-other-skill/",
        "progression_mode": "auto-continue"
      }
    ],
    "source": "authoritative_runner_state"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.backlog_count == 2
- response.data.jobs array length == 2
- response.data.source == "authoritative_runner_state"
- Each job has job_id, created_at, next_skill_target, progression_mode

### Side Effect Assertions

- No state files modified (read-only operation)
- Monitor access log recorded

### Anti-False-Pass Checks
- verify backlog_count matches actual number of job files in artifacts/jobs/ready (not cached value)
- verify no state files were modified during this read-only operation
- verify each job in response actually exists in the ready queue (no phantom entries)

### Evidence Required

- request_snapshot
- response_snapshot
- count_accuracy_check
- authoritative_source_proof
- no_state_modification_check

## Source References
- FEAT-SRC-003-007.Scope.ready-backlog
- FEAT-SRC-003-007.Constraints.authoritative-reads
- FEAT-SRC-003-007.AC-09 (read-only monitoring)

## Cleanup

- No cleanup needed (read-only operation)
- Clear monitor access log
