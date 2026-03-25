# Gate Approval And Formal SRC Publish

## Purpose

This playbook covers the governed path from an upstream `raw-to-src` package to a downstream-consumable formal SRC artifact.

Use this sequence when:

- the package is already `freeze_ready`
- gate review should explicitly approve or reject the handoff
- the approved SRC must be published into the formal registry for downstream resolution and admission

## Boundary

`gate` and `registry` do different jobs:

- `gate submit-handoff` / `decide` / `materialize` / `dispatch` handle approval and downstream execution intent
- `registry publish-formal` writes the authoritative artifact into managed storage and binds a formal registry record

`gate materialize` does **not** publish the business artifact itself. It only writes a materialized handoff or ready job.

## Required Inputs

For a `raw-to-src` package, the minimum inputs are:

- package directory
- `handoff-proposal.json`
- `src-candidate.md`
- gate decision ref after approval

Example package:

- `E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr001-003-006-unified-mainline-20260324-rerun5`

## Execution Order

1. `gate submit-handoff`
2. `gate decide` with `approve`
3. `gate materialize`
4. `gate dispatch`
5. `gate close-run`
6. `registry publish-formal`
7. `registry resolve-formal-ref`

## Repo-Local Invocation

In this repository, the most reliable direct invocation is through `cli.ll.main()`:

```powershell
@'
import sys
from cli.ll import main
sys.exit(main([
  "registry", "publish-formal",
  "--request", r"C:\path\to\request.json",
  "--response-out", r"C:\path\to\response.json",
]))
'@ | python -
```

The same pattern works for `gate submit-handoff`, `gate decide`, `gate materialize`, `gate dispatch`, `gate close-run`, and `registry resolve-formal-ref`.

## Minimal Request Templates

### 1. Gate Approval

```json
{
  "api_version": "v1",
  "command": "gate.decide",
  "request_id": "req-approve-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "gate-reviewer",
  "trace": {
    "run_ref": "your-run-id"
  },
  "payload": {
    "handoff_ref": "artifacts/active/handoffs/your-handoff.json",
    "proposal_ref": "E:/ai/LEE-Lite-skill-first/artifacts/raw-to-src/your-run/handoff-proposal.json",
    "decision": "approve",
    "decision_reason": "Approved for downstream consumption."
  }
}
```

### 2. Formal Publish

```json
{
  "api_version": "v1",
  "command": "registry.publish-formal",
  "request_id": "req-publish-formal-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "gate-reviewer",
  "trace": {
    "run_ref": "your-run-id"
  },
  "payload": {
    "artifact_ref": "formal.src.your-run-id",
    "workspace_path": "artifacts/active/formal/src/your-run-id/src-candidate.md",
    "content_ref": "E:/ai/LEE-Lite-skill-first/artifacts/raw-to-src/your-run-id/src-candidate.md",
    "lineage": [
      "artifacts/active/gates/decisions/your-decision.json"
    ],
    "metadata": {
      "layer": "formal",
      "source_workflow": "product.raw-to-src",
      "content_kind": "src-candidate-markdown"
    }
  }
}
```

### 3. Formal Resolve

```json
{
  "api_version": "v1",
  "command": "registry.resolve-formal-ref",
  "request_id": "req-resolve-formal-001",
  "workspace_root": "E:/ai/LEE-Lite-skill-first",
  "actor_ref": "downstream-consumer",
  "trace": {
    "run_ref": "your-run-id"
  },
  "payload": {
    "artifact_ref": "formal.src.your-run-id",
    "lineage_expectation": "artifacts/active/gates/decisions/your-decision.json"
  }
}
```

## Output Semantics

After `registry publish-formal`, expect:

- managed artifact under `artifacts/active/formal/...`
- receipt under `artifacts/active/receipts/...`
- registry record under `artifacts/registry/...`
- registry status `materialized`

After `registry resolve-formal-ref`, expect:

- `eligibility_result = eligible`
- `resolved_artifact_ref` pointing at the managed formal artifact

## Current Published Example

The package below has already been approved and published:

- package: `E:\ai\LEE-Lite-skill-first\artifacts\raw-to-src\adr001-003-006-unified-mainline-20260324-rerun5`
- formal artifact ref: `formal.src.adr001-003-006-unified-mainline-20260324-rerun5`
- managed artifact: `E:\ai\LEE-Lite-skill-first\artifacts\active\formal\src\adr001-003-006-unified-mainline-20260324-rerun5\src-candidate.md`
- registry record: `E:\ai\LEE-Lite-skill-first\artifacts\registry\formal-src-adr001-003-006-unified-mainline-20260324-rerun5.json`
- publish receipt: `E:\ai\LEE-Lite-skill-first\artifacts\active\receipts\publish-formal-req-raw-to-src-publish-formal-001.json`
- gate decision lineage: `E:\ai\LEE-Lite-skill-first\artifacts\active\gates\decisions\req-raw-to-src-decide-approve.json`

## Optional JSON Companion

If a downstream consumer needs a structured companion, publish `src-candidate.json` as a second formal artifact with:

- a distinct `artifact_ref`
- a distinct `workspace_path`
- the same gate decision lineage

Keep Markdown as the authoritative human-readable SRC unless the downstream contract explicitly upgrades JSON to the primary source.
