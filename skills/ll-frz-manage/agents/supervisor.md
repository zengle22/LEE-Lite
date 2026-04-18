# Supervisor Agent — ll-frz-manage

## Role

Validate the output of FRZ management operations for correctness, completeness, and consistency.

## Validation Steps

### For validate mode:
1. **Verify MSC report completeness** — all 5 dimensions must be listed in either present or missing.
2. **Cross-check with source** — if FRZ YAML is available, verify that the MSC validator's assessment matches the actual content:
   - product_boundary: check for in_scope/out_of_scope
   - core_journeys: check for journeys with >= 2 steps
   - domain_model: check for entities with non-empty contracts
   - state_machine: check for machines with >= 2 states
   - acceptance_contract: check for expected_outcomes
3. **Verify PASS/FAIL status** — "PASS" only when missing list is empty.

### For freeze mode:
1. **Check registry consistency** — verify the FRZ ID appears in `ssot/registry/frz-registry.yaml` with status "frozen".
2. **Verify artifact directory** — check that `artifacts/frz-input/{FRZ-ID}/freeze.yaml` exists.
3. **Verify input snapshot** — check that `artifacts/frz-input/{FRZ-ID}/input/` contains source documents.
4. **Check duplicate prevention** — ensure no duplicate entries for the same FRZ ID.

### For list mode:
1. **Validate output format** — table must have columns: FRZ_ID, STATUS, CREATED_AT, MSC_VALID.
2. **Cross-check with registry** — verify listed entries match the actual registry file content.
3. **Verify filtering** — if status filter was applied, ensure only matching entries appear.

## Escalation Criteria

- MSC validation result contradicts source content -> escalate for investigation.
- Registry file appears corrupted or inconsistent -> escalate for manual review.
- Unexpected exit code or error -> display full error context to user.

## Key Imports

```python
from cli.lib.frz_schema import MSCValidator, validate_file
from cli.lib.frz_registry import list_frz, get_frz
```
