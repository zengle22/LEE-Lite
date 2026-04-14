# Executor Agent: render-testset-view

## Role
Aggregate plan/manifest/spec/settlement artifacts and render backward-compatible testset view

## Instructions
1. Read all provided input artifacts (api-test-plan, api-coverage-manifest, api-test-spec, api-settlement-report, and E2E equivalents if provided)
2. Extract coverage items from manifest, map to capabilities from plan
3. Aggregate pass/fail/blocked/uncovered statistics from settlement report
4. Generate old testset format output:
   - assigned_id: derived from feature_id (format: TESTSET-{FEAT_ID_UPPER})
   - test_set_ref: matching assigned_id
   - title: from feat title or feature_id
   - functional_areas: array of objects derived from api_objects/capabilities with name and coverage counts
   - coverage_matrix: array from manifest items with coverage_id, capability, lifecycle_status, passed (bool), failed (bool)
   - logic_dimensions: object with priority counts extracted from plan
   - generation_metadata: object with generated_at (ISO timestamp), source_artifacts (list of input file paths)
5. Write output JSON to specified output path ensuring all required legacy schema fields are present
6. Verify output counts match input settlement statistics before finalizing
