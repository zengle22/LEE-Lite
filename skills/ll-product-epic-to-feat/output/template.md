---
artifact_type: feat_freeze_package
workflow_key: product.epic-to-feat
workflow_run_id: EPIC2FEAT-RUN-ID
status: accepted
schema_version: 1.0.0
epic_freeze_ref: EPIC-TODO
src_root_id: SRC-ROOT-TODO
feat_refs:
  - FEAT-TODO
downstream_workflows:
  - workflow.product.task.feat_to_delivery_prep
  - workflow.product.feat_to_plan_pipeline
source_refs:
  - product.src-to-epic::RUN-ID
  - EPIC-TODO
  - SRC-TODO
---

# {TITLE}

## FEAT Bundle Intent

[Summarize the FEAT bundle purpose, why the parent EPIC decomposes into exactly this many FEATs, and the bundle-level shared non-goals.]

## EPIC Context

[State the business goal, scope, and inherited constraints from the authoritative EPIC.]

## Boundary Matrix

[Describe what each FEAT owns, what adjacent capability boundaries it explicitly does not own, and where overlap boundaries sit.]

## FEAT Inventory

[List each FEAT with goal, scope, dependencies, constraints, and structured acceptance checks.]

## Acceptance and Review

[Summarize boundary checks, review outcomes, bundle-level acceptance conventions, and unresolved decisions.]

## Downstream Handoff

[Name the downstream workflows and expected derived child artifacts.]

## Traceability

[Map bundle-level and FEAT-level decisions back to authoritative EPIC refs.]
