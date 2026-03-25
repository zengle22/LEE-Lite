# Upstream Workflow Analysis

This reference maps ADR-012 and the canonical QA test-set production template into a lite-native FEAT to TESTSET candidate workflow.

## Canonical Source

- Template path: `E:\ai\LEE\spec-global\departments\qa\workflows\templates\test-set-production-l3-template.md`
- Template id: `template.qa.test_set_production`
- Template workflow key: `workflow.qa.test_set_production_l3`
- Upstream governed skill: `ll-product-epic-to-feat`
- Primary downstream consumer: `skill.qa.test_exec_web_e2e`

## Stage Mapping

The lite-native runtime preserves the canonical four stages inside one candidate package:

1. `requirement_analysis`
2. `strategy_design`
3. `test_set_generation`
4. `test_set_review`

## Runtime Interpretation

- Executor responsibilities:
  - resolve the authoritative selected FEAT
  - derive `analysis.md`
  - derive `strategy-draft.yaml`
  - draft one formal `test-set.yaml`
  - emit stable gate subjects and downstream handoff metadata
- Supervisor responsibilities:
  - verify that `test-set.yaml` is the only formal main object
  - verify status-model consistency between `test-set.yaml`, `package-manifest.json`, and `test-set-freeze-gate.json`
  - verify companion artifacts stay subordinate to the main object
  - decide whether the candidate package is ready for external approval

## Boundary Rules

- Input must already be freeze-ready at the FEAT layer.
- Output must remain a `test_set_candidate_package` until an external approval materializes the final freeze package.
- `analysis.md` and `strategy-draft.yaml` are companion artifacts, not new SSOTs.
- `approved` means the content is ready for external freeze materialization; it does not mean frozen.
- The package must ship stable machine-readable gate subjects for `analysis_review`, `strategy_review`, and `test_set_approval`.
