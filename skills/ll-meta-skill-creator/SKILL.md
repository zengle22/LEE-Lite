---
name: ll-meta-skill-creator
description: Create or update LEE Lite workflow skills that keep a standard agent-skill shell while adding LEE governance files for contracts, structural and semantic validation, execution and supervision evidence, revision limits, and freeze gates. Use when an agent needs to scaffold or revise a governed workflow skill, especially for requests mentioning LEE workflow skills, ll.contract.yaml, ll.lifecycle.yaml, contract/evidence/supervisor/freeze, or workflows such as src-to-epic and epic-to-feat.
---

# LL Meta Skill Creator

## Overview

Create governed workflow skills for LEE Lite. Each generated skill must remain a standard skill folder that can run in compatible agent-skill shells, but it must add a LEE governance pack for contracts, validation, evidence, supervisor review, and freeze control.

## Workflow

1. Capture the workflow boundary before writing files.
   - Record the workflow key, input artifact type, output artifact type, authoritative upstream ref, runtime mode, direct entrypoint, and freeze expectations.
   - Stop if the request does not define the workflow boundary well enough to write input and output contracts.
2. Scaffold the governed skill.
   - Run `python scripts/init_lee_workflow_skill.py <skill-name> --path <dir> --input-artifact <type> --output-artifact <type>`.
   - For LEE Lite repositories, keep the default `--runtime-mode lite_native`. Use `--runtime-mode legacy_lee` only when the user explicitly wants interop with an existing `lee` runtime.
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
6. Install when needed.
   - Prefer `python ..\ll-skill-install\scripts\install_adapter.py --source <path-to-canonical-skill> --replace` to install a canonical skill into Codex as a workspace-bound adapter.
   - Keep `python scripts/install_profile.py --profile codex` only as a compatibility wrapper that delegates to `ll-skill-install`.
   - Prefer install-time adaptation over maintaining a separate Codex source tree unless scripts, structure, or trigger logic genuinely diverge.

## Non-Negotiable Rules

- Keep the skill shell compatible with standard skills. Do not move LL governance fields into YAML frontmatter.
- Require both input and output contracts. A workflow skill is incomplete if it only templates the output.
- Split structural validation from semantic validation. Structural checks should be scriptable; semantic checks should be reviewable and evidenced.
- In LEE Lite, do not point a newly generated workflow back to `lee run` unless the user explicitly asks for a legacy bridge.
- Do not let the executor issue the final semantic pass on its own output.
- Require execution evidence and supervision evidence before any freeze gate can pass.
- Keep lifecycle semantics lightweight. Use states to align review and evidence, not to rebuild a heavy workflow engine.

## Frontmatter Guidance

- Default to standard `name` and `description` only.
- Add shell-specific extensions such as `allowed-tools`, `context`, or `agent` only when the target runtime and validator explicitly support them.
- Put LL-specific fields in `ll.contract.yaml`, never in frontmatter.

## Scripts

- `scripts/init_lee_workflow_skill.py`
  - Creates a governed workflow skill scaffold with contracts, evidence schemas, agents, resources, and either a lite-native runtime stub or a legacy `lee` placeholder profile.
- `scripts/validate_lee_workflow_skill.py`
  - Validates that a governed workflow skill includes the required LL files and core contract fields.
- `scripts/install_profile.py`
  - Compatibility wrapper. `--profile codex` delegates to `ll-skill-install`; `--profile standard` copies the canonical skill without adapter rewriting.

## References

- Read `references/ll-governance-pack.md` for the required file tree and file responsibilities.
- Read `references/authoring-patterns.md` when customizing contracts, semantic checklists, or supervisor rules for a concrete workflow such as `src-to-epic`.
- Read `references/lite-native-guardrails.md` when the target repository should run the skill directly in Codex or Claude Code instead of delegating to `lee run`.
