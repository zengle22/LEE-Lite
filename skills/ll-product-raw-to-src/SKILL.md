---
name: ll-product-raw-to-src
description: Normalize raw product inputs into one governed SRC candidate package with evidence, handoff proposals, and external-gate routing artifacts.
---

# LL Product Raw To SRC

Use this skill when a raw requirement, ADR, business opportunity, or frozen business opportunity needs to be normalized into one governed SRC candidate package for downstream routing.

## Workflow Boundary

- Workflow key: `product.raw-to-src`
- Inputs: `adr`, `raw_requirement`, `business_opportunity`, `business_opportunity_freeze`
- Primary output: one `SRC candidate` package under `artifacts/raw-to-src/<run_id>`
- Formal flow boundary: skill emits `candidate + evidence + proposed actions`, then submits an authoritative handoff into gate pending; external gate still owns decision, review, and downstream materialization
- Upstream authority: raw source only, never an already-frozen SSOT object

## Runtime Boundary Baseline

- Classify this capability under `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This skill is a governed `Skill` and `Workflow` for raw-input normalization. Candidate packages, evidence, and handoff files are emitted artifacts, not substitutes for gate or task authority.

## Required Read Order

1. Read `resources/upstream-workflow-analysis.md` for the migrated stage map.
2. Read `ll.contract.yaml`, then `input/contract.yaml` and `output/contract.yaml`.
3. Read runtime contract references under `resources/contracts/raw-to-src/` and `resources/raw-to-src-runtime-contract.md`.
4. Read `resources/checklists/acceptance-checklist.md` when running manual acceptance.
5. Run structural validation with `scripts/validate_input.sh`.
6. Run `python scripts/raw_to_src.py executor-run --input <path>` for the executor phase, then `python scripts/raw_to_src.py supervisor-review --artifacts-dir <dir>` for the supervisor phase.
7. Or use `python scripts/raw_to_src.py run --input <path>` as the compatibility wrapper that orchestrates both phases.
8. Validate the candidate package with `python scripts/raw_to_src.py validate-package-readiness --artifacts-dir <dir>` before external gate consumption.
9. Review `result-summary.json`, `proposed-next-actions.json`, `handoff-proposal.json`, `job-proposal.json`, and the gate submission refs before external gate review continues.

## Revision Return Handling

- When external gate returns `revise` or `retry`, rerun `python scripts/raw_to_src.py run --input <path> --repo-root <repo-root> --allow-update --revision-request <revision-request.json>`.
- If the executor output already exists, `python scripts/raw_to_src.py supervisor-review --artifacts-dir <dir> --repo-root <repo-root> --allow-update --revision-request <revision-request.json>` is also valid.
- The runtime materializes `revision-request.json` into the artifacts directory and records normalized `revision_context`, `revision_request_ref`, and `revision_summary`.
- `raw-to-src` keeps its dual-loop local repair model; shared revision handling does not replace `patchable/blocking`, minimal patching, or budget enforcement.

## Stage Mapping

The runner preserves the ADR-002 dual-loop model as stage outputs:

1. `input_validation`
2. `raw_input_intake`
3. `source_normalization`
4. `structural_acceptance_check`
5. `structural_fix_loop`
6. `structural_recheck`
7. `source_semantic_review`
8. `semantic_acceptance_review`
9. `semantic_fix_loop`
10. `semantic_recheck`
11. `freeze_readiness_assessment`

## Guardrails

- Reject inputs that already carry `ssot_type` with status `frozen`, `active`, or `deprecated`.
- Reject `gate-materialize` placeholders.
- Emit exactly one SRC candidate package per run.
- If the input clearly contains multiple independent problem domains, fail with a split-required signal.
- For ADR inputs, emit thin `governance_bridge_src` semantics with explicit bridge context.
- Every generated intermediate state must be validated before the next generation step continues.
- Fixes must follow the Minimal Patch Principle: patch only the recorded defect scope and do not silently rewrite the whole artifact.
- The skill does not issue final freeze or queue decisions; those belong to the external gate and queue materializer.
- `validate-package-readiness` is a package guard only. The legacy `freeze-guard` name remains as a compatibility alias and must not grow into an embedded gate.
