/# Milestone v2.0 — Project Summary

**Generated:** 2026-04-22
**Purpose:** Team onboarding and project review

---

## 1. Project Overview

**Name:** ADR-050/051 SSOT 语义治理升级

**What This Is:** A complete transformation of the SSOT (Single Source of Truth) pipeline from a "generation chain" to a "semantic extraction chain." The FRZ (freeze) package becomes the single source of truth, and all downstream artifacts (SRC, EPIC, FEAT) are deterministically extracted from it rather than independently generated. The execution layer can only supplement, never rewrite semantics. All changes are graded and routed back through governance.

**Core Value:** Ensure SSOT no longer generates layer-by-layer, but instead extracts semantics hierarchically from FRZ frozen packages. Execution layers can only complete — not rewrite — semantics.

**Timeline:** 2026-04-18 → 2026-04-22 (4 days)

**Milestone Status:** Complete (5/5 phases, 16/16 plans)

---

## 2. Architecture & Technical Decisions

- **Decision:** FRZ becomes the single source of truth (not raw input)
  - **Why:** ADR-050 identified that the old generation chain produced semantic drift at each layer
  - **Phase:** Phase 7

- **Decision:** Deterministic rule-template projection instead of LLM-based extraction
  - **Why:** Guarantees semantic fidelity; extraction is a lossless mapping, not a creative process
  - **Phase:** Phase 8

- **Decision:** MSC (Minimum Semantic Completeness) 5-dimension validation gate before freeze
  - **Why:** FRZ packages must pass semantic completeness checks (product_boundary, core_journey, domain_entity, state_machine, acceptance_contract) before being frozen
  - **Phase:** Phase 7

- **Decision:** Frozen dataclasses (not Pydantic) for all schema modules
  - **Why:** Consistency with existing `qa_schemas.py` pattern; immutability prevents hidden mutations
  - **Phase:** Phase 7

- **Decision:** Semantic drift detection with projection invariance guard
  - **Why:** Prevents extraction from adding fields beyond what FRZ defines; enforces `derived_allowed` whitelist
  - **Phase:** Phase 8

- **Decision:** Change classification (visual/interaction/semantic → Minor/Major)
  - **Why:** Not all changes are equal; Minor patches settle locally, Major patches must flow back to FRZ re-freeze
  - **Phase:** Phase 10

- **Decision:** Backwrite-as-records (not direct SSOT modification)
  - **Why:** Per ADR-049, patches create structured YAML records for human review, never directly modify SSOT files
  - **Phase:** Phase 10

- **Decision:** `graphlib.TopologicalSorter` for Task Pack dependency resolution
  - **Why:** Zero external dependencies; Python 3.9+ stdlib handles DAG resolution
  - **Phase:** Phase 11

- **Decision:** Layered baseline modes for dev skill validation (full / journey_sm / product_boundary)
  - **Why:** Different skills need different anchor scopes; full checks all FRZ anchors, journey_sm only JRN+SM, product_boundary skips anchor checks
  - **Phase:** Phase 9

---

## 3. Phases Delivered

| Phase | Name | Status | One-Liner |
|-------|------|--------|-----------|
| 7 | FRZ 冻结层 | Complete | FRZPackage frozen dataclass with MSC 5-dim validation, anchor + FRZ registries, ll-frz-manage CLI skill |
| 8 | FRZ→SRC 语义抽取链 | Complete | Drift detection, projection guard, FRZ→SRC/EPIC/FEAT extraction with anchor inheritance and cascade orchestration |
| 9 | 执行语义稳定 | Complete | silent_override.py classifier, 9th dimension in impl-spec-test, validate_output.sh integration across 6 dev skills |
| 10 | 变更分级协同 | Complete | Tri-classification runtime, Minor patch settle (backwrite-as-records), FRZ revise with circular chain prevention, grade_level context injection |
| 11 | Task Pack 结构 | Complete | YAML schema + Python validator, depends_on topological sort resolution, sample Task Pack |

---

## 4. Requirements Coverage

### Phase 7 — FRZ 冻结层 (6/6)
- ✅ FRZ-01: FRZ package structure with MSC 5-dim fields
- ✅ FRZ-02: MSC validator minimum semantic completeness
- ✅ FRZ-03: FRZ registry records version, status, created_at
- ✅ FRZ-04: ll-frz-manage skill with validate command
- ✅ FRZ-05: ll-frz-manage skill with freeze command
- ✅ FRZ-06: ll-frz-manage skill with list command

### Phase 8 — FRZ→SRC 语义抽取链 (5/5)
- ✅ EXTR-01: FRZ→SRC rule-template extraction
- ✅ EXTR-02: FRZ→FEAT extraction (via EPIC)
- ✅ EXTR-03: Anchor ID registry with register/resolve/list
- ✅ EXTR-04: Projection invariance guard
- ✅ EXTR-05: Semantic drift detection

