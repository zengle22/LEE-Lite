---
name: ll-qa-e2e-manifest-init
description: ADR-047 governed skill for initializing an E2E coverage manifest (e2e-coverage-manifest.yaml) from an e2e-journey-plan, with four-dimensional status fields and journey-based coverage items.
---

# LL QA E2E Manifest Init

This skill implements the ADR-047 E2E chain manifest initialization step. It accepts an `e2e-journey-plan.md` and produces an `e2e-coverage-manifest.yaml` with every journey expanded into coverage items. Each item carries the four-dimensional status fields: lifecycle_status, mapping_status, evidence_status, waiver_status.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-prototype-to-e2eplan` (e2e-journey-plan.md)
- Downstream skill target: `ll-qa-e2e-spec-gen`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `E2E Journey Plan -> Coverage Manifest` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one `e2e-journey-plan.md` from `ll-qa-prototype-to-e2eplan` at `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md`.
2. Validate the plan — must contain prototype_id or feature_id, journey definitions, and minimum journey count validation.
3. For each journey in the plan, generate a coverage item:
   - `coverage_id`: hierarchical ID (e.g., `e2e.login.main.happy`)
   - `journey_id`: reference to journey ID from the plan
   - `journey_type`: main, exception, branch, retry, state
   - `priority`: inherited from the journey
   - `source_prototype_ref`: reference to the prototype section or FEAT section
4. Initialize all items with four-dimensional status fields:
   - `lifecycle_status: designed`
   - `mapping_status: unmapped`
   - `evidence_status: missing`
   - `waiver_status: none`
5. Apply E2E-specific cut rules:
   - P1 exception journeys may be cut if equivalent P0 coverage exists elsewhere
   - Revisit journeys may be cut if state is validated by another journey
   - Every cut item must have a `cut_record` with: cut_target, cut_reason, source_ref, approver, approved_at
6. Add supporting fields to each item:
   - `mapped_case_ids: []`
   - `evidence_refs: []`
   - `rerun_count: 0`
   - `last_run_id: null`
   - `obsolete: false`
   - `superseded_by: null`
7. Wrap in the `e2e_coverage_manifest` root key with metadata:
   - `prototype_id` or `feature_id`, `derivation_mode`, `generated_at`, `source_plan_ref`
8. Run executor agent to draft the manifest, then supervisor agent to validate structural constraints.
9. Validate item count >= plan journeys.
10. Emit the manifest to `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`.

## Workflow Boundary

- Input: one `e2e-journey-plan.md`
- Output: one `e2e-coverage-manifest.yaml`
- Out of scope: updating manifest after test execution (downstream), generating journey specs (downstream skill)

## Non-Negotiable Rules

- Do not generate a manifest without a validated e2e-journey-plan input.
- Do not skip journey expansion — every journey must have at least one coverage item.
- Do not initialize any item with lifecycle_status other than `designed` or `cut`.
- Do not allow cut items without a complete cut_record (approver + source_ref mandatory).
- Do not modify the e2e-journey-plan content — this skill only reads it.
- Structural constraint: item count must be >= plan journey count.
- The manifest root key must be `e2e_coverage_manifest` (not bare `items:`).
- Main journey (P0) items must never be cut.
