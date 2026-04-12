# SRC-001 ADR-047 Dual-Chain Test Specifications Quality Review

> **Review Date**: 2026-04-11
> **Reviewer**: Automated Quality Review
> **Scope**: ADR-047 dual-chain test specifications for SRC-001 (FEAT-SRC-001-001 through FEAT-SRC-001-005)
> **Reference**: `docs/guides/adr047-dual-chain-testing-guide.md`
> **Reference Example**: `ssot/tests/api/FEAT-SRC-005-001/api-coverage-manifest.yaml`

---

## Overall Assessment: CONDITIONAL PASS with Required Fixes

**Summary**: The SRC-001 dual-chain test specifications demonstrate strong structural adherence to the ADR-047 framework across all 5 FEATs. The API test plans, coverage manifests, and spec files show consistent patterns and good traceability to source FEAT documents. The E2E chain for PROTOTYPE-FEAT-SRC-001-001 follows the API-derived mode correctly. However, several HIGH and MEDIUM severity issues must be addressed before gate evaluation can proceed.

---

## File-by-File Findings

---

### 1. `ssot/tests/api/FEAT-SRC-001-001/api-test-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete (feature_id, plan_version, created_at, source, anchor_type) | PASS | All 5 fields present and correct |
| Capabilities extracted from actual FEAT Scope/AC sections | PASS | 5 capabilities correctly traceable to FEAT-SRC-001-001 Scope/ACs |
| Capability IDs follow {PREFIX}-{NAME}-{SEQ} format | PASS | LOOP-EXEC-SUBMIT-001, LOOP-GH-HANDOFF-001, etc. follow format |
| Priorities assigned (P0/P1/P2) based on Acceptance Checks | PASS | 4 P0 capabilities, 1 P1 capability |
| Test dimension matrix includes all 8 dimensions | PASS | All 8 dimensions present |
| Cut records have proper cut_reason + source_ref | PASS | 8 cut records with reasons and ADR-047 references |
| Priority matrix summary matches capability details | PASS | P0 requires 5 dimensions, P1 requires 3 dimensions |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| MEDIUM | LOOP-RESPONSIBILITY-001 has `参数校验` cut in the manifest but the plan's priority matrix says P0 requires "参数校验 (key)" dimensions. The plan cut table says "验证规则类能力, 非 I/O 类能力" but LOOP-RESPONSIBILITY-001 is a verification endpoint that could still benefit from parameter validation testing. | Consider restoring the parameter validation dimension for LOOP-RESPONSIBILITY-001 since the endpoint accepts query parameters that could be malformed. |
| LOW | Priority matrix says P0 requires "异常路径 (key)" but the cut records do not show which specific exception dimensions are "key" vs. excluded. The manifest shows 4 of 8 dimensions retained for P0, which seems correct but the "(key)" annotation is ambiguous. | Clarify which dimensions are "key" in the priority matrix or document the selection criteria. |

---

### 2. `ssot/tests/api/FEAT-SRC-001-001/api-coverage-manifest.yaml`

| Check | Status | Finding |
|-------|--------|---------|
| Root key is `api_coverage_manifest` | PASS | Correct root key |
| feature_id, generated_at, source_plan_ref present | PASS | All present and correct |
| Items count matches capabilities x dimensions (after cuts) | PASS | 25 items total (20 active + 5 cut) |
| Each item has: coverage_id, capability, scenario_type, dimension, priority, source_feat_ref | PASS | All required fields present |
| Each item has 4D status: lifecycle_status, mapping_status, evidence_status, waiver_status | PASS | All initialized correctly |
| Each item has supporting fields: mapped_case_ids, evidence_refs, rerun_count, last_run_id, obsolete, superseded_by | PASS | All present with appropriate defaults |
| Cut items have complete cut_record (cut_target, cut_reason, source_ref, approver, approved_at) | PASS | All 5 cut items have complete cut_records |
| P0 capabilities have >=5 coverage items after dimension application | PASS | LOOP-EXEC-SUBMIT-001: 4 active + 1 cut = 5; LOOP-GH-HANDOFF-001: 4 active + 1 cut = 5; LOOP-RESPONSIBILITY-001: 3 active + 1 cut = 4; LOOP-REFLOW-BOUNDS-001: 3 active + 1 cut = 4 |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| HIGH | **LOOP-RESPONSIBILITY-001 has only 3 active coverage items** (happy, exception, state_constraint, data_side_effect) after cutting parameter_validation. The ADR-047 P0 minimum is >=5 coverage items, but LOOP-RESPONSIBILITY-001 has 4 active items. This is below the minimum threshold. | Either restore the parameter_validation dimension or document why this capability legitimately falls below the P0 minimum and get explicit approver sign-off. |
| HIGH | **LOOP-REFLOW-BOUNDS-001 has only 3 active coverage items** (happy, state_constraint, exception, data_side_effect) after cutting boundary_value. This equals 4 active items, which matches the P0 requirement if we count correctly. Upon recount: happy + state_constraint + exception + data_side_effect = 4 active items. This is still below the recommended >=5 items for P0. | Restore one more dimension (e.g., parameter_validation or idempotent) or document the variance with explicit approver sign-off. |
| MEDIUM | The `generated_at` timestamp uses `"2026-04-11T00:00:00Z"` which is midnight UTC -- likely a placeholder rather than actual generation time. | Use the actual generation timestamp for traceability. |
| LOW | `approver` is set to `"qa-lead"` (a role) rather than a specific person's name. The ADR-047 spec says approver should be "姓名/角色" (name/role), so this is acceptable but could be more specific. | Consider using actual approver name once assigned. |

