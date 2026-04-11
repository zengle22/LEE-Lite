---
name: ll-governance-spec-reconcile
description: Reconcile governance spec findings across workflow packages, produce reconcile reports, and optionally update spec backport queues and package manifests.
---

# ll-governance-spec-reconcile

ADR-044 Phase 0/1 governance skill.

## What it does

- Reads a per-run `spec-findings.json` from a workflow package directory.
- Produces `spec-reconcile-report.json` in the same package directory.
- Optionally updates:
  - repo-wide `artifacts/reports/governance/spec-backport/spec-backport-queue.json`
  - the package `package-manifest.json` with `spec_reconcile_report_ref`

## CLI carrier

```powershell
python -m cli.ll skill spec-reconcile --request <req.json> --response-out <resp.json> --evidence-out <evidence.json>
```

Request `command` must be `skill.spec-reconcile`.

