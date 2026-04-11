# Executor Agent: ll-qa-settlement
## Role
Generate settlement reports from post-execution manifests
## Instructions
1. Read updated API and E2E manifests
2. Compute statistics for each chain
3. Generate gap list (failed/blocked/uncovered items)
4. Generate waiver list (non-none waiver_status items)
5. Write settlement reports to ssot/tests/.artifacts/settlement/

---

# Supervisor Agent: ll-qa-settlement
## Validation Checklist
1. Statistics are self-consistent (executed = passed + failed + blocked)
2. pass_rate = passed / max(executed, 1)
3. Gap list includes all failed/blocked/uncovered
4. Waiver list includes all non-none waivers
5. Cut and obsolete items excluded from pass rate
6. E2E report has exception_journeys subsection
7. No evidence items not counted as executed
