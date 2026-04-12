---
id: IMPL-SRC-RAW-TO-SRC-ADR048-002
ssot_type: IMPL
impl_ref: IMPL-SRC-RAW-TO-SRC-ADR048-002
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-002
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-002
title: Droid Missions Runtime - API and E2E Worker Execution Implementation Task Package
status: execution_ready
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr048-droid-runtime-impl-20260412-r1
candidate_package_ref: artifacts/tech-to-impl/adr048-droid-runtime-impl-20260412-r1
frozen_at: '2026-04-12T00:00:00Z'
---

# IMPL-SRC-RAW-TO-SRC-ADR048-002

## 1. Task Identity

- impl_ref: `IMPL-SRC-RAW-TO-SRC-ADR048-002`
- title: Droid Missions Runtime - API and E2E Worker Execution Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `adr048-droid-runtime-impl-20260412-r1`
- status: `execution_ready`
- derived_from: `FEAT-SRC-RAW-TO-SRC-ADR048-002`, `TECH-SRC-RAW-TO-SRC-ADR048-002`
- package role: canonical execution package / execution-time single entrypoint

## 2. Objectives

- Coverage target: Implement Droid Missions Runtime that executes validation contracts, collects evidence, writes validation-state, and runs post-execution validators.
- Completion standard: All 5 required steps, 6 ordered tasks, 3 acceptance mappings, and handoff artifacts are complete.
- Completion condition: coder/tester can consume this contract directly without re-opening upstream TECH/ARCH/API docs.

## 3. Scope and Non-Goals

### In Scope

- Implement `cli/lib/droid_runtime.py` as core orchestrator reading features.json and dispatching workers.
- Implement `cli/lib/api_worker.py` for API validation-contract assertion execution.
- Implement `cli/lib/e2e_worker.py` for E2E user journey validation execution.
- Implement `cli/lib/evidence_collector.py` for structured evidence collection with hash binding.
- Implement `cli/lib/validation_state_writer.py` for validation-state writeback.
- Implement `cli/lib/scrutiny_validator.py` for evidence completeness and contract compliance checks.
- Implement `cli/lib/user_testing_validator.py` for E2E UX completeness checks.

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.
- Runtime does not compile features or make gate decisions.

## 4. Upstream Convergence

