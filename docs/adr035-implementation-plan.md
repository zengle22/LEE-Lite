# ADR-035 Implementation Plan

## Scope

This document defines the implementation plan for [ADR-035](E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-035-TESTSET%20驱动的需求覆盖型%20Test%20Case%20Expansion%20基线.MD).

The target state is:

- `TESTSET` is the stable test-design contract.
- `test-exec-*` expands `TESTSET` into traceable functional test cases.
- Coverage remains a reference metric unless explicit qualification mode is requested.

## Goals

1. Freeze `TESTSET` contracts for typed functional coverage.
2. Generate richer `TESTSET` artifacts from `feat-to-testset`.
3. Refactor `test-exec-cli` so the main path is case expansion and execution, not coverage convergence.
4. Validate the change set with unit tests and an ADR018 replay.

## Phase 0

Documentation freeze:

- Align ADR-007, ADR-012, and ADR-035.
- Keep qualification as an enhancement path.

Success criteria:

- No contradictory language remains across the ADRs.

## Phase 1A

Freeze upstream `TESTSET` schema and contracts.

Files:

- `skills/ll-qa-feat-to-testset/input/contract.yaml`
- `skills/ll-qa-feat-to-testset/output/contract.yaml`
- `skills/ll-qa-feat-to-testset/output/test-set.schema.json`
- `skills/ll-qa-feat-to-testset/SKILL.md`

Add or formalize:

- `functional_areas`
- `logic_dimensions`
- `state_model`
- `coverage_matrix`

Constraints:

- `functional_areas` must be typed objects.
- `logic_dimensions` must be layered as `universal`, `stateful`, `control_surface`.
- `state_model` must support transitions and guarded actions.
- `coverage_matrix` means requirement coverage, not code coverage.

Compatibility:

- Keep `coverage_goal`, `branch_families`, `expansion_hints`, `qualification_expectation`, `qualification_budget`, and `max_expansion_rounds` as optional enhancement fields.

## Phase 1B

Implement upstream derivation.

Files:

- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_derivation.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_units.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_semantics.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_profiles.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_review.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_candidate.py`
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_support.py`

Add derivation helpers for:

- `functional_areas`
- `logic_dimensions`
- `state_model`
- `coverage_matrix`

Upgrade `test_units` so each unit carries:

- `functional_area_key`
- `case_family`
- `logic_dimensions`
- `acceptance_refs`
- `risk_refs`
- `boundary_checks`

## Phase 2A

Freeze `test-exec-cli` contracts.

Files:

- `skills/ll-test-exec-cli/input/contract.yaml`
- `skills/ll-test-exec-cli/output/contract.yaml`
- `skills/ll-test-exec-cli/input/schema.json`
- `skills/ll-test-exec-cli/output/schema.json`
- `skills/ll-test-exec-cli/SKILL.md`

Contract changes:

- Main path consumes `functional_areas`, `logic_dimensions`, `state_model`, and `coverage_matrix`.
- Main path produces traceable `TestCasePack`.
- Coverage is reported but does not drive the default execution flow.

## Phase 2B

Implement case expansion and traceability.

New modules:

- `cli/lib/test_exec_case_expander.py`
- `cli/lib/test_exec_traceability.py`

Responsibilities:

- Expand `TESTSET + ResolvedSSOTContext` into traceable cases.
- Attach:
  - `functional_area`
  - `case_family`
  - `logic_dimension`
  - `acceptance_traceability`
  - `risk_traceability`

## Phase 2C

Implement fixture planning and script mapping.

New modules:

- `cli/lib/test_exec_fixture_planner.py`
- `cli/lib/test_exec_script_mapper.py`

Responsibilities:

- Map case families to executable preconditions.
- Map case families to reusable CLI execution templates.

## Phase 2D

Refactor runtime orchestration.

Files:

- `cli/lib/test_exec_runtime.py`
- `cli/lib/test_exec_execution.py`
- `cli/lib/test_exec_artifacts.py`
- `cli/lib/test_exec_reporting.py`

Main flow:

1. Resolve context.
2. Expand cases.
3. Plan fixtures.
4. Map scripts.
5. Execute.
6. Build traceable report.
7. Emit coverage as appendix data.

Qualification remains behind an explicit mode switch.

## Phase 3

Testing and migration.

Existing tests to extend:

- `tests/unit/test_lee_qa_feat_to_testset.py`
- `tests/unit/support_feat_to_testset.py`
- `tests/unit/test_cli_skill_test_exec.py`
- `tests/unit/_test_exec_skill_support.py`
- `tests/unit/test_web_skill_test_exec.py`

New tests:

- `tests/unit/test_test_exec_case_expander.py`
- `tests/unit/test_test_exec_fixture_planner.py`
- `tests/unit/test_test_exec_script_mapper.py`

Validation order:

1. Schema validation.
2. Derivation tests.
3. Case expander tests.
4. Fixture and script mapper tests.
5. ADR018 canary replay.

## ADR018 Canary

Run:

- One smoke path
- One qualification path

Verify:

- The same `TESTSET` produces a traceable `TestCasePack`
- Execution still succeeds
- Report structure emphasizes functional and acceptance coverage first

## Risks

- Qualification logic reshapes the main object model again.
- `functional_areas` remain weak text labels.
- `logic_dimensions` stay flat and ambiguous.
- Traceability only appears in reports, not contracts.
- Implementation overfits ADR018 and still needs ad hoc harnesses.

## Acceptance Criteria

The implementation is complete when:

1. New `TESTSET`s include the ADR-035 contracts.
2. `test-exec-cli` expands traceable cases in the default path.
3. Reports show functional coverage and traceability first.
4. Existing ADR018 replays still work.
5. Unit and replay validation pass.
