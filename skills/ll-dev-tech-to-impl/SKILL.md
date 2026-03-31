---
name: ll-dev-tech-to-impl
description: Governed LL workflow skill for transforming one frozen TECH package plus selected feat_ref and tech_ref into a task-first implementation candidate package aligned to ADR-008 and ADR-014.
---

# LL Dev TECH to IMPL

This skill freezes the task-first `tech2impl` boundary. It does not claim code is finished. It derives one governed `feature_impl_candidate_package` that packages the implementation task entry for the canonical Dev Feature Delivery L2 chain.

## Canonical Authority

- Department ADR: `E:\ai\LEE\spec\adr\ADR-008__dev-department-ssot-alignment-and-workflow-reframe.md`
- Local ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-014-TECH-to-IMPL Lite-Native Skill 实施候选冻结基线.MD`
- Dev template authority: `E:\ai\LEE-Lite-skill-first\skills\ll-dev-tech-to-impl\output\template.md`
- Upstream governed skill: `ll-dev-feat-to-tech`
- Upstream planning context: `E:\ai\LEE\spec-global\departments\product\workflows\templates\feat-to-delivery-prep\v1\workflow.yaml`
- Downstream target template: `template.dev.feature_delivery_l2`
- Primary runtime command: `python scripts/tech_to_impl.py run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref> --repo-root <repo-root>`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `resources/upstream-workflow-analysis.md`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `tech_design_package` emitted by `ll-dev-feat-to-tech`, plus explicit `feat_ref` and `tech_ref`.
2. Validate the package structurally before drafting any implementation candidate output.
3. Resolve the authoritative selected FEAT and its frozen `TECH / ARCH / API` references from the upstream TECH package.
4. Run `python scripts/tech_to_impl.py executor-run --input <tech-package-dir> --feat-ref <feat-ref> --tech-ref <tech-ref>` to generate the governed implementation task package.
5. Always produce `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, and `smoke-gate-subject.json`.
6. Emit frontend, backend, and migration workstreams only when the applicability assessment justifies them.
7. Record execution evidence, then hand the package to the supervisor.
8. Run `python scripts/tech_to_impl.py supervisor-review --artifacts-dir <impl-package-dir>` before marking the package execution-ready.
9. Freeze only after the supervisor records a semantic pass and `python scripts/tech_to_impl.py freeze-guard --artifacts-dir <impl-package-dir>` returns success.
10. Emit a handoff that preserves `feat_ref`, `impl_ref`, `tech_ref`, and optional `arch_ref / api_ref`, with the canonical `template.dev.feature_delivery_l2` target.
11. When external gate returns `revise` or `retry`, rerun `run`, `executor-run`, or `supervisor-review` with `--revision-request <revision-request.json>` so the regenerated implementation package preserves normalized revision context and evidence.

## Workflow Boundary

- Input: one freeze-ready `tech_design_package` plus one selected `feat_ref` and one selected `tech_ref`
- Output: one `feature_impl_candidate_package`
- Mandatory package contents: `impl-task.md`, `upstream-design-refs.json`, `integration-plan.md`, `dev-evidence-plan.json`, `smoke-gate-subject.json`
- Optional package contents: `frontend-workstream.md`, `backend-workstream.md`, `migration-cutover-plan.md`
- Out of scope: redefining technical design, inventing new product scope, claiming final code delivery completed, or bypassing the downstream Feature Delivery L2 chain

## Non-Negotiable Rules

- Do not accept raw requirements, FEAT markdown, or unfrozen TECH notes outside a governed `tech_design_package`.
- Do not let IMPL become a second technical design document; TECH remains the design truth source.
- Do not emit frontend, backend, or migration workstreams mechanically; applicability must be explicit.
- Do not allow a package with no frontend or backend execution surface to pass readiness.
- Do not let the executor self-approve semantic validity or mark execution-ready without supervisor evidence.
