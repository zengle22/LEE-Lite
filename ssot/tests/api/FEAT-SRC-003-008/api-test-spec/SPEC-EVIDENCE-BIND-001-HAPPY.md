# API Test Spec — EVIDENCE-BIND-001: 绑定 Pilot Evidence

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | api_case.evidence.bind.happy |
| coverage_id | api.evidence.bind.happy |
| capability | EVIDENCE-BIND-001 |
| scenario_type | happy_path |
| priority | P0 |
| dimension | 正常路径 |
| source_feat_ref | FEAT-SRC-003-008.Constraints.pilot-evidence-bound |

## Test Contract

### Preconditions

- Pilot chain has completed with all steps successful
- Evidence artifacts exist for each chain step
- Full chain: approve -> runner -> next-skill -> outcome

### Request

```
POST /api/v1/pilot/bind-evidence
Content-Type: application/json

{
  "pilot_id": "pilot-001",
  "evidence_chain": [
    { "step": "approve", "ref": "gate-decision-001" },
    { "step": "runner", "ref": "inv-pilot-001" },
    { "step": "next-skill", "ref": "outcome-job-pilot-001" }
  ]
}
```

### Expected Response

```json
{
  "status": "success",
  "data": {
    "pilot_id": "pilot-001",
    "evidence_chain_bound": true,
    "chain_links": 3,
    "all_links_valid": true,
    "bound_at": "<ISO8601 timestamp>",
    "evidence_ref": "pilot-evidence-pilot-001"
  },
  "error": null
}
```

### Response Assertions

- status_code == 200
- response.data.evidence_chain_bound == true
- response.data.chain_links == 3
- response.data.all_links_valid == true
- response.data.evidence_ref is not null

### Side Effect Assertions

- Evidence binding record created
- All chain links verified and recorded
- Pilot evidence file written with complete chain

### Anti-False-Pass Checks
- verify evidence binding file actually created with complete chain data (not just 200 response)
- verify all chain link refs are validated and resolvable (no dangling references)
- verify source evidence files not modified by binding operation (read-only binding)

### Evidence Required

- request_snapshot
- response_snapshot
- evidence_binding_file
- chain_link_verification
- pilot_evidence_file

## Source References
- FEAT-SRC-003-008.Constraints.pilot-evidence-bound
- FEAT-SRC-003-008.Scope.evidence-binding
- FEAT-SRC-003-008.AC-11 (chain link validation)

## Cleanup

- Delete evidence binding record
- Delete pilot evidence file
- No changes to source evidence files
