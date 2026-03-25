# Lite-Native Guardrails

Use these rules when the target repository is LEE Lite and the skill should run directly in Codex or Claude Code.

## Required Defaults

- Default `runtime.mode` to `lite_native`.
- Generate a local runtime entrypoint such as `scripts/workflow_runtime.py`.
- Point `SKILL.md`, `ll.contract.yaml`, and wrapper scripts at the local runtime, not at `lee run`.
- Treat `legacy_lee` as an explicit compatibility mode, never as the default.

## Generation Rules

- Capture runtime mode during boundary definition, before writing any files.
- If the user asks for a Codex/Claude Code skill, reject templates that only provide governance files and shell placeholders.
- Scaffold `run`, `validate-input`, `validate-output`, and `validate-package-readiness` commands even when the business logic still needs workflow-specific implementation.
- Keep the runtime contract honest: if a skill is only a governance shell, label it as such instead of pretending it is runnable.

## Validation Rules

- Fail validation when `runtime.mode = lite_native` but the skill still references `lee run` or `lee validate`.
- Fail validation when a lite-native skill has no local runtime entry script.
- Fail validation when `SKILL.md` tells the agent to prefer `lee run` but the repository expectation is direct skill execution.
- Warn when generated wrapper scripts do not route to the local runtime entrypoint.

## Review Questions

- Can the skill be run directly with a local command in the current repository?
- Does the contract match the actual implementation path?
- Does the skill expose a direct executor path and a separate supervisor path?
- Would a user reading `SKILL.md` be misled into invoking an external workflow engine that is not part of the target repo?
