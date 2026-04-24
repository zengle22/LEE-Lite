# Supervisor Agent: ll-qa-api-from-feat

## Role

Validate that the complete API test chain produced all required artifacts with correct structure and completeness.

## Validation Checklist

### Sub-skill Call Sequence Validation
1. [ ] `/ll-qa-feat-to-apiplan` was called first
2. [ ] `/ll-qa-api-manifest-init` was called second (after traceability validation)
3. [ ] `/ll-qa-api-spec-gen` was called third (or skipped with --no-spec)

### Artifact Validation

4. [ ] `ssot/tests/api/{feat_id}/api-test-plan.md` exists
5. [ ] Acceptance Traceability table is present in api-test-plan.md
6. [ ] Each capability in the plan has at least one acceptance_ref mapping
7. [ ] Each acceptance_ref in the table has at least one capability coverage
8. [ ] `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml` exists
9. [ ] At least one `ssot/tests/api/{feat_id}/api-test-spec/SPEC-*.md` exists

### Path Validation

10. [ ] All artifacts are under canonical path `ssot/tests/api/{feat_id}/`
11. [ ] Feature ID in paths matches the input feat_ref

### Completeness Validation

12. [ ] No capabilities were invented beyond FEAT Scope
13. [ ] Cut records have valid approver + source_ref
14. [ ] P0 capabilities have at least 5 dimension items

## Review Status

Return one of:
- **pass**: All checks passed
- **fail**: One or more checks failed — report which ones
- **needs_revision**: Artifacts exist but require minor fixes before acceptance
