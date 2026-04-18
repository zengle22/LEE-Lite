---
status: issues
phase: "08"
updated: "2026-04-18"
---

# Phase 08 FRZ->SRC Code Review

## Review Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0     | pass   |
| HIGH     | 3     | warn   |
| MEDIUM   | 5     | info   |
| LOW      | 3     | note   |

Verdict: WARNING -- 3 HIGH issues should be resolved before merge.

---

## Resolution Notes

- **Resolved:** `check_constraints()` false-positive — fixed in `ec3d957` to scan `output_data["constraints"]` list in addition to top-level keys. All 43 tests now pass.

---

## HIGH Findings

### HIGH-1: epic_to_feat_runtime.py exceeds 800-line file size limit (2948 lines)

**File:** `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
**Issue:** At 2948 lines (81KB), this file is nearly 4x the project maximum of 800 lines.
**Fix:** Split into focused modules: validation, payload construction, workflow orchestration. FRZ extraction already lives in `epic_to_feat_extract.py`.

### HIGH-2: src_to_epic_runtime.py exceeds 800-line file size limit (1021 lines)

**File:** `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py`
**Issue:** At 1021 lines, exceeds the 800-line project maximum.
**Fix:** Extract `validate_output_package`, `build_semantic_drift_check`, and `build_epic_payload` into separate modules.

### HIGH-3: extract_feat_from_frz_logic passes trivial target data to drift detection

**File:** `skills/ll-product-epic-to-feat/scripts/epic_to_feat_extract.py:257`
**Issue:** The drift detection call passes `{anchor_id: {"name": anchor_id}}` as target data for every anchor. This compares a bare dict with just `{"name": "JRN-001"}` against FRZ content with descriptive names like "User Login". The comparison will always fail as "tampered" -- making drift detection always report drift.
**Fix:** Build proper target data using the same pattern as `_build_target_data` in `frz_extractor.py`, passing actual semantic content for each anchor.

### HIGH-4: extract_feat_from_frz_logic silently swallows duplicate anchor registration

**File:** `skills/ll-product-epic-to-feat/scripts/epic_to_feat_extract.py:247-249`
**Issue:** When `register_projection` raises `CommandError` for a duplicate, the anchor is silently skipped and NOT added to `registered_anchors`. Contrast with `frz_extractor.py:284-295` which adds the anchor ID even on duplicate.
**Fix:** Add the anchor ID to `registered_anchors` in the except block, matching the `frz_extractor` pattern.

---

## MEDIUM Findings

### MEDIUM-1: check_constraints logic may produce false positives

**File:** `cli/lib/drift_detector.py:265-270`
**Issue:** Constraint checker verifies whether a constraint string exists as a key in output_data. Constraints are free-form text; checking for their presence as dict keys is fragile.

### MEDIUM-2: _run_gate_review has broad bare except

**File:** `skills/ll-frz-manage/scripts/frz_manage_runtime.py:535`
**Issue:** `except Exception` catches all errors during gate review and silently falls back to "approve", potentially allowing blocked extracts to proceed.

### MEDIUM-3: Cascade extract function has inconsistent argument count

**File:** `skills/ll-frz-manage/scripts/frz_manage_runtime.py:491`
**Issue:** `extract_fn(frz_id, workspace_root)` called with 2 args, but extract functions have varying signatures (e.g., `extract_epic_from_frz` takes 4 args).

### MEDIUM-4: Inconsistent FC-xxx anchor ID derivation

**File:** `skills/ll-product-src-to-epic/scripts/src_to_epic_extract.py:186-189`
**Issue:** `_collect_anchor_ids` uses sequential numbering `FC-{i+1:03d}`, but `frz_extractor.py` parses `FC-xxx` from text. Different IDs for same FRZ cause registry inconsistency.

### MEDIUM-5: sys.path manipulation at module level

**File:** `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py:17-18`
**Issue:** Modifying `sys.path` at module load time is repeated across multiple runtime files.

---

## LOW Findings

### LOW-1: _anchor_dimension function duplicated

**Files:** `epic_to_feat_extract.py:279-291` and `epic_to_feat_runtime.py:120-132`
**Issue:** Same prefix-to-dimension mapping logic duplicated.

### LOW-2: _find_workspace_root uses heuristic filesystem walking

**File:** `skills/ll-frz-manage/scripts/frz_manage_runtime.py:129-155`
**Issue:** Walking up filesystem may find wrong root in a monorepo.

### LOW-3: shutil.copytree for evidence trail copy lacks error handling

**File:** `skills/ll-frz-manage/scripts/frz_manage_runtime.py:309`
**Issue:** No try/except around the copy operation.

---

## Observations

- No security vulnerabilities found
- Good use of immutability with frozen dataclasses
- Good input validation throughout
- Test coverage is reasonable across all modules
