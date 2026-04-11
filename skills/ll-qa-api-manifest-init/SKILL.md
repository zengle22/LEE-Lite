---
name: ll-qa-api-manifest-init
description: ADR-047 governed skill for initializing an API coverage manifest (api-coverage-manifest.yaml) from an api-test-plan, with capability × dimension expansion and four-dimensional status fields.
---

# LL QA API Manifest Init

This skill implements the ADR-047 API chain manifest initialization step. It accepts an `api-test-plan.md` and produces an `api-coverage-manifest.yaml` with every capability × required dimension expanded into coverage items. Each item carries the four-dimensional status fields: lifecycle_status, mapping_status, evidence_status, waiver_status.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-feat-to-apiplan` (api-test-plan.md)
- Downstream skill target: `ll-qa-api-spec-gen`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `API Test Plan -> Coverage Manifest` derivation. The manifest is an artifact authority, not a runnable test surface.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one `api-test-plan.md` from `ll-qa-feat-to-apiplan` at `ssot/tests/api/{feat_id}/api-test-plan.md`.
2. Validate the plan — must contain feature_id, capabilities table, test dimension matrix, and priority matrix.
3. For each capability × required dimension combination, generate a coverage item:
   - `coverage_id`: hierarchical ID (e.g., `api.cand.submit.happy`)
   - `capability`: reference to capability ID from the plan
   - `scenario_type`: happy_path, parameter_validation, exception, state_constraint, authorization, idempotent, data_side_effect
   - `dimension`: the test dimension name
   - `priority`: inherited from the capability
   - `source_feat_ref`: reference to the FEAT section that defines this behavior
4. Initialize all items with four-dimensional status fields:
   - `lifecycle_status: designed`
   - `mapping_status: unmapped`
   - `evidence_status: missing`
   - `waiver_status: none`
5. Apply ADR-047 cut rules based on priority:
   - For P0: cut "幂等/并发" and "边界值 edge cases" only
   - For P1: cut "边界值", "状态约束", "权限", "幂等/并发"
   - For P2: cut everything except "正常路径"
   - Set `lifecycle_status: cut` for cut items
   - Every cut item must have a `cut_record` with: cut_target, cut_reason, source_ref, approver, approved_at
6. Add supporting fields to each item:
   - `mapped_case_ids: []`
   - `evidence_refs: []`
   - `rerun_count: 0`
   - `last_run_id: null`
   - `obsolete: false`
   - `superseded_by: null`
7. Wrap in the `api_coverage_manifest` root key with metadata:
   - `feature_id`, `generated_at`, `source_plan_ref`
8. Run executor agent to draft the manifest, then supervisor agent to validate structural constraints.
9. Emit the manifest to `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`.

## Workflow Boundary

- Input: one `api-test-plan.md`
- Output: one `api-coverage-manifest.yaml`
- Out of scope: updating manifest after test execution (downstream), generating test specs (downstream skill)

## Non-Negotiable Rules

- Do not generate a manifest without a validated api-test-plan input.
- Do not skip dimension expansion — every capability must have items for all required dimensions.
- Do not initialize any item with lifecycle_status other than `designed` or `cut`.
- Do not allow cut items without a complete cut_record (approver + source_ref mandatory).
- Do not modify the api-test-plan content — this skill only reads it.
- Structural constraint: item count must equal capabilities × required dimensions after cuts.
- The manifest root key must be `api_coverage_manifest` (not bare `items:`).
