---
artifact_type: tech_design_package
workflow_key: dev.feat-to-tech
workflow_run_id: RUN-20260403-001
status: accepted
schema_version: 1.0.0
source_refs:
  - dev.feat-to-tech::RUN-20260403-001
feat_ref: FEAT-SRC-001-001
tech_ref: TECH-FEAT-SRC-001-001
selected_feat:
  feat_ref: FEAT-SRC-001-001
  title: Example task-first feature
  goal: Keep downstream implementation aligned to frozen upstream tech truth.
  scope:
    - Derive a task-first implementation candidate package.
    - Preserve frozen upstream integration facts.
  constraints:
    - Do not redefine upstream TECH, ARCH, API, or inherited frozen refs in IMPL.
    - Keep implementation planning self-contained and execution-ready.
selected_upstream_refs:
  adr_refs:
    - ADR-013
    - ADR-014
    - ADR-034
  src_ref: SRC-SRC-001
  epic_ref: EPIC-SRC-001
  feat_ref: FEAT-SRC-001-001
  tech_ref: TECH-FEAT-SRC-001-001
  arch_ref: ARCH-FEAT-SRC-001-001
  api_ref: API-FEAT-SRC-001-001
  integration_context_ref: ICTX-SRC-001-001
  canonical_owner_refs:
    - OWNER-SRC-001-001
  state_machine_ref: STATE-SRC-001-001
  nfr_constraints_ref: NFR-SRC-001-001
  migration_constraints_ref: MIG-SRC-001-001
  algorithm_constraint_refs:
    - ALG-SRC-001-001
  ui_ref: UI-SRC-001-001
  testset_ref: TESTSET-SRC-001-001
---

# Example TECH-to-IMPL Input Package

## Selected Upstream

- feat_ref: `FEAT-SRC-001-001`
- tech_ref: `TECH-FEAT-SRC-001-001`
- arch_ref: `ARCH-FEAT-SRC-001-001`
- api_ref: `API-FEAT-SRC-001-001`
- integration_context_ref: `ICTX-SRC-001-001`

## Frozen Truth Projection

- canonical_owner_refs: `OWNER-SRC-001-001`
- state_machine_ref: `STATE-SRC-001-001`
- nfr_constraints_ref: `NFR-SRC-001-001`
- migration_constraints_ref: `MIG-SRC-001-001`
- algorithm_constraint_refs: `ALG-SRC-001-001`

## Consumption Boundary

The downstream implementation package must treat the selected upstream refs as frozen authorities. IMPL may consume them, map them to task breakdowns, and embed them in `upstream-design-refs.json`, but must not rename, reinterpret, or re-decide them.

## Expected Downstream Artifacts

- `impl-task.md`
- `upstream-design-refs.json`
- `integration-plan.md`
- `dev-evidence-plan.json`
- `smoke-gate-subject.json`

## Example Notes

- `selected_upstream_refs` is the canonical place where frozen upstream facts are carried into tech-to-impl intake.
- `upstream-design-refs.json` should mirror the same refs for execution and review.
- If any of these refs are provisional or missing, the package should be revised before execution-ready handoff.
