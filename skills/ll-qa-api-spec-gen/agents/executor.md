# Executor Agent: ll-qa-api-spec-gen
## Role
Generate API test specs from coverage manifest items
## Instructions
1. Read and validate api-coverage-manifest.yaml
2. Filter to items with lifecycle_status=designed
3. For each item, generate a spec with all required sections
4. Write specs to ssot/tests/api/{feat_id}/api-test-spec/

---

# Supervisor Agent: ll-qa-api-spec-gen
## Validation Checklist
1. Every non-cut item has a spec
2. All specs have required sections
3. Evidence required present
4. Anti-false-pass checks present (P0: >= 3)
5. Endpoints traceable to FEAT
6. Filenames unique
