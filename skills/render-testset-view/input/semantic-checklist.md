# Input Semantic Checklist: render-testset-view

- [ ] At least one chain (API or E2E) provides all 4 artifacts (plan, manifest, spec, settlement)
- [ ] All specified input files exist on disk
- [ ] Plan files conform to api_test_plan schema (feature_id, source_feat_refs, api_objects, priorities)
- [ ] Manifest files conform to api_coverage_manifest schema (items array with coverage_id, capability, lifecycle_status)
- [ ] Spec files conform to api_test_spec schema (case_id, coverage_id, endpoint, capability)
- [ ] Settlement files conform to settlement_report schema (chain, summary, gap_list, waiver_list)
- [ ] Output directory exists or can be created
- [ ] No conflicting data between API and E2E chains for the same feature_id
