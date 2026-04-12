# API Test Spec — PILOT-EXEC-001: 执行 Pilot 链

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.pilot.exec.happy |
| coverage_id | api.pilot.exec.happy |
| capability | PILOT-EXEC-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-008.AcceptanceChecks.real-pilot-chain |

## Test Contract

### Preconditions

- Onboarding scope defined for governed skills
- All skills in pilot chain available: producer, consumer, audit, gate
- Ready queue accessible
- Runner active

### Request

```
POST /api/v1/pilot/execute
Content-Type: application/json

{
  "scope": "governed-skills",
  "chain": ["producer", "consumer", "audit", "gate"],
  "mode": "full-chain"
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "pilot_id": "pilot-001",
    "chain_steps": [
      { "step": 1, "name": "producer", "status": "completed", "job_id": "job-pilot-001" },
      { "step": 2, "name": "consumer", "status": "completed", "invocation_id": "inv-pilot-001" },
      { "step": 3, "name": "audit", "status": "completed", "audit_ref": "audit-pilot-001" },
      { "step": 4, "name": "gate", "status": "completed", "decision": "pass" }
    ],
    "chain_complete": true,
    "started_at": "<ISO8601 timestamp>",
    "completed_at": "<ISO8601 timestamp>"
  },
  "error": null
}
```

### Response Assertions

- status_code == 201
- response.data.chain_steps length == 4
- All chain_steps have status = "completed"
- response.data.chain_complete == true

### Side Effect Assertions

- Job created by producer
- Invocation created by consumer
- Audit record created
- Gate decision created
- Pilot evidence files for each step

### Anti-False-Pass Checks
- verify all four chain artifacts (job, invocation, audit, gate decision) actually created on disk
- verify each chain step completed in correct sequential order (producer before consumer before audit before gate)
- verify pilot evidence files created for each step (not empty or placeholder files)

### Evidence Required

- request_snapshot
- response_snapshot
- pilot_chain_job_files
- invocation_record
- audit_record
- gate_decision_record

## Source References
- FEAT-SRC-003-008.AcceptanceChecks.real-pilot-chain
- FEAT-SRC-003-008.Scope.pilot-execution
- FEAT-SRC-003-008.Constraints

## Cleanup

- Delete all pilot chain job files
- Delete invocation, audit, and gate decision records
- Delete pilot evidence files
- Reset ready queue to prior state
