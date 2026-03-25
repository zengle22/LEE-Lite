---
name: ll-product-epic-to-feat
description: Governed LL workflow skill for transforming a frozen epic_freeze_package into a lite-native feat_freeze_package between ll-product-src-to-epic and downstream FEAT design and QA derivation flows.
---

# LL Product EPIC to FEAT

This skill is a lite-native governed workflow between `ll-product-src-to-epic` and downstream FEAT consumers. It runs directly through the local `scripts/epic_to_feat.py` runtime instead of delegating execution back to the legacy `lee run` stack.

## Canonical Authority

- Workflow template: `E:\ai\LEE\spec-global\departments\product\workflows\templates\epic-to-feat\v1\workflow.yaml`
- Upstream handoff: `ll-product-src-to-epic`
- Downstream workflows:
  - `workflow.dev.feat_to_tech`
  - `workflow.qa.feat_to_testset`
- Derived child artifacts expected downstream: `TECH`, `TESTSET`
- Preferred runtime command: `python scripts/epic_to_feat.py run --input <epic-package-dir> --repo-root <repo-root>`

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `resources/upstream-workflow-analysis.md`
5. `agents/executor.md`
6. `agents/supervisor.md`
7. `input/semantic-checklist.md` and `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `epic_freeze_package` emitted by `ll-product-src-to-epic`.
2. Validate the package structurally before deriving or editing any FEAT output.
3. Resolve the authoritative EPIC context from `epic-freeze.md`, `epic-freeze.json`, inherited `source_refs`, and the upstream acceptance evidence.
4. Run `python scripts/epic_to_feat.py executor-run --input <epic-package-dir>` to generate the governed FEAT bundle.
5. Collect execution evidence, then hand the governed FEAT bundle to the supervisor.
6. Run `python scripts/epic_to_feat.py supervisor-review --artifacts-dir <feat-package-dir>` before freeze.
7. Freeze only after the supervisor records a semantic pass and `python scripts/epic_to_feat.py freeze-guard --artifacts-dir <feat-package-dir>` returns success.
8. Emit a downstream handoff that preserves `epic_freeze_ref`, `src_root_id`, `feat_refs`, and the downstream workflow list for governed TECH and TESTSET derivation.

## Workflow Boundary

- Input: one `epic_freeze_package` that is freeze-ready and traceable to `ll-product-src-to-epic`
- Output: one `feat_freeze_package` with a FEAT inventory, governance evidence, and downstream handoff metadata
- Out of scope: direct TECH authoring, TASK planning, TESTSET authoring, or bypassing the governed EPIC to FEAT boundary

## Non-Negotiable Rules

- Do not accept raw requirements, SRC candidate packages, or informal EPIC markdown directly.
- Do not bypass `scripts/epic_to_feat.py` by hand-authoring only the final FEAT bundle without execution and supervision evidence.
- Every emitted FEAT must remain an independently acceptable capability slice, not an implementation task, screen TODO list, or architecture-only note.
- Preserve `epic_freeze_ref`, `src_root_id`, authoritative `source_refs`, and ADR-025 acceptance semantics.
- Downstream readiness must stay explicit: FEAT output must be strong enough to seed TECH and TESTSET derivation without re-deriving the parent EPIC.
- Do not let the executor self-approve the semantic validity of its own FEAT output.
