---
id: IMPL-SRC-RAW-TO-SRC-ADR048-005
ssot_type: IMPL
impl_ref: IMPL-SRC-RAW-TO-SRC-ADR048-005
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-005
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-005
title: Gate Evaluation and Milestone Decision with Fix Feature Routing Implementation Task Package
status: execution_ready
schema_version: 1.0.0
workflow_key: dev.tech-to-impl
workflow_run_id: adr048-gate-eval-impl-20260412-r1
candidate_package_ref: artifacts/tech-to-impl/adr048-gate-eval-impl-20260412-r1
frozen_at: '2026-04-12T00:00:00Z'
---

# IMPL-SRC-RAW-TO-SRC-ADR048-005

## 1. Task Identity

- impl_ref: `IMPL-SRC-RAW-TO-SRC-ADR048-005`
- title: Gate Evaluation and Milestone Decision with Fix Feature Routing Implementation Task Package
- workflow_key: `dev.tech-to-impl`
- workflow_run_id: `adr048-gate-eval-impl-20260412-r1`
- status: `execution_ready`
- derived_from: `FEAT-SRC-RAW-TO-SRC-ADR048-005`, `TECH-SRC-RAW-TO-SRC-ADR048-005`
- package role: canonical execution package / execution-time single entrypoint

## 2. Objectives

- Coverage target: Implement Gate evaluation that consumes validation-state, computes settlement, makes gate decisions, maps to milestone decisions, and creates Fix Features for block outcomes.
- Completion standard: All 5 required steps, 5 ordered tasks, 3 acceptance mappings, and handoff artifacts are complete.
- Completion condition: coder/tester can consume this contract directly without re-opening upstream TECH/ARCH/API docs.

## 3. Scope and Non-Goals

### In Scope

- Implement `cli/lib/gate_evaluator.py` as the core gate evaluation component.
- Implement `cli/lib/settlement_computer.py` for coverage settlement statistics.
- Implement `cli/lib/milestone_mapper.py` for gate-to-milestone decision mapping.
- Implement `cli/lib/fix_feature_creator.py` for Fix Feature creation on block outcomes.
- Write milestone decisions to `ssot/tests/gate/milestone-decisions/`.
- Write Fix Features to `ssot/feat/FIX-*.md`.

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.
- Gate does not execute tests or re-evaluate validation contracts.

## 4. Upstream Convergence

