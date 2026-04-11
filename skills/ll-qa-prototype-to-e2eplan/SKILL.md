---
name: ll-qa-prototype-to-e2eplan
description: ADR-047 governed skill for deriving user journeys from a frozen prototype (or feat) and generating an E2E journey plan (e2e-journey-plan.md) with main journeys and minimum exception journeys.
---

# LL QA Prototype to E2E Plan

This skill implements the ADR-047 E2E test chain entry point. It accepts a frozen prototype document (or a FEAT for API-derived mode) and produces an `e2e-journey-plan.md` that identifies user-visible journeys including at least one main journey and one exception journey. It is the first step in the E2E test chain: Prototype/FEAT → e2e-journey-plan → e2e-coverage-manifest → e2e-journey-specs.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Workflow template: `E:\ai\LEE-Lite-skill-first\ssot\tests\templates\prototype-to-e2e-journey-plan.md`
- Upstream handoff: `ll-dev-feat-to-proto` (frozen prototype) or `ll-product-epic-to-feat` (FEAT for API-derived mode)
- Downstream skill target: `ll-qa-e2e-manifest-init`

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Prototype -> E2E Journey Plan` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one frozen prototype package from `ll-dev-feat-to-proto`, or a FEAT for API-derived mode.
2. Determine mode:
   - **Prototype-Driven**: prototype exists with flow map / journey map → extract journeys directly
   - **API-Derived**: no prototype → derive user-visible journeys from FEAT capabilities
3. Apply journey identification rules:
   | 触发条件 | 必须识别的旅程 | 优先级 |
   |----------|----------------|--------|
   | 每个页面流 | 至少 1 条主旅程 | P0 |
   | 每个表单页 | 至少 1 条校验失败异常旅程 | P0 |
   | 每个有状态差异的页面 | 至少 1 条状态型旅程 | P1 |
   | 每个有回访入口的闭环 | 至少 1 条 revisit 旅程 | P1 |
   | 每个主旅程 | 至少 1 条关键分支旅程 | P1 |
   | 每个网络请求点 | 至少 1 条网络失败异常旅程 | P1 |
4. For each journey, define:
   - journey_id (format: `JOURNEY-{TYPE}-{SEQ}`, e.g., `JOURNEY-MAIN-001`)
   - journey_type (main, exception, branch, retry, state)
   - entry_point (page/URL where journey begins)
   - user_steps (ordered list of user actions)
   - expected_ui_states (UI states at key checkpoints)
   - expected_network_events (API calls expected during journey)
   - expected_persistence (data that must be saved/changed)
   - priority (P0/P1)
5. Validate minimum journey count: ≥1 main journey (P0) + ≥1 exception journey.
6. Generate `e2e-journey-plan.md` with:
   - Plan metadata (prototype_id or feature_id, derivation_mode, created_at, source, anchor_type=prototype)
   - Journey definitions table
   - Journey detail sections for each journey
   - Minimum journey count validation result
7. Run executor agent to draft the plan, then supervisor agent to validate journey completeness.
8. Emit the plan to `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md`.

## Workflow Boundary

- Input: one frozen prototype package OR one frozen FEAT (API-derived mode)
- Output: one `e2e-journey-plan.md` at `ssot/tests/e2e/{prototype_id}/`
- Out of scope: generating manifests (downstream skill), generating journey specs (downstream skill), running actual E2E tests

## Non-Negotiable Rules

- Do not accept non-frozen prototype or FEAT documents.
- Do not generate a plan with zero exception journeys — minimum 1 required.
- Do not generate a plan with zero main journeys — minimum 1 required.
- Do not skip network failure exception journeys for journeys that make API calls.
- Do not let API-derived mode skip the `derivation_mode: api-derived` annotation.
- Every journey must have an entry_point and at least 2 user_steps.
- Do not modify prototype or FEAT content during journey extraction.
