# Architecture Patterns

**Domain:** SSOT Semantic Governance — FRZ Layer, Semantic Extraction, Task Pack Orchestration
**Researched:** 2026-04-18

## Recommended Architecture

The v2.0 architecture adds a governance layer on top of the existing v1.x CLI/lib/runtime. The key principle is: **FRZ is the semantic truth source, SSOT extracts (not generates) from it, Task Packs drive execution, and changes flow back through a graded pipeline.**

### Full System Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │              EXTERNAL FRAMEWORKS            │
                    │     BMAD / Superpowers / OMC / Human        │
                    │   (PRD, Architecture, UX, Test Strategy)    │
                    └──────────────────┬──────────────────────────┘
                                       │  Discussion artifacts
                                       ▼
                    ┌─────────────────────────────────────────────┐
                    │           FRZ GOVERNANCE LAYER              │
                    │                                             │
                    │  artifacts/frz-input/   ← source documents  │
                    │  artifacts/raw-to-src/  ← frozen packages   │
                    │    frz-package/         ← default ref       │
                    │    frz-smoke-<date>/    ← history           │
                    │                                             │
                    │  Components:                                │
                    │  - FRZ Package Validator (MSC 5-dim check)  │
                    │  - Evidence Tracker (contradiction register)│
                    │  - FRZ Registry (which FRZ is active)       │
                    └──────────────────┬──────────────────────────┘
                                       │  frz_package_ref
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SSOT SEMANTIC EXTRACTION CHAIN                        │
│                                                                             │
│   FRZ ──projector──▶ SRC ──projector──▶ EPIC ──projector──▶ FEAT           │
│      (extract)         (extract)          (extract)                          │
│                                                                             │
│   CLI Commands:          Library Modules:                                   │
│   - ll frz validate      - semantic_extractor.py (core projector engine)    │
│   - ll frz msc-check     - projection_rules.py (per-layer rules)            │
│   - ll extract src       - anchor_tracker.py (FRZ anchor ID propagation)   │
│   - ll extract epic      - drift_detector.py (semantic drift detection)     │
│   - ll extract feat      - stability_guard.py (pre/post execution checks)   │
│                                                                             │
│   ssot/src/  ssot/epic/  ssot/feat/  ssot/mapping/                          │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │  FEAT refs
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TASK PACK ORCHESTRATION LAYER                           │
│                                                                             │
│   ssot/tasks/PACK-xxx.yaml  ← task pack definitions                         │
│                                                                             │
│   CLI Commands:          Library Modules:                                   │
│   - ll pack validate     - task_pack_parser.py   (YAML loader + schema)    │
│   - ll pack status       - dependency_resolver.py (topo-sort depends_on)   │
│   - ll pack run          - sequential_loop.py     (ADR-051 loop runner)    │
│   - ll pack resume       - task_state_machine.py  (state transitions)       │
│   - ll pack retry        - dual_chain_trigger.py  (test-api/test-e2e hook) │
│                                                                             │
│   Extends existing: ADR-018 execution_runner.py + loop command             │
│   New: Task Pack as loop input, not replacement                            │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │  task execution
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     EXECUTION LAYER (existing v1.x)                         │
│                                                                             │
│   ll loop run-execution      ← ADR-018 loop runtime                         │
│   ll job run/complete/fail   ← job state machine                            │
│   ll skill *                 ← skill invokers                               │
│   cli/lib/execution_runner.py, cli/lib/job_state.py, etc.                   │
│                                                                             │
│   artifacts/jobs/{ready,running,done,failed,waiting-human,deadletter}/      │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │  execution outcomes
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DUAL CHAIN VALIDATION (ADR-047)                         │
│                                                                             │
│   ll skill test-exec-web-e2e   ← E2E chain (Playwright)                    │
│   ll skill test-exec-cli       ← API chain                                  │
│   ll skill impl-spec-test      ← spec-level tests                           │
│   cli/lib/test_exec_*.py       ← test execution infrastructure              │
│                                                                             │
│   artifacts/tests/evidence/    ← evidence binding (light)                   │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │  verification results
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CHANGE GRADING & GOVERNANCE PIPELINE                    │
│                                                                             │
│   Execution discovers change ──classify──▶ Minor or Major                   │
│                                              │                               │
│                    ┌─────────────────────────┼─────────────────────────┐     │
│                    ▼                         ▼                         │     │
│              Minor Change              Major Change                     │     │
│              (visual/interaction)      (semantic)                        │     │
│                    │                         │                           │     │
│                    ▼                         ▼                           │     │
│   ┌──────────────────────┐    ┌──────────────────────────────┐           │     │
│   │ ADR-049 Patch Layer  │    │ Back to FRZ (re-freeze)      │           │     │
│   │                      │    │                              │           │     │
│   │ - patch_context_*    │    │ - New FRZ package created    │           │     │
│   │ - patch_auto_reg     │    │ - MSC re-validated           │           │     │
│   │ - Patch YAML files   │    │ - SSOT re-extracted from new │           │     │
│   │ - retain_in_code     │    │   FRZ                        │           │     │
│   │ - backwrite UI/TEST  │    │ - New SRC chain spawned      │           │     │
│   └──────────────────────┘    └──────────────────────────────┘           │     │
│                    │                         │                           │     │
│                    ▼                         ▼                           │     │
│   Patch applied,            New SSOT extracted,                          │     │
│   no SSOT rewrite            Task Pack re-driven                          │     │
│   └─────────────────────────┴────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### FRZ Governance Layer

