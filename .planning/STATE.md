---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成
status: ROADMAP_CREATED
last_updated: "2026-04-29"
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: TBD
  completed_plans: 0
  percent: 0
---

# Project State

**Project:** v2.3 ADR-055 Bug 流转闭环与 GSD Execute-Phase 集成
**Status:** Roadmap created, ready for phase planning
**Core Value:** 建立 Bug 发现→验收确认→修复→再验证的完整流转机制，与 GSD execute-phase 无缝集成
**Current focus:** Execute Phase 25 — Bug 注册表与状态机

## Accumulated Context from Previous Milestones

### v2.2 双链执行闭环 (Shipped: 2026-04-24)
Delivered:
- 需求轴统一入口：ll-qa-api-from-feat, ll-qa-e2e-from-proto
- spec 桥接层：SPEC_ADAPTER_COMPAT, spec_adapter.py, test_orchestrator.py
- 实施轴 P0 模块：run_manifest_gen.py, scenario_spec_compile.py, state_machine_executor.py
- 验收闭环：independent_verifier, settlement, gate-evaluate
- 487 个测试（Phase 17:238, Phase 18:121, Phase 19:128）

### v2.1 双链双轴测试强化 (Shipped: 2026-04-23)
Delivered:
- TESTSET/Environment/Gate YAML Schema 定义
- enum_guard.py + governance_validator.py
- Frozen Contract 追溯（FC-001~FC-007）
- SSOT 写入路径集成

### v2.0 ADR-050/051 SSOT 语义治理升级 (Shipped: 2026-04-22)
Delivered:
- FRZ 冻结层结构 + MSC 5维验证
- SSOT 语义抽取链
- 变更分级机制

### v1.0/v1.1 (Shipped: 2026-04-17~21)
Delivered:
- QA Schema 定义 + 11 个 QA 技能
- Patch 基础设施 + PatchContext

## Roadmap Summary

| Phase | Goal | Requirements | Status |
|-------|------|-------------|--------|
| 25 | Bug 注册表与状态机 | BUG-REG-01~03, BUG-PHASE-01~02, BUG-INTEG-01~02 | Pending |
| 26 | 验收层集成 | GATE-REM-01~02, GATE-INTEG-01~02, PUSH-MODEL-01 | Pending |
| 27 | GSD 闭环验证 | VERIFY-01~04, CLI-01~02, SHADOW-01, AUDIT-01, INTEG-TEST-01 | Pending |

**Coverage:** 19/19 requirements mapped (100%)

## Phase 20 Results

**Delivered:**
- `cli/lib/semantic_drift_scanner.py` — Core scanner with overlay elevation and API duplicate detection
- `cli/lib/test_semantic_drift_scanner.py` — 14 unit tests, 84% coverage
- CLI with human and JSON output formats
- Found 4 existing violations in current SSOT
- Fixed `ll-product-epic-to-feat` FEAT decomposition — now prioritizes capability_axes over product_surface
- Added 6 unit tests for FEAT derivation logic
- All tests pass (27 total tests across both components)

## Phase 21 Results

**Delivered:**
- **FIX-P1-01 (ll-dev-feat-to-proto 低保真问题修复):**
  - Fixed menu overlay blocking issue — all overlays now have `hidden` attribute by default
  - Reduced placeholder lint threshold from 10 to 3 for higher fidelity
  - Enhanced `_check_initial_view_integrity()` with explicit overlay type checking
  - Added complete modal and drawer implementations to generic-hifi template
  - All templates (src001, src002, generic-hifi) now have consistent overlay structure

- **FIX-P1-02 (Journey closure split problem):**
  - Enhanced journey structural spec with explicit wizard/hub + sheets pattern notes
  - Improved route map building with `surface_kind` and `journey_pattern` fields
  - Fixed reachability check with wizard pattern awareness (implicit hub-sheet connections)
  - Enhanced bundle building with `is_multi_feat_journey` and `journey_coherence` fields
  - Multi-FEAT journeys now maintain coherence through shared surface structure

## Phase 22 Results

**Delivered:**
- **FIX-P1-03 (ll-dev-feat-to-tech Subject Drift):**
  - Reordered `feature_axis()` to check for engineering baseline patterns BEFORE governance patterns
  - Updated `assess_optional_artifacts()` to be more conservative with ARCH/API generation
  - Added explicit engineering baseline detection at start of axis detection

