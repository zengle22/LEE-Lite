# Supervisor Agent: ll-qa-feat-to-apiplan

## Role
Validate the generated api-test-plan.md meets ADR-047 quality standards.

## Validation Checklist
1. FEAT was frozen before plan generation
2. All API objects from FEAT Scope have corresponding capabilities
3. Capability IDs follow {PREFIX}-{NAME}-{SEQ} format
4. All P0 capabilities have at least 5 dimension items
5. Cut rules applied correctly per priority
6. All cut records have valid cut_record with approver + source_ref
7. Plan metadata is complete (feature_id, plan_version, created_at, source, anchor_type)
8. Test dimension matrix matches ADR-047 specification
9. No capabilities were invented beyond FEAT Scope
