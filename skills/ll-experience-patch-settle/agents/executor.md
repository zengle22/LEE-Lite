# Executor Agent — ll-experience-patch-settle

## Role

Execute Minor patch settlement by invoking `scripts/settle_runtime.py` with the appropriate subcommand and arguments.

## Execution Steps

1. **Accept input** -- receive a validated Patch YAML file path from `ll-patch-capture`.
2. **Validate input format** -- check that required fields are present:
   - `id` must match `UXPATCH-\d{4,}` format
   - `status` must be "approved"
   - `grade_level` must be "minor"
   - `change_class` must be a valid `ChangeClass` enum value
   - `scope.feat_ref` must be present
3. **Invoke runtime** -- call `settle_runtime.py`:
   - `python scripts/settle_runtime.py settle --patch <patch-yaml-path> --workspace-root <root>`
   - Optionally: `--apply` flag (stub for future SSOT modification)
4. **Capture output** -- collect stdout/stderr, exit code, and backwrite record paths.
5. **Format response** -- present results to user:
   - Patch status transition (approved -> applied)
   - List of backwrite RECORDS created
   - Paths to backwrite files

## BACKWRITE_MAP Reference

The runtime uses BACKWRITE_MAP to determine backwrite targets based on `change_class`:

```python
BACKWRITE_MAP = {
    "ui_flow":       {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "copy_text":     {"must_backwrite_ssot": False, "backwrite_targets": []},
    "layout":        {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "navigation":    {"must_backwrite_ssot": True,  "backwrite_targets": ["ui_spec", "flow_spec"]},
    "interaction":   {"must_backwrite_ssot": True,  "backwrite_targets": ["ui_spec", "flow_spec", "testset"]},
    "error_handling":{"must_backwrite_ssot": False, "backwrite_targets": []},
    "performance":   {"must_backwrite_ssot": False, "backwrite_targets": []},
    "accessibility": {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "data_display":  {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "visual":        {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "semantic":      {"must_backwrite_ssot": True,  "backwrite_targets": ["frz_revise"]},  # NOT handled by settle
    "other":         {"must_backwrite_ssot": False, "backwrite_targets": []},
}
```

## Error Handling

- If `grade_level` is "major", runtime rejects with message referencing `ll-frz-manage --type revise`
- If `status` is already "applied", runtime returns early (idempotency -- no error)
- If filesystem write fails, runtime raises `CommandError` with specific error message
- If `change_class` is unknown, derive_grade() defaults to MAJOR with warning

## Key Imports

```python
from scripts.settle_runtime import main, build_parser, settle_minor_patch
```

## Success Indicators

- settle: exit code 0 + "Patch settled: UXPATCH-NNNN" in output
- backwrite records: N files written to `backwrites/` subdirectory
- patch YAML: status updated to "applied" with `settled_at` timestamp
