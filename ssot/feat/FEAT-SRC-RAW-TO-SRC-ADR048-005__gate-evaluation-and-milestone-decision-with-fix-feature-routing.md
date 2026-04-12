---
id: FEAT-SRC-RAW-TO-SRC-ADR048-005
ssot_type: FEAT
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-005
epic_ref: EPIC-SRC-005-001
title: Gate Evaluation and Milestone Decision with Fix Feature Routing
status: frozen
schema_version: 1.0.0
workflow_key: product.epic-to-feat
workflow_run_id: adr048-gate-eval-20260412-r1
candidate_package_ref: artifacts/epic-to-feat/adr048-gate-eval-20260412-r1
frozen_at: '2026-04-12T00:00:00Z'
---

# Gate Evaluation and Milestone Decision with Fix Feature Routing

## Goal

Implement the Gate evaluation layer that consumes validation-state and evidence from Droid Runtime, evaluates coverage settlement against waiver and priority rules, maps gate decisions to milestone decisions (release/conditional_release/block), and routes block outcomes to Fix Feature creation for closed-loop remediation.

## Scope

- Implement Gate evaluator that reads validation-state, evidence, and waiver references.
- Implement settlement computation: count passed/failed/blocked/uncovered items by chain (API/E2E) and priority (P0/P1/P2).
- Implement gate decision logic: release (all required items pass), conditional_release (failures have approved waivers), block (unwaived P0/P1 failures).
- Implement milestone decision mapping: gate decision -> milestone.passed/passed_with_waiver/failed.
- Implement Fix Feature creation for block outcomes: new feature referencing failed coverage items, with fixes_for linkage.
- Implement milestone decision recording to ssot/tests/gate/milestone-decisions/.

## Constraints

- Gate must not re-execute validation contracts; it only evaluates collected evidence.
- Gate must not modify original feat or validation-state.
- Fix Feature must be created as a new object, never by modifying the original feat.
- Gate decision is an immutable historical fact once recorded.
- Waiver must have explicit approval ref; auto-waiver is not permitted.

## Acceptance Checks

1. Gate decision correctly reflects settlement state
   Then: release when all P0/P1 items pass, conditional_release when failures have approved waivers, block when unwaived P0/P1 failures exist.
2. Milestone decision maps correctly from gate decision
   Then: release -> milestone.passed, conditional_release -> milestone.passed_with_waiver, block -> milestone.failed with fix_feature_ids.
3. Fix Feature is created as new object for block outcomes
   Then: Fix Feature has fixes_for pointing to original feat, includes failed coverage items, and enters Mission Compiler as new execution unit.