| Component | Responsibility | Location | Talks To |
|-----------|---------------|----------|----------|
| **FRZ Package Validator** | Loads FRZ package, runs MSC 5-dimension validation, returns pass/fail | `cli/lib/frz_validator.py` (NEW) | Reads `artifacts/raw-to-src/frz-package/` |
| **FRZ Evidence Tracker** | Maintains contradiction register, source refs, normalization decisions | `cli/lib/frz_evidence.py` (NEW) | Reads/writes `evidence.yaml` in FRZ package |
| **FRZ Registry** | Tracks which FRZ is active, version history, frz_package_ref resolution | `cli/lib/frz_registry.py` (NEW) | Reads `ssot/` objects for `frz_package_ref` field |

### Semantic Extraction Chain

| Component | Responsibility | Location | Talks To |
|-----------|---------------|----------|----------|
| **Semantic Extractor** (core projector) | Reads FRZ, extracts layer-specific semantics into SSOT objects | `cli/lib/semantic_extractor.py` (NEW) | FRZ Registry, writes `ssot/src/`, `ssot/epic/`, `ssot/feat/` |
| **Projection Rules** | Per-layer extraction rules (what to extract from FRZ for SRC vs EPIC vs FEAT) | `cli/lib/projection_rules.py` (NEW) | Called by Semantic Extractor |
| **Anchor Tracker** | Propagates FRZ anchor IDs (JRN-xxx, ENT-xxx, FC-xxx, etc.) through SSOT layers | `cli/lib/anchor_tracker.py` (NEW) | Called by Semantic Extractor |
| **Drift Detector** | Compares current SSOT against FRZ to detect semantic drift | `cli/lib/drift_detector.py` (NEW) | Reads FRZ + SSOT, used by CLI validate commands |
| **Stability Guard** | Pre-execution check: is the SSOT semantically stable? Post-execution check: did execution drift? | `cli/lib/stability_guard.py` (NEW) | Called before/after Task Pack execution |

### Task Pack Orchestration

| Component | Responsibility | Location | Talks To |
|-----------|---------------|----------|----------|
| **Task Pack Parser** | Loads PACK YAML, validates schema, returns typed Pack object | `cli/lib/task_pack_parser.py` (NEW) | Reads `ssot/tasks/PACK-*.yaml` |
| **Dependency Resolver** | Topological sort of `depends_on`, finds next executable task | `cli/lib/dependency_resolver.py` (NEW) | Called by Sequential Loop |
| **Sequential Loop** | ADR-051 loop runner: picks task, executes, updates state, handles failure | `cli/lib/sequential_loop.py` (NEW) | Task Pack Parser, Dependency Resolver, Execution Runner |
| **Task State Machine** | Manages task state transitions (pending→running→passed/failed/skipped/blocked) | `cli/lib/task_state_machine.py` (NEW) | Called by Sequential Loop |
| **Dual Chain Trigger** | After test-* tasks, invokes appropriate ADR-047 validation chain | `cli/lib/dual_chain_trigger.py` (NEW) | Existing test execution infrastructure |

### Change Grading Pipeline

