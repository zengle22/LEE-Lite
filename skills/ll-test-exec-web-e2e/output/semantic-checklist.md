# Output Semantic Checklist

- Confirm `response.command = skill.test-exec-web-e2e` and `response.data.skill_ref = skill.qa.test_exec_web_e2e`.
- Confirm the response contains candidate registration refs, handoff refs, and execution refs together; do not accept partial envelopes.
- Confirm `run_status` reflects execution reality rather than downstream acceptance; `completed` does not mean gate-approved.
- Confirm the Web path preserved UI source traceability in `resolved_ssot_context`, `ui_intent`, `ui_source_context`, and `ui_binding_map`.
- Confirm no post-run edits changed refs or status semantics to hide binding gaps, failed assertions, or compliance issues.
