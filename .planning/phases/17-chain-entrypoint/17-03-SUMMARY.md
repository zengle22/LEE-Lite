---
phase: "17"
plan: "03"
subsystem: "execution-axis"
tags: [ADR-054, SPEC_ADAPTER_COMPAT, test-orchestrator, ll-qa-test-run]
dependency_graph:
  requires:
    - "17-02"
  provides:
    - "test_orchestrator.py: run_spec_test() linear orchestration"
    - "test_exec_runtime.py: SPEC_ADAPTER_COMPAT branch"
    - "ll-qa-test-run skill"
tech_stack:
  added:
    - "cli/lib/test_orchestrator.py"
    - "skills/ll-qa-test-run/"
key_files:
  created:
    - "cli/lib/test_orchestrator.py"
    - "skills/ll-qa-test-run/SKILL.md"
    - "skills/ll-qa-test-run/ll.contract.yaml"
    - "skills/ll-qa-test-run/input/contract.yaml"
    - "skills/ll-qa-test-run/output/contract.yaml"
    - "skills/ll-qa-test-run/scripts/run.sh"
    - "skills/ll-qa-test-run/scripts/validate_input.sh"
    - "skills/ll-qa-test-run/scripts/validate_output.sh"
    - "skills/ll-qa-test-run/resources/examples/run.example.md"
  modified:
    - "cli/lib/test_exec_runtime.py"
    - "cli/commands/skill/command.py"
decisions: []
metrics:
  duration: "~5 minutes"
  completed: "2026-04-24"
---

# Phase 17 Plan 03: Execution Axis Integration - Summary

## One-liner

Linear test orchestration (env provision, spec adapter, exec, manifest update) with StepResult passing, SPEC_ADAPTER_COMPAT support, and ll-qa-test-run CLI skill registration.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|-------|-------|
| 1 | Create test_orchestrator.py | 7509049 | cli/lib/test_orchestrator.py |
| 2 | Modify test_exec_runtime.py for SPEC_ADAPTER_COMPAT | 9188adc | cli/lib/test_exec_runtime.py |
| 3 | Create ll-qa-test-run skill | f3b0e8f | skills/ll-qa-test-run/* |
| 4 | Register qa-test-run in CLI command.py | e729e46 | cli/commands/skill/command.py |

## What Was Built

### Task 1: test_orchestrator.py
Linear 4-step orchestration per ADR-054 §2.5:
- **Step 1**: `provision_environment()` - generates `ssot/environments/ENV-{id}.yaml`
- **Step 2**: `spec_to_testset()` - generates `ssot/tests/.spec-adapter/{id}.yaml` (SPEC_ADAPTER_COMPAT)
- **Step 3**: `execute_test_exec_skill()` - test execution via test_exec_runtime
- **Step 4**: `update_manifest()` - optimistic lock manifest update

`run_spec_test()` returns `StepResult` dataclass with `run_id`, `execution_refs`, `case_results`, and `manifest_items` for Step 4 data passing.

`--resume` support filters test_units to only include failed coverage_ids from last run (ADR-054 §5.1 R-7).

### Task 2: SPEC_ADAPTER_COMPAT Branch
Modified `_validate_testset_execution_boundary()` to accept both:
- `TESTSET` - existing branch preserved for backward compatibility
- `SPEC_ADAPTER_COMPAT` - new branch validating test_units list and feat_ref/prototype_ref presence

### Task 3: ll-qa-test-run Skill
CLI skill structure per ADR-054 §2.6:
- `SKILL.md` - user-facing CLI documentation
- `ll.contract.yaml` - skill metadata
- `input/contract.yaml` / `output/contract.yaml` - I/O contracts
- `scripts/run.sh` - calls `test_orchestrator.run_spec_test()`
- `scripts/validate_input.sh` / `validate_output.sh` - validation scripts
- `resources/examples/run.example.md` - usage examples

### Task 4: CLI Registration
Added `qa-test-run` to action whitelist in `cli/commands/skill/command.py` with handler block that calls `test_orchestrator.run_spec_test()` with parameters from payload.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface

| Flag | File | Description |
|------|------|-------------|
| threat_flag: data-integrity | test_orchestrator.py | Manifest optimistic locking prevents concurrent modification (ADR-054 R-5) |

## Verification

- [x] `test_orchestrator` imports successfully
- [x] `test_exec_runtime` with SPEC_ADAPTER_COMPAT imports successfully
- [x] `CLI command.py` with qa-test-run imports successfully
- [x] ll-qa-test-run skill files exist
- [x] All tasks committed individually

## Commits

- `7509049`: feat(phase-17-03): add test_orchestrator with linear 4-step orchestration
- `9188adc`: feat(phase-17-03): add SPEC_ADAPTER_COMPAT branch in _validate_testset_execution_boundary
- `f3b0e8f`: feat(phase-17-03): create ll-qa-test-run skill
- `e729e46`: feat(phase-17-03): register qa-test-run action in CLI command.py
