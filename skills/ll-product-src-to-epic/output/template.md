---
artifact_type: epic_freeze_package
workflow_key: product.src-to-epic
workflow_run_id: SRC2EPIC-RUN-ID
status: accepted
schema_version: 1.0.0
epic_freeze_ref: EPIC-TODO
src_root_id: SRC-ROOT-TODO
downstream_workflow: product.epic-to-feat
source_refs:
  - product.raw-to-src::RUN-ID
  - SRC-TODO
---

# {TITLE}

## Epic Intent

[Summarize the cross-FEAT product capability this EPIC governs.]

## Business Goal

[State the product outcome and why this EPIC exists.]

## Scope

[Define what is in scope at the EPIC layer.]

## Non-Goals

[List what must not be pulled into this EPIC.]

## Success Metrics

[List the measurable outcomes or review-ready indicators.]

## Decomposition Rules

[State how downstream FEATs should be split without doing the FEAT work here.]

## Rollout and Adoption

[State whether rollout/adoption is required and, when needed, make the downstream adoption/E2E FEAT split explicit inside this EPIC.]

## Constraints and Dependencies

[List inherited constraints, dependencies, and governance limits.]

## Acceptance and Review

[Summarize ADR-025 checks, review outcomes, and unresolved decisions.]

## Downstream Handoff

[Name the next workflow, required refs, and handoff expectations.]

## Traceability

[Map each major EPIC decision back to authoritative SRC refs.]
