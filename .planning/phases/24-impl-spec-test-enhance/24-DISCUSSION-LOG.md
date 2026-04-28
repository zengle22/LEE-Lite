# Phase 24: impl-spec-test 增强和验证 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 24-impl-spec-test-enhance
**Areas discussed:** Chinese section parsing strategy, api_required capability boundary heuristic, API preconditions/post-conditions depth, TESTSET auto-trigger integration point

---

## Chinese Section Parsing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Regex-based heading extraction | Pattern match markdown headings and extract nearby text. Fast, no dependencies. | |
| Integrate a markdown parser | Use mistletoe or markdown-it to build AST. More robust for nested structures. | |
| Hybrid: regex + parser | Regex for quick extraction, AST parser for structural validation when needed. | ✓ |

**User's choice:** Hybrid approach
**Notes:** User asked for detailed explanation of the three options in Chinese before selecting. Chose "All markdown docs in package" for scope.

---

## api_required Capability Boundary Heuristic

| Option | Description | Selected |
|--------|-------------|----------|
| FEAT scope/outputs inspection | Inspect scope/outputs for API endpoints or command contracts. | ✓ |
| Backend path validation | Check if implementation units touch backend service directories. | |
| Both scope + paths | FEAT must show API intent AND have backend touch points. | |
| Scope primary, keyword fallback | Use scope/outputs first, fall back to keywords when ambiguous. | |

**User's choice:** FEAT scope/outputs mention API endpoints or command contracts; remove keywords entirely
**Notes:** User explicitly chose to completely remove STRONG_API_KEYWORDS / WEAK_API_KEYWORDS keyword matching and rely purely on capability boundary detection.

---

## API Preconditions/Post-conditions Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Per-command section only | Each command gets its own preconditions/post-conditions subsection. | |
| Global API-level chapter only | One comprehensive chapter at the API-contract level. | |
| Per-command essentials + global cross-cutting patterns | Each command has caller context and idempotency; global chapter covers system state changes, UI mapping, event tracking. | ✓ |

**State description format:**

| Option | Description | Selected |
|--------|-------------|----------|
| Free-text narrative only | Human-readable description of pre-state/post-state. | |
| Structured state transition table only | Machine-readable table for downstream validation. | |
| Both narrative + structured table | Narrative for humans, table for automated checks. | ✓ |

**User's choice:** Per-command essentials + global cross-cutting patterns; Both narrative + structured table
**Notes:** User asked for analysis and recommendation before choosing. Selected the recommended options for both placement and state description.

---

## TESTSET Auto-trigger Integration Point

| Option | Description | Selected |
|--------|-------------|----------|
| During supervisor_review | After freeze gate passes but before handoff proposal. | |
| After run_workflow completes | At the very end, decoupled from tech freeze gate. | |
| Asynchronous downstream trigger | Event-based, not blocking feat-to-tech result. | |
| Conditional trigger only | Only when api_required or frontend_required is true. | ✓ |

**Blocking model:**

| Option | Description | Selected |
|--------|-------------|----------|
| Blocking | TESTSET result becomes part of feat-to-tech evidence. | |
| Non-blocking | TESTSET runs independently; feat-to-tech returns immediately. | ✓ |
| Blocking with timeout | Wait up to N seconds, then proceed. | |

**User's choice:** Conditional trigger (api_required or frontend_required); Non-blocking fire-and-forget
**Notes:** User wants to avoid unnecessary TESTSET generation for pure backend/governance FEATs, and does not want to slow down the feat-to-tech workflow.

---

## Claude's Discretion

- Exact regex pattern for Chinese heading extraction
- Whether to add a lightweight markdown parser dependency or use stdlib only
- Specific formatting of the state transition table (markdown table vs JSON block)

## Deferred Ideas

None.
