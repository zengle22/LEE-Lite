# Output Semantic Checklist

- Confirm `response.command = skill.test-exec-cli` and `response.data.skill_ref = skill.qa.test_exec_cli`.
- Confirm the response contains candidate registration refs, handoff refs, and execution refs together; do not accept partial envelopes.
- Confirm `run_status` reflects execution reality rather than downstream acceptance; `completed` does not mean gate-approved.
- Confirm the CLI path preserved executable evidence instead of replacing it with narrative summaries.
- Confirm no post-run edits changed refs or status semantics to hide command failures, timeouts, or compliance issues.
