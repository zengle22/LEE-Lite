---
id: FEAT-SRC-RAW-TO-SRC-ADR048-003
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-003
epic_ref: EPIC-SRC-005-001
title: Mission Compiler - SSOT and Dual-Chain to Droid Features
status: frozen
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr048-mission-compiler-20260412-r1
candidate_package_ref: artifacts/epic-to-feat/adr048-mission-compiler-20260412-r1
frozen_at: '2026-04-12T00:00:00Z'
---

# Mission Compiler - SSOT and Dual-Chain to Droid Features

## Goal

Compile frozen SSOT (feat / prototype / tech / api) and dual-chain test assets (manifest + spec) into machine-consumable `features.json` and `execution-manifest.yaml` that Droid Missions Runtime can execute.

## Scope

- Define field-level mapping from SSOT objects to Droid `feature` objects.
- Define field-level mapping from API/E2E coverage manifest items to `validation-contract` assertions.
- Produce `features.json` with feature_id, feature_type, capabilities, validation_contracts, progression_mode.
- Produce `execution-manifest.yaml` with scheduling metadata and priority ordering.
- Support API chain and E2E chain compilation independently.

## Constraints

- Compiler must not invent business truth or design truth beyond frozen upstream.
- Mapping spec (ADR-048 Section 2.4) must be followed exactly for field-level mapping.
- Old testset objects must not be consumed as input.
- Output must be deterministic given the same frozen input.

## Acceptance Checks

1. features.json validation contracts match manifest items 1:1
   Then: every api_coverage_manifest item and e2e_coverage_manifest item produces exactly one validation-contract in features.json.
2. Field-level mapping is faithful to ADR-048 Section 2.4
   Then: coverage_id, feature_id, capability, endpoint, scenario_type, priority, dimensions_covered map correctly for API items; coverage_id, journey_id, journey_type, priority map correctly for E2E items.
3. execution-manifest.yaml schedules features by priority
   Then: P0 features are scheduled before P1, P1 before P2.
