---
id: API-SRC-RAW-TO-SRC-ADR048-003
ssot_type: API
title: API Contract - Mission Compiler Interfaces
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-003
---

# API Contract - Mission Compiler Interfaces

## compile_features

- **input**: `feat_refs[]`, `prototype_refs[]`, `api_manifest_refs[]`, `e2e_manifest_refs[]`, `api_spec_refs[]`, `e2e_spec_refs[]`
- **output**: `features_json_ref`, `compilation_report_ref`
- **errors**: `manifest_item_unmapped`, `spec_coverage_missing`, `feat_not_frozen`
- **idempotent**: yes, by input ref hash
- **precondition**: all input refs resolve to frozen documents

## compile_execution_manifest

- **input**: `features_json_ref`
- **output**: `execution_manifest_ref`, `scheduling_report_ref`
- **errors**: `features_json_invalid`, `priority_ordering_conflict`
- **idempotent**: yes, by features_json_ref hash
- **precondition**: features.json already produced by compile_features
