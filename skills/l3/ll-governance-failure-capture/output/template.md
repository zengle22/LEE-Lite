# Failure Capture Package Layout

## Package Root

- Default root: `tests/defect/`
- `P0` / `P1`: `tests/defect/failure-cases/<failure-id>/`
- `P2`: `tests/defect/issue-log/<issue-id>/`

## Required Files

### For `failure_case`

```text
failure-cases/<failure-id>/
  capture_manifest.json
  failure_case.json
  diagnosis_stub.json
  repair_context.json
```

### For `issue_log`

```text
issue-log/<issue-id>/
  capture_manifest.json
  issue_log.json
  diagnosis_stub.json
  repair_context.json
```

## File Intent

- `capture_manifest.json`
  - package index
  - package kind
  - package id
  - triage level
  - canonical file refs
- `failure_case.json`
  - full governed failure record for `P0` / `P1`
- `issue_log.json`
  - light issue entry for `P2`
- `diagnosis_stub.json`
  - capture-time initial classification only
- `repair_context.json`
  - constrained context for later manual or human-directed AI repair

## Content Rules

- Prefer refs over copied prose.
- Keep the package local to one detected problem.
- Do not include repaired artifact content in this package.
- Do not broaden scope beyond the reported failure.
