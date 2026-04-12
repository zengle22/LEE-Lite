# E2E Journey Spec — JOURNEY-MAIN-001: 自动派发

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.dispatch.happy |
| coverage_id | e2e.journey.dispatch.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-005.AcceptanceChecks.declared-next-skill |

## Test Contract

### Entry Point

Automatic: Runner dispatching a claimed job with progression_mode=auto-continue

### Preconditions

- Job `job-ready-001` is in running state (already claimed by runner)
- Job has progression_mode = "auto-continue"
- Target next skill exists and is accessible
- Authoritative input refs are all valid and reachable

### User Steps

1. Runner detects claimed job with auto-continue progression mode
2. System validates progression_mode allows auto-dispatch
3. System validates authoritative input refs are accessible
4. System invokes next skill with input package
5. System records invocation with upstream refs and target-skill lineage
6. Downstream skill begins execution
7. Operator verifies invocation record exists with complete refs

### Expected CLI States

- Step 2: Runner log: "Progression mode: auto-continue -> auto-dispatch allowed"
- Step 3: Runner log: "Input refs validated: all accessible"
- Step 4: Runner log: "Dispatching job job-ready-001 to skills/l3/ll-next-skill/"
- Step 5: Runner log: "Invocation recorded: invocation-{id}"
- Step 7: `cat invocation-{id}.json` shows complete refs and lineage

### Expected Network Events

- Job state read: Read job-ready-001 to check progression_mode
- Input refs validation: Read all referenced files
- Skill invocation: Invoke target skill with input package
- Invocation record write: Write invocation metadata
- Lineage record write: Write upstream refs and target lineage

### Expected Persistence

- Invocation record file exists with job_id, target_skill, input_refs
- Lineage record file with upstream_refs, job_refs, target_skill_lineage
- Job state remains "running" (until outcome is written back)

### Anti-False-Pass Checks

- invocation_file_exists
- invocation_contains_correct_target_skill
- lineage_refs_match_upstream
- input_refs_all_validated
- no_silent_dispatch_failure
- job_state_unchanged (still running, not completed or failed)

### Evidence Required

- runner_dispatch_log
- invocation_file_snapshot
- lineage_file_snapshot
- input_refs_validation_log
- job_state_file
- target_skill_start_confirmation
