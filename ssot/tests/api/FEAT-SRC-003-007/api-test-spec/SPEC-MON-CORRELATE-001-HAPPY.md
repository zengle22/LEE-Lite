# API Test Spec — MON-CORRELATE-001: 关联 Lineage

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.mon.correlate.happy |
| coverage_id | api.mon.correlate.happy |
| capability | MON-CORRELATE-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-007.Constraints.lineage-correlation |

## Test Contract

### Preconditions

- Job `job-running-001` exists with invocation and outcome records
- All lineage chain links are intact

### Request

```
GET /api/v1/monitor/lineage?job_id=job-running-001
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "job_id": "job-running-001",
    "lineage_chain": [
      {
        "type": "gate_decision",
        "ref": "gate-decision-001",
        "status": "linked"
      },
      {
        "type": "job",
        "ref": "job-running-001",
        "state": "running",
        "status": "linked"
      },
      {
        "type": "invocation",
        "ref": "inv-001",
        "status": "linked"
      },
      {
        "type": "outcome",
        "ref": "outcome-job-running-001",
        "status": "linked"
      }
    ],
    "chain_complete": true
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.lineage_chain length == 4
- response.data.chain_complete == true
- Each chain link has type, ref, and status = "linked"

### Side Effect Assertions

- No state files modified (read-only)
- Lineage resolution log recorded

### Anti-False-Pass Checks
- verify each link in lineage_chain actually exists at its referenced location (not fabricated refs)
- verify chain_complete == true only when all expected links are present (not false positive)
- verify no state files modified during this read-only operation

### Evidence Required

- request_snapshot
- response_snapshot
- lineage_chain_completeness_check
- each_link_verification

## Source References
- FEAT-SRC-003-007.Constraints.lineage-correlation
- FEAT-SRC-003-007.Scope.lineage-monitoring
- FEAT-SRC-003-007.AC-10 (chain completeness verification)

## Cleanup

- No cleanup needed (read-only operation)
- Clear lineage resolution log
