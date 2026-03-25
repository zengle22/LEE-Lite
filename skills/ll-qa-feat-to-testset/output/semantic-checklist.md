# Output Semantic Checklist

Review the `test_set_candidate_package` against the selected upstream FEAT.

- Is `test-set.yaml` the only formal main object, with analysis, strategy, review, and bundle files remaining companion artifacts?
- Does the candidate `TESTSET` map FEAT acceptance checks to concrete `test_units` rather than summarizing strategy in vague prose?
- Are `environment_assumptions`, `coverage_exclusions`, and `required_environment_inputs` specific enough for downstream execution planning?
- Does `test-set.yaml.status=approved` only mean ready for external freeze materialization, rather than frozen?
- Are the three external gate subjects stable, machine-readable, and traceable back to the selected FEAT and candidate package?