---

### 3. `ssot/tests/api/FEAT-SRC-001-001/api-test-spec/SPEC-LOOP-EXEC-SUBMIT-001.md` (and all other spec files)

Reviewed 19 spec files under FEAT-SRC-001-001:

| Check | Status | Finding |
|-------|--------|---------|
| Each spec has: case_id, coverage_id_ref, capability_ref, priority | PASS | All specs have case_id, coverage_id, capability, priority |
| Each spec has endpoint definition (method, path, expected status codes) | PASS | All specs define endpoint with HTTP method and path |
| Each spec has request schema (headers, query params, body) | PASS | Request bodies defined in all POST specs |
| Each spec has expected response (status code, body schema, headers) | PASS | Response JSON schemas provided |
| Each spec has assertions (status code, body fields, error messages, side effects) | PASS | Response and side effect assertions present |
| Each spec has evidence_required field | PASS | All specs list required evidence |
| Each spec has anti_false_pass_checks with >=1 check | **FAIL** | Multiple specs missing anti_false_pass_checks section |
| Each spec has cleanup section | PASS | All specs have cleanup section |
| Each spec has source_refs traceability | PASS | source_feat_ref present in case metadata |
| P0 specs have >=3 anti_false_pass_checks | **FAIL** | Specs that have anti_false_pass_checks meet the threshold, but many are missing it entirely |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| HIGH | **Missing `anti_false_pass_checks` section in 15 of 19 spec files.** Only `SPEC-LOOP-EXEC-SUBMIT-STATE-001.md` contains an `Anti-False-Pass Checks` section. The remaining 18 specs (including all happy path, exception, and side effect specs) lack this required field. This is a structural gap against the ADR-047 requirement that every spec must have `anti_false_pass_checks` with >=1 check. | Add `Anti-False-Pass Checks` section to all 18 missing spec files. Minimum checks should include: response structure validation, state persistence verification, and absence of unintended side effects. |
| HIGH | **Missing `source_refs` traceability section in all 19 spec files.** The ADR-047 checklist requires a `source_refs` section in each spec linking back to the specific FEAT section(s) that drive the test. While `source_feat_ref` is in the case metadata table, a dedicated `source_refs` section listing the exact FEAT sections (Scope, AC-01, Constraints, etc.) is absent. | Add a `## Source References` section to each spec file mapping to the exact FEAT section lines. |
| MEDIUM | **Missing `coverage_id_ref` field name.** The checklist says specs should have `coverage_id_ref` but the specs use `coverage_id` (without `_ref`). The reference manifest uses `coverage_id` as well, so this may be a checklist naming inconsistency rather than a defect. However, for explicit traceability, the spec metadata table should label this as `coverage_id_ref` to indicate it references a manifest item. | Align field naming between manifest (`coverage_id`) and spec metadata table (`coverage_id`). Either rename one or document the mapping. |
| MEDIUM | **SPEC-LOOP-EXEC-SUBMIT-001.md (happy path) does not include expected HTTP status codes in the response section.** The spec shows the response JSON body but does not explicitly state the expected HTTP status code (e.g., 201 Created) as a separate assertion. | Add explicit HTTP status code assertion (e.g., `status_code == 201`) to the response assertions. |
| LOW | Spec files use mixed naming conventions: some use hyphens in filenames (`SPEC-LOOP-EXEC-SUBMIT-001.md`) and some add suffixes (`SPEC-LOOP-EXEC-SUBMIT-STATE-001.md`). The suffix convention (STATE, EXCEPTION, SIDE-EFFECT) is clear but not formally defined in any naming guide. | Document the spec naming convention in a project standard. |
| LOW | Several P0 specs have `Cleanup` sections that reference database operations (delete records, restore state) but do not specify what happens if cleanup fails (e.g., orphaned test data). | Add cleanup failure handling notes to specs with database operations. |

