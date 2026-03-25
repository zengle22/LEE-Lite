# Upstream Workflow Analysis

This reference maps the canonical dev tech-design L3 template into a lite-native FEAT to TECH design workflow.

## Canonical Source

- Template path: `E:\ai\LEE\spec-global\departments\dev\workflows\templates\tech-design-l3-template.yaml`
- Template id: `template.dev.tech_design_l3`
- Upstream governed skill: `ll-product-epic-to-feat`
- Primary downstream consumer: `workflow.dev.tech_to_impl`

## Stage Mapping

The lite-native runtime compresses the canonical template into executor and supervisor responsibilities while preserving the same checkpoints:

1. `input_validation`
2. `need_assessment`
3. `draft_tech`
4. `draft_arch_if_needed`
5. `draft_api_if_needed`
6. `self_review`
7. `cross_artifact_consistency_check`
8. `tech_publish_and_handoff`
9. `freeze_gate`

## Runtime Interpretation

- Executor responsibilities:
  - resolve the authoritative selected FEAT
  - decide whether `ARCH` and `API` are required
  - draft `TECH` plus any required companion artifacts
  - emit one design package with traceability and downstream handoff metadata
- Supervisor responsibilities:
  - verify the FEAT has not drifted into TASK or IMPL detail
  - verify `ARCH`, `TECH`, and `API` stay non-overlapping
  - reject optional artifacts that were emitted without need-assessment basis
  - confirm the final design package is freeze-ready for downstream `tech-impl`

## Boundary Rules

- Input must already be freeze-ready at the FEAT layer.
- Output must stay at the design layer: `TECH` always, `ARCH` / `API` only when justified.
- `ARCH` owns system placement and boundary decisions.
- `TECH` owns implementation-facing design and internal delivery constraints.
- `API` owns cross-boundary contracts, message schemas, or request/response semantics.
- Downstream `tech-impl` work must not need to re-derive the FEAT or re-decide whether `ARCH` / `API` are needed.
