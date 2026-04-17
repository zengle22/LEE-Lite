# Feature Landscape

**Domain:** SSOT Semantic Governance (FRZ Layer, Semantic Extraction, Task Pack Orchestration)
**Researched:** 2026-04-18

## Table Stakes

Features required for v2.0 to be considered complete. Missing = semantic governance is not operational.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **FRZ MSC 5-dimension validator** | ADR-050 §3.3 mandates all 5 dimensions must pass before FRZ can be `frozen`. Industry equivalent: artifact evaluation badges (SC Conference AD/AE), data contract minimum field requirements | Medium | 5 checks: product_boundary, core_journeys, domain_model, state_machine, acceptance_contract. Must block downstream if any missing. Industry pattern: "minimum viable completeness" as gate |
| **FRZ package structure definition** | ADR-045 §3.1 defines 4-file minimum: `index.md`, `freeze.yaml`, `evidence.yaml`, `frz-package.json`. Industry equivalent: artifact freeze process with immutable snapshots | Medium | New Pydantic models in `cli/lib/v2_schemas.py`. Must interop with existing `qa_schemas.py` dataclass pattern. Industry standard: tagged DOI assignment at freeze point |
| **Semantic extraction: FRZ → SRC projection** | ADR-045 §2.4 requires projection invariance — SRC can expand but not change FRZ semantics. Industry trend: semantic layer extraction (not generation) per Cloudera 2026 prediction | High | Most complex feature. Requires: anchor ID tracing (`src_element → frz_anchor_id`), semantic diff via DeepDiff, source labeling (inherited/derived/proposed). Equivalent to semantic projection patterns in data governance |
| **Semantic drift detection** | ADR-050 §5 requires detecting when execution layer attempts to change semantics. Industry patterns: drift evaluation frameworks (Mir 2026 threshold-based classification), schema drift prevention (data contracts) | Medium | DeepDiff comparison of FRZ snapshots. If test-expected behavior changes → semantic change, not clarification. Industry uses delta thresholds (δC < 0.05 = negligible, 0.05 ≤ δC < 0.1 = minor) |
| **Change classification: clarification vs semantic change** | ADR-050 §5 defines two categories with different handling. Industry equivalent: SemVer minor vs major classification, ESCO semantic revision types | Low-Medium | "If downstream test expectations change → semantic change". Simple heuristic but needs clear CLI feedback. Industry standard: test-behavior-change as the defining criterion |
| **Change grading: Minor (Patch) vs Major (FRZ回流)** | ADR-050 §6 maps ADR-049 visual/interaction/semantic to Minor/Major paths. Industry equivalent: data contract change routing (minor → patch, major → re-freeze) | Medium | visual → Minor (Patch retain_in_code), interaction → Minor (Patch backwrite UI/TESTSET), semantic → Major (new FRZ + new SRC). Tri-classification finer than typical binary |
| **Task Pack YAML parser** | ADR-051 §2.1 defines PACK structure with tasks array, depends_on, type enum. Industry equivalent: sequential orchestration input format (Azure AI Agent patterns 2026) | Low | Parse YAML into typed objects. Validate task type enum, depends_on references exist. Task types: impl, test-api, test-e2e, review, doc, gate |
| **Task Pack sequential loop executor** | ADR-051 §2.3 defines the execution loop: pick ready task → execute → update status → next. Industry pattern: sequential pipeline in agentic orchestration | Medium | Thin wrapper around existing `execution_runner.py`. Uses `graphlib.TopologicalSorter` for dependency ordering. Explicitly rejects DAG scheduling (ADR-051 §5.1) |
| **Task Pack failure pause + human intervention** | ADR-051 §2.4 rule 3: "failure stops loop, no skip". Industry standard in regulated development: fail-fast with manual review | Low | Existing job state machine already supports `waiting-human` state. Just needs loop to check for it. No auto-skip (technical debt accumulation) |
| **Task Pack status persistence** | ADR-051 §2.5 defines task state machine (pending → running → passed/failed/skipped/blocked). Standard pattern in workflow systems | Low | Write updated Pack YAML back to `ssot/tasks/` after each task completes. States: pending, running, passed, failed, still_failed (max 2 retries), skipped, blocked |
| **Dual-chain test binding** | ADR-051 §2.4 rule 4: test-api binds API chain, test-e2e binds E2E chain (ADR-047). Industry pattern: test-to-requirement traceability (IREB, ISO 26262) | Medium | After test-* task completes, invoke existing ADR-047 chain validation. Evidence writes back to `verifies` field |
| **Three-axis management intensity** | ADR-050 §7: requirements strong, implementation weak, evidence light. Industry problem: uniform strong governance (DOORS, Jama) is too heavy | Low | Documentation + schema field-level guidance. Requirements axis gets frozen+version+change_flow; implementation axis gets status-only; evidence axis gets binding-only |
| **Version tracking for Patches** | ADR-049 requires audit trail for all patches. Industry equivalent: semantic versioning of documentation (SemVerDoc) | Low | Every patch gets a version. Clean rebase triggers after N patches. Links to ADR-049 auto-registration |