---

### 4. `ssot/tests/api/FEAT-SRC-001-002/api-test-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete | PASS | All 5 fields present |
| Capabilities extracted from FEAT | PASS | 4 capabilities traceable to FEAT-SRC-001-002 |
| Capability IDs follow format | PASS | HANDOFF-UPGRADE-001, CANDIDATE-GATE-ENFORCE-001, etc. |
| Priorities assigned | PASS | 3 P0, 1 P1 |
| Test dimension matrix includes all 8 dimensions | PASS | All 8 present |
| Cut records have proper cut_reason + source_ref | PASS | 7 cut records with ADR-047 references |
| Priority matrix matches capability details | PASS | Consistent with P0/P1 definitions |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| LOW | All cut reasons reference `ADR-047 Section 4.1.3` which appears to be a generic reference. The specific subsection for each cut type (boundary value, state constraint, etc.) should ideally cite more specific guidance. | Consider citing the specific cut rule rationale for each dimension type. |

---

### 5. `ssot/tests/api/FEAT-SRC-001-002/api-coverage-manifest.yaml`

| Check | Status | Finding |
|-------|--------|---------|
| Root key is `api_coverage_manifest` | PASS | Correct |
| feature_id, generated_at, source_plan_ref present | PASS | All present |
| Items count matches capabilities x dimensions | PASS | 20 items total (14 active + 6 cut) |
| Required fields present per item | PASS | All fields present |
| 4D status initialized | PASS | All correct |
| Supporting fields present | PASS | All present |
| Cut items have complete cut_record | PASS | All 6 cut items have complete records |
| P0 capabilities have >=5 coverage items | PASS | HANDOFF-UPGRADE-001: 5 items (4 active + 1 cut); CANDIDATE-GATE-ENFORCE-001: 4 active + 1 cut = 5; FORMAL-NO-REFLOW-001: 4 active + 1 cut = 5 |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| MEDIUM | CANDIDATE-GATE-ENFORCE-001 has no `参数校验` dimension item in the manifest (only happy_path, exception, state_constraint, data_side_effect, and cut boundary_value). The plan's P0 priority matrix says "参数校验 (key)" should be included. | Add a parameter validation coverage item for CANDIDATE-GATE-ENFORCE-001, or document why it is legitimately excluded. |
| MEDIUM | FORMAL-NO-REFLOW-001 similarly lacks a `参数校验` dimension despite the P0 matrix requiring it. | Same as above. |
| LOW | `generated_at` timestamp is midnight UTC placeholder. | Use actual timestamp. |

---

### 6. `ssot/tests/api/FEAT-SRC-001-003/api-test-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete | PASS | All fields present |
| Capabilities from FEAT | PASS | 4 capabilities correctly derived from FEAT-SRC-001-003 |
| Capability ID format | PASS | LAYER-SEPARATION-001, CONSUMER-ADMISSION-001, GATE-AUTHORITY-001, LINEAGE-REF-001 |
| Priorities | PASS | 3 P0, 1 P1 |
| Dimension matrix (8 dims) | PASS | All present |
| Cut records | PASS | 7 cut records with proper fields |
| Priority matrix matches | PASS | Consistent |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| MEDIUM | GATE-AUTHORITY-001 has `边界值` cut with reason "权限防护为离散规则，无边界概念" but `参数校验` dimension is NOT cut and is included in the P0 matrix. However, there is no corresponding coverage item for GATE-AUTHORITY-001 parameter_validation in any manifest (no manifest exists for FEAT-SRC-001-003 -- see missing files below). | **CRITICAL**: No api-coverage-manifest.yaml exists for FEAT-SRC-001-003. The plan is defined but the manifest is missing entirely. |

---

