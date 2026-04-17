## ADR-049: Experience Patch Layer — Automatic Patch Context

### Patch Context Injection (Before Code Changes)

When you are about to modify code files, BEFORE making any Edit or Write:

1. Run: `python cli/lib/patch_context_injector.py inject --workspace-root . --target-files {list of files you plan to edit}`
2. Read the output — it contains active Patch summaries relevant to your target files
3. Incorporate Patch constraints into your code changes
4. Proceed with the Edit/Write

If the script returns "No active patches found", proceed normally.

### Automatic Patch Registration (After Code Changes)

After you have made code changes (Edit/Write completed):

1. Run: `python cli/lib/patch_auto_register.py detect --workspace-root .`
2. If changes detected, run: `python cli/lib/patch_auto_register.py draft --workspace-root .`
3. Review the drafted Patch YAML — confirm or adjust `change_class` and `test_impact`
4. Present the Patch to the user for confirmation
5. Only after user confirmation, register the Patch

**Critical constraints:**
- Do NOT auto-register Patches without user confirmation (ADR-049 §12.2)
- test_impact MUST be specified (ADR-049 §10.1)
- Context budget: max 3000 tokens for Patch injection, max 10 full Patches (ADR-049 §12.1)
- Only show Patches relevant to the files being edited (by changed_files matching)
