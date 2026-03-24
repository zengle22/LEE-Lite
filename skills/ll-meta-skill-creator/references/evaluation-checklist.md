# Evaluation Checklist

Use this checklist after structural validation passes.

## Skill Design

- Does the frontmatter clearly say when the skill should trigger?
- Does `SKILL.md` stay concise while still giving the target agent enough procedural knowledge?
- Are long details moved into references instead of bloating the main body?

## Governance Coverage

- Are input and output contracts both explicit?
- Are structural and semantic validation clearly separated?
- Are executor and supervisor responsibilities distinct?
- Are execution and supervision evidence both required?
- Is the freeze gate explicit and reviewable?

## Runtime Practicality

- Are scripts executable and named predictably?
- Are placeholder commands clearly marked when project-specific integration is still required?
- Does the skill remain valid in a standard skill environment?

## Forward-Testing Readiness

- Is there at least one realistic prompt that should succeed?
- Is there at least one realistic prompt that should fail or request clarification?
- Are there known risky cases worth probing in an independent pass?

## Release Decision

- `ready`: structural validation passes and forward-testing shows acceptable behavior
- `revise`: structural validation passes but forward-testing shows unclear or brittle behavior
- `reject`: the skill violates core contracts or cannot be trusted as a governed workflow skill