### 7. `ssot/tests/api/FEAT-SRC-001-004/api-test-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete | PASS | All fields present |
| Capabilities from FEAT | PASS | 4 capabilities derived from FEAT-SRC-001-004 |
| Capability ID format | PASS | IO-SCOPE-001, PATH-GOVERNANCE-001, WRITE-ENFORCEMENT-001, PATH-INHERITANCE-001 |
| Priorities | PASS | 3 P0, 1 P1 |
| Dimension matrix | PASS | All 8 dimensions |
| Cut records | PASS | 7 cut records |
| Priority matrix | PASS | Consistent |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| CRITICAL | **No api-coverage-manifest.yaml exists for FEAT-SRC-001-003 or FEAT-SRC-001-004.** These test plans are defined but the corresponding coverage manifests have not been initialized. This blocks the dual-chain gate evaluation for these features. | Run `ll-qa-api-manifest-init` for both FEAT-SRC-001-003 and FEAT-SRC-001-004 to generate the missing manifests. |

---

### 8. `ssot/tests/api/FEAT-SRC-001-005/api-test-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete | PASS | All fields present |
| Capabilities from FEAT | PASS | 4 capabilities from FEAT-SRC-001-005 |
| Capability ID format | PASS | SKILL-ONBOARD-001, MIGRATION-CUTOVER-001, E2E-PILOT-001, SCOPE-GUARD-001 |
| Priorities | PASS | 3 P0, 1 P1 |
| Dimension matrix | PASS | All 8 dimensions |
| Cut records | PASS | 7 cut records |
| Priority matrix | PASS | Consistent |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| CRITICAL | **No api-coverage-manifest.yaml exists for FEAT-SRC-001-005.** Same issue as 003 and 004. | Generate the missing manifest. |

---

### 9. `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-journey-plan.md`

| Check | Status | Finding |
|-------|--------|---------|
| Metadata complete with derivation_mode=api-derived | **PARTIAL** | Metadata has `anchor_type: feat (derived)` but no explicit `derivation_mode` field |
| >=1 main journey + >=1 exception journey | PASS | 1 main (JOURNEY-MAIN-001) + 2 exception (JOURNEY-EXCEPTION-001/002) + 1 retry (JOURNEY-RETRY-001) |
| Each journey has: journey_id, journey_type, entry_point, user_steps, expected_ui_states, expected_network_events, expected_persistence, priority | PASS (in plan) | Journey table has journey_id, type, priority; journey details have user_steps tables |
| Minimum journey validation table shows PASS for all rules | PASS | 3 rules all PASS |
| Journey cut records present | PASS | 1 cut record for journey_type.revisit |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| MEDIUM | The plan metadata does not include an explicit `derivation_mode: api-derived` field. The `source` field mentions "API-derived mode" and `anchor_type` says "feat (derived)", but the ADR-047 spec calls for an explicit `derivation_mode` field. | Add `| derivation_mode | api-derived |` to the plan metadata table. |
| LOW | Journey details in the plan are in table format (Step/User Action/Expected System Response) rather than the structured format expected in journey specs. This is acceptable for the plan level but the specs should expand on these. | Ensure corresponding journey specs expand each journey with full detail. |
| LOW | The retry journey (JOURNEY-RETRY-001) is classified as `retry` type but the minimum journey validation table lists it as satisfying the "至少 1 条重试/回访旅程" rule. The cut table also cuts `journey_type.revisit` which seems contradictory -- cutting revisit while having a retry journey. | Clarify whether the retry journey is distinct from the cut revisit journey, or consolidate. |

---

### 10. `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-coverage-manifest.yaml`