| Component | Responsibility | Location | Talks To |
|-----------|---------------|----------|----------|
| **Change Classifier** | Determines if a change is visual/interaction/semantic (maps to ADR-049 categories) | `cli/lib/change_classifier.py` (NEW) | Called by patch_auto_register, Stability Guard |
| **Minor Change Handler** | Routes visual/interaction changes through Patch layer, backwrites where needed | Extends existing `cli/lib/patch_auto_register.py` | ADR-049 Patch infrastructure |
| **Major Change Handler** | Triggers FRZ re-freeze workflow, spawns new SRC chain | `cli/lib/major_change_handler.py` (NEW) | FRZ Governance, Semantic Extractor |

### Three-Axis Management

| Axis | Management Intensity | Components | Storage |
|------|---------------------|------------|---------|
| **Requirements** (strong) | Full SSOT governance: freeze, version, change flow | Semantic Extractor, Drift Detector, Change Grading | `ssot/src/`, `ssot/epic/`, `ssot/feat/` |
| **Implementation** (weak) | Lightweight status tracking only | Task State Machine, Sequential Loop | `ssot/tasks/PACK-*.yaml` (status field) |
| **Evidence** (light) | Binding relationship only (verifies + evidence_ref) | Dual Chain Trigger, existing evidence infrastructure | `artifacts/tests/evidence/` |

## Data Flow

### Primary Flow (happy path)

```
1. External frameworks produce PRD/Arch/UX/Test docs
2. FRZ is frozen (human-driven, not AI-generated)
   └─ MSC validation passes → frz_package_ref recorded
3. SSOT extraction: FRZ → SRC → EPIC → FEAT
   └─ Each layer extracts relevant semantics, preserves anchor IDs
4. Task Pack created for a FEAT (PACK YAML in ssot/tasks/)
5. Sequential loop reads Pack, executes tasks in dependency order
6. After impl tasks → test tasks run → dual chain validation
7. Test results bind to AC verifies (evidence light mount)
8. Pack completes → Gate check (if configured) → done
```

### Change Detection Flow (execution discovers issues)

```
1. During execution, a change is detected (code diff, test failure, human feedback)
2. Patch auto-register detects changed files (existing ADR-049)
3. Change Classifier evaluates: visual / interaction / semantic
4a. Minor (visual/interaction):
    - Patch applied via ADR-049 Patch Layer
    - Backwrite to UI Spec / Test Spec if interaction
    - retain_in_code if visual
    - No SSOT rewrite
4b. Major (semantic):
    - Change flagged, loop pauses
    - Human decision: re-freeze FRZ or accept as clarification
    - If re-freeze: new FRZ package → MSC validation → new SSOT extraction
    - New Task Pack spawned from updated SSOT
    - Old Pack marked superseded
```

### Semantic Stability Flow (pre/during/post execution)

```
Pre-execution (Stability Guard check):
  - Is FRZ frozen and MSC-valid?
  - Has SSOT been extracted from current FRZ?
  - Any pending patches that could affect semantics?
  → All clear → proceed

During execution (Drift Detector):
  - After each impl task, check: did the code change alter semantics?
  - Compare against FRZ anchor IDs (JRN, ENT, FC references)
  → If drift detected → trigger Change Classification

Post-execution (Stability Guard check):
  - Did test outcomes match FRZ acceptance_contract?
  - Any semantic changes introduced that bypassed grading?
  → Write stability report to Pack execution record
```

## Patterns to Follow

### Pattern 1: Projection Invariance

**What:** SSOT layers must preserve FRZ semantics exactly — no addition, no deletion, only extraction and organization.

**When:** Any code that writes to `ssot/src/`, `ssot/epic/`, or `ssot/feat/`.

**Example:**
```python
@dataclass(frozen=True)
class ProjectionResult:
    """Result of projecting FRZ content into an SSOT layer."""
    source_anchors: list[str]   # FRZ anchor IDs used
    extracted_fields: dict      # What was extracted
    invariant_check: bool       # True = no semantic drift from FRZ

def project_frz_to_src(frz_package: dict, projection: str) -> ProjectionResult:
    """Extract SRC-level semantics from FRZ without modifying meaning."""
    result = extract_by_dimension(frz_package, dimension=projection)
    drift = detect_drift(result, frz_package)
    return ProjectionResult(
        source_anchors=result.anchors,
        extracted_fields=result.fields,
        invariant_check=(drift == NO_DRIFT),
    )
```

### Pattern 2: Sequential Loop with Failure Pause

**What:** Task Pack loop picks one ready task, executes, checks result, pauses on failure.

**When:** Running any Task Pack (ADR-051).

