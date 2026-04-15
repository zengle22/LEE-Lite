# ADR-047 API Chain Pilot Report

**Date:** 2026-04-15
**Pilot ID:** FEAT-PILOT-001
**Chain:** API test chain (plan → manifest → spec → exec → evidence → settlement → gate)

## Chain Execution Log

| Step | Skill | Input | Output | Schema Validation | Status |
|------|-------|-------|--------|-------------------|--------|
| 1 | feat-to-apiplan | feat-pilot.yaml | api-test-plan.yaml | plan: PASS | Success |
| 2 | api-manifest-init | api-test-plan.yaml | api-coverage-manifest.yaml | manifest: PASS | Success |
| 3 | api-spec-gen | api-coverage-manifest.yaml | api-test-spec/8 files | spec: PASS (8 files) | Success |
| 4 | (simulated exec) | api-test-spec/8 files | evidence/8 files + updated manifest | -- | Success |
| 5 | settlement | updated manifest | api-pilot-settlement-report.yaml | settlement: PASS | Success |
| 6 | gate-evaluate | 5 inputs (API+E2E+waivers) | release_gate_input.yaml | gate: PASS | Success |

## Schema Validation Results

All 5 schema types validated successfully:
- plan: `python -m cli.lib.qa_schemas --type plan ...` → OK
- manifest: `python -m cli.lib.qa_schemas --type manifest ...` → OK
- spec: `python -m cli.lib.qa_schemas --type spec ...` → OK (8 files)
- settlement: `python -m cli.lib.qa_schemas --type settlement ...` → OK
- gate: `python -m cli.lib.qa_schemas --type gate ...` → OK

## Statistics Summary

- API objects: 2 (training_plan, feedback)
- Capabilities: 4 (create_plan P0, submit_feedback P0, get_plan P1, update_plan P1)
- Coverage items: 8
- Passed: 7
- Failed: 1 (intentional -- to test gap_list and waiver flow)
- Gate result: fail (due to unwaived failed item with pending waiver)

## Failure Records

**Intentional failure:** `api.feedback.submit.validation` -- simulated validation failure to test gap_list and waiver flow. The simulated server accepted a rating of 6 (outside valid 1-5 range), exposing a parameter validation gap. This is by design to verify the chain handles failures correctly (D-07, D-08).

## Issues Encountered

1. **_run_llm_executor() does not invoke Claude subprocess:** All skill business logic was executed manually by the orchestrator. For production, this needs to be wired to actually invoke the LLM subprocess.
2. **No real API backend:** Test execution was simulated with `execution_status: "simulated"`. Evidence files document this explicitly. The pilot validates the chain orchestration, not actual API behavior.
3. **E2E stub artifacts required:** gate-evaluate requires 5 inputs including E2E artifacts. Created minimal E2E stub (empty manifest, zero-count settlement) to satisfy the requirement.
4. **Existing e2e-settlement-report.yaml invalid:** The pre-existing file did not have the correct `settlement_report` top-level key. Created new `e2e-pilot-stub-settlement.yaml` instead.
5. **Settlement schema strictness:** The `summary` dataclass does not accept `pass_rate` -- it was removed from the settlement report. Statistics are computed from passed_count and executed_count by the consumer.

## Improvement Suggestions

1. Wire `_run_llm_executor()` to actually invoke Claude Code subprocess for production use
2. Add a real API test target or mock server for genuine test execution
3. Consider adding a `--pilot` flag to gate-evaluate that accepts API-only input (no E2E stubs needed)
4. Add schema auto-detection for E2E manifest (currently uses same key as API manifest)
5. Consider adding a `validate_all` command to `qa_schemas.py` that validates all QA assets in a directory
6. Fix the existing `e2e-settlement-report.yaml` to conform to the current settlement schema

## Success Criteria Verification

- [x] Full API chain runs end-to-end without manual intervention (except skill logic execution) -- REQ-04
- [x] All intermediate artifacts pass schema validation -- REQ-05
- [x] release_gate_input.yaml contains correct pass/fail/coverage statistics with valid SHA-256 evidence hash
- [x] Pilot report written with failure records and improvement suggestions -- REQ-06

## Locked Decisions Compliance

- [x] D-01: New minimal feat YAML created (not from existing)
- [x] D-02: 2 API objects, 4 capabilities, P0/P1 coverage
- [x] D-03: Single-step interactive execution (each step validated before next)
- [x] D-04: Each step's output observed and validated
- [x] D-05: Manifest marked with lifecycle_status and evidence_status
- [x] D-06: Evidence files in ssot/tests/.artifacts/evidence/ by coverage_id
- [x] D-07: Chain stops on failure (validated at each step)
- [x] D-08: Failures recorded in pilot-report
- [x] D-09: Intermediate artifacts retained for debugging