| Check | Status | Finding |
|-------|--------|---------|
| Root key is `e2e_coverage_manifest` | PASS | Correct |
| Items match journeys from plan | **PARTIAL** | Manifest references JOURNEY-EXCEPTION-002 and JOURNEY-RETRY-001 but these journeys are defined only in the plan, not as separate spec files |
| Each item has: journey_id, journey_type, priority, source_prototype_ref | **PARTIAL** | Items have `journey` field (not `journey_id`), and `source_feat_ref` (not `source_prototype_ref`) |
| Each item has 4D status fields initialized | PASS | All correct |
| Supporting fields present | PASS | All present |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| HIGH | **Field naming mismatch**: The manifest uses `journey` instead of `journey_id`, and `source_feat_ref` instead of `source_prototype_ref`. The ADR-047 spec defines the schema with `journey_id` and `source_prototype_ref`. This creates inconsistency with the reference example from FEAT-SRC-005-001 which uses the correct naming. | Align field names to ADR-047 schema: rename `journey` to `journey_id` and `source_feat_ref` to `source_prototype_ref`. |
| HIGH | **Missing journey spec files**: The manifest references 4 journeys (MAIN-001, EXCEPTION-001, EXCEPTION-002, RETRY-001) but only `JOURNEY-MAIN-001.md` exists as a spec file. The other 3 journeys lack dedicated spec files. | Create spec files for JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, and JOURNEY-RETRY-001. |
| MEDIUM | The manifest has 8 items (2 per journey) which is a reasonable split. However, JOURNEY-RETRY-001 is P1 priority while the gate rule requires at least 1 exception journey. The current 2 exception journeys (EXCEPTION-001, EXCEPTION-002) satisfy this at P0, but the retry journey's P1 status means its tests could be cut without violating the minimum exception journey requirement. | No immediate action required, but document this in the settlement report. |

---

### 11. `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-journey-spec/JOURNEY-MAIN-001.md`

| Check | Status | Finding |
|-------|--------|---------|
| Each spec has: entry_point, user_steps, expected_ui_states, expected_network_events, expected_persistence | PASS | All sections present |
| Each spec has evidence_required with >=playwright_trace and screenshot | PASS | Contains playwright_trace, screenshot_final, network_log, persistence_assertion, console_error_check_result |
| Each spec has anti_false_pass_checks with >=1 check | PASS | 5 checks present (no_console_error, backend_submission_exists, submission_id_matches_response_id, no_pending_network_requests, responsibility_verification_matches_displayed_state) |
| Each spec has source_refs traceability | PASS | `source_prototype_ref` in case metadata |
| Exception journey specs include error condition trigger | N/A | This is a main journey; not applicable |

**Issues:**

| Severity | Description | Recommendation |
|----------|-------------|----------------|
| MEDIUM | The spec uses `source_prototype_ref: FEAT-SRC-001-001.Scope` as the prototype reference. Since this is an API-derived journey (no actual prototype), the reference should point to the FEAT document that drives the journey, not a prototype. | Change to `source_feat_ref: FEAT-SRC-001-001.Scope` for consistency with API-derived mode. |
| LOW | The `case_id` field uses `e2e_case.journey.main.happy` but the coverage manifest uses `e2e.journey.main.happy`. These should align for traceability. | Align naming: either both use the `e2e_case.` prefix or both omit it. |

---

## Cross-Cutting Issues

### Missing Files (CRITICAL)

| Expected File | Status | Impact |
|---------------|--------|--------|
| `ssot/tests/api/FEAT-SRC-001-003/api-coverage-manifest.yaml` | **MISSING** | Blocks gate evaluation for FEAT-SRC-001-003 |
| `ssot/tests/api/FEAT-SRC-001-004/api-coverage-manifest.yaml` | **MISSING** | Blocks gate evaluation for FEAT-SRC-001-004 |
| `ssot/tests/api/FEAT-SRC-001-005/api-coverage-manifest.yaml` | **MISSING** | Blocks gate evaluation for FEAT-SRC-001-005 |
| `ssot/tests/api/FEAT-SRC-001-003/api-test-spec/` (directory) | **MISSING** | No test specs for 4 capabilities in FEAT-SRC-001-003 |
| `ssot/tests/api/FEAT-SRC-001-004/api-test-spec/` (directory) | **MISSING** | No test specs for 4 capabilities in FEAT-SRC-001-004 |
| `ssot/tests/api/FEAT-SRC-001-005/api-test-spec/` (directory) | **MISSING** | No test specs for 4 capabilities in FEAT-SRC-001-005 |
| `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-journey-spec/JOURNEY-EXCEPTION-001.md` | **MISSING** | E2E journey without spec |
| `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-journey-spec/JOURNEY-EXCEPTION-002.md` | **MISSING** | E2E journey without spec |
| `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-001-001/e2e-journey-spec/JOURNEY-RETRY-001.md` | **MISSING** | E2E journey without spec |

### Traceability Gaps