### Phase 9 — 执行语义稳定 (4/4)
- ✅ STAB-01: silent_override.py classifier
- ✅ STAB-02: 9th dimension in impl-spec-test
- ✅ STAB-03: Dev skill validate_output.sh integration
- ✅ STAB-04: Change vs clarification classification

### Phase 10 — 变更分级协同 (4/4)
- ✅ GRADE-01: Tri-classification + GradeLevel enum
- ✅ GRADE-02: Minor patch settle (backwrite-as-records)
- ✅ GRADE-03: FRZ revise with circular chain prevention
- ✅ GRADE-04: Patch-aware context grade_level injection

### Phase 11 — Task Pack 结构 (2/2 active, 3 deferred)
- ✅ PACK-01: Task Pack YAML schema + validator
- ✅ PACK-02: depends_on topological sort resolution
- ⏭️ PACK-03: Deferred to v2.1 (automated execution loop)
- ⏭️ PACK-04: Deferred to v2.1 (failure handling)
- ⏭️ PACK-05: Deferred to v2.1 (settlement integration)

**Total:** 21/21 active requirements satisfied. 3 deferred to v2.1.

---

## 5. Key Decisions Log

| ID | Decision | Phase | Rationale |
|----|----------|-------|-----------|
| D-07-01 | Frozen dataclasses over Pydantic | 7 | Consistency with qa_schemas.py pattern |
| D-07-02 | MSC validation gate before freeze | 7 | Cannot freeze semantically incomplete packages |
| D-08-01 | Rule-template projection (deterministic, no LLM) | 8 | Guarantees semantic fidelity |
| D-08-02 | GUARD_INTRINSIC_KEYS broader than INTRINSIC_KEYS | 8 | Guard operates at broader projection context |
| D-08-03 | Cascade handles both ExtractResult dataclass and dict | 8 | Downstream extract functions may return either type |
| D-09-01 | Anchor ID keys filtered from derived_allowed check | 9 | Anchor IDs are valid content keys, not derived metadata |
| D-09-02 | Layered baseline modes for different skill scopes | 9 | Different skills need different anchor validation depth |
| D-10-01 | Semantic dominates: mixed inputs always → MAJOR | 10 | Safety-first: any semantic change requires FRZ re-freeze |
| D-10-02 | Backwrite-as-records, not direct SSOT modification | 10 | Human review gate before SSOT changes |
| D-10-03 | FIXED column list output (not conditional) | 10 | Preserves downstream column-position parsing |
| D-11-01 | Orphan depends_on detection at schema level | 11 | Catch errors early before resolver runs |
| D-11-02 | graphlib.TopologicalSorter (stdlib, zero deps) | 11 | No external dependencies needed |

---

## 6. Tech Debt & Deferred Items

### Deferred to v2.1
- **PACK-03/04/05:** Automated execution loop, failure handling, settlement integration — deferred to allow v2.0 to ship with schema + resolver foundation
- **ll-frz-manage --apply flag:** Stub for future SSOT modification capability; currently prints warning

### Known Stubs
- **STEP_MODULE_MAP downstream layers:** Cascade defines modules for EPIC, FEAT, TECH, UI, TEST, IMPL — only SRC extraction is implemented; others gracefully skipped with warnings (by design)

### Lessons Learned
- Hyphenated skill directory names are not valid Python module names — requires `importlib` or `sys.path` workarounds
- Worktree isolation caused file visibility issues (silent_override.py missing from different worktree)
- Shallow copy of test fixtures caused mutation bugs across tests — use `deepcopy`
- Empty output_data should pass guard early — no content to violate constraints

---

## 7. Getting Started

- **Codebase root:** `E:\ai\LEE-Lite-skill-first`
- **Core library modules:** `cli/lib/` — FRZ schema, registries, drift detection, projection guard, silent override, task pack schema/resolver
- **Skills:** `skills/` — ll-frz-manage, ll-product-src-to-epic, ll-product-epic-to-feat, ll-patch-capture, ll-experience-patch-settle, ll-qa-impl-spec-test, ll-patch-aware-context, ll-dev-*
- **SSOT artifacts:** `ssot/` — ADRs, SRC, EPIC, FEAT, TECH, registry, schemas, tasks
- **Planning artifacts:** `.planning/` — ROADMAP, STATE, phase summaries, reports
- **Run tests:** `pytest cli/lib/ -v` for core library tests
- **Run skill tests:** `pytest skills/*/scripts/test_*.py -v` per skill
- **FRZ CLI:** `python skills/ll-frz-manage/scripts/frz_manage_runtime.py --help`

---

## Stats

- **Timeline:** 2026-04-18 → 2026-04-22 (4 days)
- **Phases:** 5 / 5 complete
- **Commits:** 78
- **Files changed:** 125 (+22,654 / -3,251)
- **Contributors:** shadowyang-42
- **Total tests:** ~300+ passing across all modules
