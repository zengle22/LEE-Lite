# Raw-to-SRC Runtime Contract

This document anchors the machine-readable raw-to-src runtime objects in `spec/contracts/raw-to-src/`.

## Scope

These contracts support the ADR-002 / ADR-003 design for:

- result summary
- run state
- patch lineage
- source semantic findings
- acceptance report
- proposed next actions
- handoff proposal
- job proposal
- retry budget report
- candidate artifact validation

For `governance_bridge_src`, the runtime contract also assumes:

- dedicated ADR bridge synthesis
- a governance summary section in the candidate
- non-generic bridge context fields
- semantic review checks for bridge density and downstream actionability

## Boundary

- `raw-to-src` emits candidate artifacts, evidence, and proposals.
- External gate / queue handlers materialize final handoffs and jobs.
- Final `SRC` freeze is outside the skill runtime boundary.

## Canonical Contract Set

- `spec/contracts/raw-to-src/result-summary.schema.json`
- `spec/contracts/raw-to-src/run-state.schema.json`
- `spec/contracts/raw-to-src/patch-lineage.schema.json`
- `spec/contracts/raw-to-src/source-semantic-findings.schema.json`
- `spec/contracts/raw-to-src/acceptance-report.schema.json`
- `spec/contracts/raw-to-src/proposed-next-actions.schema.json`
- `spec/contracts/raw-to-src/handoff-proposal.schema.json`
- `spec/contracts/raw-to-src/job-proposal.schema.json`
- `spec/contracts/raw-to-src/retry-budget-report.schema.json`
- `spec/contracts/raw-to-src/candidate-artifact.schema.json`
