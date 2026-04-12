# API Test Spec — ENTRY-RESUME-001: 恢复 Runner 入口

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.entry.resume.happy |
| coverage_id | api.entry.resume.happy |
| capability | ENTRY-RESUME-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-002.Constraints.explicit-resume |

## Test Contract

### Preconditions

- A prior runner session exists with saved run context
- Session was interrupted (not cleanly completed)
- Saved session file exists at known location

### Request

```
POST /api/v1/runner/resume
Content-Type: application/json

{
  "session_id": "session-runner-001",
  "mode": "resume"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "session_id": "session-runner-001",
    "skill_bundle_path": "skills/l3/ll-execution-loop-job-runner/",
    "run_context": {
      "resumed_at": "<ISO8601 timestamp>",
      "original_started_at": "<ISO8601 timestamp>",
      "lineage_refs": ["prior-lineage-ref"],
      "mode": "resume",
      "prior_state": "interrupted"
    },
    "runner_status": "active"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.session_id == "session-runner-001"
- response.data.run_context.mode == "resume"
- response.data.run_context.prior_state == "interrupted"
- response.data.runner_status == "active"
- response.data.run_context.lineage_refs match prior session

### Side Effect Assertions

- Session file updated with resumed_at timestamp
- Runner process restarted with prior context
- Lineage refs preserved from prior session

### Anti-False-Pass Checks
- verify session file actually updated with resumed_at timestamp (not unchanged)
- verify runner process actually restarted with prior context (not new session)
- verify lineage refs match original session (no lineage break or data loss)

### Evidence Required

- request_snapshot
- response_snapshot
- session_file_before_and_after
- lineage_continuity_check
- runner_process_status

## Source References
- FEAT-SRC-003-002.Constraints.explicit-resume
- FEAT-SRC-003-002.Scope.runner-resume
- FEAT-SRC-003-002.AC-03 (lineage continuity on resume)

## Cleanup

- Stop resumed runner session
- Reset session file to pre-resume state
- Clean up any new state files
