# Input Semantic Checklist: ll-qa-api-test-exec

- [ ] spec_path file exists and is valid YAML
- [ ] Spec has `api_test_spec` root key
- [ ] Spec passes `python -m cli.lib.qa_schemas --type spec <spec_path>` validation
- [ ] test_dir directory exists
- [ ] test_dir contains at least one .py file (generated test scripts)
- [ ] Each .py file passes `python -m py_compile` (no syntax errors)
- [ ] manifest_path file exists and is valid YAML
- [ ] Manifest passes `python -m cli.lib.qa_schemas --type manifest <manifest_path>` validation
- [ ] base_url is valid URL format (if provided)
