# Phase 25: Bug 注册表与状态机 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-29
**Phase:** 025-bug-registry-state-machine
**Areas discussed:** State Machine, Integration, Bug ID
**Mode:** Decision delegation (user preferred simple/stable, Claude decided)

---

## State Machine Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| A: Reuse StateMachineExecutor | Extend cli/lib/state_machine_executor.py pattern. Proven YAML persistence, _get_valid_transitions() abstraction. Needs heavy adaptation for 9-state branching model + multi-instance. | |
| B: Purpose-built in bug_registry.py | State logic entirely in bug_registry.py. BUG_STATE_TRANSITIONS dict + transition_bug_status() function. Self-contained, no external dependencies. | ✓ |
| C: Composition pattern | Extract YAML persistence into reusable base, keep bug-specific logic in bug_registry.py. Reuses atomic write from frz_registry.py. Good for long-term but premature abstraction for Phase 25. | |

**Decision rationale:** Simplest and most stable. Single dict defines all transitions. YAML persistence directly copied from frz_registry.py (~30 lines). No coupling to state_machine_executor.py which has incompatible model (5-state linear vs 9-state branching).

---

## Integration with test_orchestrator.py

| Option | Description | Selected |
|--------|-------------|----------|
| A: Hook/callback injection | run_spec_test() gets on_complete=None parameter. Bug registry provides callback. Decoupled — orchestrator doesn't import bug_registry. | ✓ |
| B: Direct integration | test_orchestrator imports and calls sync_bugs_to_registry() directly. Simplest but tight coupling. Risk: bug_registry import failure breaks orchestrator. | |
| C: Event file | Orchestrator writes run-completed.json event. Separate CLI reads it and syncs. Fully decoupled but adds manual step. | |

**Decision rationale:** One parameter addition (default None = backward compatible). Decoupled architecture protects orchestrator from bug_registry failures. Debug runs safe (no callback = no sync). Future --verify-bugs mode injects different callback without changing orchestrator.

---

## Bug ID Generation

| Option | Description | Selected |
|--------|-------------|----------|
| A: case_id + 6-char hash | BUG-api.job.gen.invalid-progression-A1B2C3. Human-readable prefix + collision-resistant suffix. Naturally concurrent-safe. | ✓ |
| B: UUID v4 | BUG-a1b2c3d4-e5f6-7890-abcd-ef1234567890. Globally unique but not human-readable. Cannot grep by case. | |
| C: Sequential counter | BUG-001, BUG-002. Simplest but needs global counter lock. Lost on registry rebuild. No case traceability. | |

**Decision rationale:** Human-readable — developer sees case name instantly in terminal output. No global state needed (concurrent-safe). Survives registry rebuild via case_id fuzzy matching. Grep-friendly for daily debugging.

---

## OQ-4: not_reproducible N Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed N=3 | Simple, same threshold for all test levels. Risk: E2E noise baseline too high, misclassify real intermittent bugs. | |
| Tiered: Unit=3, Int=4, E2E=5 | Per-level thresholds matching stability baselines. E2E gets more samples due to browser timing/network noise. | ✓ |
| Dynamic N | Smoke use 3, full-suite use 5. Complex, different mode frequencies hard to align. | |

**Decision rationale:** Murat's "one-size-fits-all is lazy" argument is correct. E2E tests have far higher noise baseline than unit tests. Tiered adds minimal complexity but significantly improves accuracy.

---

## OQ-5: Severity Assignment

| Option | Description | Selected |
|--------|-------------|----------|
| A: Fully automatic | Settlement/gate auto-assigns severity. Fast but lacks business context. | |
| B: Fully manual | Developer reviews and marks each. Most accurate but high friction. | |
| C: System auto-assign + manual override | System gives initial assignment per rules. Developer can override via CLI. Covers 80% auto, 20% manual. | ✓ |

**Decision rationale:** Best cost-benefit ratio. Auto rules cover common patterns (contract_violation→high, env_flake→none, etc). Manual override via ll-bug-transition handles edge cases without high friction.

---

## Deferred Ideas

- Generic YamlRegistry abstraction layer — wait until 2+ registry consumers exist
- PR Check shadow fix detection — Phase 27
- Multi-feat conflict strategy — v2
- Batch aggregation logic migration (Execution→Gate) — v2 optimization
