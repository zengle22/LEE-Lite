# Domain Pitfalls: SSOT Semantic Governance (FRZ Layer, Semantic Extraction, Task Pack Orchestration)

**Domain:** AI-assisted development governance — freeze-package management, semantic extraction chains, sequential task orchestration
**Researched:** 2026-04-18
**Sources:** ADR-050, ADR-051, ADR-045, ADR-047, ADR-049, ADR-018; academic and industry research on semantic governance, AI agent orchestration, requirement traceability, configuration drift

---

## Critical Pitfalls

Mistakes that cause rewrites, semantic corruption, or governance collapse.

### Pitfall 1: FRZ Semantic Incompleteness (Missing MSC Dimensions)

**What goes wrong:** The FRZ freeze package enters the downstream pipeline with one or more of the 5 MSC dimensions (product_boundary, core_journeys, domain_model, state_machine, acceptance_contract) absent, empty, or superficially filled. ADR-050 §3.3 defines the gate, but without automated enforcement, teams bypass it with "good enough" FRZ content.

**Why it happens:**
- Pressure to "unblock" downstream phases leads to accepting incomplete FRZ
- AI agents generate plausible-looking but semantically shallow MSC content
- The MSC gate check is implemented as a passive validation (warning-only) instead of a hard block
- `known_unknowns` entries lack real owner + expires_in tracking, making gaps invisible

**Consequences:**
- Semantic extraction chain produces shallow, hallucinated SSOT content (ADR-050 §4)
- Downstream tasks execute against ambiguous requirements — defect rate compounds (research shows AI-generated code already has 1.7x higher defect rate)
- Test chains (ADR-047) verify against wrong acceptance criteria

**Prevention:**
- Implement MSC validation as a **hard gate** in the FRZ ingestion CLI — return non-zero exit code if any dimension is missing or empty
- Add a `frz validate` command that checks all 5 dimensions + `known_unknowns` expiration tracking
- Require human sign-off on FRZ content quality before frozen status is granted
- Warning sign: FRZ freeze.yaml has any section with fewer than 3 meaningful entries

**Phase to address:** FRZ Structure Definition + MSC Validation (first v2.0 phase)

### Pitfall 2: Semantic Extraction Becomes Covert Generation

**What goes wrong:** The extraction chain (FRZ → SRC → EPIC → FEAT) silently transitions back into generation mode. Instead of projecting FRZ content into SSOT objects, the AI fills gaps by inventing details not present in the FRZ, violating ADR-050 §4's core principle.

**Why it happens:**
- FRZ content is incomplete (see Pitfall 1), and the extraction agent "helps" by filling blanks
- No automated diff mechanism compares extracted SSOT against FRZ source to detect invented content
- The extraction prompt doesn't include a strict "no invention" constraint, or the constraint is too weak to override the model's completion tendency
- Multi-hop extraction (FRZ → SRC → EPIC → FEAT) amplifies small inventions at each hop

**Consequences:**
- Semantic drift between FRZ and SSOT — the "single source of truth" diverges from actual truth
- Tests verify against invented requirements, not frozen ones
- The entire governance model collapses because the extraction chain is indistinguishable from the old generation chain

**Prevention:**
- Implement a **semantic projection validator** that compares each SSOT object against its FRZ source anchors — flag any content without a traceable FRZ reference
- Use extraction prompts with explicit "quote or cite FRZ anchor, do not invent" constraints
- Add an `ssot audit` command that reports all SSOT content without FRZ provenance
- Warning sign: SSOT objects contain details (specific field names, UI labels, business rules) that appear nowhere in the FRZ freeze.yaml

**Phase to address:** SSOT Semantic Extraction Chain (second v2.0 phase)

### Pitfall 3: Execution Layer Semantic Drift (Silent Override)

**What goes wrong:** During implementation, the AI agent makes changes that alter the semantic meaning of requirements (user paths, business logic, acceptance criteria) but classifies them as "execution clarifications" (ADR-050 §5) to avoid the Major change回流 path. This is the "silent override" problem documented in AI agent research — agents rewrite parameters while reporting success.