## Differentiators

Features that set this product apart. Not expected in generic tools, but critical for this project's value proposition.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Projection invariance enforcement** | Guarantees FRZ semantics survive SRC projection — AI cannot silently rename entities or change state machines. Unique to this governance model | High | Requires: anchor ID registry, canonical term dictionary, automated reconcile checks. No equivalent in commercial requirements tools |
| **FRZ as External Framework Output** | FRZ comes from human discussions in BMAD/Superpowers/OMC, not AI generation. Ensures semantic quality at source. Novel vs AI-generated requirements tools | Medium | Governance quality determined upstream. System trusts the freeze, doesn't try to generate it. Contrasts with tools that auto-generate requirements from prompts |
| **Semantic Extraction (Not Generation)** | SSOT layers project from unified FRZ, not from parent layer. Eliminates cumulative drift from chained generation. Industry trend toward semantic layers | High | Requires building projection rules per layer. More complex than generation but vastly more stable. Ahead of typical "generate from template" approaches |
| **Visual/Interaction/Semantic Tri-Classification** | ADR-049's three-way classification maps to two governance paths. Finer-grained than typical binary minor/major. Visual changes don't touch SSOT at all | Medium | Visual → retain_in_code only. Interaction → backwrite UI/TESTSET. Semantic → FRZ re-freeze. More nuanced than SemVer's 3-tier (which still affects all consumers) |
| **Differential Axis Management** | Three-axis approach (strong/weak/light) avoids overhead of uniform strong governance. Solves the "DOORS problem" — everything feels heavy | Medium | Requirements gets full SSOT treatment. Implementation gets simple status. Evidence gets lightweight binding. Prevents system bloat that kills adoption |
| **Patch-SSOT Integration** | ADR-049 Patch layer + ADR-050 governance creates closed-loop experience capture. Code-level insights flow back through classified paths | High | Auto-detect changes → classify → route appropriately. Visual stays in code, interaction updates SSOT specs, semantic triggers governance escalation |
| **One-Pack-One-FEAT Binding** | Tight coupling between feature and task organization. Unlike loose task boards, every Pack traces to a specific FEAT | Low | Simplifies traceability. Pack naming convention encodes SRC/FEAT references. Clean audit trail from governance to execution |
| **Sequential-Only Execution (Deliberate Constraint)** | Rejecting concurrency/DAG as a governance feature, not a limitation. Predictable, reproducible, debuggable | Low | WLOK (Weak Loop Orchestration Kit) philosophy. Trade throughput for certainty. Appropriate for AI-agent execution where non-determinism is the enemy |
| **proposed expiration mechanism** | ADR-045 §2.6: proposed items expire after N cycles, preventing permanent unknowns from being treated as stable | Low-Medium | Timer-based check on `known_unknowns` with `expires_in` and `owner` fields. Forces decision on open items |
| **Multi-layer trace inheritance** | ADR-045 §2.7: single primary inheritance + multi-layer read-only回溯. Prevents "skip layer" semantic pollution | Medium | Each SSOT layer must declare source labels. Validation rejects unlabelled semantic additions |
| **FRZ瘦身 principle enforcement** | ADR-045 §2.8: FRZ only contains semantics that affect downstream decisions | Low | Warning system: flag FRZ content not referenced by any downstream artifact |
| **Batch Patch settlement operations** | ADR-049 §8.3: approve-by-class, bulk-upgrade-to-src, merge-patches | Medium | CLI commands for bulk Patch processing. Reduces settlement fatigue |
| **Change classification decision tree** | ADR-049 §2.4: three independent gates (business rules? stakeholder alignment? visual-only?) | Low | Deterministic decision tree — no AI judgment needed for classification |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Complex DAG scheduler** | ADR-051 §5.1 explicitly rejects. Implementation complexity > benefit for current scale. Industry: sequential patterns preferred for stability (Azure AI Agent patterns) | Use `graphlib.TopologicalSorter` for simple tree/linear dependencies |
| **Concurrent task execution** | ADR-051 §5.2 explicitly rejects. Task dependencies are inherently sequential (impl → test-api → test-e2e → review). Race conditions destroy reproducibility | Sequential loop only, one task at a time |
| **Auto-skip failed tasks** | ADR-051 §5.3 explicitly rejects. Skipping accumulates technical debt silently. Governance requires visibility into failures | Pause loop, mark FAILED, wait for human intervention |
| **AI auto-submitted Patches** | ADR-049 §12.2 explicitly requires human review. AI classification is error-prone | AI pre-fills, human confirms. `human_confirmed_class` is mandatory |
| **FRZ inside ssot/ directory** | ADR-045 §2.1: FRZ belongs in `artifacts/`, not `ssot/`. Mixing frozen artifacts with active chain breaks separation of concerns | Keep FRZ in `artifacts/raw-to-src/`, reference via `frz_package_ref` |
| **Execution layer semantic modification** | ADR-050 §5: execution can only complete, not change semantics. Allowing this destroys SSOT stability | Semantic changes must回流 to FRZ for re-freezing |
| **Uniform strong management for all three axes** | ADR-050 §7.2: would make system too heavy, slow execution. Industry lesson: DOORS/Jama suffer from governance bloat | Differentiated: requirements=strong, implementation=weak, evidence=light |
| **LLM-based semantic extraction** | Semantic extraction is structural projection, not natural language understanding. LLMs introduce non-determinism | Use deterministic YAML transformation + Pydantic validation |
| **AI-Generated FRZ Content** | ADR-050 §3.1 explicit rule: FRZ must come from human discussions, not AI generation. AI cannot be the source of truth | AI can assist extraction FROM FRZ, but never generate FRZ content |
| **Bypassing FRZ for SSOT Direct Modification** | Creates governance holes, breaks traceability, enables semantic pollution. Industry equivalent: editing requirements without change control | All semantic changes must go through FRZ → re-freeze → SSOT update path |
| **Patch Accumulation Without Clean Rebase** | Unbounded patch growth creates maintenance burden, slows loading, increases conflict risk | Every N patches, trigger clean rebase. Human-reviewed consolidation |
| **Second SSOT from Implementation Axis** | Implementation tracking must not evolve into parallel governance system. Creates dual-source-of-truth problem | Keep implementation axis intentionally weak: only task_id + status. No semantic modeling |

