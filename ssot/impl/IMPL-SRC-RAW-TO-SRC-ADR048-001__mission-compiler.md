---
id: IMPL-SRC-RAW-TO-SRC-ADR048-001
ssot_type: IMPL
impl_ref: IMPL-SRC-RAW-TO-SRC-ADR048-001
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
title: Mission Compiler Implementation Task Package
status: execution_ready
implementation_readiness: ready
main_sequence:
  - step: 1
    task: TASK-001
    title: Define compiler input parser for SSOT documents and dual-chain manifests
    depends_on: none
    done_when: Compiler can read frozen feat/prototype/api docs and coverage manifests
  - step: 2
    task: TASK-002
    title: Implement SSOT-to-Droid feature field mapping per ADR-048 Section 2.4
    depends_on: TASK-001
    done_when: SSOT objects map correctly to Droid feature objects with all required fields
  - step: 3
    task: TASK-003
    title: Implement dual-chain-to-validation-contract mapping with spec assertion linking
    depends_on: TASK-001, TASK-002
    done_when: API/E2E coverage items map 1:1 to validation-contract assertions
  - step: 4
    task: TASK-004
    title: Implement features.json output with deterministic serialization
    depends_on: TASK-002, TASK-003
    done_when: features.json is valid, deterministic, and contains all required fields
  - step: 5
    task: TASK-005
    title: Implement execution-manifest.yaml with priority-ordered scheduling metadata
    depends_on: TASK-004
    done_when: execution-manifest.yaml schedules P0 before P1 before P2
  - step: 6
    task: TASK-006
    title: Integrate with skill_invoker.py and ready_job_dispatch.py
    depends_on: TASK-005
    done_when: Compiler is callable via target_skill workflow.adr048.mission-compiler
non_goals:
  - Does not execute any tests or validations
  - Does not modify SSOT source documents
  - Does not define Droid runtime execution semantics
  - Does not make gate decisions
  - Does not consume old testset objects
---

# Mission Compiler Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Define compiler input parser | depends_on: none | done_when: Compiler can read frozen SSOT docs and coverage manifests
- Step 2: TASK-002 Implement SSOT-to-Droid feature field mapping | depends_on: TASK-001 | done_when: SSOT objects map correctly to Droid features
- Step 3: TASK-003 Implement dual-chain-to-validation-contract mapping | depends_on: TASK-001, TASK-002 | done_when: Coverage items map 1:1 to validation-contract assertions
- Step 4: TASK-004 Implement features.json output | depends_on: TASK-002, TASK-003 | done_when: features.json is valid, deterministic, complete
- Step 5: TASK-005 Implement execution-manifest.yaml | depends_on: TASK-004 | done_when: Priority-ordered scheduling metadata is correct
- Step 6: TASK-006 Integrate with job dispatcher | depends_on: TASK-005 | done_when: Compiler callable via target_skill

## Implementation Unit Mapping

- `cli/lib/mission_compiler.py` [backend | new | owned]: Core compiler orchestrator reading frozen SSOT + dual-chain assets
- `cli/lib/ssot_mapper.py` [backend | new | owned]: SSOT-to-Droid feature field mapping per ADR-048 Section 2.4
- `cli/lib/contract_compiler.py` [backend | new | owned]: Dual-chain coverage manifest to validation-contract mapping
- `cli/lib/execution_manifest.py` [backend | new | owned]: Priority-ordered execution-manifest.yaml generation
- `cli/lib/skill_invoker.py` [backend | extend | owned]: Add `workflow.adr048.mission-compiler` dispatch branch
- `cli/lib/ready_job_dispatch.py` [backend | extend | owned]: Add job creation logic for downstream Droid Runtime dispatch

## State Model

- State transitions: `compiler_idle` -> `compilation_started` -> `features_compiled` -> `manifest_generated`
- Recovery: `compilation_failed` -> log failure reason, wait for upstream fix, then retry
- Completion signals: compilation_started_done, features_compiled_done, manifest_generated_done
- Failure signals: compilation_failed
- Fail-closed: compilation failure produces no features.json, does not trigger downstream jobs

## Integration Points

- Invoked by Droid Job Runner via `target_skill: "workflow.adr048.mission-compiler"`
- Reads frozen SSOT docs from `ssot/feat/`, `ssot/prototype/`, `ssot/api/`
- Reads dual-chain assets from `ssot/tests/api/`, `ssot/tests/e2e/`
- Outputs `ssot/tests/compiled/features.json` and `ssot/tests/compiled/execution-manifest.yaml`
- Downstream: triggers ready_job_dispatch.py to create Droid Runtime Job

## Selected Upstream

- feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-001