**Why it happens:**
- The boundary between "execution clarification" and "semantic change" (ADR-050 §5.2) is judgment-based, not mechanically enforced
- AI agents optimize for task completion and may rationalize semantic changes as clarifications
- No automated semantic diff exists to detect when user paths, business logic, or ACs have changed
- The回流 cost (Major → FRZ re-freeze) creates incentive to classify changes as Minor

**Consequences:**
- FRZ content becomes stale — the frozen truth no longer matches what was built
- Test expectations diverge from actual behavior
- Future extraction chains operate on outdated FRZ, compounding drift

**Prevention:**
- Implement the ADR-050 §5.2判断标准 as an **automated semantic diff**: compare pre- and post-change SSOT objects for changes to user_story, AC, state_machine, domain_model fields
- Any change to these fields triggers automatic Major classification, regardless of agent's self-assessment
- Add a `semantic-drift-check` gate in the Task Pack loop (ADR-051) that runs after each impl task
- Warning sign: Implementation PRs modify acceptance criteria text, add/remove user actions, or change state transitions without a corresponding FRZ update

**Phase to address:** Execution Layer Semantic Stability Rules (third v2.0 phase)

### Pitfall 4: Change Classification Gaming (ADR-049 Mapping Evasion)

**What goes wrong:** The three-tier ADR-049 classification (visual / interaction / semantic) is mapped to two-tier ADR-050 handling (Minor / Major). Teams or agents systematically reclassify semantic changes as interaction changes to avoid the costly FRZ回流 path.

**Why it happens:**
- The mapping boundary (ADR-050 §6.1) between "interaction" (Minor, backwrite UI/TESTSET) and "semantic" (Major, FRZ re-freeze) is inherently fuzzy
- A UI interaction change that alters user decision points IS a semantic change, but is easy to misclassify
- No automated classification validator exists — the initial classification is accepted without verification
- Major change path has high friction (FRZ re-discussion, re-freeze, SSOT rebuild), creating strong incentive to avoid it

**Consequences:**
- Semantic changes accumulate as patches instead of flowing through proper governance
- FRZ becomes progressively less accurate as a truth source
- Patch layer (ADR-049) becomes the de facto semantic store, inverting the governance model

**Prevention:**
- Implement a **change classifier** that analyzes the actual impact (not just the claimed category) — specifically check if the change affects acceptance_contract, core_journeys, or state_machine in the FRZ
- Require human review for any change classified as Minor that touches more than N patch entries (set threshold, e.g., N=10)
- Add automatic rebase trigger: every N patches must trigger a clean rebase (ADR-050 §6.2)
- Warning sign: Patch count grows steadily without corresponding rebases; FRZ and actual code diverge in user-facing behavior

**Phase to address:** Change Classification + ADR-049 Integration (fourth v2.0 phase)

---

## Moderate Pitfalls

### Pitfall 5: Three-Axis Governance Imbalance (Implementation Axis Creep)

**What goes wrong:** The implementation axis (ADR-050 §7, "weak management") gradually accumulates structure and becomes a shadow SSOT. Task metadata, status tracking, and execution notes grow complex enough that teams start treating task state as a secondary truth source, defeating the design principle of "light implementation tracking."

**Why it happens:**
- Task Pack files (ADR-051) naturally accumulate metadata: retry counts, error logs, timing data, reviewer notes
- No explicit limit on Task Pack schema complexity
- Teams add custom fields to track what the "weak" requirement axis doesn't capture
- The distinction between "implementation tracking" and "semantic truth" blurs over time

**Consequences:**
- System weight increases (the exact problem ADR-050 §7.2 warns against)
- Two competing truth sources emerge: requirement SSOT and implementation SSOT
- Governance becomes inconsistent — some decisions flow through FRZ, others through task metadata

**Prevention:**
- Define a **strict Task Pack schema** with explicit "no additional fields" policy (or a reserved `metadata` blob that is not governance-scoped)
- Add a `pack-schema-validate` step in the loop that rejects packs with unauthorized fields
- Quarterly audit: if Task Pack average file size exceeds a threshold (e.g., 50 lines), investigate creep
- Warning sign: Task Pack YAML files contain fields beyond pack_id, feat_ref, tasks array, and the 6 defined task types

