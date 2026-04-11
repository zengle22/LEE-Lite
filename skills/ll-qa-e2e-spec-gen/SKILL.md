---
name: ll-qa-e2e-spec-gen
description: ADR-047 governed skill for generating structured E2E journey specs from coverage items in e2e-coverage-manifest.yaml, with user steps, UI states, network events, anti_false_pass_checks, and evidence requirements.
---

# LL QA E2E Spec Gen

This skill implements the ADR-047 E2E journey spec generation step. It accepts an `e2e-coverage-manifest.yaml` and generates structured `e2e-journey-spec` files for each coverage item that is not cut. Each spec contains entry points, user steps, expected UI states, network events, persistence expectations, anti-false-pass checks, and evidence requirements.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-e2e-manifest-init` (e2e-coverage-manifest.yaml)
- Downstream consumer: E2E test execution engine (ll-test-exec-web-e2e)

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `E2E Coverage Manifest -> Journey Specs` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one `e2e-coverage-manifest.yaml` from `ll-qa-e2e-manifest-init` at `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`.
2. Validate the manifest — must contain `e2e_coverage_manifest` root key, items array, and all items must have coverage_id, journey_id, journey_type, priority, lifecycle_status.
3. Filter items: only process items where `lifecycle_status` is `designed` (skip `cut`, `obsolete`, `superseded`).
4. For each coverage item, generate a structured journey spec file at `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/JOURNEY-{journey_type}-{seq}.md`:
   - **Spec metadata**: spec_id, coverage_id_ref, journey_id_ref, journey_type, priority
   - **entry_point**: page/URL where the journey begins, initial state requirements
   - **user_steps**: ordered list of user actions with expected UI feedback after each step
   - **expected_ui_states**: UI state assertions at key checkpoints (element visibility, text content, navigation, error messages, loading states)
   - **expected_network_events**: API calls expected during the journey (endpoint, method, expected status, response shape)
   - **expected_persistence**: data that must be saved/changed as a result of the journey (DB records, cookies, local storage)
   - **evidence_required**: list of evidence types to collect (playwright_trace, screenshot, network_log, console_log, storage_state)
   - **anti_false_pass_checks**: checks to prevent false positives (e.g., "verify page actually navigated", "verify success message is specific not generic", "verify API call was made not just UI change")
   - **source_refs**: traceability back to prototype/FEAT sections and coverage item
5. Run executor agent to draft specs, then supervisor agent to validate each spec contains all required sections.
6. Emit specs to `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/` directory.

## Workflow Boundary

- Input: one `e2e-coverage-manifest.yaml`
- Output: multiple `e2e-journey-spec` files in `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/`
- Out of scope: running the tests (downstream execution engine), updating manifest (downstream)

## Non-Negotiable Rules

- Do not generate specs for items with lifecycle_status = `cut`, `obsolete`, or `superseded`.
- Every spec must contain `evidence_required` field listing at least `playwright_trace` and `screenshot`.
- Every spec must contain `anti_false_pass_checks` with at least one check.
- Do not invent user steps not traceable to the prototype/FEAT — all steps must map to a journey.
- Do not generate generic UI assertions — each assertion must be specific to the expected state.
- Exception journey specs must include the error condition trigger and the expected error recovery path.
- Main journey (P0) specs must have at least 3 anti_false_pass_checks.
- Every spec must include at least one `expected_network_events` entry if the journey makes API calls.
