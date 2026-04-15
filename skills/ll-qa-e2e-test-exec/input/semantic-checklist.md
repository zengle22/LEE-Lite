# Input Semantic Checklist: ll-qa-e2e-test-exec

- [ ] spec_path file exists and is valid YAML
- [ ] Spec has `e2e_journey_spec` root key
- [ ] Spec passes `python -m cli.lib.qa_schemas --type e2e_spec <spec_path>` validation
- [ ] test_dir directory exists
- [ ] test_dir contains at least one .spec.ts file (generated Playwright test scripts)
- [ ] manifest_path file exists and is valid YAML
- [ ] Manifest passes `python -m cli.lib.qa_schemas --type manifest <manifest_path>` validation
- [ ] target_url is valid URL format (if provided)
