# Output Semantic Checklist: ll-qa-api-manifest-init

- [ ] api-coverage-manifest.yaml exists at ssot/tests/api/{feat_id}/
- [ ] Root key is api_coverage_manifest
- [ ] Metadata contains feature_id, generated_at, source_plan_ref
- [ ] Items array is non-empty
- [ ] Each item has coverage_id, capability, scenario_type, dimension, priority
- [ ] Each item has all four status fields
- [ ] Cut items have complete cut_record
- [ ] item count matches capabilities × dimensions after cuts
