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
  - workflow.dev.feat_to_surface_map
  - workflow.dev.feat_to_tech
  - workflow.qa.feat_to_testset
source_refs:
  - product.src-to-epic::RUN-ID
  - EPIC-TODO
  - SRC-TODO
---

# {TITLE}

## FEAT Bundle Intent

[Summarize the FEAT bundle purpose, why the parent EPIC decomposes into exactly this many FEATs, whether rollout/adoption/E2E requires a dedicated FEAT track, and the bundle-level shared non-goals.]

## EPIC Context

[State the business goal, scope, and inherited constraints from the authoritative EPIC.]

## Canonical Glossary

[Freeze one canonical glossary for candidate, handoff submission, decision object, formal object, formal ref, lineage, managed ref, receipt, admission, and any additional bundle-specific terms. Each term should state its canonical meaning, owning FEAT, and near-miss term that must not be confused with it.]

## Boundary Matrix

[Describe what each FEAT owns, what adjacent capability boundaries it explicitly does not own, and where overlap boundaries sit.]

## FEAT Inventory

[For each FEAT, freeze the product shape, not just the capability boundary. Each FEAT should include:]

- Identity and Scenario
- Business Flow
- Product Objects and Deliverables
- Collaboration and Timeline
- Acceptance and Testability
- Frozen Downstream Boundary
- Design Impact and Candidate Surfaces

[Each FEAT must also make the product interface, completed state, business deliverable, and cross-cutting capability constraints explicit so downstream TECH does not need to infer product shape.]
[Each FEAT must also state `design_impact_required`, `candidate_design_surfaces`, and optional `ui_required` compatibility hints so downstream design derivations know whether `surface_map_package` is mandatory.]
[Each FEAT must also expose explicit machine-readable relationship fields: upstream_feat, downstream_feat, consumes, produces, authoritative_artifact, gate_decision_dependency_feat_refs, gate_decision_dependency, admission_dependency_feat_refs, admission_dependency, and dependency_kinds.]

## Prohibited Inference Rules

[State bundle-level rules that downstream TECH / TESTSET / consumer flows must not infer on their own, especially around product completion state, authoritative outputs, candidate vs formal objects, and admission vs path guessing.]
[Downstream Handoff must also carry forward glossary, prohibited inference rules, authoritative_artifact_map, feature_dependency_map, and `integration_context_ref` so downstream flows do not need to reopen the full bundle just to recover machine constraints.]

## Acceptance and Review

[Summarize boundary checks, review outcomes, bundle-level acceptance conventions, and unresolved decisions.]

## Downstream Handoff

[Name the downstream workflows and expected derived child artifacts.]

## Traceability

[Map bundle-level and FEAT-level decisions back to authoritative EPIC refs.]
