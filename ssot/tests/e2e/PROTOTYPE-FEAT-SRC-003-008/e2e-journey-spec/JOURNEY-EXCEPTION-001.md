# E2E Journey Spec — JOURNEY-EXCEPTION-001: 仅组件级测试

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.component-only |
| coverage_id | e2e.journey.exception.component-only |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-003-008.Constraints.no-component-only |

## Test Contract

### Entry Point

`ll loop pilot-run --mode component-test` (or equivalent component-only mode)

### Preconditions

- Onboarding scope is defined
- Pilot chain configuration exists
- Individual component tests are available

### User Steps

1. Operator attempts to run pilot chain in component-test mode only
2. System detects chain type is component-test (not real end-to-end)
3. System returns COMPONENT_TEST_ONLY_REJECTED error
4. System explains requirement for real end-to-end chain
5. Pilot is NOT marked as passed (remains pending)
6. Operator sees guidance for executing real chain

### Expected CLI States

- Step 3: CLI outputs "Error: COMPONENT_TEST_ONLY_REJECTED - Pilot must verify through a real end-to-end chain. Component-level tests are insufficient."
- Step 4: CLI outputs "Required: producer -> consumer -> audit -> gate full chain execution"
- Step 4: Exit code != 0
- Step 5: Pilot status remains "pending"
- Step 6: Output includes `ll loop pilot-run --chain producer-consumer-audit-gate`

### Expected Network Events

- Chain type check: Validate pilot mode
- No chain execution
- No pilot evidence collection
- Audit log: Record rejected component-only attempt

### Expected Persistence

- No pilot evidence files created
- Pilot status unchanged (pending)
- No cutover decision generated
- Audit log records the rejection

### Anti-False-Pass Checks

- no_chain_executed
- pilot_status_pending (not passed)
- no_cutover_decision
- error_message_explains_requirement
- exit_code_nonzero
- audit_log_has_rejection

### Evidence Required

- cli_output_log
- exit_code_capture
- pilot_status_check (still pending)
- no_evidence_files_created
- audit_log_entry
