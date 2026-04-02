---
name: ll-product-src-to-epic
description: Governed LL workflow skill for transforming a freeze-ready src_candidate_package into a lite-native epic_freeze_package between ll-product-raw-to-src and product.epic-to-feat.
---

# LL Product SRC to EPIC

This skill is a lite-native governed workflow between `ll-product-raw-to-src` and `product.epic-to-feat`. It runs directly through the local `scripts/src_to_epic.py` runtime instead of delegating execution back to the legacy `lee run` stack.

## Canonical Authority

- Workflow template: `E:\ai\LEE\spec-global\departments\product\workflows\templates\src-to-epic\v1\workflow.yaml`
- Upstream handoff: `ll-product-raw-to-src`
- Downstream workflow: `product.epic-to-feat`
- Preferred runtime command: `python scripts/src_to_epic.py run --input <src-package-dir> --repo-root <repo-root>`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` and `Workflow` for `SRC -> EPIC` derivation. Generated EPIC packages are artifacts and handoffs, not replacement authorities for session, task, or gate state.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `src_candidate_package` emitted by `ll-product-raw-to-src`.
2. Validate the package structurally before deriving or editing any EPIC artifact.
3. Resolve the authoritative SRC context from the package manifest, `src-candidate.md`, and trace refs.
4. Run `python scripts/src_to_epic.py executor-run --input <src-package-dir>` to generate the governed EPIC package.
5. Collect execution evidence, then hand the governed output package to the supervisor.
6. Run `python scripts/src_to_epic.py supervisor-review --artifacts-dir <epic-package-dir>` before freeze.
7. Freeze only after the supervisor records a semantic pass and `python scripts/src_to_epic.py freeze-guard --artifacts-dir <epic-package-dir>` returns success.
8. Emit a downstream handoff that names `product.epic-to-feat` and the resulting `epic_freeze_ref`.
9. When external gate returns `revise` or `retry`, rerun `run`, `executor-run`, or `supervisor-review` with `--revision-request <revision-request.json>` so the rebuilt package preserves normalized revision context and evidence lineage.

## Workflow Boundary

- Input: one `src_candidate_package` that is freeze-ready and traceable to `ll-product-raw-to-src`
- Output: one `epic_freeze_package` with governance evidence and a handoff to `product.epic-to-feat`
- Out of scope: manual FEAT decomposition, direct task planning, or bypassing the governed SRC to EPIC boundary

## Non-Negotiable Rules

- Do not accept raw requirements, ADR text, or unfrozen SRC drafts directly.
- Do not bypass `scripts/src_to_epic.py` by hand-authoring only the final files without execution and supervision evidence.
- Reject input that collapses to a single FEAT; route that case to the appropriate lower-layer flow instead.
- Preserve `src_root_id`, authoritative `source_refs`, and ADR-025 acceptance semantics.
- Do not let the executor self-approve the semantic validity of its own EPIC output.
