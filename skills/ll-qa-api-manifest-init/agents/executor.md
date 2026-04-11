# Executor Agent: ll-qa-api-manifest-init

## Role
Generate api-coverage-manifest.yaml from api-test-plan.md

## Instructions
1. Read and validate api-test-plan.md
2. For each capability × required dimension, generate a coverage item
3. Apply ADR-047 cut rules based on priority
4. Initialize all items with lifecycle_status=designed (or cut for cut items)
5. Add all supporting fields (mapped_case_ids, evidence_refs, etc.)
6. Write to ssot/tests/api/{feat_id}/api-coverage-manifest.yaml