## Feature Dependencies

```
FRZ MSC Validator → FRZ Package Structure (MSC checks require structure)
FRZ Package Structure → Semantic Extraction (extraction reads FRZ)
Semantic Extraction → Semantic Drift Detection (drift = diff between extractions)
Semantic Drift Detection → Change Classification (drift detected → classify as change or clarification)
Change Classification → Change Grading (classification output feeds grading)
Change Grading → ADR-049 Patch Layer (Minor → Patch, Major → FRZ回流)
Task Pack YAML Parser → Task Pack Loop Executor (parser output feeds executor)
Task Pack Loop Executor → Dual-Chain Test Binding (executor triggers chain validation after test tasks)
Task Pack Loop Executor → Existing execution_runner.py (executor wraps runner)
Dual-Chain Test Binding → ADR-047 chain infrastructure (uses existing chain validation)
Patch-Aware Harness → ADR-049 Patch Layer (reads Patch YAML)
Projection Invariance → Semantic Extraction (invariance is a property of extraction)
proposed Expiration → Multi-layer Trace Inheritance (expiration applies to proposed items)

ADR-049 Patch Layer → Change Classification → Minor Path (visual/interaction)
ADR-049 Patch Layer → Change Classification → Major Path (semantic → FRZ re-freeze)

Three-Axis Management → Requirements (strong) → FRZ + SSOT + Change Classification
Three-Axis Management → Implementation (weak) → Task Status Tracking
Three-Axis Management → Evidence (light) → verifies binding
```

