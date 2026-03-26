# Input Semantic Checklist

- Confirm `command = skill.test-exec-cli` and the request is not a Web request copied into the wrong skill.
- Confirm `payload.test_set_ref` points to a formal `TESTSET`, not analysis notes, strategy drafts, or freeform governance prose.
- Confirm the resolved environment contract is CLI and provides a real `command_entry` or `runner_command`.
- Confirm command execution semantics come from the environment contract, not from hidden shell assumptions in the request body.
- Confirm the request does not rely on unstated local setup that would make the produced evidence untrustworthy.