**Example:**
```python
def run_pack_sequential(workspace_root: str, pack_file: str) -> PackResult:
    pack = load_and_validate_pack(pack_file)
    resolver = DependencyResolver(pack.tasks)

    while True:
        ready = resolver.next_ready()
        if not ready:
            if resolver.all_done():
                return PackResult(status="completed")
            if resolver.any_blocked():
                return PackResult(status="blocked", tasks=resolver.blocked())
            break

        task = ready[0]  # Single task (no concurrency)
        result = execute_task(workspace_root, task)

        if result.status == "failed" and task.type.startswith("test-"):
            trigger_dual_chain(workspace_root, task, result)

        if result.status in ("failed", "still_failed"):
            return PackResult(status="paused", failed_task=task.task_id)

        resolver.mark_done(task.task_id, result)
```

### Pattern 3: Change Classification at Boundary

**What:** All changes detected during execution must pass through the Change Classifier before any action is taken.

**When:** patch_auto_register, Stability Guard post-execution, human-reported changes.

**Decision tree:**
```
change detected
  ├─ Does it alter user paths?          → Major (semantic) → back to FRZ
  ├─ Does it alter function logic?      → Major (semantic) → back to FRZ
  ├─ Does it alter acceptance criteria? → Major (semantic) → back to FRZ
  ├─ Is it UI styling only?             → Minor (visual)   → Patch retain_in_code
  ├─ Is it navigation flow tweak?       → Minor (interaction) → Patch backwrite UI
  └─ Is it parameter default addition?  → Minor (execution clarification) → Patch backwrite
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: SSOT Generation from Parent Node Only

**What:** Extracting EPIC semantics only from SRC, rather than from FRZ directly.
**Why bad:** Causes逐层 semantic drift — each layer loses context from the original FRZ.
**Instead:** Every layer (SRC, EPIC, FEAT) extracts directly from FRZ using projection rules appropriate to that layer.

### Anti-Pattern 2: Execution Layer Writing SSOT Semantics

**What:** Task execution directly modifying SSOT files to "clarify" or "correct" semantics.
**Why bad:** Pollutes the semantic truth source. Tests become unstable. AI re-interprets requirements.
**Instead:** Execution layer writes to Patch files (ADR-049). Semantic changes flow back to FRZ.

### Anti-Pattern 3: Complex DAG Scheduling for Task Packs

**What:** Building a general-purpose DAG scheduler for Task Pack execution.
**Why bad:** ADR-051 explicitly rejects this. Over-engineering, instability, unnecessary for current scale.
**Instead:** Simple sequential loop with `depends_on` resolution. One task at a time, failure pauses.

### Anti-Pattern 4: Treating All Three Axes Equally

**What:** Applying full SSOT governance (freeze, version, change flow) to implementation status or evidence bindings.
**Why bad:** System becomes too heavy. Implementation changes too fast for strong governance. Evidence only needs traceability.
**Instead:** Differentiate intensity — Requirements strong, Implementation weak, Evidence light.

## Integration with Existing Architecture

### What Already Exists (v1.x)

| Existing Component | Role in v2.0 | Action |
|-------------------|-------------|--------|
| `cli/ll.py` CLI entrypoint | Add new `frz`, `extract`, `pack` subcommand groups | EXTEND |
| `cli/lib/execution_runner.py` | Task execution runtime — Task Pack feeds into this | REUSE |
| `cli/lib/job_state.py` | Job lifecycle (ready→claimed→running→done/failed) | REUSE — Task state maps onto job state |
| `cli/lib/patch_schema.py` | Patch dataclasses, PatchStatus, ChangeClass | REUSE + EXTEND — add Major change flow |
| `cli/lib/patch_context_injector.py` | Injects patch context before code edits | REUSE |
| `cli/lib/patch_auto_register.py` | Detects changed files, drafts patches | EXTEND — add change classification |
| `cli/lib/qa_schemas.py` | QA schema validation | REUSE |
| `cli/commands/loop/command.py` | Execution loop command | EXTEND — add Task Pack as loop input |
| `cli/lib/test_exec_*.py` | Dual chain test execution | REUSE |
| `ssot/` directory structure | SSOT objects (SRC, EPIC, FEAT, etc.) | REUSE — extraction writes here |
| `ssot/adr/` | ADR files | REUSE — ADR-050/051 added |
| `ssot/tasks/` | Task Pack YAML storage | EXISTING DIR — new content |
| `artifacts/` | Job artifacts, evidence, FRZ packages | EXTEND — add FRZ package structure |

### New Components to Build

| New Component | Depends On | Provides To |
|--------------|-----------|-------------|
| FRZ Validator | FRZ package structure (ADR-045) | Semantic Extractor |
| Semantic Extractor | FRZ Validator, Projection Rules | SSOT directory (src/epic/feat) |
| Task Pack Parser | PACK YAML schema (ADR-051) | Sequential Loop |
| Sequential Loop | Task Pack Parser, Dependency Resolver, Execution Runner | Task state, evidence |
| Change Classifier | Patch Schema (ADR-049), Stability Guard | Minor/Major handlers |
| Stability Guard | Drift Detector, FRZ Registry | Pre/post execution gates |

## Suggested Build Order

### Phase 1: FRZ Foundation (governability first)

1. **FRZ Package Validator** — MSC 5-dimension check. Without this, nothing downstream can trust FRZ.
2. **FRZ Registry** — Track active FRZ, resolve references. Required before any extraction.
3. **FRZ CLI commands** (`ll frz validate`, `ll frz msc-check`) — Enable human verification workflow.

*Rationale:* FRZ is the semantic truth source. Must be validated before anything reads from it.

### Phase 2: Semantic Extraction (SSOT transformation)

4. **Projection Rules** — Define what each SSOT layer extracts from FRZ.
5. **Semantic Extractor** — Core projector engine (FRZ → SRC → EPIC → FEAT).
6. **Anchor Tracker** — Ensure FRZ anchor IDs propagate through all layers.
7. **Drift Detector** — Compare SSOT against FRZ to validate extraction correctness.
8. **Extract CLI commands** (`ll extract src`, `ll extract epic`, `ll extract feat`).

*Rationale:* Transform SSOT from generation chain to extraction chain. Must complete before Task Packs can reference valid SSOT.

### Phase 3: Task Pack Orchestration (execution)

9. **Task Pack Parser** — YAML loader with schema validation.
10. **Dependency Resolver** — Topological sort of `depends_on`.
11. **Task State Machine** — State transitions per ADR-051.
12. **Sequential Loop** — Core loop runner, integrates with existing `execution_runner.py`.
13. **Dual Chain Trigger** — Hook test-api/test-e2e tasks into ADR-047 validation.
14. **Pack CLI commands** (`ll pack validate`, `ll pack run`, `ll pack status`, `ll pack resume`).

*Rationale:* Task Packs drive execution. Built on top of validated SSOT and existing job/loop infrastructure.

### Phase 4: Change Grading & Stability (governance closure)

15. **Change Classifier** — visual/interaction/semantic classification.
16. **Stability Guard** — Pre/post execution semantic stability checks.
17. **Minor Change Handler** — Extend existing patch_auto_register for classified routing.
18. **Major Change Handler** — FRZ re-freeze workflow trigger.

*Rationale:* Closes the governance loop. Ensures changes discovered during execution flow back correctly.

### Phase 5: Three-Axis Integration & Hardening

19. **Three-axis metadata** — Add `frz_package_ref` to SSOT objects, `verifies` bindings to evidence.
20. **Pack-level reporting** — Aggregate Task Pack results, evidence summaries.
21. **End-to-end validation** — Run full pipeline: FRZ → Extract → Pack → Execute → Grade → Loop.

## Scalability Considerations

| Concern | Current (single project) | At 10 projects | At 100 projects |
|---------|------------------------|----------------|-----------------|
| FRZ packages | Single `artifacts/raw-to-src/` | Namespace by project | Centralized FRZ registry |
| Task Packs | Sequential per Pack | Pack-level parallelism | Queue-based dispatch |
| SSOT objects | Filesystem-based | Filesystem + index | Database-backed |
| Change grading | In-process | Async event stream | Event sourcing |

**For v2.0 scope:** All current patterns work at single-project scale. No database or async infrastructure needed. Filesystem + YAML + JSON is sufficient.

## Sources

- ADR-050: SSOT Semantic Governance Master Plan (internal)
- ADR-051: Task Pack Sequential Execution Loop (internal)
- ADR-045: FRZ Freeze Layer specification (internal)
- ADR-047: Dual Chain Testing (internal)
- ADR-049: Experience Patch Layer (internal)
- ADR-018: Execution Loop Job Runner (internal)
- Existing `cli/lib/` module analysis (execution_runner.py, patch_schema.py, job_state.py, loop/command.py)
