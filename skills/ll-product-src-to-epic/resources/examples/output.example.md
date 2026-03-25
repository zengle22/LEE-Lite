---
artifact_type: epic_freeze_package
workflow_key: product.src-to-epic
workflow_run_id: SRC2EPIC-20260324-001
status: frozen
schema_version: 1.0.0
epic_freeze_ref: EPIC-20260324-001
src_root_id: SRC-ROOT-001
downstream_workflow: product.epic-to-feat
source_refs:
  - product.raw-to-src::RAW2SRC-20260324-001
  - SRC-20260324-001
---

# Example EPIC Freeze Package

## Epic Intent

Create a governed recovery capability that can be decomposed into verification, communication, and operator tooling FEATs.

## Scope

User-facing recovery entry points, recovery decisioning, and operator review support.

## Non-Goals

Low-level implementation tasks and UI pixel detail.

## Downstream Handoff

The next governed workflow is `product.epic-to-feat`, using `EPIC-20260324-001`.

## Traceability

Each EPIC decision maps back to the raw-to-src run and SRC freeze refs above.
