# Phase 22: TECH and IMPL Defect Fix - Discussion Log

## Discussion Points

### 1. FIX-P1-03: Subject Drift Root Cause
**Observation**: The `feature_axis()` function in `feat_to_tech_derivation.py` checked for governance patterns (collaboration, layering, formalization, io_governance, adoption_e2e) BEFORE checking for engineering baseline patterns. This caused engineering baseline features that accidentally contained words like "registry" or "gateway" to be misclassified as governance features.

**Resolution**: Reordered the axis detection logic to check for engineering baseline patterns first. Added explicit checks for:
- SRC-003 references
- Engineering baseline keywords in feat_ref/title/axis_id
- Specific engineering baseline axis patterns

### 2. FIX-P1-04: Template Over-Sharing Root Cause
**Observation**: The `build_tech_docs()` function always included the full "Minimal Code Skeleton" section, regardless of feature type. For engineering baseline features, this was redundant because they already have concrete implementation unit mappings.

**Resolution**: Modified the document building logic to skip the generic "Minimal Code Skeleton" section for engineering baseline features, since they already have specific implementation units defined.

### 3. FIX-P1-05: Execution Layer Drift Root Cause
**Observation**: The tech-to-impl skill had legacy references to `src/be/` (old backend structure) and didn't filter out temporary directories like `.tmp/external/` or test directories like `ssot/testset/`. However, we discovered that much of the engineering baseline support was already present in the codebase!

**Resolution**: 
- Built upon the existing `_is_engineering_baseline()` function in tech_to_impl_contract_projection.py
- Built upon the existing `_is_allowed_engineering_baseline_repo_path()` function that already excludes src/, ssot/, .tmp/, etc.
- Added filtering in `implementation_units()` to exclude problematic paths at the source
- Updated `classified_touch_units()` to be aware of engineering baseline feature classification

## What We Learned
- The codebase already had strong engineering baseline support in place!
- The main issues were:
  1. Axis detection ordering
  2. Template section over-inclusion
  3. Path filtering consistency

## Open Questions
None - all defects have clear root causes and solutions.

## Action Items
- [x] Reorder axis detection in feature_axis()
- [x] Modify build_tech_docs() to skip generic skeleton for engineering baseline
- [x] Add path filtering in implementation_units()
- [x] Leverage existing engineering baseline detection logic
