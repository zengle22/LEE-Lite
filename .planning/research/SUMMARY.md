# Project Research Summary

**Project:** LEE-Lite-skill-first v2.0 — SSOT Semantic Governance
**Domain:** AI-assisted development governance — freeze-package management, semantic extraction chains, sequential task orchestration
**Researched:** 2026-04-18
**Confidence:** HIGH

## Executive Summary

This is a CLI-first governance tool that enforces semantic traceability from frozen requirements (FRZ) through downstream SSOT objects (SRC, EPIC, FEAT), task execution (Task Packs), and validation (dual-chain testing). The v2.0 upgrade transforms the existing v1.x generation-model SSOT into an extraction-model where all downstream layers project from a single frozen source, preventing the cumulative semantic drift inherent in chained generation.

The recommended approach is conservative: reuse the existing `execution_runner.py`, `job_state.py`, and loop infrastructure; add Pydantic v2 for runtime validation, DeepDiff for drift detection, and `graphlib.TopologicalSorter` for dependency resolution; explicitly reject complex orchestration frameworks (Airflow, Prefect) in favor of a simple sequential loop. The architecture introduces five layers — FRZ Governance, SSOT Extraction, Task Pack Orchestration, existing Execution, and Change Grading — with a closed-loop feedback path where changes discovered during execution are classified and routed back through the appropriate governance channel.

The primary risk is semantic corruption at three boundaries: (1) incomplete FRZ entering the pipeline, (2) extraction agents covertly inventing content instead of projecting, and (3) execution-layer changes bypassing the Major change path. All three are prevented by automated gates: MSC hard-block on FRZ ingestion, anchor-ID provenance tracking on extraction, and automated semantic-diff classification on execution changes. These gates must be implemented early — they are the backbone of the entire governance model.

## Key Findings

### Recommended Stack

**Core technologies:**
- **Pydantic v2 (2.13.0):** FRZ MSC validation, Task Pack schema, Patch schema upgrade — existing dataclass pattern in `qa_schemas.py` (29 classes) maps cleanly to Pydantic `BaseModel`
- **DeepDiff (9.0.0):** Semantic drift detection between FRZ/SRC/EPIC/FEAT snapshots — handles arbitrary nested dicts/lists
- **ruamel.yaml (0.19.1):** Round-trip YAML parsing with comment preservation — critical for maintaining human-readable SSOT artifacts
- **graphlib.TopologicalSorter (stdlib):** Linear dependency resolution for Task Pack `depends_on` — no external dependency needed
- **PyYAML (6.0.2) + jsonschema (4.26.0):** Existing YAML stack + interoperable schema validation for external tools
- **rich (13.9+):** CLI output formatting for Pack status and MSC validation results

**What NOT to add:** Airflow/Prefect/Dagster (ADR-051 rejects complex orchestration), ORMs (filesystem-based is sufficient), web frameworks (CLI-first), LLM frameworks (extraction is structural, not NLP-based).

### Expected Features

**Must have (table stakes):**
- FRZ MSC 5-dimension validator — gate that blocks downstream if any dimension (product_boundary, core_journeys, domain_model, state_machine, acceptance_contract) is missing or empty
- FRZ package structure (4-file minimum) — index.md, freeze.yaml, evidence.yaml, frz-package.json
- Semantic extraction: FRZ to SRC projection — anchor ID tracing, DeepDiff comparison, source labeling
- Semantic drift detection — compare FRZ snapshots to detect when semantics change vs clarify
- Change classification: clarification vs semantic change — "does downstream test expectation change?" is the defining criterion
- Change grading: Minor (Patch) vs Major (FRZ re-freeze) — tri-classification (visual/interaction/semantic) mapped to two governance paths
- Task Pack YAML parser + sequential loop executor — thin wrapper around existing `execution_runner.py`
- Task Pack failure pause + human intervention — no auto-skip, loop waits for human
- Dual-chain test binding — test-api/test-e2e tasks trigger ADR-047 chains, evidence binds to verifies field
- Three-axis management intensity — requirements (strong), implementation (weak), evidence (light)

**Should have (competitive differentiators):**
- Projection invariance enforcement — guarantees FRZ semantics survive projection
- Patch-SSOT Integration — closed-loop experience capture from code changes back through governance
- Sequential-only execution as a deliberate constraint — predictable, reproducible, debuggable

