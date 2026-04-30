# Discussion Log: Phase 27 (GSD Closure Verify)

## Decisions Made

### 2026-04-30 (Initial Setup)
1. **Verify Mode**: Flag to qa-test-run (not separate command)
   - Add `--verify-bugs` (boolean) and `--verify-mode` (targeted|full-suite)
   - Rationale: Reuse existing test orchestration infrastructure

2. **Audit Logging**: Centralized in transition_bug_status()
   - Move audit logging from gate_remediation.py to bug_registry.py
   - All state transitions automatically audited

3. **Shadow Fix Detection**: CLI + auto-check
   - `ll-bug-check-shadow` manual command
   - Automatic checks in existing commands like gate-evaluate

## Open Issues

None yet - all requirements are clearly defined in ADR-055.

## Notes

- Phase 25 (Bug Registry) and Phase 26 (Gate Integration) are already completed
- We have all the building blocks ready to implement Phase 27
