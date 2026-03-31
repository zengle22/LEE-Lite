# Output Semantic Checklist

Review the `test_set_candidate_package` against the selected upstream FEAT.

- Is `test-set.yaml` the only formal main object, with analysis, strategy, review, and bundle files remaining companion artifacts?
- Does every `test_unit` read like a minimum executable coverage unit, with explicit preconditions, trigger action, observation points, pass/fail conditions, and required evidence?
- Does the candidate `TESTSET` map FEAT acceptance checks to concrete `test_units` rather than summarizing strategy in vague prose?
- Is `acceptance_traceability` explicit enough to show scenario/given/when/then plus the unit refs that cover each FEAT acceptance?
- Are `functional_areas`, `logic_dimensions`, `state_model`, and `coverage_matrix` present and internally consistent with the derived `test_units`?
- Are `functional_areas` typed, `logic_dimensions` layered, `state_model` stateful, and `coverage_matrix` traceable to both acceptances and risks?
- Are `environment_assumptions`, `coverage_exclusions`, and `required_environment_inputs` specific enough for downstream execution planning?
- Does `test-set.yaml.status=approved` only mean ready for external freeze materialization, rather than frozen?
- Are the three external gate subjects stable, machine-readable, and traceable back to the selected FEAT and candidate package?