- ADR refs: ADR-048, ADR-047, ADR-034 -> Gate evaluation governance and Fix Feature immutability rules.
- FEAT: `FEAT-SRC-RAW-TO-SRC-ADR048-005` -> Gate evaluation, milestone mapping, Fix Feature routing.
- TECH: `TECH-SRC-RAW-TO-SRC-ADR048-005` -> Read-only gate evaluation, deterministic settlement, Fix Feature as new object.
- ARCH: `ARCH-SRC-RAW-TO-SRC-ADR048-005` -> Gate reads from .droid/, writes to ssot/tests/gate/ and ssot/feat/FIX-*.
- API: `API-SRC-RAW-TO-SRC-ADR048-005` -> evaluate_gate, map_milestone, create_fix_feature interfaces.
- UI: `missing_authority` -> Gate evaluation is backend-only; no user-facing surface.
- TESTSET: `missing_authority` -> Dual-chain settlement serves as acceptance authority.

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-048, ADR-047, ADR-034` | required_for: gate decision rules and Fix Feature immutability | execution_effect: gate follows ADR-048 Section 2.5 gate-to-milestone mapping exactly | follow_up: none
- `ARCH` status=`bound` ref=`ARCH-SRC-RAW-TO-SRC-ADR048-005` | required_for: layering and ownership constraints | execution_effect: gate reads from .droid/, writes to ssot/tests/gate/ and ssot/feat/FIX-* | follow_up: none
- `API` status=`bound` ref=`API-SRC-RAW-TO-SRC-ADR048-005` | required_for: interface contract snapshots | execution_effect: evaluate_gate, map_milestone, create_fix_feature signatures are frozen | follow_up: none
- `UI` status=`missing` ref=`UI-FEAT-SRC-RAW-TO-SRC-ADR048-005` | required_for: UI entry/exit constraints | execution_effect: no UI surface for gate evaluation | follow_up: not_applicable
- `TESTSET` status=`missing` ref=`TESTSET-FEAT-SRC-RAW-TO-SRC-ADR048-005` | required_for: acceptance truth | execution_effect: dual-chain settlement serves as acceptance proxy | follow_up: freeze_dual_chain_as_acceptance_authority

## Main Sequence Snapshot

- 1. Read validation-state, evidence, and waiver references from .droid/ state.
- 2. Compute settlement statistics: count passed/failed/blocked/uncovered by chain and priority.
- 3. Apply waiver rules and make gate decision (release/conditional_release/block).
- 4. Map gate decision to milestone decision (passed/passed_with_waiver/failed).
- 5. For block outcomes, create Fix Feature with fixes_for linkage and failed item details.

## Implementation Unit Mapping Snapshot

- `cli/lib/settlement_computer.py` (new): Compute coverage settlement statistics from validation-state.
- `cli/lib/gate_evaluator.py` (new): Core gate evaluation with waiver validation and decision logic.
- `cli/lib/milestone_mapper.py` (new): Map gate decision to milestone decision per ADR-048 Section 2.5.
- `cli/lib/fix_feature_creator.py` (new): Create Fix Feature objects for block outcomes with fixes_for linkage.

## State Model Snapshot

- `validation_state_read` -> `settlement_computed` -> `waivers_validated` -> `gate_decision_made` -> `milestone_mapped` -> `fix_feature_created_if_blocked`
- `invalid_validation_state` must never transition into `settlement_computed`.
- `gate_decision_release` must never transition into `fix_feature_created`.
- Recovery: on `invalid_validation_state`, reject with structured error listing missing or inconsistent fields, require manual resolution before retry.
- Recovery: on `evidence_hash_mismatch`, return error listing coverage_ids with mismatches, allow re-collection and retry.
- Recovery: on `waiver_not_approved`, reject auto-waiver, require explicit approval ref, allow resubmission with valid waiver.
- Recovery: on `gate_not_blocked`, reject fix_feature creation, log warning, continue with release or conditional_release flow.
- Recovery: on `original_feat_not_found`, block fix_feature creation, escalate to manual review with missing ref detail.
- Completion signals: validation_state_read_done, settlement_computed_done, waivers_validated_done, gate_decision_made_done, milestone_mapped_done, fix_feature_created_done.

## Integration Points Snapshot

- Input sources: `.droid/state/validation-state.yaml`, `.droid/evidence/`, waiver references - read-only consumption.
- Output destination: `ssot/tests/gate/milestone-decisions/`, `ssot/feat/FIX-*.md` (for block outcomes).
- Downstream consumer: Fix Feature (if block) re-enters Mission Compiler (FEAT-003) as new execution unit.
- CLI invocation: invoked after Droid Runtime completes all workers and validators.

## TECH Contract Snapshot

- Gate evaluation is read-only against validation-state; no test re-execution.
- Settlement computation is deterministic: same inputs produce same outputs.
- Fix Feature is created as new document, never modifying original feat.
- Waiver requires explicit approval ref; auto-waiver is rejected.

## ARCH Constraint Snapshot

- Gate reads only from .droid/ state and evidence directories.
- Gate writes only to ssot/tests/gate/ and ssot/feat/FIX-*.
- Gate must not modify validation-state, evidence, or original feat documents.

## API Contract Snapshot

- `evaluate_gate`: input=`validation_state_ref`, `evidence_refs[]`, `waiver_refs[]`; output=`gate_decision_ref`, `settlement_report_ref`; errors=`validation_state_invalid`, `evidence_hash_mismatch`, `waiver_not_approved`.
- `map_milestone`: input=`gate_decision_ref`; output=`milestone_decision_ref`; errors=`gate_decision_invalid`, `milestone_mapping_undefined`.
- `create_fix_feature`: input=`gate_decision_ref`, `original_feat_ref`, `failed_items[]`; output=`fix_feature_ref`; errors=`gate_not_blocked`, `original_feat_not_found`, `failed_items_empty`.

## Embedded Execution Contract

### State Machine

- `validation_state_read` -> `settlement_computed` -> `waivers_validated` -> `gate_decision_made` -> `milestone_mapped` -> `fix_feature_created_if_blocked`
- `gate_decision_release` must never transition into `fix_feature_created`.

### API Contracts

- `evaluate_gate`: input=`validation_state_ref`, `evidence_refs[]`, `waiver_refs[]`; output=`gate_decision_ref`, `settlement_report_ref`; errors=`validation_state_invalid`, `evidence_hash_mismatch`, `waiver_not_approved`.
- `map_milestone`: input=`gate_decision_ref`; output=`milestone_decision_ref`; errors=`gate_decision_invalid`.
- `create_fix_feature`: input=`gate_decision_ref`, `original_feat_ref`, `failed_items[]`; output=`fix_feature_ref`; errors=`gate_not_blocked`.

### UI Entry

- N/A - gate evaluation is backend-only, no user-facing surface.

### UI Success Exit

- Gate decision recorded, milestone mapped, Fix Feature created if block.

### UI Failure Exit

- Validation-state invalid: return structured error listing missing or inconsistent fields.
- Evidence hash mismatch: return error listing coverage_ids with hash mismatches.
- Waiver not approved: reject auto-waiver, require explicit approval ref.

### Invariants

- Gate must not re-execute validation contracts.
- Gate decision is immutable once recorded.
- Fix Feature is always a new object, never a modification of original feat.
- Settlement is deterministic given same validation-state and waivers.

### Boundary Guardrails

- Boundary to Droid Runtime: Gate consumes validation-state but does not re-run workers or validators.
- Boundary to Mission Compiler: Fix Feature re-enters as new execution unit, not as modification of original.
- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not expand touch set beyond declared modules without re-derive.

## 5. Normative Constraints

### Normative / MUST

- Gate must not re-execute validation contracts.
- Gate decision must be immutable once recorded.
- Fix Feature must be a new object with fixes_for linkage.
- Waiver must have explicit approval ref.

### Informative / Context Only

- Dual-chain settlement serves as acceptance authority for this scope.

## 6. Implementation Requirements

### Touch Set / Module Plan

- `cli/lib/settlement_computer.py` [backend | new | existing_match] <- Coverage settlement statistics; nearby matches: cli/lib/fs.py, cli/lib/errors.py
- `cli/lib/gate_evaluator.py` [backend | new | existing_match] <- Core gate evaluation; nearby matches: cli/lib/errors.py, cli/lib/policy.py
- `cli/lib/milestone_mapper.py` [backend | new | existing_match] <- Gate-to-milestone mapping; nearby matches: cli/lib/errors.py, cli/lib/fs.py
- `cli/lib/fix_feature_creator.py` [backend | new | existing_match] <- Fix Feature creation; nearby matches: cli/lib/fs.py, cli/lib/errors.py

### Repo Touch Points

- `cli/lib/settlement_computer.py` [backend | new]
- `cli/lib/gate_evaluator.py` [backend | new]
- `cli/lib/milestone_mapper.py` [backend | new]
- `cli/lib/fix_feature_creator.py` [backend | new]

### Allowed

- Implement only the declared repo touch points.
- Wire gate logic within frozen TECH/ARCH/API boundaries.
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

- AC-001: Frozen touch set is implemented without design drift. -> The declared touch set is implemented: all 4 new backend modules. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. -> Evidence proves evaluate_gate produces valid gate decision and settlement report. Main sequence covers: validation-state read, settlement computed, waivers validated, gate decision made, milestone mapped. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`
- AC-003: Gate output is consumed by downstream Fix Feature routing without boundary violation. -> Fix Feature is created as new object with correct fixes_for linkage and failed item details. | mapping_status: `package_bound_gap` | mapped_test_units: `none` | mapped_to: `dual-chain-manifest-as-proxy`

