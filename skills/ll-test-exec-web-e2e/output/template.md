# Test Exec Web E2E Response

## Envelope

- `command`: `skill.test-exec-web-e2e`
- `request_id`: `<request-id>`
- `result_status`: `success|error`
- `status_code`: `OK|...`

## Runtime Summary

- `skill_ref`: `skill.qa.test_exec_web_e2e`
- `runner_skill_ref`: `skill.runner.test_e2e`
- `run_status`: `<completed|completed_with_failures|completed_with_warnings|invalid_run|failed>`
- `candidate_artifact_ref`: `<candidate ref>`
- `handoff_ref`: `<handoff ref>`

## Execution Artifacts

- `resolved_ssot_context_ref`
- `ui_intent_ref`
- `ui_source_context_ref`
- `ui_binding_map_ref`
- `test_case_pack_ref`
- `script_pack_ref`
- `evidence_bundle_ref`
- `test_report_ref`
- `tse_ref`

## Notes

- Acceptance remains downstream of this response.
- A non-failed response may still represent `completed_with_failures` or `invalid_run`.