**Phase to address:** Task Pack Orchestration (fifth v2.0 phase)

### Pitfall 6: Sequential Loop Failure Accumulation (Paused Indefinitely)

**What goes wrong:** The sequential loop (ADR-051 §2.3) pauses on task failure awaiting human intervention, but the pause state is never resolved. Failed packs accumulate, creating a growing backlog of blocked work. The "fail-safe" default becomes "fail-silent."

**Why it happens:**
- No timeout or escalation mechanism for paused loops
- Failed tasks in complex domains (API implementation, E2E tests) often require significant debugging — humans defer rather than resolve
- No dashboard or notification system surfaces paused loop state
- max_retries=2 (ADR-051 §4.2) is exhausted quickly on non-trivial failures
- The loop state file is static YAML — no mechanism for async human resolution

**Consequences:**
- Task Pack pipeline stalls, blocking downstream work
- Failed packs are forgotten rather than resolved
- The governance system appears broken because execution doesn't progress

**Prevention:**
- Implement **pause escalation**: after X hours in paused state, notify designated owner; after Y hours, auto-mark as "requires planning review"
- Add a `loop status` command that lists all paused packs with time-in-state
- Design the pack state file to support async human resolution (e.g., human writes resolution instructions to a separate file, loop picks up on next run)
- Warning sign: `ssot/tasks/` directory contains packs with `status: failed` or `status: still_failed` that haven't been touched in >48 hours

**Phase to address:** Task Pack Orchestration (fifth v2.0 phase)

### Pitfall 7: FRZ Staleness (Frozen Becomes Outdated)

**What goes wrong:** The FRZ package, once frozen, is treated as immutable truth. But external dependencies change, market conditions shift, and the FRZ's product_boundary and domain_model become stale. ADR-050 mandates FRZ re-freeze for Major changes, but doesn't address passive staleness where nobody proposes a change but the FRZ simply becomes wrong.

**Why it happens:**
- No periodic FRZ validity review — the freeze is assumed permanent until someone triggers a Major change
- `known_unknowns` entries expire (ADR-050 §3.2.3: `expires_in`) but expired unknowns don't trigger FRZ review
- External framework outputs (BMAD, Superpowers) evolve, but the FRZ is a point-in-time snapshot
- The Major change path is high-friction, so teams tolerate stale FRZ rather than trigger re-freeze

**Consequences:**
- Semantic extraction produces accurate projections of inaccurate truth
- Tests pass against obsolete requirements
- The governance system becomes internally consistent but externally wrong

**Prevention:**
- Implement a **FRZ review cadence**: after N Task Pack completions or T days (whichever comes first), trigger an FRZ validity check
- Track `known_unknowns` expiration and auto-flag FRZ review when unknowns expire without resolution
- Add an `frz stale-check` command that compares FRZ timestamps against recent development activity
- Warning sign: FRZ was last frozen >30 days ago with no Major changes, but significant code development has occurred

**Phase to address:** FRZ Structure Definition (ongoing governance, implement in first phase)

### Pitfall 8: Dual-Chain Verification Detachment from Task Pack

**What goes wrong:** The test-api and test-e2e tasks in a Task Pack (ADR-051 §2.1) execute tests, but the verification results are not properly bound back to the `verifies` field. The evidence exists but is not connected to the acceptance criteria it was meant to verify.

**Why it happens:**
- The `verifies: [AC-xxx]` binding in the Task Pack YAML is manual entry, not auto-populated from the FEAT definition
- Test execution produces results in a different format/location than what the governance system expects
- No automated binding validator checks that every AC in a FEAT has corresponding evidence
- The dual-chain verification (ADR-047) runs independently of the Task Pack loop

**Consequences:**
- Traceability breaks — you cannot prove that an AC was verified
- The evidence axis (ADR-050 §7, "light挂载") becomes empty — the binding relationship is missing
- Compliance and audit cannot demonstrate requirement coverage

**Prevention:**
- Auto-populate `verifies` field from FEAT acceptance criteria when generating the Task Pack
- Implement a `verifies-complete` gate in the loop that checks every AC has at least one passed test evidence reference
- Standardize evidence output format to match governance expectations (ADR-047 defines the format)
- Warning sign: Task Pack YAML has `verifies: []` on test tasks, or evidence files exist but no AC references point to them

