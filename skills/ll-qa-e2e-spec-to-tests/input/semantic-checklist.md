# Input Semantic Checklist: ll-qa-e2e-spec-to-tests

- [ ] Spec YAML file(s) exist at spec_path
- [ ] Each spec passes `python -m cli.lib.qa_schemas --type e2e_spec <file>`
- [ ] Each spec has case_id field
- [ ] Each spec has coverage_id field
- [ ] Each spec has journey_id field
- [ ] Each spec has entry_point field
- [ ] Each spec has non-empty user_steps array
- [ ] Each user_step has step_number, action, target, expected_result
- [ ] Each spec has evidence_required list
