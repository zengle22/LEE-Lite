---
artifact_type: epic_freeze_package
workflow_key: product.src-to-epic
workflow_run_id: src2epic-src-001-001
status: accepted
schema_version: 1.0.0
epic_freeze_ref: EPIC-SRC-001-001
src_root_id: src-root-src-001
source_refs:
  - product.src-to-epic::src2epic-src-001-001
  - SRC-001
---

# Managed Artifact IO Governance Foundation

## Epic Intent

Turn the upstream SRC problem space into a stable multi-FEAT capability boundary.

## Business Goal

Provide enough EPIC structure for downstream FEAT decomposition without reopening the SRC layer.

## Scope

- Managed artifact gateway surface
- Path policy and write-mode governance
- Artifact identity and registry rules

## Non-Goals

- Do not author TASKs here.
- Do not collapse the EPIC into implementation tickets.

## Decomposition Rules

- Split FEATs by independently acceptable capability boundary.
- Preserve traceability, source refs, and downstream readiness.

## Constraints and Dependencies

- Preserve `src_root_id`, `epic_freeze_ref`, and authoritative `source_refs`.
- Keep the output actionable for downstream governed TECH and TESTSET derivation.

## Downstream Handoff

- product.epic-to-feat

## Traceability

- Derived from `SRC-001` and `product.raw-to-src::RAW2SRC-001`.