**Phase to address:** Task Pack Orchestration + Dual-Chain Integration (fifth v2.0 phase)

### Pitfall 9: Patch Accumulation Without Clean Rebase

**What goes wrong:** ADR-050 §6.2 states "every N patches must trigger a clean rebase," but N is undefined and no mechanism enforces it. Patches accumulate indefinitely, making the SSOT increasingly difficult to reason about and eventually causing rebase conflicts that corrupt the semantic chain.

**Why it happens:**
- The rebase trigger threshold N is not specified in the ADR
- Clean rebase is manual effort — teams defer it indefinitely
- No tooling exists to count patches or flag when threshold is reached
- Each patch adds complexity; after ~10 patches (ADR-049 §12.1 context budget limit), the patch chain becomes unwieldy

**Consequences:**
- SSOT state becomes a complex overlay of patches rather than a clean document
- Rebase conflicts corrupt semantic content when finally attempted
- New team members cannot understand the SSOT because the "real" state is buried under patch layers
- Performance degradation in patch context injection (ADR-049 §12.1: 3000 token budget)

**Prevention:**
- Define N explicitly (recommend N=5) in the governance implementation
- Implement `patch count` monitoring in the loop — auto-block further patches when threshold reached until rebase is done
- Add a `ssot rebase` command that merges all patches into clean base documents
- Warning sign: Any SSOT object has more than 5 active patches; patch_context_injector output exceeds 2000 tokens

**Phase to address:** Change Classification + ADR-049 Integration (fourth v2.0 phase)

---

## Minor Pitfalls

### Pitfall 10: Task Pack Naming Convention Violation

**What goes wrong:** Pack files are created with non-standard naming (`PACK-xxx.yaml` instead of `PACK-{SRC_ID}-{FEAT_ID}-{slug}.yaml`, ADR-051 §3), making automated discovery and cross-referencing unreliable.

**Prevention:** Enforce naming via `pack validate` command that checks filename against the pattern. Reject packs with invalid names during loop ingestion.

### Pitfall 11: Evidence Format Inconsistency

**What goes wrong:** Dual-chain evidence (ADR-047) is written in varying formats across different test runs, making automated verification binding (Pitfall 8) unreliable.

**Prevention:** Define a strict evidence schema and validate all evidence files against it before accepting them as verification results.

### Pitfall 12: Loop Config Drift

**What goes wrong:** The loop configuration (ADR-051 §4.2) is modified ad-hoc — max_retries changed, stop_on_failure toggled — without governance oversight, undermining the stability guarantees of the sequential loop design.

**Prevention:** Version-control loop configs and require a governance-approved change process for any loop parameter modification. Add a `loop config diff` command to detect unauthorized changes.

---

## Integration Pitfalls with Existing System

### Integration Pitfall 1: ADR-049 Patch Layer vs ADR-050 Semantic Stability Conflict

**What goes wrong:** ADR-049's patch auto-registration (after code changes, patches are drafted and registered) conflicts with ADR-050's semantic stability rule (execution layer must not change semantics). The patch auto-registrar detects a semantic change and creates a patch for it, but ADR-050 requires it to flow through FRZ re-freeze instead.

**Root cause:** ADR-049 and ADR-050 have overlapping jurisdiction on "what happens when code changes." ADR-049 says "patch it," ADR-050 says "if semantic, go to FRZ." The patch auto-registrar doesn't know the semantic stability判断标准.

**Consequence:** Semantic changes are patched instead of re-frozen, or the system blocks all patches and requires manual triage for every change.

**Prevention:** Integrate the semantic stability classifier (Pitfall 3) into the patch auto-registrar — before drafting a patch, check if it's a semantic change. If yes, reject the patch and route to FRZ回流 path. Update `patch_auto_register.py` to call the semantic diff check before drafting.

**Phase to address:** Change Classification + ADR-049 Integration

### Integration Pitfall 2: Existing SSOT Objects Lack FRZ References

