# Output Semantic Checklist: render-testset-view

- [ ] Output file exists at specified output path
- [ ] Output file is valid JSON
- [ ] Output has assigned_id as non-empty string field
- [ ] Output has test_set_ref as non-empty string field matching assigned_id
- [ ] Output has title as non-empty string field
- [ ] functional_areas is a non-empty array
- [ ] Each functional_area has name, coverage_count, passed_count, failed_count
- [ ] coverage_matrix is a non-empty array
- [ ] Each coverage_matrix entry has coverage_id, capability, lifecycle_status, passed, failed fields
- [ ] Coverage counts match input manifest item counts
- [ ] Pass/fail statistics match input settlement report numbers
- [ ] generation_metadata has generated_at and source_artifacts
