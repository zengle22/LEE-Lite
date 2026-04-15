# Output Semantic Checklist: ll-qa-e2e-test-exec

- [ ] Evidence directory exists with evidence YAML files
- [ ] Each evidence file is valid YAML
- [ ] Each evidence file passes `python -m cli.lib.qa_schemas --type evidence <file>` validation
- [ ] Each evidence file contains all items from spec.evidence_required
- [ ] Playwright JSON report exists in evidence directory
- [ ] Manifest updated with lifecycle_status for all executed cases
- [ ] Manifest evidence_status set to "complete" for executed cases
- [ ] Manifest evidence_refs contains paths to evidence files
- [ ] Run ID is consistent across all evidence files and manifest
- [ ] Execution summary JSON reflects actual Playwright results (total, passed, failed)
