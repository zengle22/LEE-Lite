---
name: ll-project-init
description: Initialize a repository to the governed LEE Lite skill-first project skeleton used by this workspace.
---

# LL Project Init

Use this skill when a new repository needs the standard LEE Lite project layout, root control files, runtime shells, and durable directory scaffolding that this workspace expects.

## Workflow Boundary

- Workflow key: `repo.project-init`
- Input: one `project_init_request`
- Primary output: one `project_init_package` under `artifacts/project-init/<run_id>`
- Side effect: the runtime creates or refreshes managed scaffold files inside the target repository root

## Required Read Order

1. `resources/project-structure-reference.md`
2. `ll.contract.yaml`
3. `input/contract.yaml`
4. `output/contract.yaml`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a governed `project_init_request` that names the target root, project slug, and `lee-skill-first` profile.
2. Run `python scripts/workflow_runtime.py validate-input --input <request>` before touching the repository.
3. Materialize the scaffold with `python scripts/workflow_runtime.py run --input <request> --repo-root <target-root> --allow-update`.
4. Create only the managed scaffold files and shell directories defined by this skill. Skip unrelated pre-existing files unless the request explicitly chooses `refresh_managed`.
5. Emit a package under `artifacts/project-init/<run_id>` that records the initialization plan, created paths, skipped paths, execution evidence, supervision evidence, and the human-readable bootstrap report.
6. Run `python scripts/workflow_runtime.py validate-output --artifacts-dir <package-dir>` and `python scripts/workflow_runtime.py validate-package-readiness --artifacts-dir <package-dir>` before reporting success.

## Non-Negotiable Rules

- Do not invent a project layout that drifts from the current workspace conventions without updating `resources/project-structure-reference.md`.
- Do not overwrite unmanaged existing files.
- Do not place runtime state inside durable governed directories.
- Do not report completion without both execution evidence and supervision evidence.
- Do not treat this skill as a gate-return-driven document regeneration workflow. `project-init` is intentionally outside the shared revision module coverage.