| Issue | Severity | Description |
|-------|----------|-------------|
| Anti-false-pass checks missing in 18/19 API specs | HIGH | ADR-047 requires this in every spec; only 1 of 19 has it |
| Source_refs sections missing in all 19 API specs | HIGH | Each spec needs a dedicated source_refs section linking to exact FEAT sections |
| E2E manifest field naming inconsistent with schema | HIGH | `journey` vs `journey_id`, `source_feat_ref` vs `source_prototype_ref` |

### Structural Consistency

| Issue | Severity | Description |
|-------|----------|-------------|
| P0 coverage item counts below minimum for some capabilities | HIGH | LOOP-RESPONSIBILITY-001 (4 items) and LOOP-REFLOW-BOUNDS-001 (4 items) are below the >=5 recommended minimum for P0 |
| Parameter validation dimension missing from manifest items | MEDIUM | Several P0 capabilities in FEAT-SRC-001-002 lack parameter_validation coverage items despite the priority matrix requiring it |
| Timestamps are placeholder values | LOW | All `generated_at` fields use `2026-04-11T00:00:00Z` |

---

## Issue Summary by Severity

| Severity | Count | Action Required |
|----------|-------|-----------------|
| CRITICAL | 6 | **BLOCK** - Missing manifest files and spec directories for FEAT-SRC-001-003/004/005 |
| HIGH | 7 | **WARN** - Missing anti-false-pass checks, missing E2E journey specs, field naming inconsistencies, P0 coverage minimum |
| MEDIUM | 9 | **INFO** - Parameter validation gaps, derivation_mode field, source_refs sections |
| LOW | 7 | **NOTE** - Timestamp placeholders, naming conventions, cleanup failure handling |

---

## Remediation Priority

### Must Fix Before Gate (CRITICAL + HIGH)

1. **Generate missing manifests** for FEAT-SRC-001-003, FEAT-SRC-001-004, FEAT-SRC-001-005 using `ll-qa-api-manifest-init`
2. **Generate API test specs** for all 3 missing feature directories using `ll-qa-api-spec-gen`
3. **Add anti_false_pass_checks** to all 18 missing API spec files under FEAT-SRC-001-001
4. **Add source_refs sections** to all 19 API spec files under FEAT-SRC-001-001
5. **Create E2E journey specs** for JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-RETRY-001
6. **Fix E2E manifest field naming** to align with ADR-047 schema
7. **Address P0 coverage minimum** for LOOP-RESPONSIBILITY-001 and LOOP-REFLOW-BOUNDS-001

### Should Fix Before Gate (MEDIUM)

8. Add explicit `derivation_mode` field to E2E journey plan metadata
9. Add missing parameter_validation coverage items to FEAT-SRC-001-002 manifest
10. Clarify retry vs revisit journey cut relationship in E2E plan
11. Add expected HTTP status code assertions to happy path specs

### Nice to Have (LOW)

12. Replace placeholder timestamps with actual generation times
13. Document spec naming convention
14. Add cleanup failure handling to database-operating specs

---

## Comparison with Reference (FEAT-SRC-005-001)

The reference manifest for FEAT-SRC-005-001 demonstrates several patterns that the SRC-001 artifacts should follow:

1. **Complete chain**: FEAT-SRC-005-001 has all 3 layers (plan, manifest, specs) fully populated. SRC-001 has this only for 001 and 002.
2. **Coverage item depth**: FEAT-SRC-005-001's reference manifest has 19 items across 7 capabilities with consistent field naming. SRC-001-001's manifest has 25 items which is good depth.
3. **Field naming consistency**: The reference uses standard field names. SRC-001's E2E manifest deviates with `journey` vs `journey_id`.
4. **Spec coverage**: FEAT-SRC-005-001 has 5 spec files for its capabilities. SRC-001-001 has 19 spec files which exceeds the reference in quantity but lacks anti-false-pass checks.

---

## Final Verdict

**CONDITIONAL PASS** -- The SRC-001 dual-chain test specifications are structurally sound for the completed portions (FEAT-SRC-001-001 and FEAT-SRC-001-002) but are incomplete for FEAT-SRC-001-003, FEAT-SRC-001-004, and FEAT-SRC-001-005. The 6 CRITICAL missing files and 7 HIGH severity structural gaps must be resolved before the release gate can evaluate the full SRC-001 chain.

The quality of completed artifacts (particularly the 19 API specs for FEAT-SRC-001-001 and the E2E journey plan) demonstrates good understanding of the ADR-047 framework, but the missing anti-false-pass checks across specs represents a systematic gap that should be addressed via batch regeneration rather than manual editing.
