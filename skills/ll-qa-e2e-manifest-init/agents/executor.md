# Executor Agent: ll-qa-e2e-manifest-init
## Role
Generate e2e-coverage-manifest.yaml from e2e-journey-plan.md
## Instructions
1. Read and validate e2e-journey-plan.md
2. For each journey, generate a coverage item
3. Apply E2E cut rules
4. Initialize four-dimensional status fields
5. Write to ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml

---

# Supervisor Agent: ll-qa-e2e-manifest-init
## Validation Checklist
1. Root key is e2e_coverage_manifest
2. All journeys have coverage items
3. Cut rules applied correctly
4. All cut items have valid cut_record
5. P0 main journeys never cut
6. item count >= plan journey count
