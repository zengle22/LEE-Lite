---
id: TECH-SRC-RAW-TO-SRC-ADR048-004
ssot_type: TECH
title: Technical Design - Droid Missions Runtime
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-004
---

# Technical Design - Droid Missions Runtime

## Design Summary

Implement a worker-based runtime that consumes compiled features.json, dispatches validation-contract assertions to API/E2E workers, collects evidence, and writes structured validation-state with evidence hash binding.

## Runtime Carriers

- `cli/lib/droid_runtime.py` (new): core runtime orchestrator, reads features.json, dispatches workers by priority.
- `cli/lib/api_worker.py` (new): executes API validation-contract assertions, collects request/response snapshots and DB assertion results.
- `cli/lib/e2e_worker.py` (new): executes E2E validation-contract assertions, collects UI state screenshots, network logs, persistence checks.
- `cli/lib/evidence_collector.py` (new): structured evidence collection with hash generation and log binding.
- `cli/lib/validation_state_writer.py` (new): writes validation-state with lifecycle_status, evidence_status, and evidence_hash.
- `cli/lib/scrutiny_validator.py` (new): verifies evidence completeness, contract compliance, anti-false-pass checks.
- `cli/lib/user_testing_validator.py` (new): verifies E2E UX completeness including UI states, network events, persistence.

## Key Design Decisions

- Workers are dispatched in P0 -> P1 -> P2 priority order from execution-manifest.yaml.
- Evidence is stored per coverage_id under .droid/evidence/{chain}/{coverage_id}/.
- validation-state is written to .droid/state/validation-state.yaml after each worker completion.
- Scrutiny-Validator and User-TestingValidator run as post-execution checks, not inline with workers.

## Interface Contracts

- `execute_mission(features_json_ref, execution_manifest_ref) -> validation_state_ref, evidence_refs[]`
- `validate_scrutiny(validation_state_ref) -> scrutiny_report_ref`
- `validate_user_testing(validation_state_ref) -> ux_validation_report_ref`
- Error handling: worker timeout produces `execution_timeout` error with partial evidence preserved.
