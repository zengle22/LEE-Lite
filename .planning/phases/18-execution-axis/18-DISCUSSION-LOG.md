# Phase 18: 实施轴 P0 模块 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-24
**Phase:** 18-execution-axis
**Areas discussed:** run-manifest 存储位置, scenario spec A/B/C 层, state machine 持久化, step 执行粒度

---

## Area 1: run-manifest 存储位置

| Option | Description | Selected |
|--------|-------------|----------|
| ssot/tests/.artifacts/runs/{run_id}/ | Dedicated runs directory with run_id-based subdirectories | ✓ |
| ssot/tests/.artifacts/evidence/{run_id}/ | Same as evidence, grouped by run_id | |
| ssot/environments/{run_id}-manifest.yaml | Alongside ENV files | |

**User's choice:** `ssot/tests/.artifacts/runs/{run_id}/`
**Notes:** Clean separation from evidence

### Versioning & Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Append-only (keep all) | Never delete run manifests. Full audit trail. | ✓ |
| Keep last N runs | Retain last 5-10 runs per proto/feat | |
| Keep failed only | Delete successful runs, keep failures | |

**User's choice:** Append-only

---

## Area 2: scenario spec A/B/C 层

| Option | Description | Selected |
|--------|-------------|----------|
| Placeholder + evidence collection | Mark C_MISSING, collect evidence for manual review | ✓ |
| Skip entirely | C-layer out of scope for P0 | |
| Fail-fast if C_MISSING | Mark scenario incomplete, require resolution | |

**User's choice:** Placeholder + evidence collection

### C_MISSING Evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Network logs (HAR capture) | Capture HAR logs for later API verification | |
| Screenshot + console logs | Visual evidence + console output | |
| Both HAR + screenshot | Comprehensive evidence | ✓ |

**User's choice:** Both HAR + screenshot

---

## Area 3: state machine 持久化

| Option | Description | Selected |
|--------|-------------|----------|
| Embed in run-manifest.yaml | State in run-manifest with step markers | |
| Separate state file | Separate {run_id}-state.yaml alongside | ✓ |
| Manifest-level completion markers | Update coverage-manifest with step_refs | |

**User's choice:** Separate `{run_id}-state.yaml` file

### State Tracking Granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Journey-level completion | Track completed journeys only | |
| Step-level within journeys | Track each step within journeys | ✓ |
| Assertion-level within steps | Track each assertion | |

**User's choice:** Step-level tracking

---

## Area 4: step 执行粒度

| Option | Description | Selected |
|--------|-------------|----------|
| Per-journey (atomic) | Each journey = one atomic unit | |
| Per-step within journey | Each UI action = one step | ✓ |
| Per-assertion | Each assertion = one step | |

**User's choice:** Per-step within journey

### Error Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Stop journey, collect evidence | On failure, stop journey, go to COLLECT | ✓ |
| Skip failed, continue journey | Continue with remaining steps | |
| Per-assertion level decision | A-layer stops, B-layer logs + continues | |

**User's choice:** Stop journey, collect evidence

---

## Claude's Discretion

None — all decisions made by user

## Deferred Ideas

None