- ADR refs: ADR-048, ADR-047, ADR-038 -> Droid Runtime governance under ADR-048 worker responsibility boundaries.
- FEAT: `FEAT-SRC-RAW-TO-SRC-ADR048-002` -> Execute validation contracts via API/E2E workers with evidence collection.
- TECH: `TECH-SRC-RAW-TO-SRC-ADR048-002` -> Worker-based dispatch, priority ordering, evidence hash binding.
- ARCH: `ARCH-SRC-RAW-TO-SRC-ADR048-002` -> Runtime reads from ssot/tests/compiled/, writes to .droid/.
- API: `API-SRC-RAW-TO-SRC-ADR048-002` -> execute_mission, validate_scrutiny, validate_user_testing interfaces.
- UI: `missing_authority` -> E2E worker validates UI states declared in validation-contract; no separate UI authority.
- TESTSET: `missing_authority` -> Dual-chain manifest/spec serve as acceptance authority.

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-048, ADR-047, ADR-038` | required_for: worker responsibility boundaries and runtime layering | execution_effect: runtime follows ADR-048 worker constraints exactly | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-RAW-TO-SRC-ADR048-002` | required_for: layering and ownership constraints | execution_effect: runtime writes only to .droid/ | follow_up: none
- `API` status=`bound` ref=`API-SRC-RAW-TO-SRC-ADR048-002` | required_for: interface contract snapshots | execution_effect: execute_mission, validate_scrutiny, validate_user_testing signatures are frozen | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-RAW-TO-SRC-ADR048-002` | required_for: UI entry/exit constraints | execution_effect: E2E worker validates UI states from validation-contract only | follow_up: not_applicable
- `TESTSET` status=`missing` ref=`TESTSET-FEAT-SRC-RAW-TO-SRC-ADR048-002` | required_for: acceptance truth | execution_effect: dual-chain validation serves as acceptance proxy | follow_up: freeze_dual_chain_as_acceptance_authority

## Main Sequence Snapshot

- 1. Read compiled features.json and execution-manifest.yaml from ssot/tests/compiled/.
- 2. Dispatch API/E2E workers by priority order (P0 -> P1 -> P2) from execution-manifest.
- 3. Execute validation-contract assertions per feature, collecting required evidence.
- 4. Write validation-state with lifecycle_status, evidence_status, and evidence_hash.
- 5. Run Scrutiny-Validator for evidence completeness and contract compliance.
- 6. Run User-Testing-Validator for E2E UX completeness checks.

## Implementation Unit Mapping Snapshot

- `cli/lib/droid_runtime.py` (new): Core orchestrator that reads compiled input and dispatches workers by priority.
- `cli/lib/api_worker.py` (new): Executes API validation-contract assertions with evidence collection.
- `cli/lib/e2e_worker.py` (new): Executes E2E user journey validation with UI, network, and persistence checks.
- `cli/lib/evidence_collector.py` (new): Structured evidence collection with hash generation and log binding.
- `cli/lib/validation_state_writer.py` (new): Writes validation-state to .droid/state/ with consistency guarantees.
- `cli/lib/scrutiny_validator.py` (new): Post-execution evidence completeness and contract compliance verification.
- `cli/lib/user_testing_validator.py` (new): Post-execution E2E UX completeness verification.

## State Model Snapshot

- `inputs_loaded` -> `workers_dispatched` -> `assertions_executed` -> `evidence_collected` -> `validation_state_written` -> `scrutiny_validated` -> `user_testing_validated`
- `worker_failure` transitions to `validation_state_written` with lifecycle_status=failed and partial evidence preserved.
- `evidence_incomplete` must never transition to lifecycle_status=passed.
- Recovery: on `worker_failure`, preserve partial evidence, log failure detail, continue with remaining workers, mark lifecycle_status=failed_done.
- Recovery: on `features_json_invalid`, reject with structured error, allow retry with corrected input, retry up to 3 times before escalation.
- Recovery: on `worker_timeout`, preserve partial evidence with lease recovery, retry worker with extended timeout, fail-closed after 2 retries.
- Recovery: on `evidence_collection_failed`, mark specific coverage_id as failed with error detail, continue remaining assertions, escalate if critical coverage missing.
- Recovery: on `validation_state_missing`, fail-closed, require manual resolution before proceeding.
- Recovery: on `evidence_incomplete`, block passed status, generate gap report, route to fix-feature flow.
- Completion signals: inputs_loaded_done, workers_dispatched_done, assertions_executed_done, evidence_collected_done, validation_state_written_done, scrutiny_validated_done, user_testing_validated_done.

## Integration Points Snapshot

- Input sources: `ssot/tests/compiled/features.json`, `ssot/tests/compiled/execution-manifest.yaml` - read-only consumption.
- Output destination: `.droid/evidence/`, `.droid/state/validation-state.yaml`, `.droid/state/execution-log.jsonl`.
- Downstream consumer: Gate evaluator (FEAT-005) reads validation-state and evidence for release/block decisions.
- CLI invocation: `cli loop dispatch` as target_skill for compiled missions.

## TECH Contract Snapshot

- Workers execute only what validation-contract declares; no autonomous test scope decisions.
- Evidence collection produces verifiable hashes bound to execution logs.
- validation-state is consistent: passed requires complete evidence with valid hash.
- Worker timeout preserves partial evidence and marks failed status.

## ARCH Constraint Snapshot

- Runtime writes only to .droid/ directory tree.
- Runtime must not modify SSOT, dual-chain, or compiled documents.
- No gate decision responsibility; runtime only produces execution evidence.

## API Contract Snapshot

- `execute_mission`: input=`features_json_ref`, `execution_manifest_ref`; output=`validation_state_ref`, `evidence_refs[]`; errors=`features_json_invalid`, `worker_timeout`, `evidence_collection_failed`; idempotent=`yes by input hash`.
- `validate_scrutiny`: input=`validation_state_ref`; output=`scrutiny_report_ref`; errors=`validation_state_missing`, `evidence_incomplete`.
- `validate_user_testing`: input=`validation_state_ref`; output=`ux_validation_report_ref`; errors=`validation_state_missing`, `ui_state_unverified`.

## Embedded Execution Contract

### State Machine

- `inputs_loaded` -> `workers_dispatched` -> `assertions_executed` -> `evidence_collected` -> `validation_state_written` -> `scrutiny_validated` -> `user_testing_validated`
- `evidence_incomplete` must never transition to lifecycle_status=passed.

### API Contracts

- `execute_mission`: input=`features_json_ref`, `execution_manifest_ref`; output=`validation_state_ref`, `evidence_refs[]`; errors=`features_json_invalid`, `worker_timeout`, `evidence_collection_failed`.
- `validate_scrutiny`: input=`validation_state_ref`; output=`scrutiny_report_ref`; errors=`validation_state_missing`, `evidence_incomplete`.
- `validate_user_testing`: input=`validation_state_ref`; output=`ux_validation_report_ref`; errors=`validation_state_missing`, `ui_state_unverified`.

### UI Entry

- N/A - backend execution runtime, no user-facing surface for worker execution.

### UI Success Exit

- All validation-contracts executed, evidence collected, validation-state written, post-execution validators passed.

### UI Failure Exit

- Worker timeout: preserve partial evidence, mark lifecycle_status=failed, continue with remaining workers.
- Evidence collection failed: mark specific coverage_id as failed with error detail, continue with remaining assertions.

### Invariants

- Workers must not decide test scope beyond validation-contract.
- Evidence collection must be complete for passed status.
- validation-state must include valid evidence hash when passed.
- Execution order follows P0 -> P1 -> P2 priority.

### Boundary Guardrails

- Boundary to Mission Compiler: Runtime consumes compiled output but does not re-compile or modify features.json.
- Boundary to Gate: Runtime produces evidence but does not make release/block decisions.
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not expand touch set beyond declared modules without re-derive.

## 5. Normative Constraints

### Normative / MUST

- Workers must follow validation-contract assertions exactly.
- Evidence must be collected for all evidence_required declarations before marking passed.
- validation-state must include valid evidence hash when lifecycle_status=passed.
- Workers must not skip anti_false_pass_checks.

### Informative / Context Only

- Dual-chain manifest/spec serve as acceptance authority for validation-contract definitions.

## 6. Implementation Requirements

### Touch Set / Module Plan

- `cli/lib/droid_runtime.py` [backend | new | existing_match] <- Core mission orchestrator; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/api_worker.py` [backend | new | existing_match] <- API assertion executor; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/e2e_worker.py` [backend | new | existing_match] <- E2E journey executor; nearby matches: cli/lib/errors.py, cli/lib/fs.py
- `cli/lib/evidence_collector.py` [backend | new | existing_match] <- Evidence collection with hashing; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/validation_state_writer.py` [backend | new | existing_match] <- State writeback; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/scrutiny_validator.py` [backend | new | existing_match] <- Evidence completeness checks; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/user_testing_validator.py` [backend | new | existing_match] <- UX completeness checks; nearby matches: cli/lib/errors.py, cli/lib/policy.py

