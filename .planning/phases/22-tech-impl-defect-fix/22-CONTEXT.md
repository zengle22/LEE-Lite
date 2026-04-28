# Phase 22: TECH and IMPL Defect Fix - Context

## Summary
Fixes three critical defects in the ll-dev-feat-to-tech and ll-dev-tech-to-impl skills:
- FIX-P1-03: Subject drift from engineering baseline to ADR-005 governance IO/Gateway/Registry patterns
- FIX-P1-04: Template over-sharing where TECH docs include full engineering skeleton for every feature
- FIX-P1-05: Execution layer drift with references to src/be/, .tmp/external/, and ssot/testset/ paths

## Decisions Made

### 1. FIX-P1-03: Subject Drift Fix
**Problem**: ll-dev-feat-to-tech was drifting from engineering baseline focus to ADR-005 governance patterns when engineering baseline features contained words like "registry" or "gateway".

**Solution**:
- Modified `feature_axis()` in `feat_to_tech_derivation.py` to check for engineering baseline patterns BEFORE governance patterns
- Added explicit engineering baseline detection at the start of the axis detection flow
- Updated `assess_optional_artifacts()` to skip ARCH/API generation for engineering baseline features unless explicit keywords are present

### 2. FIX-P1-04: Template Over-Sharing Fix
**Problem**: TECH docs were including the full minimal code skeleton for every feature, causing template over-sharing.

**Solution**:
- Modified `build_tech_docs()` in `feat_to_tech_documents.py` to skip the generic "Minimal Code Skeleton" section for engineering baseline features
- For engineering baseline features, we rely on the specific "Implementation Unit Mapping" instead of the generic skeleton
- Added conditional section rendering based on feature type

### 3. FIX-P1-05: Execution Layer Drift Fix
**Problem**: ll-dev-tech-to-impl was referencing legacy `src/be/` paths, including `.tmp/external/` and `ssot/testset/` in scope, and using generic frontend/backend templates for engineering baseline features.

**Solution**:
- Added `is_engineering_baseline_feature()` helper function in `tech_to_impl_derivation.py`
- Updated `implementation_units()` to filter out excluded paths:
  - `src/be/` (legacy backend paths)
  - `.tmp/external/` (temporary external content)
  - `ssot/testset/` (test sets should not be in execution scope)
- Updated `classified_touch_units()` to accept a feature parameter and use engineering baseline classification
- Leveraged existing engineering baseline task models already present in the codebase

## Verification
- The changes maintain backward compatibility with existing code
- Engineering baseline features will now correctly stay focused on their specific scope
- Path filtering prevents accidental inclusion of legacy directories and test sets
- Existing governance flows continue to work unchanged

## Next Steps
- Run tests to verify the fixes
- Create a summary document
