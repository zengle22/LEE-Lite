---
id: IMPL-SRC-RAW-TO-SRC-ADR048-005
ssot_type: IMPL
title: "Governed Skill接入与Pilot验证流 Implementation Task Package"
status: execution_ready
feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-005
tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-001
api_ref: API-SRC-RAW-TO-SRC-ADR048-001
main_sequence:
  - step: 1
    task: TASK-001
    title: Define skill registration contract and validation rules
    depends_on: none
    done_when: All skill registration contracts and validation rules are explicit
  - step: 2
    task: TASK-002
    title: Implement skill onboarding pipeline with compatibility checks
    depends_on: TASK-001
    done_when: Skills can register and pass all compatibility validation
  - step: 3
    task: TASK-003
    title: Implement pilot execution framework and evidence collection
    depends_on: TASK-001, TASK-002
    done_when: Pilot runs produce structured evidence and acceptance data
  - step: 4
    task: TASK-004
    title: Wire cross-skill E2E validation and pilot reporting
    depends_on: TASK-002, TASK-003
    done_when: Cross-skill E2E tests pass and pilot reports are generated
  - step: 5
    task: TASK-005
    title: Collect acceptance evidence and close delivery handoff
    depends_on: TASK-004
    done_when: Every acceptance check backed by explicit evidence artifacts
implementation_units:
  - path: cli/lib/skill_registry.py
    type: backend
    action: extend
    purpose: Skill registration, validation, and contract enforcement
  - path: cli/lib/pilot_runner.py
    type: backend
    action: new
    purpose: Pilot execution framework with evidence collection
  - path: cli/lib/cross_skill_validation.py
    type: backend
    action: new
    purpose: Cross-skill E2E validation and compatibility checks
  - path: cli/commands/skill/command.py
    type: backend
    action: extend
    purpose: Skill management CLI entry points for registration and pilot
non_goals:
  - Does not redefine skill execution semantics
  - Does not handle gate decision or formal publication
  - Does not define FEAT/TECH derivation rules
  - Does not manage UI surface or user testing
implementation_readiness: true
---

# Governed Skill接入与Pilot验证流 Implementation Task Package

## Main Sequence Snapshot

- Step 1: TASK-001 Define skill registration contract | depends_on: none | done_when: All skill registration contracts and validation rules are explicit
- Step 2: TASK-002 Implement skill onboarding pipeline | depends_on: TASK-001 | done_when: Skills can register and pass all compatibility validation
- Step 3: TASK-003 Implement pilot execution framework | depends_on: TASK-001, TASK-002 | done_when: Pilot runs produce structured evidence and acceptance data
- Step 4: TASK-004 Wire cross-skill E2E validation | depends_on: TASK-002, TASK-003 | done_when: Cross-skill E2E tests pass and pilot reports are generated
- Step 5: TASK-005 Collect acceptance evidence | depends_on: TASK-004 | done_when: Every acceptance check backed by explicit evidence artifacts

## Implementation Unit Mapping Snapshot

- `cli/lib/skill_registry.py` [backend | extend | owned]: Skill registration, validation, and contract enforcement
- `cli/lib/pilot_runner.py` [backend | new | owned]: Pilot execution framework with evidence collection
- `cli/lib/cross_skill_validation.py` [backend | new | owned]: Cross-skill E2E validation and compatibility checks
- `cli/commands/skill/command.py` [backend | extend | owned]: Skill management CLI entry points for registration and pilot

## State Model Snapshot

- State transitions: `skill_registered` -> `onboarded` -> `pilot_ready` -> `pilot_passed` -> `production_done`
- Recovery: `registration_failed` -> reject with clear validation errors, allow retry
- Recovery: `onboarding_blocked` -> log blocking reason, require contract fix, then retry
- Recovery: `pilot_failed` -> collect evidence, route to fix-feature for pilot retry
- Completion signals: skill_registered_done, onboarded_done, pilot_passed_done, production_done
- Fail-closed behavior: if any recovery path exhausts retries, escalate to manual review

## Integration Points Snapshot

- Skill registration validates against contract before onboarding
- Pilot runner executes skills in controlled environment with evidence collection
- Cross-skill validation ensures E2E compatibility before production promotion
- Backward compat: legacy skills can register in compat mode with warnings

## Completion Signals

- **skill_registered_done**: skill registered and validated against contract successfully
- **onboarded_done**: skill onboarded and passing all compatibility checks completed
- **pilot_passed_done**: pilot execution completed with full evidence collected
- **production_done**: skill promoted to production after E2E validation passed

## Selected Upstream

- feat_ref: FEAT-SRC-RAW-TO-SRC-ADR048-005
- tech_ref: TECH-SRC-RAW-TO-SRC-ADR048-001
- arch_ref: ARCH-SRC-RAW-TO-SRC-ADR048-001
- api_ref: API-SRC-RAW-TO-SRC-ADR048-001
