# E2E Journey Spec — JOURNEY-MAIN-001: 完整 Pilot 验证

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.pilot.happy |
| coverage_id | e2e.journey.pilot.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-008.AcceptanceChecks.real-pilot-chain |

## Test Contract

### Entry Point

`ll loop pilot-run --scope governed-skills --chain producer-consumer-audit-gate`

### Preconditions

- Onboarding scope and migration waves are defined
- Cutover/fallback rules are configured
- All skills in the pilot chain are available
- artifacts/jobs/ready directory is accessible

### User Steps

1. Operator executes `ll loop pilot-run` with governed-skills scope
2. System validates onboarding scope is within governed skill boundaries
3. System executes pilot chain: producer -> consumer -> audit -> gate
4. Producer generates test job into ready queue
5. Runner auto-consumes job (claim + running)
6. Runner dispatches to next skill
7. Skill executes and returns outcome
8. Outcome is written back (done)
9. Gate evaluates pilot result
10. System collects pilot evidence bound to full chain
11. System generates integration matrix and cutover decision report
12. Operator verifies complete pilot report

### Expected CLI States

- Step 2: "Onboarding scope validated: governed skills only"
- Step 3: "Pilot chain started: producer -> consumer -> audit -> gate"
- Step 4: "Producer: test job generated (job-pilot-001)"
- Step 5: "Runner: claimed and running job-pilot-001"
- Step 6: "Dispatch: job-pilot-001 -> next-skill"
- Step 7: "Skill execution: completed"
- Step 8: "Outcome: job-pilot-001 -> done"
- Step 9: "Gate evaluation: pilot passed"
- Step 10: "Pilot evidence collected: full chain bound"
- Step 11: "Integration matrix and cutover decision generated"
- Step 12: Report shows all chain steps succeeded with evidence

### Expected Network Events

- Scope validation: Read onboarding scope config
- Producer: Write test job to ready queue
- Runner: Claim + state update + dispatch
- Skill: Execute and write outcome
- Gate: Evaluate and write decision
- Evidence: Write pilot evidence files for each chain step
- Report: Generate integration matrix and cutover decision

### Expected Persistence

- Pilot chain job files (ready -> running -> done)
- Invocation records for each chain step
- Pilot evidence files bound to each step
- Integration matrix file
- Cutover decision report

### Anti-False-Pass Checks

- full_chain_executed (not component-only)
- evidence_bound_to_each_step
- no_manual_relay_involved
- no_third_session_relay
- cutover_decision_generated
- no_console_error

### Evidence Required

- pilot_chain_log (all steps)
- job_state_transitions
- invocation_records
- pilot_evidence_files
- integration_matrix_snapshot
- cutover_decision_report
