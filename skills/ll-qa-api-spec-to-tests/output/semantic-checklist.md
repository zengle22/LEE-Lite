# Output Semantic Checklist: ll-qa-api-spec-to-tests

- [ ] Generated .py test files exist in output directory
- [ ] Each .py file passes `python -m py_compile` (no syntax errors)
- [ ] Each file contains `import pytest`
- [ ] Each file contains `import yaml`
- [ ] Each file contains a test class with correct case_id in docstring
- [ ] Each file contains evidence-writing code (evidence_record dict + yaml.safe_dump)
- [ ] Each file references all evidence_required items from spec
- [ ] Each file does NOT contain code to modify input spec files
- [ ] Each file has try/except error handling
- [ ] Evidence YAML output path includes run_id for collision avoidance
