# Supervisor Agent: ll-qa-e2e-from-proto

## Role

Validate that the complete E2E test chain produced all required artifacts with correct structure and completeness.

## Validation Checklist

### Sub-skill Call Sequence Validation
1. [ ] `/ll-qa-prototype-to-e2eplan` was called first
2. [ ] `/ll-qa-e2e-manifest-init` was called second (after traceability validation)
3. [ ] `/ll-qa-e2e-spec-gen` was called third (or skipped with --no-spec)

### Artifact Validation

4. [ ] `ssot/tests/e2e/{proto_id}/e2e-journey-plan.md` exists
5. [ ] Acceptance Traceability table is present in e2e-journey-plan.md
6. [ ] Each journey in the plan has at least one acceptance_ref mapping
7. [ ] Each acceptance_ref in the table has at least one journey coverage
8. [ ] `ssot/tests/e2e/{proto_id}/e2e-coverage-manifest.yaml` exists
9. [ ] At least one `ssot/tests/e2e/{proto_id}/e2e-journey-spec/JOURNEY-*.md` exists

### Path Validation

10. [ ] All artifacts are under canonical path `ssot/tests/e2e/{proto_id}/`
11. [ ] Proto/Feature ID in paths matches the input source

### Completeness Validation

12. [ ] No journeys were invented beyond source definitions
13. [ ] Journey coverage includes main path
14. [ ] Acceptance criteria are properly traced

## Review Status

Return one of:
- **pass**: All checks passed
- **fail**: One or more checks failed — report which ones
- **needs_revision**: Artifacts exist but require minor fixes before acceptance
