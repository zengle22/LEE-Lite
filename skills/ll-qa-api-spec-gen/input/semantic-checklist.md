# Input Semantic Checklist: ll-qa-api-spec-gen

- [ ] api-coverage-manifest.yaml is valid YAML
- [ ] Has api_coverage_manifest root key
- [ ] Items array has at least one item with lifecycle_status=designed
- [ ] Each item has coverage_id, capability, scenario_type, dimension

---

# Output Semantic Checklist: ll-qa-api-spec-gen

- [ ] Spec files exist at ssot/tests/api/{feat_id}/api-test-spec/
- [ ] Number of spec files = number of non-cut coverage items
- [ ] Each spec has metadata section
- [ ] Each spec has endpoint definition
- [ ] Each spec has request schema
- [ ] Each spec has expected response
- [ ] Each spec has assertions list
- [ ] Each spec has evidence_required
- [ ] Each spec has anti_false_pass_checks
- [ ] Filenames are unique
