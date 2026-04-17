# Executor: Patch-Aware Context

## Role

You are the patch-awareness executor. Before any SSOT artifact generation (TECH/UI/PROTO), you ensure the AI agent has awareness of active experience patches for the target FEAT.

## Prerequisites

- `scripts/patch_aware_context.py` exists and is executable
- Workspace root contains `ssot/experience-patches/` directory
- FEAT reference is provided (e.g., FEAT-SRC-001-001)

## Execution Steps

### Step 1: Resolve Patch Context

Run the patch context resolver to scan for active patches:

```bash
python scripts/patch_aware_context.py resolve \
  --workspace-root $WORKSPACE_ROOT \
  --feat-ref {FEAT_REF} \
  --output-dir {OUTPUT_DIR}
```

This invokes `resolve_patch_context()` from Phase 4 (`cli/lib/test_exec_artifacts.py`), which scans `ssot/experience-patches/` for validated and pending_backwrite patches, computes the directory hash, and produces the awareness recording.

### Step 2: Read Awareness File

Read the generated `{OUTPUT_DIR}/patch-awareness.yaml`. This file contains the structured awareness recording with the `patch_awareness` top-level key.

### Step 3: Evaluate Patches

Check `patch_scan_status` and `has_active_patches`:

- **If `patch_scan_status` is `"none_found"`:** Note "No active patches found for this FEAT. Proceeding without patch constraints." and continue to SSOT generation.

- **If `has_active_patches` is `true`:**
  - Review each entry in `validated_patches_summary` and `pending_patches_summary`
  - For each patch, note its `change_class` (visual, interaction, semantic) and `scope` (page, module)
  - Determine whether the patch's scope overlaps with the SSOT artifact you are about to generate

### Step 4: Record Consideration

If patches were found and you need to document your reasoning, re-run the resolver with your consideration:

```bash
python scripts/patch_aware_context.py resolve \
  --workspace-root $WORKSPACE_ROOT \
  --feat-ref {FEAT_REF} \
  --output-dir {OUTPUT_DIR} \
  --ai-reasoning "{your consideration text}"
```

Your consideration text should be specific:

- **If following patches:** "Patch UXPATCH-NNNN change_class=semantic for scope.page=X was considered. The generated TECH document incorporates the documented behavior."
- **If diverging:** "Patch UXPATCH-NNNN change_class=interaction for scope.page=X was reviewed but not followed because [specific rationale]."

### Step 5: Proceed

SSOT chain generation proceeds normally. The `patch-awareness.yaml` file serves as an audit record that patch context was acknowledged.

## Constraints

- **Do NOT enforce patch compliance** — this is awareness only (Phase 6 handles enforcement)
- **Do NOT modify existing SSOT skill executor.md files** (per D-10)
- **Always produce patch-awareness.yaml**, even with zero patches found
- **Use `resolve_patch_context()` from Phase 4** — do not reimplement patch scanning logic
