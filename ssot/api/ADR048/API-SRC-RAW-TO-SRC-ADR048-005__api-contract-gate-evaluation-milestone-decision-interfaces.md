---
id: API-SRC-RAW-TO-SRC-ADR048-005
ssot_type: API
title: API Contract - Gate Evaluation and Milestone Decision Interfaces
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-005
---

# API Contract - Gate Evaluation and Milestone Decision Interfaces

## evaluate_gate

- **input**: `validation_state_ref`, `evidence_refs[]`, `waiver_refs[]`
- **output**: `gate_decision_ref`, `settlement_report_ref`
- **errors**: `validation_state_invalid`, `evidence_hash_mismatch`, `waiver_not_approved`
- **idempotent**: yes, by validation_state_ref hash + waiver_refs hash
- **precondition**: validation-state and evidence already produced by Droid Runtime

## map_milestone

- **input**: `gate_decision_ref`
- **output**: `milestone_decision_ref`
- **errors**: `gate_decision_invalid`, `milestone_mapping_undefined`
- **idempotent**: yes, by gate_decision_ref hash
- **precondition**: gate decision already recorded by evaluate_gate

## create_fix_feature

- **input**: `gate_decision_ref`, `original_feat_ref`, `failed_items[]`
- **output**: `fix_feature_ref`
- **errors**: `gate_not_blocked`, `original_feat_not_found`, `failed_items_empty`
- **idempotent**: yes, by gate_decision_ref hash + original_feat_ref hash
- **precondition**: gate decision is block, failed items are non-empty
