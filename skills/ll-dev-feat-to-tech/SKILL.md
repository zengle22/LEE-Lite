---
name: ll-dev-feat-to-tech
description: Governed LL workflow skill for transforming one frozen FEAT inside a feat_freeze_package into a TECH-first design package with optional ARCH and API companions before downstream tech-impl work.
---

# LL Dev FEAT to TECH

This skill is a lite-native governed workflow between `ll-product-epic-to-feat` and downstream `tech-impl` consumers. It turns one selected frozen FEAT into a design package where `TECH` is mandatory and `ARCH` / `API` are conditionally derived companions.

## Canonical Authority

- Workflow template: `E:\ai\LEE\spec-global\departments\dev\workflows\templates\tech-design-l3-template.yaml`
- Upstream handoff: `ll-product-epic-to-feat`
- Downstream workflow: `workflow.dev.tech_to_impl`
- Primary runtime command: `python scripts/feat_to_tech.py run --input <feat-package-dir> --feat-ref <feat-ref> --repo-root <repo-root>`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `resources/upstream-workflow-analysis.md`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `feat_freeze_package` emitted by `ll-product-epic-to-feat`, plus an explicit `feat_ref`.
2. Validate the package structurally before drafting or editing any design output.
3. Resolve the authoritative FEAT context from `feat-freeze-bundle.md`, `feat-freeze-bundle.json`, inherited `source_refs`, and the upstream acceptance evidence.
4. Run `python scripts/feat_to_tech.py executor-run --input <feat-package-dir> --feat-ref <feat-ref>` to generate the governed design package.
5. Always produce `TECH`; produce `ARCH` only when the FEAT is architecture-impacting; produce `API` only when a cross-boundary contract exists.
6. Record execution evidence, then hand the package to the supervisor.
7. Run `python scripts/feat_to_tech.py supervisor-review --artifacts-dir <tech-package-dir>` before freeze.
8. Freeze only after the supervisor records a semantic pass and `python scripts/feat_to_tech.py freeze-guard --artifacts-dir <tech-package-dir>` returns success.
9. Emit a downstream handoff that preserves `feat_ref`, `tech_ref`, optional `arch_ref` / `api_ref`, and the `workflow.dev.tech_to_impl` target.

## Workflow Boundary

- Input: one `feat_freeze_package` plus one selected `feat_ref`
- Output: one `tech_design_package` containing a mandatory `TECH` design object and optional `ARCH` / `API` design companions
- Out of scope: direct implementation planning, TASK authoring, TESTSET authoring, or bypassing the governed FEAT to TECH boundary

## Non-Negotiable Rules

- Do not accept raw requirements, SRC candidates, EPIC packages, or standalone FEAT markdown outside a governed `feat_freeze_package`.
- Do not treat `ARCH` and `API` as unconditional peers of `TECH`; they are conditional child artifacts decided by need assessment.
- Do not let `ARCH`, `TECH`, and `API` restate the same material. `ARCH` owns system placement and boundaries, `TECH` owns implementation design, `API` owns external contracts.
- Do not bypass the final cross-artifact consistency check before freeze.
- Do not let the executor self-approve semantic validity.
