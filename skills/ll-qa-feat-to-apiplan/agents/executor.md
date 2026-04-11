# Executor Agent: ll-qa-feat-to-apiplan

## Role
Draft the api-test-plan.md from a frozen FEAT document.

## Instructions
1. Read the FEAT freeze package at the specified path
2. Extract API capabilities from Scope section
3. Assign capability IDs and priorities
4. Apply the ADR-047 test dimension matrix
5. Apply priority-based cut rules
6. Generate the api-test-plan.md with all required sections
7. Write to ssot/tests/api/{feat_id}/api-test-plan.md

## Constraints
- Do not invent capabilities not present in the FEAT
- Do not skip any API-capable object in Scope
- All cut records must have approver + source_ref
