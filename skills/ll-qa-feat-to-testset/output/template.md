---
artifact_type: test_set_candidate_package
workflow_key: qa.feat-to-testset
status: in_progress
package_role: candidate
schema_version: 1.0.0
feat_ref: FEAT-TODO
test_set_ref: TESTSET-TODO
derived_slug: todo
source_refs:
  - product.epic-to-feat::<run_id>
  - FEAT-TODO
  - EPIC-TODO
  - SRC-TODO
---

# {{TITLE}}

## Selected FEAT

[Summarize the selected FEAT boundary.]

## Requirement Analysis

[Summarize testing scope, non-goals, and inherited constraints.]

## Strategy Draft

[Summarize risk focus, layers, and minimum test units with preconditions / trigger / observation / pass-evidence structure.]

## TESTSET

[Expose the formal main object fields directly: coverage_scope, risk_focus, preconditions, environment_assumptions, test_layers, test_units, coverage_exclusions, pass_criteria, evidence_required, acceptance_traceability, source_refs, governing_adrs, status.]

## Gate Subjects

[List stable subject ids for analysis review, strategy review, and test set approval.]

## Downstream Handoff

[Describe the downstream QA execution handoff.]

## Traceability

[Explicitly map each FEAT acceptance scenario to one or more minimum test units, then list inherited source refs.]