### Acceptance-to-Task Mapping

- AC-001: Frozen touch set is implemented without design drift. | implemented_by: TASK-001 through TASK-004
- AC-002: Frozen contracts and runtime sequence execute through the implementation entry. | implemented_by: TASK-001, TASK-002, TASK-003
- AC-003: Gate output is consumed by downstream Fix Feature routing without boundary violation. | implemented_by: TASK-003, TASK-004

## 9. Execution Sequence

### Required

- 1. Freeze refs and repo touch points.
- 2. Implement settlement computer and gate evaluator.
- 3. Implement milestone mapper and Fix Feature creator.
- 4. Collect acceptance evidence and close delivery handoff.

### Suggested

- None.

### Ordered Task Breakdown

- TASK-001 Freeze refs and repo touch points | depends_on: none | parallel: none | touch_points: all 4 new backend modules | outputs: frozen upstream refs, repo-aware touch set | acceptance: none | done_when: The implementation package states exactly where coding may occur and which upstream refs remain authoritative.
- TASK-002 Implement settlement computer and gate evaluator | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/settlement_computer.py, cli/lib/gate_evaluator.py | outputs: settlement statistics, gate decision logic | acceptance: AC-002 | done_when: Gate evaluator reads validation-state, computes settlement, applies waivers, and makes deterministic gate decision.
- TASK-003 Implement milestone mapper and Fix Feature creator | depends_on: TASK-002 | parallel: none | touch_points: cli/lib/milestone_mapper.py, cli/lib/fix_feature_creator.py | outputs: milestone decisions, Fix Feature objects for block | acceptance: AC-002, AC-003 | done_when: Milestone mapping follows ADR-048 Section 2.5 exactly; Fix Feature created as new object with fixes_for linkage.
- TASK-004 Collect acceptance evidence and close delivery handoff | depends_on: TASK-003 | parallel: none | touch_points: none | outputs: acceptance evidence, handoff package | acceptance: AC-001, AC-002, AC-003 | done_when: Every acceptance check is backed by explicit evidence artifacts.

## 10. Risks and Notes

- Waiver approval workflow may need integration with external approval system -> gate evaluator checks for approval ref presence, not approval process itself.
- Fix Feature iteration limit (3 per ADR-048) must be enforced -> creator checks existing fix feature count for same original feat.
- Gate decision recording must be atomic and immutable -> use write-once file with hash verification.

## Completion Signals

- **validation_state_read_done**: Validation-state, evidence, and waiver references read successfully from .droid/ state.
- **settlement_computed_done**: Coverage settlement statistics computed: passed/failed/blocked/uncovered by chain and priority.
- **waivers_validated_done**: All waiver rules applied with explicit approval refs validated.
- **gate_decision_made_done**: Gate decision (release/conditional_release/block) computed deterministically.
- **milestone_mapped_done**: Gate decision mapped to milestone decision (passed/passed_with_waiver/failed) per ADR-048 Section 2.5.
- **fix_feature_created_done**: Fix Feature created as new object with fixes_for linkage and failed item details for block outcomes.
