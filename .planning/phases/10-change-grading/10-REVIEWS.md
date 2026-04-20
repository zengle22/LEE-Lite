---
phase: 10
reviewers: [codex, orchestrator-analysis]
reviewed_at: 2026-04-19T00:15:00+08:00
plans_reviewed: [10-01-PLAN.md, 10-02-PLAN.md, 10-03-PLAN.md, 10-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 10

## Gemini Review

**Status:** CLI available but not authenticated (no API key configured). Review not obtained.

## Codex Review

### Plan 10-01 — Tri-Classification + GradeLevel Schema

**Summary:** Good intent with deterministic grade derivation, but risky if ChangeClass is already semantically loaded — adding visual/semantic could break existing switch logic.

**Strengths:**
- Deterministic `grade_level = derive_grade(change_class)` fits SSOT governance
- Capturing grade early enables consistent routing across settle + context injection
- "Major recorded but not settled" preserves evidence without violating FRZ primacy

**Concerns:**
- **HIGH**: Overloading ChangeClass with visual/semantic may break existing validators/consumers
- **HIGH**: Keyword-based CN classification will misclassify mixed inputs (visual + semantic in one patch); no "highest grade wins" rule defined
- **MEDIUM**: No "unknown/uncertain" classification path; forced binary can cause wrong routing
- **MEDIUM**: CLI `--input <text|path>` needs strict path handling
- **LOW**: Patch YAML evolution (grade_level new field) needs backward-compat policy

**Suggestions:**
- Introduce separate field for tri-classification (e.g. `change_dimension`) instead of overloading ChangeClass
- Define multi-signal rule: `grade_level = max(detected_dimensions)` where semantic dominates; store `dimensions_detected` for audit
- Add `confidence` + `needs_human_review` flag when signals conflict; default to "treat as Major"
- Add tests for: mixed inputs, negations ("不改语义，只调颜色"), domain synonyms, no-indicator inputs

**Risk Assessment:** HIGH — schema meaning risk + classification robustness risk

### Plan 10-02 — Build ll-experience-patch-settle from Scratch

**Summary:** Building from scratch is correct given only __pycache__ exists. "Backwrite-as-record" is governance-friendly but may not meet stated success criteria.

**Strengths:**
- Explicit Major rejection enforces "semantic must flow back to FRZ" rule
- Recording backwrites (not auto-modifying SSOT) fits "supplement, not rewrite"
- Clear dependency on 10-01/grade derivation

**Concerns:**
- **HIGH**: Mismatch with success criteria #4 — records may be interpreted as insufficient vs actual SSOT edits
- **HIGH**: BACKWRITE_MAP depends on correct taxonomy; if 10-01 changes ChangeClass, settle couples to shaky schema
- **MEDIUM**: Needs idempotency rules (re-settle shouldn't duplicate records)
- **MEDIUM**: Where are backwrite records consumed? Risk of "evidence produced, no closure"

**Suggestions:**
- Clarify success criteria: backwrite = (A) apply SSOT edits, or (B) produce records? If A, add controlled apply mechanism gated by human approval
- Add `--dry-run` / `--overwrite` semantics; store machine-readable `backwrite_plan.yaml` per patch

**Risk Assessment:** MEDIUM-HIGH — definition-of-done ambiguity + taxonomy coupling

### Plan 10-03 — Verify/Enhance FRZ Revise Path

**Summary:** Appropriately conservative. Verify what exists, avoid rewriting, improve observability. Risk is "80% claim could be wrong in edge flows."

**Strengths:**
- Minimal surface area changes reduce regression probability
- Better list display improves governance traceability
- Adding revise-specific tests aligns with critical path

**Concerns:**
- **MEDIUM**: Conditional columns can break scripts/fixtures that parse columns
- **MEDIUM**: Corner cases: missing previous_frz, circular references, reason length/encoding
- **LOW**: MSC validation blocking revise flows — ensure intended for all scenarios

**Suggestions:**
- Provide machine-readable `--json` for listing FRZ registry
- Add tests for: multi-hop chain, invalid previous ref, CN text encoding
- Ensure registry enforces "no cycles" and validates previous FRZ existence

**Risk Assessment:** LOW-MEDIUM — safest plan; output compatibility + hidden edge cases

### Plan 10-04 — Patch-Aware Context Grading

**Summary:** Good wiring: makes grade visible during injection, tolerates old patches by deriving grade. WARNING informational avoids over-enforcement.

**Strengths:**
- Backward compatibility via auto-derive reduces migration friction
- Surfacing Major warnings improves human decision quality
- Centralizing derivation encourages consistency

**Concerns:**
- **HIGH**: If derivation happens in multiple places, drift is likely — "single source of grading truth" must be enforced
- **MEDIUM**: What if change_class is missing/invalid? No safe default defined
- **LOW**: Context output changes can affect prompt stability

**Suggestions:**
- Enforce one grading function (import from patch_schema.py); forbid local re-implementations
- Define fail-safe: if cannot derive, set grade_level = MAJOR (or UNKNOWN + treat-as-major)
- Add tests for legacy patches (no grade_level), malformed YAML, unknown change_class

**Risk Assessment:** MEDIUM — consistency risk (grading drift) + robustness risk

---

## Orchestrator Analysis (Second Reviewer)

### Plan 10-01 — Additional Concerns

**Strengths:**
- Well-structured tasks with clear acceptance criteria and automated verification
- TDD approach for runtime script ensures test coverage from the start
- Indicator lists in Chinese are appropriate for the domain (Chinese UX inputs)

**Concerns:**
- **HIGH**: The `_suggest_change_class()` in `patch_auto_register.py` already uses file-pattern heuristics. The new keyword-based classifier needs to integrate with or supersede this existing logic, but the plan says "Do NOT import from patch_auto_register.py" — this creates two independent classification systems that may disagree
- **MEDIUM**: Indicator lists are hardcoded and will drift as the domain evolves. No mechanism for updating indicator lists without code changes
- **MEDIUM**: Document input path (`--input-type document`) is described but implementation details are vague ("Check document content for semantic indicators")

### Plan 10-02 — Additional Concerns

**Strengths:**
- Clear BACKWRITE_MAP with explicit targets per change_class
- Skill skeleton follows established project patterns (ll-frz-manage reference)

**Concerns:**
- **HIGH**: The settle_runtime.py needs to FIND the actual UI Spec / Flow Spec / TESTSET files to write backwrite records. The plan mentions writing to `ssot/experience-patches/{feat_ref}/backwrites/` but doesn't specify how feat_ref maps to actual file paths — this depends on the SSOT directory structure which may not be consistent
- **MEDIUM**: Building an entire skill skeleton (7+ files) from scratch is high effort for a single phase. Risk of over-engineering with agents, contracts, lifecycle YAMLs when a simpler runtime-only approach might suffice
- **LOW**: The plan claims to cover GRADE-04 but GRADE-04 is about patch-aware context injection (covered in 10-04), not settle. The dependency on GRADE-04 seems misplaced

### Plan 10-03 — Additional Concerns

**Strengths:**
- Correct restraint: "Do NOT modify freeze_frz() or register_frz()"
- Conditional column rendering is good UX

**Concerns:**
- **MEDIUM**: The `_format_frz_list()` enhancement changes column positions conditionally, which could break any downstream tooling that parses by column position. A better approach would be fixed columns with `-` for empty values
- **LOW**: validate_output.sh uses `yq` which may not be installed on all systems (plan mentions fallback but doesn't check availability)

### Plan 10-04 — Additional Concerns

**Strengths:**
- Auto-deriving grade_level on load is elegant backward-compat
- Separating informational WARNING from policy enforcement is architecturally correct

**Concerns:**
- **HIGH**: `_load_patch_yaml()` re-deriving grade_level creates the exact drift Codex warned about — if patch_schema.py's mapping changes, old loaded patches get new grades silently. Consider storing `grade_derived_at` timestamp or checksum of the mapping used
- **MEDIUM**: The `PatchContext` dataclass doesn't need grade_level (correctly noted) but `patches_found` entries are dicts loaded from YAML — if the YAML lacks grade_level, derive_grade is called at load time in two places (_load_patch_yaml AND patch_aware_context.py summarize_patch). This duplication is the drift risk

---

## Consensus Summary

### Agreed Strengths (2+ reviewers)
- Deterministic grade derivation from change_class is the right architectural choice for SSOT governance
- Plan 10-03 is appropriately conservative — verify existing code, don't rewrite
- Major patch rejection in settle_runtime correctly enforces "semantic must flow back to FRZ"
- Backward compatibility via auto-derive of grade_level on load reduces migration friction

### Agreed Concerns (2+ reviewers — highest priority)
1. **HIGH — ChangeClass enum overload risk**: Adding `visual` and `semantic` to the existing ChangeClass enum may break existing consumers. Consider a separate `change_dimension` field or ensure all consumers are updated.
2. **HIGH — Mixed/unknown classification handling**: Keyword-based classification will fail on mixed inputs (both visual and semantic indicators in one text). Need a "highest grade wins" rule and `needs_human_review` fallback.
3. **HIGH — Grading drift**: derive_grade() is called in patch_capture_runtime, _load_patch_yaml, summarize_patch_for_context, and patch_aware_context.py. If any diverges, patches get inconsistent grades. Enforce single source of truth.
4. **HIGH — Backwrite definition ambiguity**: Success criteria says "backwrite to UI Spec / Flow Spec" but implementation writes records to backwrites/ subdirectory, not actual spec modifications. Clarify definition of done.
5. **MEDIUM — Dual classification systems**: patch_capture_runtime.py's keyword classifier and patch_auto_register.py's file-pattern `_suggest_change_class()` are independent and may disagree on the same input.

### Divergent Views
- **Plan 10-02 scope**: Codex sees the skill skeleton (7 files) as potentially ballooning; orchestrator sees it as following established project patterns but high effort for one phase. Both agree it could be simplified.
- **Conditional columns in list**: Codex sees this as a scripting compatibility risk; orchestrator agrees and suggests fixed columns with empty values instead.

### Overall Risk Assessment: MEDIUM-HIGH

The phase is architecturally sound but carries governance risks from misclassification and schema changes. The three HIGH-concern areas (ChangeClass overload, classification robustness, grading drift) could undermine the entire SSOT semantic governance model if not addressed. Mitigation:

1. **Don't overload ChangeClass** — use a separate `change_dimension` or ensure a migration path for all consumers
2. **Add `needs_human_review` fallback** for ambiguous inputs, defaulting to Major
3. **Centralize derive_grade()** as the single grading function with unit tests asserting all callers use the same mapping
4. **Clarify backwrite = records vs apply** in success criteria and ADR text
