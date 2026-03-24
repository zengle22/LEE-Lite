# Forward-Testing

Use this reference when a generated skill is important enough that structural validation alone is not sufficient.

## Goal

Forward-testing checks whether the skill works on realistic tasks without relying on leaked expectations.

You can use `scripts/evaluate_skill.py --run-forward-tests` as a harness when Codex CLI or Claude Code CLI is available in the environment.

## Rules

- Use a fresh thread or fresh agent context for each independent pass.
- Pass the skill path and a realistic user-style request.
- Do not pass your diagnosis, intended fix, or expected output unless the evaluation explicitly requires it.
- Prefer raw prompts, artifacts, logs, and diffs over summaries of what should happen.
- Clean up temporary outputs between passes when residue could contaminate the next run.

## Prompt Shape

Good:

```text
Use $skill-name at /path/to/skill-name to convert this frozen SRC artifact into a governed EPIC skill output.
```

Bad:

```text
Review this skill and confirm that it correctly preserves non-goals and rejects scope drift.
```

## What To Review

- Did the agent load the right files first?
- Did it follow the workflow without inventing missing structure?
- Did it honor contracts and role separation?
- Did it produce evidence or explain why it could not?
- Did it surface uncertainty instead of silently bypassing governance?

## Decision Rule

- Err on the side of forward-testing when the skill is complex, high-leverage, or likely to be reused.
- Ask for approval before forward-testing if the task could take significant time, require more permissions, or touch live systems.
