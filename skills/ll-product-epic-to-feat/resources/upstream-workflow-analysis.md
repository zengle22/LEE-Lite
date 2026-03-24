# Upstream Workflow Analysis

This reference maps the checked-in EPIC to FEAT template into the lite-native governed skill runtime.

## Canonical Source

- Template path: `E:\ai\LEE\spec-global\departments\product\workflows\templates\epic-to-feat\v1\workflow.yaml`
- Workflow id: `workflow.product.task.epic_to_feat`
- Upstream: `ll-product-src-to-epic`
- Primary downstream consumers:
  - `workflow.product.task.feat_to_delivery_prep`
  - `workflow.product.feat_to_plan_pipeline`

## Stage Mapping

The lite-native runtime compresses the canonical template into executor and supervisor responsibilities while preserving the original checkpoints:

1. `input_validation`
2. `feat_boundary_design`
3. `feat_spec_generation`
4. `feat_identity_prepare`
5. `feat_review`
6. `feat_acceptance_review`
7. `feat_identity_formalize`
8. `feat_freeze_gate`

## Runtime Interpretation

- Executor responsibilities:
  - resolve the authoritative EPIC package
  - derive FEAT boundaries and FEAT specs
  - preserve traceability and parent-child identity fields
  - emit structured FEAT acceptance checks
- Supervisor responsibilities:
  - verify each FEAT remains independently acceptable
  - reject FEATs that collapse into TASK, UI, or implementation detail
  - verify downstream readiness for delivery-prep and plan flows
  - decide whether the FEAT package is freeze-ready

## Boundary Rules

- Input must already be freeze-ready at the EPIC layer.
- Output must stay at the FEAT layer.
- Downstream delivery-prep and plan flows must not need to re-derive the parent EPIC.
- `TESTSET` is treated as a downstream derived child, not an object authored directly inside this workflow.
