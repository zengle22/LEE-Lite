---
id: TECH-SRC-RAW-TO-SRC-ADR048-003
ssot_type: TECH
title: Technical Design - Mission Compiler
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-003
---

# Technical Design - Mission Compiler

## Design Summary

Implement a CLI-invoked compiler that reads frozen SSOT and dual-chain test assets, applies field-level mapping per ADR-048 Section 2.4, and outputs structured `features.json` and `execution-manifest.yaml`.

## Runtime Carriers

- `cli/lib/mission_compiler.py` (new): core compiler logic
- `cli/lib/feature_mapping.py` (new): field-level mapping from SSOT to Droid feature
- `cli/lib/validation_contract_builder.py` (new): builds validation-contract assertions from manifest items and specs
- `cli/lib/execution_manifest_builder.py` (new): builds execution-manifest.yaml with scheduling metadata

## Key Design Decisions

- Input sources are resolved via `ssot/` directory tree lookup, not hardcoded paths.
- Mapping functions are pure: same input produces same output.
- Validation contracts reference source spec documents by relative path within ssot/tests/.
- The compiler does not execute tests; it only produces the execution plan.

## Interface Contracts

- `compile_features(feat_refs, prototype_refs, manifest_refs, spec_refs) -> features.json`
- `compile_execution_manifest(features) -> execution-manifest.yaml`
- Error handling: missing manifest item referenced by spec produces `mapping_gap` warning, not failure.