**Defer (post-MVP):**
- Batch Patch settlement operations — quality of life, not blocking
- FRZ slimming principle enforcement — warning system
- proposed expiration mechanism — add once trace inheritance is stable

### Architecture Approach

The architecture is a layered governance pipeline with a closed-loop feedback path. Data flows from external frameworks into FRZ (human-driven freeze), then through SSOT extraction (FRZ directly to each layer via projection rules), then through Task Pack execution (sequential loop over existing runner), then through dual-chain validation, and finally through change grading where discovered changes are classified and routed back to either the Patch layer (minor) or FRZ re-freeze (major).

**Major components:**
1. **FRZ Governance Layer** (validator, evidence tracker, registry) — ensures FRZ is complete and trustworthy before anything reads from it
2. **Semantic Extraction Chain** (extractor, projection rules, anchor tracker, drift detector, stability guard) — transforms FRZ into SSOT objects without inventing content
3. **Task Pack Orchestration** (parser, dependency resolver, sequential loop, state machine, dual-chain trigger) — drives execution in dependency order with failure pause
4. **Change Grading Pipeline** (classifier, minor handler, major handler) — routes execution-discovered changes through correct governance channel

**Key patterns:** Projection Invariance (extract, never generate), Sequential Loop with Failure Pause (one task at a time, pause on failure), Change Classification at Boundary (all changes pass through classifier before action).

### Critical Pitfalls

1. **FRZ Semantic Incompleteness** — Incomplete FRZ causes the entire downstream chain to produce shallow or hallucinated content. Prevention: MSC validation as a hard gate (non-zero exit code), human sign-off required before frozen status.
2. **Semantic Extraction Becomes Covert Generation** — AI fills gaps by inventing details not in FRZ. Prevention: anchor-ID provenance tracking on every SSOT object, `ssot audit` command to flag content without FRZ reference.
3. **Execution Layer Semantic Drift (Silent Override)** — Agents reclassify semantic changes as clarifications to avoid costly FRZ re-freeze. Prevention: automated semantic diff on user_story, AC, state_machine fields — any change triggers Major classification regardless of agent self-assessment.
4. **Change Classification Gaming** — Teams reclassify semantic changes as interaction changes. Prevention: automated impact analysis (not just claimed category), human review for Minor changes exceeding threshold.
5. **Patch Accumulation Without Clean Rebase** — Patches grow unbounded, degrading performance and readability. Prevention: enforce N=5 patch threshold, auto-block further patches until rebase is complete.

## Implications for Roadmap

Based on research, suggested phase structure (5 phases):

