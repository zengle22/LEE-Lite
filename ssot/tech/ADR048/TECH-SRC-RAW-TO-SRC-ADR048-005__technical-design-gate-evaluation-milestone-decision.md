---
id: TECH-SRC-RAW-TO-SRC-ADR048-005
ssot_type: TECH
title: Technical Design - Gate Evaluation and Milestone Decision
status: frozen
schema_version: 1.0.0
derived_from: FEAT-SRC-RAW-TO-SRC-ADR048-005
---

# Technical Design - Gate Evaluation and Milestone Decision

## Design Summary

Implement a gate evaluation component that reads validation-state and evidence from Droid Runtime, computes settlement statistics, applies waiver rules, makes gate decisions, maps to milestone decisions, and creates Fix Features for block outcomes.

## Runtime Carriers

- `cli/lib/gate_evaluator.py` (new): reads validation-state, evidence, waivers; computes settlement; makes gate decision.
- `cli/lib/milestone_mapper.py` (new): maps gate decision to milestone decision (passed/passed_with_waiver/failed).
- `cli/lib/fix_feature_creator.py` (new): creates Fix Feature objects for block outcomes with fixes_for linkage.
- `cli/lib/settlement_computer.py` (new): counts passed/failed/blocked/uncovered items by chain and priority.

## Key Design Decisions

- Gate evaluation is read-only against validation-state; it never re-executes tests.
- Settlement computation is deterministic: same validation-state + waivers = same gate decision.
- Fix Feature is written to ssot/feat/ as a new document with FIX- prefix.
- Milestone decision is written to ssot/tests/gate/milestone-decisions/ with timestamp.
- Waiver validation checks for explicit approval ref; auto-waiver is rejected.

## Interface Contracts

- `evaluate_gate(validation_state_ref, evidence_refs[], waiver_refs[]) -> gate_decision_ref`
- `map_milestone(gate_decision_ref) -> milestone_decision_ref`
- `create_fix_feature(gate_decision_ref, original_feat_ref) -> fix_feature_ref`
- Error handling: invalid validation-state produces `validation_state_invalid` error.
