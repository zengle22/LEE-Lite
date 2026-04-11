# Supervisor Agent: ll-qa-gate-evaluate
## Validation Checklist
1. All input artifacts were read
2. API chain metrics correct
3. E2E chain metrics correct
4. All 7 anti-laziness checks evaluated
5. Pass rate excludes obsolete and approved waivers
6. Pending waivers counted as failed
7. No-evidence items not counted as executed
8. final_decision is pass/fail/conditional_pass
9. evidence_hash is valid SHA-256
10. decision_reason explains decision
