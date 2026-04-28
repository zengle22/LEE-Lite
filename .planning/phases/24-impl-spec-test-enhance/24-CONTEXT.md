# Phase 24: impl-spec-test 增强和验证 - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 24 delivers the final set of bug fixes and quality enhancements for the v2.2.1 Failure Case Resolution milestone:

1. **FIX-P1-09:** Fix ll-qa-impl-spec-test Chinese markdown section parsing — recognize Chinese headings like "### 5.5 完成状态定义" and correctly extract excerpts
2. **ENH-P1-01:** Enhance ll-dev-feat-to-tech api_required logic — capability-boundary-based detection instead of keyword matching
3. **ENH-P1-02:** Enforce ssot_type declaration in TECH/ARCH/API output frontmatter
4. **ENH-P1-03:** Enhance API design quality — add "Preconditions and Post-conditions" chapter with caller context, idempotency, system dependency pre-state, state changes, UI surface mapping, caller follow-up flow, event tracking output
5. **ENH-P1-04:** Enhance ll-dev-tech-to-impl source_refs generation — auto-generate complete traceability chain including FEAT/TECH/ARCH/API full SSOT paths
6. **ENH-P1-05:** Auto-trigger TESTSET generation after feat-to-tech completes (conditional, non-blocking)

All changes must preserve existing test compatibility and close remaining failure-case documents.

</domain>

<decisions>
## Implementation Decisions

### FIX-P1-09: Chinese Section Parsing Strategy
- **D-01:** Use a **hybrid parsing approach**: regex-based heading extraction as the primary mechanism, with an optional AST parser (e.g., mistletoe) for structural validation when complex nesting is detected
- **D-02:** Apply parsing to **all markdown documents** in the impl package, not just specific files
- **D-03:** Regex pattern must match both Chinese and mixed Chinese/English headings (e.g., `### 5.5 完成状态定义`, `## API Contracts`)
- **D-04:** Excerpt extraction should capture 2-3 lines of content following the heading, with fallback to heading text alone if no body content exists

### ENH-P1-01: api_required Capability Boundary Detection
- **D-05:** Replace keyword-based detection entirely. Remove `STRONG_API_KEYWORDS`, `WEAK_API_KEYWORDS`, and `NEGATION_MARKERS` from `assess_optional_artifacts()`
- **D-06:** **Primary signal**: Inspect FEAT `scope` and `outputs` fields for explicit API endpoint mentions or command contract surfaces
- **D-07:** `api_required = true` when the FEAT's scope/outputs declare backend service interfaces, REST/gRPC endpoints, command handlers, or webhook contracts
- **D-08:** Engineering baseline FEATs remain conservative — only set `api_required=true` if their scope/outputs explicitly declare API surfaces (do not infer from skeleton patterns)

### ENH-P1-02: ssot_type Declaration Enforcement
- **D-09:** Add `ssot_type` field to frontmatter of all TECH/ARCH/API output documents
- **D-10:** Values: `ssot_type: "TECH"` for tech-spec.md, `ssot_type: "ARCH"` for arch-design.md, `ssot_type: "API"` for api-contract.md
- **D-11:** Also inject `ssot_type` into the JSON payload (`tech-design-bundle.json`) under each optional artifact block

### ENH-P1-03: API Preconditions and Post-conditions Chapter
- **D-12:** **Placement**: Hybrid structure
  - Per-command: caller context, idempotency key strategy, preconditions list
  - Global API-level chapter (after Command Contracts): system dependency pre-state, state changes, UI surface mapping, caller follow-up flow, event tracking output
- **D-13:** **State description format**: Both narrative text (human-readable) AND structured state transition table (machine-readable)
- **D-14:** Table schema: `| command | pre-state | post-state | side_effects | ui_surface_impact | event_outputs |`
- **D-15:** Narrative should be embedded in the markdown body; table should be embedded as a code block or JSON snippet for downstream consumption

### ENH-P1-04: source_refs Completeness
- **D-16:** `_normalized_source_refs()` in `tech_to_impl_package_builder.py` must include complete upstream traceability: FEAT ref, TECH ref, ARCH ref (if present), API ref (if present), epic freeze ref, SRC root ref, surface map ref
- **D-17:** Add `ssot_type` tagged refs format where appropriate (e.g., `TECH-xxx`, `ARCH-xxx`, `API-xxx`)
- **D-18:** Ensure `upstream_design_refs.json` also carries the complete source_refs list for bidirectional traceability

