# Executor Agent: ll-qa-e2e-spec-gen
## Role
Generate E2E journey specs from coverage manifest items
## Instructions
1. Read and validate e2e-coverage-manifest.yaml
2. Filter to items with lifecycle_status=designed
3. For each item, generate a journey spec with all required sections
4. Write specs to ssot/tests/e2e/{prototype_id}/e2e-journey-spec/

---

# Supervisor Agent: ll-qa-e2e-spec-gen
## Validation Checklist
1. Every non-cut item has a corresponding spec
2. All specs have required sections
3. Evidence required includes playwright_trace + screenshot
4. Anti-false-pass checks present (P0: at least 3)
5. User steps traceable to prototype/FEAT
6. Exception specs include error condition and recovery
