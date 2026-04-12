# API Test Spec — DISPATCH-INV-001: 调用下游 Skill

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.dispatch.inv.happy |
| coverage_id | api.dispatch.inv.happy |
| capability | DISPATCH-INV-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-005.AcceptanceChecks.declared-next-skill |

## Test Contract

### Preconditions

- Job `job-running-001` is in running state with progression_mode = "auto-continue"
- Target next skill exists and is accessible
- Authoritative input refs are all valid and reachable

### Request

```
POST /api/v1/skills/dispatch
Content-Type: application/json

{
  "job_id": "job-running-001",
  "target_skill": "skills/l3/ll-next-skill/",
  "input_package": {
    "refs": ["artifacts/jobs/running/job-running-001.json"],
    "authoritative_refs": {
      "gate_decision_ref": "gate-decision-001",
      "proposal_ref": "adr011-proposal-v1",
      "evidence_refs": ["artifacts/evidence-001.md"]
    }
  }
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-running-001",
    "invocation_id": "inv-001",
    "target_skill": "skills/l3/ll-next-skill/",
    "dispatched_at": "<ISO8601 timestamp>",
    "input_package_refs_count": 1,
    "lineage_preserved": true
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.invocation_id is not null
- response.data.target_skill == "skills/l3/ll-next-skill/"
- response.data.lineage_preserved == true

### Side Effect Assertions

- Invocation record file created
- Lineage record file written with upstream refs
- Target skill receives execution request

### Anti-False-Pass Checks
- verify invocation record file actually created with correct invocation_id (not just 201 response)
- verify target skill actually received the execution request (not dropped silently)
- verify lineage record contains all upstream refs from input_package (no refs lost)

### Evidence Required

- request_snapshot
- response_snapshot
- invocation_file_assertion
- lineage_file_assertion
- skill_invocation_confirmation

## Source References
- FEAT-SRC-003-005.AcceptanceChecks.declared-next-skill
- FEAT-SRC-003-005.Scope.skill-dispatch
- FEAT-SRC-003-005.Constraints

## Cleanup

- Delete invocation record
- Delete lineage record
- Reset job state to prior state
