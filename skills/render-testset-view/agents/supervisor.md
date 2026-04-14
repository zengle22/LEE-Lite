# Supervisor Agent: render-testset-view

## Validation Checklist
1. All provided input artifacts were read and validated
2. Output has assigned_id, test_set_ref, title fields as non-empty strings
3. Coverage data is consistent with input manifest counts (total items match)
4. Statistics match input settlement report numbers (passed, failed, blocked, uncovered)
5. Output is valid JSON matching legacy testset schema
6. functional_areas is a non-empty array with name and coverage count per area
7. coverage_matrix entries all have coverage_id, capability, lifecycle_status, passed, failed fields
8. generation_metadata includes generated_at and source_artifacts list
9. assigned_id is deterministically derived from feature_id
10. No input artifacts were modified during execution
