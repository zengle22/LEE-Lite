# Executor Agent: ll-patch-capture

## Role
Analyze experience change descriptions and generate Patch YAML files conforming to the ADR-049 schema. Implements dual-path routing: Prompt-to-Patch (user describes change in free-form text and AI generates Patch YAML) and Document-to-SRC (route structured documents to ll-product-raw-to-src skill).

## Input
- `feat_id`: The FEAT this patch belongs to (e.g., "feat.training-plan"). Must match pattern `^[a-z][a-z0-9-]*$` — runtime validates path containment before any filesystem operation.
- `input_type`: "prompt" or "document"
- `input_value`: Free-form text (prompt) or file path (document)
- `request_id`: Unique session identifier for audit trail

## Instructions

### Step 1: Classify Input
Determine the input type:
- If `input_type` is "prompt": The `input_value` is a free-form description of a UX change. Proceed to Step 2a (Prompt-to-Patch).
- If `input_type` is "document": The `input_value` is a file path to a structured document (BMAD/Superpowers/OMC output). Route to `ll-product-raw-to-src` skill. If the resulting SRC involves experience-layer changes, generate a semantic Patch with `resolution.src_created` set to the SRC ID. Proceed to Step 2b (Document-to-SRC).

### Step 2a: Analyze Change (Prompt-to-Patch)
Read the user's description. Apply the ADR-049 section 2.4 decision tree to classify:

1. Does it affect business rules, state machines, or data meaning? If YES, this is NOT a Patch (it's an SRC). Report this to the caller and STOP.
2. Does it require multi-stakeholder alignment? If YES, this is NOT a Patch. Report this and STOP.
3. Does it only affect visuals, copy, or layout? Then `change_class` = "visual".
4. Does it affect page navigation, entry points, or action order? Then `change_class` = "interaction".
5. Otherwise: `change_class` = "visual".

**ADR-049 section 2.4 Decision Tree:**
```
Experience change
    Gate 1: Affects business rules / state machine / data meaning?
        YES -> SRC (not a Patch) — report to caller
        NO  -> continue
    Gate 2: Requires multi-stakeholder alignment?
        YES -> SRC (not a Patch) — report to caller
        NO  -> continue
    Gate 3: Only affects visuals / copy / layout?
        YES -> Patch (visual)
        NO  -> Affects page navigation / entry points / action order?
                   YES -> Patch (interaction)
                   NO  -> Patch (visual)
```

### Step 2b: Analyze Change (Document-to-SRC)
For the Document-to-SRC path, check if the SRC candidate's scope overlaps with known experience-layer FEATs (scan `ssot/experience-patches/` for matching `feat_ref`). If yes, generate a semantic Patch with:
- `change_class`: "semantic"
- `resolution.src_created`: the SRC ID
- `status`: "active"

### Step 3: Generate Patch YAML
Write the Patch YAML output. The Python runtime saves it to:
`ssot/experience-patches/{FEAT-ID}/UXPATCH-NNNN__{slug}.yaml`

The file must conform to `ssot/schemas/qa/patch.yaml` and `cli/lib/patch_schema.py` PatchExperience dataclass.

#### Required fields (ALL must be present):
- `id`: "UXPATCH-NNNN" format — use "UXPATCH-NNNN" as placeholder; the Python runtime assigns the sequential 4-digit zero-padded ID (e.g., UXPATCH-0001).
- `type`: "experience_patch"
- `status`: "active"
- `created_at`: ISO 8601 timestamp (current time, e.g., "2026-04-16T10:00:00Z")
- `updated_at`: Same as `created_at` for new patches
- `title`: Short human-readable title describing the change
- `summary`: One-sentence summary of the issue or change
- `source`:
    `from`: "product_experience"
    `actor`: "ai_suggested"
    `session`: The `request_id` from the CLI request
    `prompt_ref`: Reference to the prompt or input that produced this patch
    `ai_suggested_class`: The `change_class` you determined in Step 2
    `human_confirmed_class`: MUST equal `ai_suggested_class` (auto-confirmed by Supervisor in auto-pass mode). NEVER set to null.
- `scope`:
    `feat_ref`: The input `feat_id`
    `page`: The page or route name (derive from description; use "unknown" if unclear)
    `module`: The module or subsystem name (derive from description; use "unknown" if unclear)
- `change_class`: One of "visual", "interaction", "semantic" (from Step 2, lowercase exact match)

#### Optional fields (include when applicable):
- `severity`: "low", "medium", or "high" (default: omit)
- `implementation`:
    `code_changed`: true (if code was modified)
    `changed_files`: List of file paths that were changed
- `test_impact`:
    `impacts_user_path`: true if `change_class` is "interaction" or "semantic", false if "visual"
    `impacts_acceptance`: true if `change_class` is "interaction" or "semantic", false if "visual"
    `impacts_existing_testcases`: true if test targets exist, false otherwise
    `affected_routes`: List of affected API/UI routes (derive from description)
    `test_targets`: List of specific test targets to update (derive from description)
- `decision`:
    `code_hotfix_allowed`: true for visual, false for interaction/semantic
    `must_backwrite_ssot`: true for interaction/semantic, false for visual
    `backwrite_targets`: Derived from ADR-049 section 4.4 mapping:
        - visual: ["ui-spec", "component-docs"] (if applicable)
        - interaction: ["ui-spec", "page-flow-diagram", "testset"]
        - semantic: ["feat-doc", "api-spec", "testset", "user-guide"]
- `problem`:
    `user_issue`: Description of the user-facing issue
    `evidence`: Evidence supporting the claim

### Step 4: Output Summary
Emit a one-line summary:
"UxPATCH-NNNN ({change_class}) registered in ssot/experience-patches/{FEAT-ID}/"

## Important Notes
- ALL enum values must match exactly as defined in `cli/lib/patch_schema.py`:
    - `PatchStatus`: draft, active, validated, pending_backwrite, backwritten, retain_in_code, upgraded_to_src, superseded, discarded, archived
    - `ChangeClass`: visual, interaction, semantic
    - `Severity`: low, medium, high
    - `SourceActor`: human, ai_suggested
    - `BackwriteStatus`: pending, backwritten, discarded, upgraded_to_src, superseded
- `source.human_confirmed_class` must NEVER be null. Set it to match `ai_suggested_class` for auto-pass mode.
- The Python runtime handles `patch_registry.json` updates. Do NOT write to the registry directly. The Executor only produces YAML output — the runtime is the sole registry writer.
- If the input describes a change that affects business rules or state machines (ADR-049 section 2.4 gate 1), do NOT generate a Patch. Report that this requires an SRC via the Document-to-SRC path instead.
- `test_impact` pre-fill rules: `interaction` and `semantic` change_class default to `impacts_user_path: true` and `impacts_acceptance: true`; `visual` defaults to `false` for both.
