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

## Business Value and Problem

[State the business problem, why it matters now, and the user-visible consequence of not doing this EPIC.]

## Product Positioning

[Explain where this EPIC sits in the end-to-end product flow, what upstream it absorbs, and what downstream product slices it enables.]

## Actors and Roles

[List the core product/business roles and what each role is responsible for at the EPIC layer.]

## Capability Scope

[Define what is in scope at the EPIC layer.]

## Upstream and Downstream

[State what upstream package/context this EPIC consumes and what downstream FEAT layer must inherit from it.]

## Non-Goals

[List what must not be pulled into this EPIC.]

## Epic Success Criteria

[List the measurable or review-ready product outcomes that prove the EPIC is complete.]

## Decomposition Rules

[State that downstream FEATs must be split by product behavior slices, while capability axes remain cross-cutting constraints and rollout/adoption stays as overlay.]

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
