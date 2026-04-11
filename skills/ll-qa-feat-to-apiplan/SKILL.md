---
name: ll-qa-feat-to-apiplan
description: ADR-047 governed skill for transforming one frozen FEAT into an API test plan (api-test-plan.md) with capability extraction, dimension matrix, and priority-based cut rules.
---

# LL QA FEAT to API Plan

This skill implements the ADR-047 API test chain entry point. It accepts one frozen FEAT document and produces an `api-test-plan.md` that defines API capabilities, test dimensions, and a priority matrix. It is the first step in the API test chain: FEAT → api-test-plan → api-coverage-manifest → api-test-specs.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Workflow template: `E:\ai\LEE-Lite-skill-first\ssot\tests\templates\feat-to-api-test-plan.md`
- Upstream handoff: `ll-product-epic-to-feat` (frozen FEAT package)
- Downstream skill target: `ll-qa-api-manifest-init`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `FEAT -> API Test Plan` derivation. The emitted plan is an artifact authority, not a runnable test surface.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept only a freeze-ready `feat_freeze_package` emitted by `ll-product-epic-to-feat`, plus an explicit `feat_ref`.
2. Validate the package structurally — FEAT must have id, title, status=frozen, Scope, Acceptance Checks, and Constraints sections.
3. Extract all API capabilities from the FEAT:
   - Identify API objects from Scope (e.g., candidate_package, handoff, gate_decision)
   - For each object, extract capabilities (submit, validate, create, read, transition, evaluate, record)
   - Assign capability IDs in format `{PREFIX}-{NAME}-{SEQ}` (e.g., `CAND-SUBMIT-001`)
   - Assign priority (P0/P1/P2) based on Acceptance Checks mapping
4. Apply the ADR-047 test dimension matrix to each capability:
   - 正常路径 (happy path)
   - 参数校验 (parameter validation) — P0/P1 required
   - 边界值 (boundary values) — P0 selected, P1/P2 cut
   - 状态约束 (state constraints) — P0 required
   - 权限与身份 (auth/identity) — P0 required
   - 异常路径 (exception paths) — P0/P1 required
   - 幂等/重试/并发 (idempotent/retry/concurrent) — P0 selected
   - 数据副作用 (data side effects) — P0 required
5. Apply priority-based cut rules:
   - P0: only cut "幂等/并发" and "边界值 edge cases"
   - P1: cut "边界值", "状态约束", "权限", "幂等/并发"
   - P2: only keep "正常路径"
   - Every cut must have a `cut_record` (approver + source_ref)
6. Generate `api-test-plan.md` with:
   - Plan metadata (feature_id, plan_version, created_at, source, anchor_type=feat)
   - Source references to the FEAT document
   - Capabilities table with IDs, names, descriptions, priorities
   - Test dimension matrix
   - Coverage cut records table
   - Priority matrix summary
7. Run executor agent to draft the plan, then supervisor agent to validate quality checks.
8. Emit the plan to `ssot/tests/api/{feat_id}/api-test-plan.md`.

## Workflow Boundary

- Input: one `feat_freeze_package` plus one selected `feat_ref`
- Output: one `api-test-plan.md` at `ssot/tests/api/{feat_id}/`
- Out of scope: generating manifests (downstream skill), generating specs (downstream skill), running actual tests

## Non-Negotiable Rules

- Do not accept raw requirements, SRC candidates, or non-frozen FEAT documents.
- Do not skip capability extraction — every API-capable object in Scope must yield at least one capability.
- Do not generate a plan with fewer dimensions than the ADR-047 matrix specifies.
- Do not self-approve the plan — external QA review consumers own the approval decision.
- Do not let cut rules bypass the cut_record requirement (approver + source_ref mandatory).
- Do not modify FEAT scope or acceptance boundaries during extraction.
- P0 capabilities must have at least 5 coverage items after dimension application.
