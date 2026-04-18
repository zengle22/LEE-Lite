# Executor Agent — ll-frz-manage

## Role

Execute FRZ management operations by invoking `scripts/frz_manage_runtime.py` with appropriate subcommands and arguments.

## Execution Steps

1. **Accept input** — receive the user's request (validate, freeze, list, or extract).
2. **Validate input format** — check that required parameters are present and correctly formatted:
   - `doc_dir` must be an existing directory (for validate/freeze)
   - `frz_id` must match `FRZ-\d{3,}` format (for freeze)
   - `status` must be one of: frozen, blocked, draft (for list filter)
3. **Determine mode** — map user intent to runtime subcommand:
   - User wants to check FRZ validity -> `validate`
   - User wants to register FRZ -> `freeze`
   - User wants to see registered FRZs -> `list`
   - User wants to extract FRZ contents -> `extract` (Phase 8 stub)
4. **Invoke runtime** — call the appropriate function from `frz_manage_runtime.py`:
   - `validate_frz(args)` for validation
   - `freeze_frz(args)` for freezing
   - `list_frz(args)` for listing
5. **Capture output** — collect stdout/stderr and exit code.
6. **Format response** — present results to user in a clear, structured format.

## Error Handling

- If `CommandError` is raised, display the status code and message to the user.
- If MSC validation fails, display the list of missing dimensions.
- If registry operation fails, display the specific error (duplicate ID, not found, etc.).

## Key Imports

```python
from scripts.frz_manage_runtime import main, build_parser, validate_frz, freeze_frz, list_frz
```

## Success Indicators

- validate: exit code 0 + "STATUS: PASS" in output
- freeze: exit code 0 + "FRZ-xxx registered, status: frozen" in output
- list: exit code 0 + formatted table with FRZ entries
