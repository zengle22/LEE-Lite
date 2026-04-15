# Supervisor: ll-qa-e2e-test-exec

## Role
Supervisory validation for E2E test execution results.

## Supervisor Validation Checklist
1. Evidence directory exists with evidence YAML files
2. Each evidence file passes validate_evidence schema check
3. Manifest lifecycle_status updated for all executed cases
4. Manifest evidence_status set to "complete" for executed cases
5. Manifest evidence_refs contains paths to evidence files
6. Run ID is consistent across all evidence files and manifest
7. No evidence_required items from e2e_spec are missing in evidence files
8. Execution summary JSON reflects actual Playwright results (total, passed, failed counts match JSON report)
