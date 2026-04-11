# Input Semantic Checklist: ll-qa-e2e-manifest-init

- [ ] e2e-journey-plan.md is valid
- [ ] Has prototype_id or feature_id
- [ ] Has at least 1 main + 1 exception journey
- [ ] Journeys have IDs, types, and priorities

---

# Output Semantic Checklist: ll-qa-e2e-manifest-init

- [ ] e2e-coverage-manifest.yaml exists
- [ ] Root key is e2e_coverage_manifest
- [ ] Metadata complete (prototype_id, derivation_mode, generated_at, source_plan_ref)
- [ ] Items array non-empty
- [ ] Each item has coverage_id, journey_id, journey_type, priority, all four status fields
- [ ] item count >= plan journey count
- [ ] Cut items have complete cut_record
- [ ] P0 main journey items not cut
