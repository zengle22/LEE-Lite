---
name: ll-qa-api-spec-gen
description: ADR-047 governed skill for generating structured API test specs from coverage items in api-coverage-manifest.yaml, with evidence_required, anti_false_pass_checks, and cleanup requirements.
---

# LL QA API Spec Gen

This skill implements the ADR-047 API test spec generation step. It accepts an `api-coverage-manifest.yaml` and generates structured `api-test-spec` files for each coverage item that is not cut. Each spec contains endpoint definitions, request/response schemas, assertions, evidence requirements, and anti-false-pass checks.

## Canonical Authority

- ADR: `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-047-双链测试架构与防偷懒治理框架.MD`
- Upstream handoff: `ll-qa-api-manifest-init` (api-coverage-manifest.yaml)
- Downstream consumer: API test execution engine (ll-test-exec-cli)

## Runtime Boundary Baseline

- Interpret this workflow using `E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `Coverage Manifest -> Test Specs` derivation.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`
5. `agents/supervisor.md`
6. `input/semantic-checklist.md`
7. `output/semantic-checklist.md`

## Execution Protocol

1. Accept one `api-coverage-manifest.yaml` from `ll-qa-api-manifest-init` at `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`.
2. Validate the manifest — must contain `api_coverage_manifest` root key, items array, and all items must have coverage_id, capability, scenario_type, dimension, priority, lifecycle_status.
3. Filter items: only process items where `lifecycle_status` is `designed` (skip `cut`, `obsolete`, `superseded`).
4. For each coverage item, generate a structured test spec file at `ssot/tests/api/{feat_id}/api-test-spec/SPEC-{capability-id}.{scenario_type}.md`:
   - **Spec metadata**: spec_id, coverage_id_ref, capability_ref, priority
   - **Endpoint definition**: method, path, expected status codes
   - **Request schema**: headers, query params, body schema for the given scenario
   - **Expected response**: status code, response body schema, headers
   - **Assertions**: explicit assertion list (status code, body fields, error messages, side effects)
   - **evidence_required**: list of evidence types to collect (request_log, response_log, error_response, assertion_result, token_refresh_log, device_binding_log, token_lifecycle_log, db_state)
   - **anti_false_pass_checks**: checks to prevent false positives (e.g., "verify response is not a generic 200 OK", "verify error_code matches expected", "verify side effects in DB")
   - **cleanup**: any cleanup steps needed after test execution
   - **source_refs**: traceability back to FEAT sections and coverage item
5. Run executor agent to draft specs, then supervisor agent to validate each spec contains all required sections.
6. Emit specs to `ssot/tests/api/{feat_id}/api-test-spec/` directory.

## Workflow Boundary

- Input: one `api-coverage-manifest.yaml`
- Output: multiple `api-test-spec` files in `ssot/tests/api/{feat_id}/api-test-spec/`
- Out of scope: running the tests (downstream execution engine), updating manifest (downstream)

## Non-Negotiable Rules

- Do not generate specs for items with lifecycle_status = `cut`, `obsolete`, or `superseded`.
- Every spec must contain `evidence_required` field listing required evidence types.
- Every spec must contain `anti_false_pass_checks` with at least one check.
- Do not invent endpoint definitions not traceable to the FEAT Scope — all endpoints must map to a capability.
- Do not generate generic assertions — each assertion must be specific to the scenario type and dimension.
- Spec filenames must be unique and reference the capability ID and scenario type.
- P0 specs must have at least 3 anti_false_pass_checks.