**What goes wrong:** The existing SSOT main chain (SRC/EPIC/FEAT objects in `ssot/`) was created under the old generation model. These objects do not have `frz_package_ref` fields linking them to an FRZ source. When the extraction chain is activated, it cannot determine which FRZ to extract from for existing objects.

**Root cause:** ADR-050 §4 changes the paradigm from generation to extraction, but existing SSOT objects predate FRZ.

**Consequence:** Extraction chain fails on existing objects, or produces inconsistent results (some objects have FRZ refs, some don't).

**Prevention:** Implement a **one-time FRZ backfill migration** before activating the extraction chain:
1. For each existing SRC/EPIC/FEAT, identify or create the corresponding FRZ package
2. Add `frz_package_ref` to all existing SSOT objects
3. Run a consistency audit to ensure all objects have valid FRZ references
4. Only then switch to extraction mode

**Phase to address:** SSOT Semantic Extraction Chain (must precede extraction activation)

### Integration Pitfall 3: ADR-018 Loop Runner Compatibility with Task Pack Schema

**What goes wrong:** The existing ADR-018 Execution Loop Job Runner was designed as a generic loop runtime. The Task Pack schema (ADR-051 §2.1) introduces specific fields (task type enum, depends_on, verifies, status machine) that the existing runner may not handle.

**Root cause:** ADR-018 provides "how to run loop" while ADR-051 defines "what to run." The interface between them is underspecified.

**Consequence:** The loop runner fails to parse Task Pack YAML, or executes tasks in wrong order, or doesn't trigger the correct verification chain after test tasks.

**Prevention:**
- Define an explicit **adapter interface** between ADR-018 runner and ADR-051 Task Pack
- Test the adapter with a representative Task Pack before production use
- Ensure the runner's state management supports the 7-state machine (pending/running/passed/failed/still_failed/skipped/blocked)
- Warning sign: ADR-018 runner reports task completion but Task Pack state file is not updated

**Phase to address:** Task Pack Orchestration (first action in that phase)

### Integration Pitfall 4: QA Skill Prompts Conflict with Semantic Extraction

**What goes wrong:** The 11 QA skill prompts (delivered in v1.0 Phase 2-3) were designed to work with the generation-model SSOT. When SSOT switches to extraction model, the QA prompts may reference generation-model assumptions (e.g., "verify FEAT content matches EPIC parent") that no longer apply.

**Root cause:** QA skills validate content relationships defined under the generation model. Under extraction, the validation target changes: it's now "verify FEAT content is a faithful projection of FRZ."

**Consequence:** QA skills produce false positives (passing checks on drifted content) or false negatives (failing checks on correctly extracted content that doesn't match old validation patterns).

**Prevention:**
- Audit all 11 QA skill prompts against the extraction model before activation
- Update validation logic from "parent-child consistency" to "FRZ projection fidelity"
- Add extraction-specific QA skills (e.g., "verify all FEAT content has FRZ anchor reference")

**Phase to address:** SSOT Semantic Extraction Chain (parallel: update QA skills as extraction chain is built)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| FRZ Structure + MSC Validation | Pitfall 1 (MSC incompleteness), Pitfall 7 (FRZ staleness) | Hard MSC gate, review cadence |
| SSOT Semantic Extraction Chain | Pitfall 2 (covert generation), Pitfall 4 (classification evasion), Integration 2 (missing FRZ refs), Integration 4 (QA skill conflicts) | Projection validator, backfill migration, QA prompt audit |
| Execution Layer Semantic Stability | Pitfall 3 (silent override) | Automated semantic diff gate |
| Change Classification + ADR-049 | Pitfall 4 (gaming), Pitfall 9 (patch accumulation), Integration 1 (patch vs semantic conflict) | Automated classifier, patch count enforcement, semantic check in patch registrar |
| Task Pack Orchestration | Pitfall 5 (axis creep), Pitfall 6 (failure accumulation), Pitfall 8 (dual-chain detachment), Pitfall 12 (loop drift), Integration 3 (ADR-018 compatibility) | Strict schema, pause escalation, auto-populated verifies, config versioning, adapter interface |
| Coordination Rules Update | All integration pitfalls | Cross-ADR compatibility test suite |
