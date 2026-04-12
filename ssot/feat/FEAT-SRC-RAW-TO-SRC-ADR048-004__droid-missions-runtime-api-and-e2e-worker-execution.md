---
id: FEAT-SRC-RAW-TO-SRC-ADR048-004
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-004
epic_ref: EPIC-SRC-005-001
title: Droid Missions Runtime - API and E2E Worker Execution
status: frozen
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr048-droid-runtime-20260412-r1
candidate_package_ref: artifacts/epic-to-feat/adr048-droid-runtime-20260412-r1
frozen_at: '2026-04-12T00:00:00Z'
---

# Droid Missions Runtime - API and E2E Worker Execution

## Goal

Implement the Droid Missions Runtime that consumes compiled features.json and execution-manifest.yaml, executes validation contracts via API/E2E workers, collects evidence, writes validation-state, and integrates Scrutiny-Validator and User-Testing-Validator for post-execution checks.

## Scope

- Implement API Worker that reads validation-contracts from features.json and executes assertions.
- Implement E2E Worker that executes user journey validation with UI state, network event, and persistence checks.
- Implement evidence collection satisfying evidence_required declarations per contract.
- Implement validation-state writeback with evidence hash binding.
- Implement Scrutiny-Validator for evidence completeness and contract compliance.
- Implement User-Testing-Validator for E2E UX completeness checks.

## Constraints

- Workers must not decide what to test or skip beyond what validation-contract declares.
- Workers must not modify spec assertions or evidence requirements.
- Workers must not skip anti_false_pass_checks.
- Workers must not mark passed without collecting all required evidence.
- Evidence collection must produce verifiable hashes bound to execution logs.

## Acceptance Checks

1. API Worker executes all validation-contract assertions for API-type features
   Then: every assertion in each API validation-contract is executed with evidence collected per evidence_required declaration.
2. E2E Worker executes user journey validation with all required checks
   Then: expected_ui_states, expected_network_events, expected_persistence, and anti_false_pass_checks are all verified per E2E contract.
3. validation-state is consistent with lifecycle_status and evidence_status
   Then: lifecycle_status=passed implies evidence_status=complete with valid evidence hash.
