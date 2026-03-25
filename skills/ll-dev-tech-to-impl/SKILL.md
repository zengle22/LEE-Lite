---
name: ll-dev-tech-to-impl
description: Workspace-bound adapter for the canonical dev.tech-to-impl governed workflow
  in E:\ai\LEE-Lite-skill-first. Use when a tech_design_package needs to be transformed
  into a feature_impl_candidate_package.
---

# LL Dev Tech To Impl

This installed skill is an adapter to the canonical implementation in the current workspace:

- Skill root: `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl`
- Workflow template authority: `E:\ai\LEE\spec-global\departments\dev\workflows\templates\feature-delivery-l2-template.yaml`
- Workflow key: `dev.tech-to-impl`
- Upstream governed skill: `C:\Users\shado\.codex\skills\ll-dev-feat-to-tech`

Use this skill only when operating inside `E:\ai\LEE-Lite-skill-first` or an equivalent checkout with the same canonical paths.

## Required Read Order

1. Read `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\SKILL.md`.
2. Read `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\ll.contract.yaml`.
3. Read `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\input\contract.yaml`.
4. Read `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\output\contract.yaml`.
5. Read the semantic checklists and role prompts under `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl` only as needed.

## Runtime Entry Points

- Canonical workflow command:
  - `python scripts/tech_to_impl.py run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref> --repo-root <repo-root>`
- Canonical validation helpers:
  - `bash E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\scripts\validate_input.sh <input-artifact-dir>`
  - `bash E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\scripts\validate_output.sh <output-artifact-dir>`
  - `bash E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\scripts\freeze_guard.sh <artifact-dir>`

## Workflow Boundary

- Input boundary: one `tech_design_package` from the canonical workflow boundary
- Output boundary: one `feature_impl_candidate_package` under the canonical workspace skill/runtime expectations
- Downstream handoff: `unspecified`
- Out of scope: bypassing the canonical workflow template, hand-editing installed metadata in place, and inventing alternate canonical paths

## Guardrails

- Treat the workspace skill as the canonical source of truth.
- Prefer the canonical workflow command over manually drafting workflow outputs.
- Preserve provenance, source refs, and freeze refs when the canonical contract requires them.
- Refresh the installed copy from the canonical source instead of making drift-only edits in the installed adapter.

