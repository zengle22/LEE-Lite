---
name: ll-qa-e2e-spec-to-tests
description: ADR-047 governed skill for converting frozen e2e-journey-spec YAML files into executable Playwright TypeScript test scripts with embedded evidence collection.
---

# LL QA E2E Spec-to-Tests Generation

This skill implements the ADR-047 E2E test script generation step (D-GEN-02). It accepts one or more frozen `e2e-journey-spec` YAML files and generates executable Playwright TypeScript `.spec.ts` test scripts. Each generated script includes embedded evidence-writing hooks per ADR-047 Section 6.3 E2E evidence format.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-e2e-spec-gen` (e2e-journey-spec YAML files)
- Downstream consumer: E2E test execution engine (`ll-qa-e2e-test-exec`)

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `E2E Journey Spec -> Playwright Test Script` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one or more `e2e-journey-spec` YAML files from input path.
2. Validate each spec — must contain `e2e_journey_spec` root key with case_id, coverage_id, journey_id, entry_point, user_steps, and all required sections.
3. For each spec, generate a Playwright TypeScript test file at `{output_dir}/{case_id}.spec.ts`:
   - **Import**: `{ test, expect } from '@playwright/test'`
   - **Test definition**: `test()` with descriptive name from case_id
   - **Test body** that:
     - Navigates to entry_point via `page.goto()`
     - Iterates user_steps: performs action (click, fill, navigate) on target selector
     - Asserts expected_ui_states: `expect(page.locator(selector)).toHaveText/toBeVisible`
     - Asserts expected_persistence: reload page and verify state persists
     - Checks anti_false_pass_checks: no console errors, no 404 responses
     - Collects evidence per ADR-047 Section 6.3 E2E evidence format
     - Writes evidence YAML for every item in `spec.evidence_required`
4. Run executor agent to generate Playwright scripts, then supervisor agent to validate each script.
5. Emit `.spec.ts` files to `{output_dir}` directory.

## Workflow Boundary

- Input: one or more `e2e-journey-spec` YAML files
- Output: Playwright TypeScript `.spec.ts` test files with evidence-writing hooks
- Out of scope: running the tests (downstream execution engine), collecting evidence (downstream)

## Non-Negotiable Rules

- Do not modify the input spec file (specs are frozen).
- Every generated script must write evidence YAML for every item in `evidence_required`.
- Generated scripts must be valid Playwright TypeScript (.spec.ts extension).
- Evidence path must include run_id for collision avoidance.
- Scripts must include try/catch error handling with evidence write in catch block.
- Do not invent UI selectors not present in the spec — all selectors must map to `expected_ui_states` or `user_steps`.
