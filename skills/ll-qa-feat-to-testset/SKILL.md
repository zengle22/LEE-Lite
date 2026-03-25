---
name: ll-qa-feat-to-testset
description: Governed LL workflow skill for transforming one frozen FEAT inside a feat_freeze_package into a TESTSET-first candidate package that is ready for external QA review and approval gates.
---

# LL QA FEAT to TESTSET

This skill implements ADR-012 as a lite-native governed workflow between `ll-product-epic-to-feat` and downstream QA execution consumers. It accepts one selected frozen FEAT and produces a `test_set_candidate_package`; it does not self-materialize a final `test_set_freeze_package`.

## Canonical Authority

- Workflow template: `E:\ai\LEE\spec-global\departments\qa\workflows\templates\test-set-production-l3-template.md`
- Upstream handoff: `ll-product-epic-to-feat`
- Downstream skill target: `skill.qa.test_exec_web_e2e`
- Primary runtime command: `python scripts/feat_to_testset.py run --input <feat-package-dir> --feat-ref <feat-ref> --repo-root <repo-root>`

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
2. Validate the package structurally before drafting any QA artifact.
3. Resolve the authoritative FEAT context from `feat-freeze-bundle.md`, `feat-freeze-bundle.json`, inherited `source_refs`, and upstream evidence.
4. Run `python scripts/feat_to_testset.py executor-run --input <feat-package-dir> --feat-ref <feat-ref>` to draft the candidate package.
5. Preserve the four QA production stages in package form: `analysis`, `strategy`, `test_set_generation`, `test_set_review`.
6. Record execution evidence and stable gate subjects for `analysis_review`, `strategy_review`, and `test_set_approval`.
7. Run `python scripts/feat_to_testset.py supervisor-review --artifacts-dir <candidate-package-dir>` to bring the package to `review_pending` or `approval_pending`.
8. Run `python scripts/feat_to_testset.py freeze-guard --artifacts-dir <candidate-package-dir>` only to verify candidate readiness for external approval, not to self-freeze.
9. Emit `handoff-to-test-execution.json` so downstream QA execution can consume the formal `TESTSET` after external approval materializes the freeze package.

## Workflow Boundary

- Input: one `feat_freeze_package` plus one selected `feat_ref`
- Output: one `test_set_candidate_package` with one formal `TESTSET` draft object, companion QA artifacts, and machine-readable gate subjects
- Out of scope: self-issuing human approval decisions, materializing the final `test_set_freeze_package`, generating `TestCasePack`, `ScriptPack`, or `TSE`

## Non-Negotiable Rules

- Do not accept raw requirements, SRC candidates, EPIC packages, or standalone FEAT markdown outside a governed `feat_freeze_package`.
- Do not treat `analysis.md`, `strategy-draft.yaml`, or `test-set-bundle.md` as parallel SSOTs. Only `test-set.yaml` is the formal main object.
- Do not let optional context such as TECH, delivery prep, or UI refs overwrite FEAT scope or acceptance boundaries.
- Do not self-approve `test_set_approval` inside the skill. External gate and human-review consumers own that decision.
- Do not mark the package as frozen from inside the candidate workflow. `approved` means ready for external freeze materialization, not frozen.
