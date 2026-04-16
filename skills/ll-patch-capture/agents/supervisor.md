# Supervisor Agent: ll-patch-capture

## Role
Validate generated Patch YAML files and decide whether to auto-pass (register immediately) or escalate to human confirmation. Implements four-layer validation: mechanical schema checks, semantic validation, conflict detection, and escalation decision logic.

## Input
- Path to generated Patch YAML file
- FEAT-ID for conflict scanning
- Input type (prompt or document)

## Validation Protocol

The Supervisor runs validation in FOUR layers. Layer 1 is mechanical (Python), Layers 2-3 are semantic (LLM judgment), Layer 4 is the escalation decision.

### Layer 1: Mechanical Schema Validation

Run: `python -m cli.lib.patch_schema --type patch <patch_file_path>`

This validates against `cli/lib/patch_schema.py` PatchExperience dataclass using `validate_file()`.
- Check exit code: 0 = pass, non-zero = fail
- If fail: Record the error message, set status to "draft", ESCALATE to human (D-09: schema validation failure)
- Never rely on LLM judgment for schema compliance — the Python validator is the authority

### Layer 2: Semantic Validation Checklist

After Layer 1 passes, verify each item:

1. **[SCHEMA-PASS]** Schema validation completed successfully (confirmed from Layer 1 result)
2. **[REQUIRED-FIELDS]** All required fields present: id, type, status, created_at, updated_at, title, summary, source, scope, change_class
3. **[SOURCE-VALID]** source.from = "product_experience", source.actor = "ai_suggested", source.human_confirmed_class is non-null and matches source.ai_suggested_class
4. **[SCOPE-VALID]** scope.feat_ref is non-empty, scope.page is non-empty, scope.module is non-empty
5. **[CHANGE-CLASS]** change_class is one of: "visual", "interaction", "semantic" (exact lowercase match)
6. **[STATUS]** status is "active" for new registrations
7. **[ENUM-VALUES]** All enum fields use valid values from ssot/schemas/qa/patch.yaml
8. **[TIMESTAMPS]** created_at and updated_at are valid ISO 8601 timestamps
9. **[TEST-IMPACT]** test_impact pre-fill rules followed: interaction/semantic -> impacts_user_path=true; visual -> impacts_user_path=false

### Layer 3: Conflict Detection

Scan `ssot/experience-patches/{FEAT-ID}/` for existing active patches:
- For each UXPATCH-*.yaml in the directory:
  - Skip if status is not in (active, validated, pending_backwrite)
  - Skip if id matches the current patch (self-comparison)
  - Compare `implementation.changed_files` arrays for overlap
  - Compare `scope.page` and `scope.module` for same-target conflicts
- If any overlapping files or same-target conflicts found: set `conflict=true`, populate `conflict_details` (with_patch_id, description), ESCALATE to human (D-09: conflict detected)

### Layer 4: Escalation Decision

After all validation layers, decide based on the following criteria.

**Auto-pass conditions (ALL must be true, per D-08):**
- Layer 1 schema validation passed (exit code 0)
- Layer 2 all 9 checklist items pass
- Layer 3 no conflicts detected
- change_class is NOT "semantic"
- change_class confidence is high (clear decision tree match from ADR-049 section 2.4)

**Escalation triggers (ANY single trigger causes escalation, per D-09):**
1. Schema validation failed (Layer 1 failure — Python validator returned non-zero)
2. change_class confidence is low (visual vs interaction ambiguous from input description)
3. Conflict detected (Layer 3 found overlapping files or same-target conflicts with existing active patch)
4. change_class is "semantic" (may require SRC creation decision — Document-to-SRC path)
5. This is the first Patch for this FEAT (patch_registry.json has 0 entries before this one)
6. test_impact is disputed (impacts test path but AI confidence is low on classification)

### Auto-pass Action

If auto-pass decision (all conditions met):
1. Confirm `patch_registry.json` has been updated with the new entry by the Python runtime
2. Confirm the Patch YAML file exists at the expected path
3. Emit success notification: "UxPATCH-NNNN ({change_class}) registered in ssot/experience-patches/{FEAT-ID}/"

### Escalation Action

If escalate decision (any trigger matched):
1. Set patch status to "draft"
2. Present structured review checklist to user:
   - List each failed validation item with clear explanation
   - For conflicts: show which existing Patch conflicts (by ID) and which files or targets overlap
   - For low confidence: explain why change_class is ambiguous (which gates were unclear)
   - For semantic: explain that this may require SRC creation instead of a Patch
   - For first-patch: flag that this is the inaugural Patch for this FEAT and warrants human review
3. Wait for user confirmation or correction before proceeding
4. If user corrects the change_class, update `human_confirmed_class` to the corrected value and re-evaluate

## Output
- If auto-pass: Patch registered, registry updated by runtime, one-line notification emitted
- If escalate: Structured review checklist presented to user, patch held in "draft" status awaiting human decision
