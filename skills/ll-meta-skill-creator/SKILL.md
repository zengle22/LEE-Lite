---
name: ll-meta-skill-creator
description: Create or update LEE Lite workflow skills that keep a standard agent-skill shell while adding LEE governance files for contracts, structural and semantic validation, execution and supervision evidence, revision limits, and freeze gates. Use when an agent needs to scaffold or revise a governed workflow skill, especially for requests mentioning LEE workflow skills, ll.contract.yaml, ll.lifecycle.yaml, contract/evidence/supervisor/freeze, or workflows such as src-to-epic and epic-to-feat.
---

# LL Meta Skill Creator

## Overview

Create governed workflow skills for LEE Lite. Each generated skill must remain a standard skill folder that can run in compatible agent-skill shells, but it must add a LEE governance pack for contracts, validation, evidence, supervisor review, and freeze control.

## Workflow

1. Capture the workflow boundary before writing files.
   - Record the workflow key, input artifact type, output artifact type, authoritative upstream ref, CLI command family, and freeze expectations.
   - Stop if the request does not define the workflow boundary well enough to write input and output contracts.
2. Scaffold the governed skill.
   - Run `python scripts/init_lee_workflow_skill.py <skill-name> --path <dir> --input-artifact <type> --output-artifact <type>`.
   - Prefer the generated layout over ad hoc file creation so every workflow skill starts from the same LL baseline.
3. Fill the governance pack, not just `SKILL.md`.
   - Keep the generated `SKILL.md` as the standard-compatible shell.
   - Put workflow rules, contracts, lifecycle, evidence schemas, and gates into `ll.contract.yaml`, `ll.lifecycle.yaml`, `input/`, `output/`, `evidence/`, `agents/`, and workflow scripts.
4. Separate execution from supervision.
   - Executor content belongs in `agents/executor.md`, execution evidence, draft generation, and structural validation.
   - Supervisor content belongs in `agents/supervisor.md`, semantic review, revision decisions, and freeze approval or rejection.
5. Validate before handing the skill over.
   - Run `python scripts/validate_lee_workflow_skill.py <path/to/generated-skill>`.
   - If the standard skill validator is available in the environment, run it too.
6. Install with a runtime profile when needed.
   - Run `python scripts/install_profile.py --profile codex` to install the canonical skill into Codex with lightweight runtime-specific metadata adjustments.
   - Prefer install-time adaptation over maintaining a separate Codex source tree unless scripts, structure, or trigger logic genuinely diverge.

## Non-Negotiable Rules

- Keep the skill shell compatible with standard skills. Do not move LL governance fields into YAML frontmatter.
- Require both input and output contracts. A workflow skill is incomplete if it only templates the output.
- Split structural validation from semantic validation. Structural checks should be scriptable; semantic checks should be reviewable and evidenced.
- Do not let the executor issue the final semantic pass on its own output.
- Require execution evidence and supervision evidence before any freeze gate can pass.
- Keep lifecycle semantics lightweight. Use states to align review and evidence, not to rebuild a heavy workflow engine.

## Frontmatter Guidance

- Default to standard `name` and `description` only.
- Add shell-specific extensions such as `allowed-tools`, `context`, or `agent` only when the target runtime and validator explicitly support them.
- Put LL-specific fields in `ll.contract.yaml`, never in frontmatter.

## Scripts

- `scripts/init_lee_workflow_skill.py`
  - Creates a governed workflow skill scaffold with contracts, evidence schemas, agents, resources, and placeholder workflow scripts.
- `scripts/validate_lee_workflow_skill.py`
  - Validates that a governed workflow skill includes the required LL files and core contract fields.
- `scripts/install_profile.py`
  - Installs the canonical skill into a target skills directory and applies a lightweight runtime profile such as `codex`.

## References

- Read `references/ll-governance-pack.md` for the required file tree and file responsibilities.
- Read `references/authoring-patterns.md` when customizing contracts, semantic checklists, or supervisor rules for a concrete workflow such as `src-to-epic`.