### Dependency Graph (Critical Path)

```
FRZ Package Definition (BLOCKS everything)
  └─ MSC Validation
       └─ FRZ Frozen
            ├─ Semantic Extraction Chain
            │    ├─ Projection Invariance Verification
            │    └─ Semantic Drift Detection
            │         └─ Change Classification
            │              └─ Change Grading
            │                   ├─ Minor → ADR-049 Patch
            │                   └─ Major → FRZ Re-freeze
            │
            └─ Task Pack Execution
                 ├─ Sequential Loop Executor
                 │    ├─ Task State Machine
                 │    │    └─ Failure Pause
                 │    └─ Dual-Chain Test Binding
                 └─ Three-Axis Tracking
```

## MVP Recommendation

**Priority 1 (Table Stakes — governance foundation):**
1. **FRZ MSC validator** — gating feature, blocks everything else if FRZ is invalid. Industry standard: artifact evaluation requires minimum completeness before acceptance
2. **FRZ package structure definition** — foundation for all downstream operations. Must define schemas before extraction can read them
3. **Task Pack YAML parser + sequential loop executor** — highest usage frequency, builds on existing ADR-018 infrastructure. Immediate productivity gain

**Priority 2 (Table Stakes — governance + execution):**
4. **Change classification + grading** — essential for ADR-049协同, connects v1.1 to v2.0. Bridges existing Patch layer to new governance
5. **Semantic drift detection (basic)** — DeepDiff-based comparison of two FRZ snapshots. Industry pattern: delta threshold detection
6. **FRZ → SRC projection (basic)** — anchor ID tracing, source labeling. Prove the extraction pattern at first layer
7. **Dual-chain test binding** — verification integration. Connects Task Pack to existing ADR-047 chains

**Priority 3 (Table Stakes — governance completion):**
8. **Three-axis management intensity** — structural enforcement. Documentation + schema field-level guidance
9. **Task Pack failure pause + human intervention** — safety mechanism for governance
10. **Version tracking for Patches** — audit trail requirement

**Priority 4 (Differentiators — competitive edge):**
11. **Projection invariance enforcement (automated)** — ensure extraction fidelity. Can start with manual checks
12. **Patch-SSOT Integration** — closed-loop experience capture
13. **One-Pack-One-FEAT Binding** — tight traceability

**Defer to post-MVP:**
- **Patch-aware Harness** — requires test infrastructure changes, can work without it initially
- **Batch Patch settlement** — quality-of-life feature, not blocking
- **FRZ瘦身 principle enforcement** — warning system, not blocking
- **proposed expiration mechanism** — can be added once trace inheritance is stable

## Integration with Existing Infrastructure

| Existing Component | New Feature Integration | Notes |
|-------------------|------------------------|-------|
| **ADR-049 Patch Layer** | Change classification routes to Patch for Minor changes. Auto-registration feeds drift detection. Patch context injector already handles code→SSOT flow. | Needs classification gate added before Patch auto-registration |
| **ADR-047 Dual-Chain Tests** | Task Pack test-api/test-e2e tasks trigger existing API/E2E chains. Evidence binds to verifies field. | Test infrastructure exists. Task Pack adds orchestration layer on top |
| **ADR-018 Execution Loop** | Task Pack YAML becomes loop input. Sequential mode is default. State machine extends loop's status tracking. | Loop runtime exists. Task Pack adds structure, dependency resolution, failure handling |
| **ADR-045 FRZ Spec** | FRZ Package Definition implements ADR-045's structure. MSC validation enforces ADR-045 completeness rules. | ADR-045 defines the spec; v2.0 builds the validator and package manager |
| **CLI Artifact Gateway** | FRZ packages register through artifact gateway. Task Packs as a new artifact type. | Extend existing registry schema for FRZ and PACK artifacts |
| **QA Skills (11 skills)** | QA skills execute within Task Pack loop. Each skill maps to task types (impl, test-api, test-e2e, review). | Skills become Task Pack workers. Loop orchestrates skill execution order |
| **YAML Schema Validators** | New schemas for FRZ packages, Task Packs, three-axis tracking. Python dataclass validators extend existing pattern. | Reuse existing validation infrastructure. Add MSC validator as new component |

