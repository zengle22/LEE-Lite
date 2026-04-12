---
id: API-SRC-RAW-TO-SRC-ADR048-004
ssot_type: API
title: API Contract - Droid Missions Runtime Interfaces
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-004
---

# API Contract - Droid Missions Runtime Interfaces

## execute_mission

- **input**: `features_json_ref`, `execution_manifest_ref`
- **output**: `validation_state_ref`, `evidence_refs[]`, `execution_log_ref`
- **errors**: `features_json_invalid`, `worker_timeout`, `evidence_collection_failed`, `validation_state_write_failed`
- **idempotent**: yes, by features_json_ref hash + execution_manifest_ref hash
- **precondition**: features.json and execution-manifest.yaml already produced by Mission Compiler

## validate_scrutiny

- **input**: `validation_state_ref`
- **output**: `scrutiny_report_ref`
- **errors**: `validation_state_missing`, `evidence_incomplete`, `contract_compliance_failed`
- **idempotent**: yes, by validation_state_ref hash
- **precondition**: validation-state already written by execute_mission

## validate_user_testing

- **input**: `validation_state_ref`
- **output**: `ux_validation_report_ref`
- **errors**: `validation_state_missing`, `ui_state_unverified`, `persistence_check_failed`
- **idempotent**: yes, by validation_state_ref hash
- **precondition**: validation-state already written by execute_mission