### Repo Touch Points

- `cli/lib/droid_runtime.py` [backend | new]
- `cli/lib/api_worker.py` [backend | new]
- `cli/lib/e2e_worker.py` [backend | new]
- `cli/lib/evidence_collector.py` [backend | new]
- `cli/lib/validation_state_writer.py` [backend | new]
- `cli/lib/scrutiny_validator.py` [backend | new]
- `cli/lib/user_testing_validator.py` [backend | new]

### Allowed

- Implement only the declared repo touch points.
- Wire runtime logic within frozen TECH/ARCH/API boundaries.
- Create new modules only at declared touch points.

### Forbidden

- Modify modules outside declared touch points without re-derive.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.

### Execution Boundary

- Inherited rule: upstream frozen decisions can only be implemented and verified, not rewritten in IMPL.
- Discrepancy handling: if repo shape conflicts with frozen upstream objects, do not default to code shape.

## 7. Deliverables

- impl-bundle.md, impl-bundle.json, impl-task.md
- upstream-design-refs.json, integration-plan.md
- dev-evidence-plan.json, smoke-gate-subject.json
- impl-review-report.json, impl-acceptance-report.json
- impl-defect-list.json, handoff-to-feature-delivery.json
- execution-evidence.json, supervision-evidence.json
- backend-workstream.md

### Handoff Artifacts

