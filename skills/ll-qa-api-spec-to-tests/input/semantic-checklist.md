# Input Semantic Checklist: ll-qa-api-spec-to-tests

- [ ] Spec YAML file exists and is valid YAML
- [ ] Has `api_test_spec` root key
- [ ] `case_id` is non-empty string
- [ ] `coverage_id` is non-empty string
- [ ] `endpoint` is non-empty string
- [ ] `capability` is non-empty string
- [ ] `expected` section present with `status_code` (integer)
- [ ] `evidence_required` list present (may be empty)
- [ ] Passes `python -m cli.lib.qa_schemas --type spec <file>` validation
