# Output Semantic Checklist

Review the `test_set_candidate_package` against the selected upstream FEAT.

- Is `test-set.yaml` the only formal main object, with analysis, strategy, review, and bundle files remaining companion artifacts?
- Does every `test_unit` read like a minimum executable coverage unit, with explicit preconditions, trigger action, observation points, pass/fail conditions, and required evidence?
- Does the candidate `TESTSET` map FEAT acceptance checks to concrete `test_units` rather than summarizing strategy in vague prose?
- Is `acceptance_traceability` explicit enough to show scenario/given/when/then plus the unit refs that cover each FEAT acceptance?
- Are `environment_assumptions`, `coverage_exclusions`, and `required_environment_inputs` specific enough for downstream execution planning?
- Does `test-set.yaml.status=approved` only mean ready for external freeze materialization, rather than frozen?
- Are the three external gate subjects stable, machine-readable, and traceable back to the selected FEAT and candidate package?