- **FIX-P1-04 (ll-dev-feat-to-tech Template Over-Sharing):**
  - Modified `build_tech_docs()` to skip generic "Minimal Code Skeleton" for engineering baseline features
  - Engineering baseline features now rely solely on specific implementation unit mappings

- **FIX-P1-05 (ll-dev-tech-to-impl Execution Layer Drift):**
  - Added `is_engineering_baseline_feature()` helper function
  - Updated `implementation_units()` to filter out legacy paths: `src/be/`, `.tmp/external/`, `ssot/testset/`
  - Updated `classified_touch_units()` to use engineering baseline classification

## Phase 23 Results

**Delivered:**
- **FIX-P1-06 (ll-qa-feat-to-testset Template Issue):**
  - Already resolved by ADR-053 — skill was deprecated and fully removed in v2.2
  - Replaced by `ll-qa-api-from-feat` and `ll-qa-e2e-from-proto`

- **FIX-P1-07 (ll-governance-failure-capture Output Location):**
  - Already implemented correctly — outputs to `tests/defect/failure-cases/`
  - Code in `workflow_runtime.py` confirms proper routing

- **FIX-P1-08 (ll-dev-proto-to-ui Single Document Output):**
  - Already implemented correctly — outputs single `ui-spec-bundle.md` with embedded flow map

## Phase 24 Results

**Delivered:**
- **FIX-P1-09 (impl-spec-test Chinese Markdown Parsing):**
  - Added `_parse_markdown_sections()` with Chinese heading support
  - Added `validate_markdown_sections()` for file validation
  - Added 8 comprehensive tests for Chinese heading parsing
  - All 17 tests pass (no regression)

- **ENH-P1-01 (api_required Capability-Boundary Detection):**
  - Removed STRONG_API_KEYWORDS, WEAK_API_KEYWORDS, NEGATION_MARKERS
  - Added `detect_api_surface_in_scope()` with regex-based detection
  - Only checks scope and outputs fields (per D-06)
  - Conservative for engineering baseline FEATs (per D-08)

- **ENH-P1-02 (ssot_type Declaration Enforcement):**
  - Added ssot_type to TECH/ARCH/API frontmatter
  - Added ssot_type to JSON payload blocks
  - Added ssot_type to bundle root and frontmatter

- **ENH-P1-03 (API Preconditions and Post-conditions Chapter):**
  - Extended DEFAULT_API_COMMAND_SPECS with 7 new fields
  - Added Preconditions and Post-conditions chapter with per-command context
  - Added 6-column state transition table
  - Added narrative summary helper
  - Updated consistency checks for preconditions completeness

- **ENH-P1-04 (Complete source_refs Generation):**
  - Enhanced `build_refs()` to return epic_ref and src_ref
  - Enhanced `_normalized_source_refs()` with complete upstream traceability
  - Added type-tagged refs: ARCH:, API:, EPIC:, SRC:, SURFACE:

- **ENH-P1-05 (TESTSET Auto-Trigger):**
  - Added `_trigger_testset_generation()` to feat_to_tech_runtime.py
  - Non-blocking, fire-and-forget trigger
  - Triggers when api_required or frontend_required is true
  - Writes audit trail to testset-trigger-record.json
  - Integrated into run_workflow() after validate_package_readiness()

## v2.3 Phase Overview

| Phase | Name | Target Requirements | Status |
|-------|------|-------------------|--------|
| 25 | Bug 注册表与状态机 | BUG-REG-01~03, BUG-PHASE-01~02, BUG-INTEG-01~02 | **Pending** |
| 26 | 验收层集成 | GATE-REM-01~02, GATE-INTEG-01~02, PUSH-MODEL-01 | **Pending** |
| 27 | GSD 闭环验证 | VERIFY-01~04, CLI-01~02, SHADOW-01, AUDIT-01, INTEG-TEST-01 | **Pending** |

## Artifacts

- `.planning/PROJECT.md` — Project context (updated for v2.3)
- `.planning/config.json` — Workflow preferences
- `.planning/ROADMAP.md` — Phase structure (v2.3 roadmap created)
- `.planning/REQUIREMENTS.md` — Requirements (19 v2.3 requirements defined)
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` — ADR (source of truth)

---
*Last updated: 2026-04-29 — v2.3 roadmap created, Phase 25-27 defined, ready for planning*