### ENH-P1-05: TESTSET Auto-trigger
- **D-19:** **Trigger condition**: Only when `api_required` or `frontend_required` is true in the tech package assessment
- **D-20:** **Integration point**: Non-blocking downstream workflow invocation at the end of `run_workflow()` in `feat_to_tech_runtime.py`, after `validate_package_readiness()` passes
- **D-21:** **Blocking model**: Fire-and-forget — feat-to-tech returns immediately; TESTSET generation runs independently
- **D-22:** TESTSET trigger should pass the same `artifacts_dir`, `feat_ref`, and `tech_ref` to the downstream TESTSET skill

### Claude's Discretion
- The exact regex pattern for Chinese heading extraction (Claude can decide based on common markdown heading patterns)
- Whether to add a lightweight markdown parser dependency or use stdlib only
- Specific formatting of the state transition table (markdown table vs JSON block)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and Milestone Context
- `.planning/REQUIREMENTS.md` — v2.2.1 Failure Case Resolution requirements (FIX-P1-09, ENH-P1-01~05)
- `.planning/ROADMAP.md` §Phase 24 — Phase goals, success criteria, planned work
- `.planning/PROJECT.md` — v2.2.1 milestone context and validated requirements

### FIX-P1-09: impl-spec-test
- `skills/ll-qa-impl-spec-test/scripts/impl_spec_test_skill_guard.py` — Current validation logic (JSON envelope only, no markdown parsing)
- `skills/ll-qa-impl-spec-test/tests/test_impl_spec_test_surface_map.py` — Existing test coverage

### ENH-P1-01~03: feat-to-tech
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py` — Contains `assess_optional_artifacts()`, `feature_axis()`, keyword-based detection logic
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_content.py` — `build_source_refs()`, `build_json_payload()`, `build_optional_api_block()`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_documents.py` — `build_api_docs()`, `build_tech_docs()`, `build_arch_docs()` — document rendering
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_contract_content.py` — `DEFAULT_API_COMMAND_SPECS`, `api_command_specs()`, `INTERFACE_CONTRACTS_BY_AXIS`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_package_builder.py` — `build_tech_package()`, `build_semantic_drift_check()`
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_runtime.py` — `run_workflow()`, `executor_run()`, `supervisor_review()` — main runtime entrypoints

### ENH-P1-04: tech-to-impl
- `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_package_builder.py` — `_normalized_source_refs()`, `build_candidate_package()`
- `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_derivation.py` — `build_refs()`, `implementation_units()`, `classified_touch_units()`
- `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_package_documents.py` — `_build_text_sections()`, document body builders

### Prior Phase Decisions
- `skills/ll-dev-feat-to-tech/scripts/feat_to_tech_derivation.py` §is_engineering_baseline_feature() — Engineering baseline detection (Phase 22)
- `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_derivation.py` §implementation_units() — Execution layer drift exclusion (Phase 22)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `keyword_hits()` in `feat_to_tech_derivation.py` — Pattern matching utility that can be repurposed for scope/outputs inspection
- `_normalized_source_refs()` in `tech_to_impl_package_builder.py` — Existing source ref normalization logic to extend
- `build_api_docs()` in `feat_to_tech_documents.py` — API document renderer to inject new preconditions/post-conditions chapter
- `impl_spec_test_skill_guard.py` — JSON envelope validator; markdown parsing needs to be added alongside existing validation

### Established Patterns
- **Frontmatter-based artifact typing**: All documents use YAML frontmatter with `artifact_type`, `status`, `schema_version`, `*_ref` fields
- **Assessment-driven conditional output**: `assessment["arch_required"]` and `assessment["api_required"]` gate optional artifact generation
- **Non-blocking downstream handoffs**: `feat_to_tech_runtime.py` already creates handoff proposals without blocking upstream
- **JSON + Markdown dual output**: Every artifact generates both `.json` and `.md` variants

### Integration Points
- **feat-to-tech → tech-to-impl**: `DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"` in `feat_to_tech_package_content.py`
- **TESTSET trigger location**: `run_workflow()` in `feat_to_tech_runtime.py` is the natural hook point — after `supervisor_review()` and `validate_output_package()`
- **API contract completeness check**: `consistency_check()` in `feat_to_tech_derivation.py` validates API contract fields — should be updated to check for preconditions/post-conditions presence

</code_context>

<specifics>
## Specific Ideas

- Chinese heading regex should handle common patterns: `^#{2,4}\s+\d+(\.\d+)*\s*[一-鿿]` and `^#{2,4}\s+[一-鿿]`
- For ENH-P1-01, consider adding a helper like `detect_api_surface_in_scope(feature)` that scans scope/outputs for endpoint URL patterns (`/v1/...`, `POST /...`), command names, or schema references
- The state transition table should be included in both `api-contract.md` body and `api-contract.json` payload for dual consumption
- TESTSET auto-trigger should log its invocation in `execution_decisions` list for audit trail

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-impl-spec-test-enhance*
*Context gathered: 2026-04-28*
