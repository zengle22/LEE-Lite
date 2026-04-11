# Executor Agent: ll-qa-gate-evaluate
## Role
Execute gate evaluation and generate release_gate_input.yaml
## Instructions
1. Read all 5 input artifacts (API manifest, E2E manifest, API settlement, E2E settlement, waivers)
2. Compute API chain metrics (total, passed, failed, blocked, uncovered, pass_rate)
3. Compute E2E chain metrics (same + exception_journeys_executed)
4. Apply 7 anti-laziness checks
5. Generate gate decision (pass/fail/conditional_pass)
6. Compute evidence_hash (SHA-256)
7. Write release_gate_input.yaml to ssot/tests/.artifacts/tests/settlement/

---

# Supervisor Agent: ll-qa-gate-evaluate
## Validation Checklist
1. All 5 input artifacts were read
2. API chain metrics are correct
3. E2E chain metrics are correct
4. All 7 anti-laziness checks evaluated
5. Pass rate excludes obsolete and approved waivers
6. Pending waivers counted as failed
7. No-evidence items not counted as executed
8. final_decision is one of: pass, fail, conditional_pass
9. evidence_hash is valid SHA-256
10. decision_reason explains the decision