- impl-bundle.md, impl-bundle.json, impl-task.md
- upstream-design-refs.json, integration-plan.md
- dev-evidence-plan.json, smoke-gate-subject.json
- impl-review-report.json, impl-acceptance-report.json
- impl-defect-list.json, handoff-to-feature-delivery.json
- execution-evidence.json, supervision-evidence.json
- backend-workstream.md

## 8. Acceptance Criteria and TESTSET Mapping

- testset_ref: `dual-chain-manifest-as-proxy`
- mapping_policy: `dual_chain_over_IMPL_when_present`

### Acceptance Trace

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is implemented: all 7 new backend modules. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Evidence proves execute_mission produces valid validation-state with evidence hash. Main sequence covers: inputs loaded, workers dispatched, assertions executed, evidence collected, validation-state written. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`
- AC-003: Runtime output is consumed by downstream Gate without boundary violation. -> validation-state and evidence are structurally valid for Gate evaluation, with consistent lifecycle_status and evidence_status. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-001 through TASK-006
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-001, TASK-002, TASK-003, TASK-004
- AC-003: Runtime output is consumed by downstream Gate without boundary violation. | implemented_by: TASK-004, TASK-005, TASK-006

## 9. Execution Sequence

### Required

- 1. Freeze refs and repo touch points.
- 2. Implement core orchestrator and worker dispatch logic.
- 3. Implement API and E2E workers with assertion execution.
- 4. Implement evidence collector and validation-state writer.
- 5. Implement Scrutiny-Validator and User-Testing-Validator.
- 6. Collect acceptance evidence and close delivery handoff.

### Suggested

- None.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: all 7 new backend modules | outputs: frozen upstream refs, repo-aware touch set | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Implement core orchestrator and worker dispatch logic | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/droid_runtime.py | outputs: mission orchestrator with priority-based dispatch | acceptance: AC-002 | done_when: Orchestrator reads features.json and dispatches workers in P0->P1->P2 order.
- TASK-003 Implement API and E2E workers with assertion execution | depends_on: TASK-002 | parallel: TASK-003a, TASK-003b | touch_points: cli/lib/api_worker.py, cli/lib/e2e_worker.py | outputs: API worker, E2E worker | acceptance: AC-002 | done_when: Workers execute validation-contract assertions with correct evidence collection per chain type.
- TASK-004 Implement evidence collector and validation-state writer | depends_on: TASK-003 | parallel: none | touch_points: cli/lib/evidence_collector.py, cli/lib/validation_state_writer.py | outputs: evidence collection with hashing, validation-state writeback | acceptance: AC-002, AC-003 | done_when: Evidence is collected with valid hashes and validation-state is written consistently.
- TASK-005 Implement Scrutiny-Validator and User-Testing-Validator | depends_on: TASK-004 | parallel: none | touch_points: cli/lib/scrutiny_validator.py, cli/lib/user_testing_validator.py | outputs: post-execution validation reports | acceptance: AC-003 | done_when: Both validators produce reports confirming evidence completeness and UX completeness.
- TASK-006 Collect acceptance evidence and close delivery handoff | depends_on: TASK-005 | parallel: none | touch_points: none | outputs: acceptance evidence, handoff package | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is backed by explicit evidence artifacts.

## 10. Risks and Notes

- Worker timeout for long-running E2E journeys -> implement claim timeout with lease recovery.
- Evidence storage may grow large -> implement per-coverage_id归档 with periodic cleanup.
- validation-state consistency if multiple workers write concurrently -> use atomic writes with file locking.
- API assertion semantics may vary by endpoint type -> worker must handle diverse request/response patterns.

## Completion Signals

- **inputs_loaded_done**: Compiled features.json and execution-manifest.yaml loaded successfully, all references validated.
- **workers_dispatched_done**: All workers dispatched in P0->P1->P2 priority order.
- **assertions_executed_done**: All validation-contract assertions executed with evidence collected.
- **evidence_collected_done**: All evidence collected with valid hashes bound to execution logs.
- **validation_state_written_done**: Validation-state written to .droid/state/ with consistent lifecycle_status and evidence_hash.
- **scrutiny_validated_done**: Evidence completeness and contract compliance verified, scrutiny report generated.
- **user_testing_validated_done**: E2E UX completeness verified, UX validation report generated.