### Phase 1: FRZ Foundation
**Rationale:** FRZ is the semantic truth source. Everything downstream depends on it being complete and validated. Must be built first.
**Delivers:** FRZ package schema (Pydantic), MSC 5-dimension validator (hard gate), FRZ Registry, CLI commands (`ll frz validate`, `ll frz msc-check`)
**Addresses:** FRZ package structure, FRZ MSC validator (table stakes #1, #2)
**Avoids:** Pitfall 1 (MSC incompleteness) by implementing hard gate; Pitfall 7 (FRZ staleness) by establishing registry with version tracking
**Uses:** Pydantic v2 for schema, PyYAML for FRZ package loading
**Research flag:** Standard patterns — unlikely to need deeper research. Existing `qa_schemas.py` provides migration pattern.

### Phase 2: Semantic Extraction Chain
**Rationale:** Transform SSOT from generation to extraction model. Requires validated FRZ from Phase 1. Must complete before Task Packs can reference valid SSOT.
**Delivers:** Projection Rules module, Semantic Extractor (FRZ to SRC, EPIC, FEAT), Anchor Tracker, Drift Detector (DeepDiff-based), Extract CLI commands (`ll extract src`, `ll extract epic`, `ll extract feat`)
**Addresses:** Semantic extraction (table stakes #3), semantic drift detection (#4), projection invariance (differentiator)
**Avoids:** Pitfall 2 (covert generation) via anchor-ID provenance; Integration Pitfall 2 (missing FRZ refs) via one-time backfill migration of existing SSOT objects
**Uses:** DeepDiff for drift detection, ruamel.yaml for comment-preserving writes
**Research flag:** Needs deeper research — projection rules per layer need precise definition; QA skill prompt audit needed for extraction model compatibility; anchor-ID propagation mechanism through multi-hop extraction needs concrete design.

### Phase 3: Task Pack Orchestration
**Rationale:** Task Packs drive execution. Built on validated SSOT from Phase 2 and existing `execution_runner.py`. Highest usage frequency, immediate productivity gain.
**Delivers:** Task Pack Parser (YAML + schema validation), Dependency Resolver, Task State Machine (7 states), Sequential Loop (ADR-051), Dual Chain Trigger, Pack CLI commands (`ll pack validate`, `ll pack run`, `ll pack status`, `ll pack resume`)
**Addresses:** Task Pack YAML parser (#7), sequential loop executor (#8), failure pause + human intervention (#9), status persistence (#10), dual-chain test binding (#11)
**Avoids:** Pitfall 5 (axis creep) via strict schema; Pitfall 6 (failure accumulation) via pause escalation; Integration Pitfall 3 (ADR-018 compatibility) via explicit adapter interface
**Uses:** graphlib.TopologicalSorter (stdlib), existing execution_runner.py + job_state.py
**Research flag:** Standard patterns — unlikely to need deeper research. ADR-051 is explicit, existing infrastructure is well-understood.

### Phase 4: Change Classification & Grading
**Rationale:** Closes the governance loop. Ensures changes discovered during execution flow back correctly. Integrates existing ADR-049 Patch layer with new governance rules.
**Delivers:** Change Classifier (visual/interaction/semantic), Stability Guard (pre/post execution checks), Minor Change Handler (extends patch_auto_register), Major Change Handler (FRZ re-freeze workflow trigger)
**Addresses:** Change classification (#5), change grading (#6), Patch-SSOT Integration (differentiator), version tracking for Patches (#12)
**Avoids:** Pitfall 3 (silent override) via automated semantic diff gate; Pitfall 4 (classification gaming) via impact-based classifier; Integration Pitfall 1 (patch vs semantic conflict) by routing semantic check through patch registrar
**Uses:** DeepDiff for semantic comparison, existing patch_schema.py as base
**Research flag:** Needs deeper research — the boundary between "interaction" (Minor) and "semantic" (Major) is inherently fuzzy; needs concrete decision-tree implementation research with test cases.

### Phase 5: Three-Axis Integration & Hardening
**Rationale:** Structural enforcement and end-to-end validation. Low implementation complexity but requires the full system to be in place.
**Delivers:** Three-axis metadata enforcement (`frz_package_ref` on SSOT objects, `verifies` bindings), Pack-level reporting, End-to-end validation pipeline, patch count monitoring and rebase enforcement
**Addresses:** Three-axis management intensity (#12), One-Pack-One-FEAT Binding (differentiator)
**Avoids:** Pitfall 8 (dual-chain detachment) via auto-populated verifies; Pitfall 9 (patch accumulation) via enforced rebase threshold
**Research flag:** Standard patterns — structural decisions, not implementation complexity. No deeper research needed.

### Phase Ordering Rationale

The order is dictated by the dependency graph discovered in FEATURES.md and confirmed by ARCHITECTURE.md:
- **Phase 1 blocks everything** — no extraction can happen without a validated FRZ
- **Phase 2 before Phase 3** — Task Packs reference FEAT objects that must exist via extraction
- **Phase 4 after Phase 3** — change classification requires both the execution layer (Phase 3) and the Patch layer (existing) to be operational
- **Phase 5 last** — integration and reporting require all upstream components to be functional

This ordering avoids pitfalls by implementing gates before the behaviors they guard: MSC gate (Phase 1) before extraction starts, provenance tracking (Phase 2) before SSOT objects are written, semantic diff (Phase 4) before execution generates changes.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Semantic Extraction):** Projection rules per layer need precise definition. QA skill prompts (11 skills) must be audited against the extraction model. The anchor-ID propagation mechanism through multi-hop extraction needs concrete design.
- **Phase 4 (Change Classification):** The boundary between "interaction change" (Minor) and "semantic change" (Major) is fuzzy — needs concrete decision-tree implementation research with test cases.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (FRZ Foundation):** Pydantic validation + hard-gate CLI is well-documented. Existing `qa_schemas.py` provides migration pattern.
- **Phase 3 (Task Pack Orchestration):** Sequential loop + topological sort + state machine are established patterns. ADR-051 is explicit. Existing `execution_runner.py` is the foundation.
- **Phase 5 (Integration & Hardening):** Metadata enforcement and reporting are structural decisions with no novel implementation challenges.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommended technologies are mature, well-documented, and verified against PyPI. Alternatives were explicitly evaluated. Migration path from existing dataclasses to Pydantic is clear. |
| Features | HIGH | Features are directly derived from ADR-050, ADR-051, ADR-045, ADR-047, ADR-049. Table stakes vs differentiators distinction is well-reasoned. MVP prioritization aligns with dependency graph. |
| Architecture | HIGH | Component boundaries are clearly defined with explicit input/output contracts. Data flows are documented with happy path, change detection path, and stability path. Anti-patterns are identified. |
| Pitfalls | HIGH | Critical pitfalls are grounded in ADR text and AI agent orchestration research. Prevention strategies are specific and actionable. Integration pitfalls address real conflicts between ADRs. |

**Overall confidence:** HIGH

### Gaps to Address

- **MSC dimension precision:** The 5 MSC dimensions need precise, programmatic validation criteria. "Complete" vs "sufficient" boundary is still judgment-based for some dimensions (especially `state_machine`).
- **Projection rules specification:** What exactly gets extracted from FRZ for SRC vs EPIC vs FEAT is defined in principle but not yet in concrete field-level rules.
- **Existing SSOT backfill strategy:** The one-time migration to add `frz_package_ref` to existing SSOT objects needs a concrete plan — which existing objects map to which FRZ packages.
- **Patch count threshold N:** ADR-050 recommends N patches trigger rebase but does not specify N. Research recommends N=5 but this needs validation against the 3000-token context budget.
- **QA skill prompt compatibility:** The 11 v1.0 QA skill prompts were designed for generation-model SSOT. Their validation logic needs auditing before extraction mode is activated.
- **DeepDiff ordered vs unordered dimensions:** Which FRZ dimensions are order-sensitive (state machine transitions) vs unordered (domain model entities) needs explicit documentation to avoid false positives in drift detection.

## Sources

### Primary (HIGH confidence)
- ADR-050: SSOT Semantic Governance Master Plan (internal) — Primary governance specification
- ADR-051: Task Pack Sequential Execution Loop (internal) — Task Pack orchestration spec
- ADR-045: FRZ Freeze Layer specification (internal) — FRZ structure and projection invariance
- ADR-047: Dual Chain Testing (internal) — API + E2E test chain verification
- ADR-049: Experience Patch Layer (internal) — Patch layer infrastructure
- ADR-018: Execution Loop Job Runner (internal) — Loop runtime foundation
- Pydantic v2.13.0 (PyPI) — Validation engine
- DeepDiff 9.0.0 (PyPI) — Structural diff engine
- ruamel.yaml 0.19.1 (PyPI) — Round-trip YAML
- Python graphlib.TopologicalSorter (stdlib docs) — Dependency resolution

### Secondary (MEDIUM confidence)
- Semantic Drift Framework (Mir 2026, preprints.org) — Drift classification with thresholds
- Data Contracts: Schema and Semantic Drift Governance (Boddu 2025/2026) — Change classification patterns
- Azure AI Agent Orchestration Patterns (Microsoft Learn) — Sequential orchestration patterns
- SC Conference AD/AE Artifact Freeze Process — Artifact freeze best practices
- ESCO Versioning System (EC) — Major/minor semantic revision classification
- IREB CPRE Requirements Management Handbook — Requirements management standards

### Tertiary (LOW confidence)
- 2026 Predictions: Architecture, Governance, and AI (Cloudera) — Data as living semantic memory trend
- CodeTracer: Towards Traceable Agent States (arXiv 2604.11641) — AI agent traceability research
- Securing the Agentic Development Lifecycle (Cycode) — AI code traceability requirements

---
*Research completed: 2026-04-18*
*Ready for roadmap: yes*
