---
phase: 24-impl-spec-test-enhance
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py
  - skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_content.py
  - skills/ll-dev-feat-to-tech/scripts/feat_to_tech_documents.py
  - skills/ll-dev-feat-to-tech/scripts/feat_to_tech_contract_content.py
  - skills/ll-dev-feat-to-tech/scripts/feat_to_tech_governance.py
---

## Summary of Changes

### Task 1: Replace keyword-based api_required with capability-boundary detection

**Changes made:**
- **Removed constants**: STRONG_API_KEYWORDS, WEAK_API_KEYWORDS, NEGATION_MARKERS
- **Added API_SURFACE_PATTERNS**: Regex patterns to detect explicit API surfaces in scope/outputs
- **Added detect_api_surface_in_scope()**: New function that:
  - Only checks scope and outputs fields (per D-06)
  - Uses regex patterns instead of keyword matching
  - Is conservative for engineering baseline FEATs (per D-08)
- **Updated assess_optional_artifacts()**: Uses new detection logic
- **Updated feat_to_tech_governance.py**: Uses detect_api_surface_in_scope() instead of keywords

**Verification passed:**
- Explicit API surfaces detected correctly
- Engineering baseline FEATs remain conservative
- No API detection without explicit scope/output mentions

### Task 2: Add ssot_type to frontmatter and JSON payload

**Changes made:**
- **Updated feat_to_tech_documents.py**: Added ssot_type to:
  - build_tech_docs() → "TECH"
  - build_arch_docs() → "ARCH"
  - build_api_docs() → "API"
- **Updated feat_to_tech_package_content.py**: Added ssot_type to:
  - build_optional_arch_block() → "ARCH"
  - build_optional_api_block() → "API"
  - build_frontmatter() → "TECH" (bundle is primarily a TECH artifact)
  - build_json_payload() → "TECH" (root level of payload)

**Verification passed:**
- All document types have correct ssot_type values
- JSON payload includes ssot_type in optional blocks and root
- Bundle frontmatter has appropriate ssot_type

### Task 3: Add API Preconditions and Post-conditions chapter

**Changes made:**
- **Updated DEFAULT_API_COMMAND_SPECS**: Added new fields per spec:
  - caller_context: Who calls the command and from what surface
  - idempotency_key_strategy: How idempotency is achieved
  - post_conditions: What state is guaranteed after success
  - system_dependency_pre_state: What must be true before calling
  - side_effects: Changes outside the command's direct output
  - ui_surface_impact: What UI updates occur
  - event_outputs: What events are emitted for tracking
- **Updated build_api_docs()**: Added chapter with:
  - Per-Command Context: Caller, idempotency, preconditions, post-conditions
  - Global API-Level State Transitions: Markdown table with 6 columns (D-14/D-15)
  - Narrative Summary: Brief description of overall state flow
- **Added helper functions**:
  - build_api_state_transition_table(): Generates markdown table
  - build_api_preconditions_narrative(): Generates narrative text
- **Updated consistency checks**: Added semantic check for preconditions completeness

**Verification passed:**
- All new fields present in DEFAULT_API_COMMAND_SPECS
- Preconditions and Post-conditions section rendered correctly
- State transition table with exact schema
- Helper functions generate valid output

## Verification Summary

### All Tasks Passed

1. **Task 1 verification**: ✓ Detect API surface in scope/outputs, engineering baseline conservative
2. **Task 2 verification**: ✓ All document types have ssot_type
3. **Task 3 verification**: ✓ All new fields present in API specs
4. **Constants removed**: ✓ No STRONG_API_KEYWORDS, WEAK_API_KEYWORDS, NEGATION_MARKERS remaining
5. **Function exists**: ✓ detect_api_surface_in_scope() exists
6. **Preconditions chapter**: ✓ Chapter exists with table and narrative

### Files Modified

1. `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py`
2. `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_content.py`
3. `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_documents.py`
4. `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_contract_content.py`
5. `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_governance.py`
