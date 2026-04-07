---
name: ll-dev-feat-to-surface-map
description: Governed workflow skill for transforming one frozen FEAT inside a feat_freeze_package into a surface_map_package that binds design ownership before downstream tech, proto, ui, and impl derivation.
---

# LL Dev FEAT to Surface Map

This skill turns one selected frozen FEAT into one governed `surface_map_package`.
It is the mandatory归属 layer between FEAT and shared design assets.

## Canonical Authority

- Upstream handoff: `ll-product-epic-to-feat`
- Downstream consumers: `ll-dev-feat-to-tech`, `ll-dev-feat-to-proto`, `ll-dev-proto-to-ui`, `ll-dev-tech-to-impl`
- Primary runtime command: `python scripts/feat_to_surface_map.py run --input <feat-package-dir> --feat-ref <feat-ref> --repo-root <repo-root>`

## Runtime Boundary Baseline

- Classify this capability under `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-042-FEAT 与 ARCH-UI-PROTOTYPE 解耦并引入 Surface Map 归属层基线.MD`.
- This skill is a governed `Skill` and `Workflow` authority for FEAT to surface-map derivation.
- Its scripts and package files are carriers, not independent runtime authorities.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept only one freeze-ready `feat_freeze_package` plus one explicit `feat_ref`.
2. Validate the selected FEAT before any design-ownership work.
3. Resolve whether the FEAT is `design_impact_required`.
4. Produce a `surface_map_package` with explicit `owner`, `action`, `scope`, and `reason` for each impacted surface.
5. Use `update` when an existing owner is already known; use `create` only when a new long-lived responsibility boundary is justified.
6. If the FEAT is not design-impacting, emit a bypass package with an explicit rationale instead of silently inventing downstream design work.
7. Record execution evidence, review evidence, and a freeze gate.
8. Freeze only after `python scripts/feat_to_surface_map.py freeze-guard --artifacts-dir <surface-map-package-dir>` returns success.

## Workflow Boundary

- Input: one `feat_freeze_package` plus one selected `feat_ref`
- Output: one `surface_map_package`
- Out of scope: drafting TECH / PROTO / UI / IMPL packages directly

## Non-Negotiable Rules

- Do not accept raw requirements, SRC candidates, EPIC packages, or standalone FEAT markdown outside a governed `feat_freeze_package`.
- Do not let downstream design derivations skip `surface-map` when `design_impact_required=true`.
- Do not let `create` escape without a justification and a long-lived boundary reason.
- Do not let `owner` values drift between the surface-map package and downstream consumers.
- Do not self-approve a review failure by editing the freeze gate by hand.