## Complexity Assessment

| Feature Area | Overall Complexity | Primary Risk |
|--------------|-------------------|--------------|
| FRZ Package + MSC | Medium | Defining MSC dimensions precisely enough to validate programmatically. Ambiguous boundaries between "complete" and "sufficient" |
| Semantic Extraction Chain | High | Building correct projection rules that prevent drift without blocking legitimate complements. Risk: over-constraining valid derivation |
| Change Classification | Low-Medium | Distinguishing clarification from semantic change requires clear heuristics. ADR-050 §5.2 test criterion ("does it change downstream test expectations?") is workable |
| Task Pack Orchestration | Low | Simple sequential loop. depends_on resolution is straightforward topological sort. Low risk |
| Semantic Drift Detection | Medium-High | Requires baseline comparison logic. DeepDiff handles structural changes; semantic similarity may need additional logic |
| Three-Axis Management | Low | Structural decision, not implementation complexity. Enforcement discipline is the challenge |
| Patch-SSOT Integration | High | Cross-component coordination between Patch layer and governance rules. Risk: circular dependencies |
| Projection Invariance | High | Anchor ID registry + canonical term dictionary + automated reconcile. Unique problem domain, no off-the-shelf solution |

## Sources

### Project Documents (HIGH confidence)
- [ADR-050: SSOT语义治理总纲](E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-050-SSOT语义治理总纲.md) — Primary governance specification
- [ADR-051: TaskPack顺序执行循环模式](E:\ai\LEE-Lite-skill-first\ssot\adr\ADR-051-TaskPack顺序执行循环模式.md) — Task Pack orchestration spec
- [ADR-045: 引入FRZ冻结层](project) — FRZ structure and projection invariance
- [ADR-047: 双链测试](project) — API + E2E test chain verification
- [ADR-049: 体验修正层](project) — Patch layer infrastructure
- [ADR-018: Execution Loop](project) — Loop job runner runtime
- [PROJECT.md v2.0](E:\ai\LEE-Lite-skill-first\.planning\PROJECT.md) — Project context and requirements

### Industry Standards (HIGH confidence)
- [Semantic Versioning 2.0.0](https://semver.org/) — Standard minor/major/patch classification
- [IREB CPRE Requirements Management Handbook](https://cockpit-v1.ireb.org/media/pages/downloads/cpre-requirements-management-handbook/) — Requirements management standards
- [ESCO Versioning System](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/esco-versions) — Major/minor semantic revision classification
- [SC Conference AD/AE Artifact Freeze Process](https://sc24.supercomputing.org/program/papers/reproducibility-appendices-badges/) — Artifact freeze best practices
- [Azure AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) — Sequential orchestration patterns

### Industry Research (MEDIUM confidence)
- [Quantifying Conceptual Evolution: Semantic Drift Framework](https://www.preprints.org/manuscript/202601.1456) — Drift classification with thresholds (Mir 2026)
- [Data Contracts: Schema and Semantic Drift Governance](https://ijcesen.com/index.php/ijcesen/article/view/5152) — Change classification + versioning (Boddu 2025/2026)
- [Semantic Governance Framework for AI Systems](https://zhuanlan.zhihu.com/p/2023445176299915252) — AI governance patterns
- [2026 Predictions: Architecture, Governance, and AI](https://www.cloudera.com/blog/business/2026-predictions-the-architecture-governance-and-ai-trends-every-enterprise-must-prepare-for.html) — Data as living semantic memory
- [Multi-Agent Orchestration Patterns 2026](https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production) — Production orchestration patterns
- [CodeTracer: Towards Traceable Agent States](https://arxiv.org/html/2604.11641v3) — AI agent traceability
- [Securing the Agentic Development Lifecycle](https://cycode.com/blog/securing-adlc/) — AI code traceability requirements
