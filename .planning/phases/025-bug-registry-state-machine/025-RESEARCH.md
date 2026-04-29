# Phase 25: Bug Registry & State Machine - Research

**Researched:** 2026-04-29
**Domain:** Bug lifecycle management, state machines, YAML persistence, test orchestration integration
**Confidence:** HIGH

## Summary

Phase 25 implements the bug tracking foundation for ADR-055's three-layer architecture (Execution -> Acceptance -> Remediation). It produces three deliverables: (1) `bug_registry.py` with an independent state machine and YAML persistence, (2) `bug_phase_generator.py` for generating GSD fix-phase directories, and (3) integration with `test_orchestrator.py` via a callback injection pattern.

The design is tightly constrained by locked decisions in CONTEXT.md. The state machine is NOT reused from `state_machine_executor.py` -- it is a simple dict-based transition matrix. YAML persistence directly replicates the atomic write pattern from `frz_registry.py`. The integration with `test_orchestrator.py` uses a callback (`on_complete`) to avoid creating a direct import dependency.

**Primary recommendation:** Implement `bug_registry.py` as a ~200-line module mirroring `frz_registry.py`'s structure, with a `BUG_STATE_TRANSITIONS` dict and `transition_bug_status()` function. Use `frz_registry.py`'s `_load_registry` / `_save_registry` pattern verbatim for YAML atomic writes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Independent state machine in bug_registry.py, NOT reusing state_machine_executor.py
- **D-02:** BUG_STATE_TRANSITIONS dict + transition_bug_status() function
- **D-03:** YAML persistence reusing frz_registry.py's atomic write pattern (tempfile + os.replace)
- **D-04:** run_spec_test() gets on_complete=None callback parameter
- **D-05:** sync_bugs_to_registry() as callback, test_orchestrator doesn't import bug_registry
- **D-06:** bug_id format: BUG-{case_id}-{md5_hash_6char}
- **D-08:** not_reproducible N thresholds: Unit=3, Integration=4, E2E=5
- **D-11:** gap_type: code_defect / test_defect / env_issue
- **D-13:** Single bug single phase, --batch for mini-batch (max 2-3)
- **D-14:** Generated directory includes CONTEXT.md + PLAN.md (6 standard tasks) + DISCUSSION-LOG.md + SUMMARY.md

### Claude's Discretion
- build_bug_bundle() and test_exec_reporting.py integration granularity
- Optimistic lock version field generation (UUID vs timestamp hash)
- bug_phase_generator.py PLAN.md 6-task content template

### Deferred Ideas (OUT OF SCOPE)
- Generic YamlRegistry abstraction layer (Option C) -- wait for 2+ consumers
- PR Check shadow fix detection (ADR-055 §2.10 layer 2) -- Phase 27
- Multi-feat parallel conflict strategy (ADR-055 §2.11) -- v2
- Batch aggregation logic migration from Execution to Gate layer (Winston audit) -- v2 optimization
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUG-REG-01 | Bug registry module can create/read/update `artifacts/bugs/{feat_ref}/bug-registry.yaml` with optimistic locking | frz_registry.py pattern provides exact _load/_save implementation; update_manifest() provides optimistic lock reference |
| BUG-REG-02 | State machine: `detected -> open -> fixing -> fixed -> re_verify_passed -> closed` with clear triggers and fallbacks | ADR-055 §2.2 defines complete 9-state transition matrix; state_machine_executor.py _get_valid_transitions() shows dict pattern |
| BUG-REG-03 | Terminal states: wont_fix (needs resolution_reason), duplicate (needs duplicate_of), not_reproducible (auto, N=3/4/5). Resurrection creates new record with resurrected_from | ADR-055 §2.2 terminal state rules + §5.1 OQ-4 N threshold design |
| BUG-PHASE-01 | Phase generator creates `.planning/phases/{N}-bug-fix-{bug_id}/` with CONTEXT.md + PLAN.md (6 tasks) + DISCUSSION-LOG.md + SUMMARY.md | ADR-055 §2.4 generation flow + §2.5 6-task structure |
| BUG-PHASE-02 | Default single bug single phase, --batch mode for mini-batch (max 2-3 same-feat same-module bugs) | ADR-055 §2.4 mini-batch strategy |
| BUG-INTEG-01 | build_bug_bundle() output includes status:detected and gap_type (auto-inferred + manual override) | test_exec_reporting.py:174 existing build_bug_bundle() + ADR-055 §2.14 gap_type inference rules |
| BUG-INTEG-02 | sync_bugs_to_registry() persists detected bugs to `artifacts/bugs/{feat_ref}/bug-registry.yaml` with inline diagnostics | ADR-055 §2.3 schema + §2.9 execution subject matrix |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Bug state machine transitions | cli/lib/bug_registry.py | -- | Pure logic, no external dependencies; owns all state validation and transition execution |
| YAML persistence (atomic write) | cli/lib/bug_registry.py | cli/lib/fs.py | Reuses frz_registry.py pattern; fs.py provides ensure_parent/read_text/write_text |
| Bug ID generation | cli/lib/bug_registry.py | -- | Deterministic hash from case_id + run_id + timestamp; pure function |
| Phase directory generation | cli/lib/bug_phase_generator.py | -- | File system operations to create .planning/phases/{N}-bug-fix-*/ structure |
| Test orchestration integration | cli/lib/test_orchestrator.py | cli/lib/test_exec_reporting.py | Callback injection (on_complete); build_bug_bundle() upgrade for gap_type |
| CLI entry point | cli/commands/skill/command.py | -- | Future: register ll-bug-remediate, ll-bug-transition commands (Phase 27 scope, but plumbing needed) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | (installed) | YAML read/write for bug-registry.yaml | Already used by frz_registry.py, test_orchestrator.py; safe_load/safe_dump |
| hashlib (stdlib) | -- | MD5 hash for bug_id generation | D-06 specifies md5_hash_6char; stdlib, no dependency |
| tempfile (stdlib) | -- | Atomic write temp file creation | frz_registry.py pattern uses tempfile.mkstemp() |
| os (stdlib) | -- | Atomic rename via os.replace() | Cross-platform atomic file replacement |
| uuid (stdlib) | -- | UUID generation for optimistic lock version | test_orchestrator.py update_manifest() uses uuid.uuid4() |
| pathlib (stdlib) | -- | Path manipulation | Consistent with entire codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | (installed) | Unit tests for bug_registry, bug_phase_generator | All test files; @pytest.mark.unit |
| tempfile (test) | -- | tmp_workspace fixture for isolated test dirs | Same pattern as test_frz_registry.py |

**Installation:** No new packages required. All dependencies are stdlib or already installed.

## Architecture Patterns

### System Architecture Diagram

```
test_orchestrator.py:run_spec_test()
    |
    |  Step 3: execute_test_exec_skill()
    |  -> case_results (list of {case_id, status, actual, expected, ...})
    |
    v  on_complete callback (D-04, D-05)
sync_bugs_to_registry(workspace_root, feat_ref, proto_ref, run_id, case_results)
    |
    |  1. Filter case_results for status="failed"
    |  2. For each failed case:
    |     a. Generate bug_id: BUG-{case_id}-{md5_6char}
    |     b. Infer gap_type (flaky? -> env_issue, test code? -> test_defect, else code_defect)
    |     c. Build bug record dict (full schema per ADR-055 §2.3)
    |
    v
bug_registry.py:load_or_create_registry(feat_ref)
    |
    |  _load_registry(path) -- reads artifacts/bugs/{feat_ref}/bug-registry.yaml
    |  Returns existing bugs list or empty []
    |
    v
bug_registry.py:upsert_bug(bug_record)
    |
    |  Check if bug_id exists -> update
    |  If new -> append
    |  Optimistic lock: compare version, increment
    |
    v
bug_registry.py:_save_registry(path, data)
    |
    |  Atomic write: tempfile.mkstemp() -> yaml.dump() -> os.replace()
    |
    v
artifacts/bugs/{feat_ref}/bug-registry.yaml   (persisted)
```

### Recommended Project Structure
```
cli/lib/
├── bug_registry.py          # NEW: State machine + YAML persistence (~200 lines)
├── bug_phase_generator.py   # NEW: Phase directory generation (~150 lines)
├── test_orchestrator.py     # MODIFY: Add on_complete callback parameter
├── test_exec_reporting.py   # MODIFY: Upgrade build_bug_bundle() for gap_type
└── test_bug_registry.py     # NEW: Unit tests for bug_registry
└── test_bug_phase_generator.py  # NEW: Unit tests for bug_phase_generator
```

### Pattern 1: YAML Atomic Write (from frz_registry.py)

**What:** Write YAML to a temp file in the same directory, then atomically replace the target file. Prevents corruption from interrupted writes.

**When to use:** Any YAML registry that may be written concurrently or during interrupted sessions.

**Verified code from `cli/lib/frz_registry.py:45-66`:**
```python
def _save_registry(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to YAML using atomic write (temp file + os.replace)."""
    ensure_parent(path)
    content = yaml.dump(
        {"frz_registry": records},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    dir_name = path.parent
    fd, temp_path = tempfile.mkstemp(dir=str(dir_name), suffix=".yaml.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, str(path))
    except BaseException:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
```

**bug_registry.py adaptation:** Replace `{"frz_registry": records}` with `{"bug_registry": registry_dict}` where registry_dict contains schema_version, feat_ref, bugs list, and version field.

### Pattern 2: Dict-Based State Transition Matrix

**What:** A dict mapping each state to its set of valid next states. Transition validation is a simple set membership check.

**When to use:** Simple state machines with < 15 states and no side-effect-heavy transitions.

**Reference from `cli/lib/state_machine_executor.py:318-337` (design reference only, not code reuse):**
```python
# Design pattern only -- bug_registry uses a simpler dict
transitions: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.SETUP: {ExecutionState.EXECUTE},
    ExecutionState.EXECUTE: {ExecutionState.VERIFY, ExecutionState.COLLECT, ExecutionState.DONE},
    ...
}
```

**bug_registry.py implementation (locked by D-02):**
```python
BUG_STATE_TRANSITIONS: dict[str, set[str]] = {
    "detected":         {"open", "wont_fix", "duplicate"},
    "open":             {"fixing", "wont_fix", "duplicate"},
    "fixing":           {"fixed", "wont_fix", "duplicate"},
    "fixed":            {"re_verify_passed", "open", "wont_fix", "duplicate"},
    "re_verify_passed": {"closed", "wont_fix", "duplicate"},
    "archived":         {"wont_fix", "duplicate", "not_reproducible"},
    # Terminal states -- no outgoing transitions
    "closed":           set(),
    "wont_fix":         set(),
    "duplicate":        set(),
    "not_reproducible": set(),
}
```

### Pattern 3: Optimistic Locking (from test_orchestrator.py)

**What:** Each registry file has a `version` field (UUID). Before writing, read the current version; if it changed since last read, the write is rejected with a conflict error.

**Reference from `cli/lib/test_orchestrator.py:116-148`:**
```python
# Optimistic lock: read version, update, write with new version
expected_version = manifest_root.get("_version", manifest.get("_version", "0"))
# ... perform updates ...
manifest_root["_version"] = str(uuid.uuid4())
manifest_root["_last_updated"] = _timestamp()
```

**bug_registry.py adaptation:** The registry root gets a `version` field. `transition_bug_status()` reads the current version, validates it matches the caller's expected version, then writes with a new UUID. On mismatch, raise `CommandError("CONFLICT", "Registry version conflict")`.

### Pattern 4: Callback Injection (for test_orchestrator integration)

**What:** `run_spec_test()` accepts an optional `on_complete` callback. After Step 4 (update_manifest), if the callback is provided, it is invoked with the execution results. This decouples test_orchestrator from bug_registry.

**D-04 callback signature:**
```python
on_complete: Callable[[Path, str | None, str | None, str, list[dict[str, Any]]], None] | None = None
```

Parameters: `(workspace_root, feat_ref, proto_ref, run_id, case_results) -> None`

**Integration point in test_orchestrator.py (add after line 295, the update_manifest call):**
```python
if on_complete is not None:
    on_complete(workspace_root, feat_ref, proto_ref, run_id, case_results)
```

### Anti-Patterns to Avoid

- **Direct import of bug_registry from test_orchestrator:** D-05 explicitly forbids this. Use callback injection.
- **Class-based state machine:** D-02 specifies a dict + function pattern, not a class. Keep it simple.
- **Skipping version field:** Optimistic locking is required (BUG-REG-01). Without it, concurrent writes corrupt the registry.
- **Storing terminal states in the happy-path transition matrix:** Terminal states (wont_fix, duplicate, not_reproducible) can be reached from ANY non-terminal state. Model them as a separate rule, not as transitions from every state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML atomic write | Custom write-then-rename | Copy frz_registry.py _save_registry pattern verbatim | Handles temp file cleanup, cross-platform atomicity, encoding |
| Bug ID hash | Custom hash function | hashlib.md5 (stdlib) | D-06 specifies MD5; stdlib, correct length, no dependency |
| UUID generation | Custom timestamp-based version | uuid.uuid4() (stdlib) | test_orchestrator.py already uses this; proven collision-free |
| YAML parsing | Custom YAML parser | yaml.safe_load / yaml.dump (PyYAML) | Already installed, used everywhere |
| File path manipulation | os.path.join chains | pathlib.Path (stdlib) | Consistent with entire codebase |

**Key insight:** This phase has zero new dependencies. Every building block exists in stdlib or the current project.

## State Machine Implementation

### Complete Transition Matrix (from ADR-055 §2.2)

| From \ To | open | fixing | fixed | re_verify_passed | closed | wont_fix | duplicate | not_reproducible |
|-----------|------|--------|-------|------------------|--------|----------|-----------|------------------|
| detected  | gate FAIL | x | x | x | x | any time | any time | x |
| open      | x | manual | x | x | x | any time | any time | x |
| fixing    | x | x | commit | x | x | any time | any time | x |
| fixed     | verify fail | x | x | verify pass | x | any time | any time | x |
| re_verify_passed | x | x | x | x | 2-cond/auto | any time | any time | x |
| archived  | x | x | x | x | x | any time | any time | 3-strike |

### Validation Logic

```python
def transition_bug_status(
    bug: dict[str, Any],
    new_status: str,
    *,
    reason: str | None = None,
    actor: str = "system",
    **extra_fields,
) -> dict[str, Any]:
    """Transition a bug to a new status. Returns new bug dict (immutable)."""
    current = bug["status"]
    valid = BUG_STATE_TRANSITIONS.get(current, set())

    # Terminal state exceptions: wont_fix and duplicate reachable from any non-terminal
    if new_status in {"wont_fix", "duplicate"} and current not in {"closed", "wont_fix", "duplicate", "not_reproducible"}:
        pass  # allowed
    elif new_status not in valid:
        raise CommandError(
            "INVALID_REQUEST",
            f"Cannot transition bug {bug['bug_id']} from '{current}' to '{new_status}'",
        )

    # Terminal state field requirements
    if new_status == "wont_fix" and not reason:
        raise CommandError("INVALID_REQUEST", "wont_fix requires resolution_reason")
    if new_status == "duplicate" and not extra_fields.get("duplicate_of"):
        raise CommandError("INVALID_REQUEST", "duplicate requires duplicate_of")

    # Build new bug dict (immutable -- return new copy)
    new_bug = {**bug, "status": new_status}
    new_bug["trace"] = [*bug.get("trace", []), {
        "event": "status_changed",
        "at": _timestamp(),
        "from": current,
        "to": new_status,
        "actor": actor,
    }]
    if reason:
        new_bug["resolution_reason"] = reason
    for k, v in extra_fields.items():
        new_bug[k] = v

    return new_bug
```

### Error Handling for Invalid Transitions

- Raise `CommandError("INVALID_REQUEST", ...)` with descriptive message
- Include current status and attempted target status in the error
- The caller (CLI or script) catches this and displays to the user

### not_reproducible Auto-Mark Logic

```python
NOT_REPRODUCIBLE_THRESHOLDS = {
    "unit": 3,
    "integration": 4,
    "e2e": 5,
}

def check_not_reproducible(
    bug: dict[str, Any],
    consecutive_nonappearances: int,
    test_level: str = "integration",
) -> bool:
    """Should this bug be auto-marked as not_reproducible?"""
    threshold = NOT_REPRODUCIBLE_THRESHOLDS.get(test_level, 4)
    return (
        bug["status"] == "archived"
        and consecutive_nonappearances >= threshold
    )
```

## YAML Schema

### bug-registry.yaml Complete Structure

```yaml
bug_registry:
  schema_version: "1.0"
  registry_id: BUG-REG-{feat_ref}
  feat_ref: FEAT-SRC-003-001
  proto_ref: null
  version: "uuid-v4-string"          # Optimistic lock field
  generated_at: "2026-04-28T10:00:00Z"
  last_synced_at: "2026-04-28T12:00:00Z"
  last_sync_run_id: RUN-20260428-ABC12345
  bugs:
    - bug_id: BUG-api.job.gen.invalid-progression-A1B2C3
      case_id: api.job.gen.invalid-progression
      coverage_id: api.job.gen.invalid-progression
      title: "JOB-GEN-001: invalid-progression"
      status: detected              # Core field: one of 10 states
      severity: high                # auto-inferred + manual override
      gap_type: code_defect         # MVP: code_defect | test_defect | env_issue
      actual: "HTTP 200 with invalid progression state"
      expected: "HTTP 400 with validation error"
      evidence_ref: artifacts/active/qa/executions/run-xxx/evidence/result.json
      stdout_ref: artifacts/active/qa/executions/run-xxx/evidence/stdout.txt
      stderr_ref: artifacts/active/qa/executions/run-xxx/evidence/stderr.txt
      diagnostics:
        - "AssertionError: expected status 400, got 200"
      run_id: RUN-20260428-ABC12345
      discovered_at: "2026-04-28T10:00:00Z"
      fixed_at: null
      verified_at: null
      closed_at: null
      resolution: null              # closed_by: auto | manual_override
      fix_commit: null
      duplicate_of: null
      resolution_reason: null
      re_verify_result: null
      resurrected_from: null
      strike_count: 0               # For not_reproducible 3-strike tracking
      fix_hypothesis: null          # Populated during fix phase Task 1
      trace:
        - event: discovered
          at: "2026-04-28T10:00:00Z"
          run_id: RUN-20260428-ABC12345
      manifest_ref: ssot/tests/api/FEAT-SRC-003-001/api-coverage-manifest.yaml
```

### Field Defaults for New Bug Record

```python
def _build_bug_record(
    case_id: str,
    run_id: str,
    case_result: dict[str, Any],
    feat_ref: str | None,
    proto_ref: str | None,
) -> dict[str, Any]:
    """Build a new bug record from a failed case result."""
    now = datetime.now(timezone.utc).isoformat()
    hash_input = f"{case_id}{run_id}{now}"
    hash_6 = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
    bug_id = f"BUG-{case_id}-{hash_6}"

    return {
        "bug_id": bug_id,
        "case_id": case_id,
        "coverage_id": case_result.get("coverage_id", case_id),
        "title": case_result.get("title", case_id),
        "status": "detected",
        "severity": _infer_severity(case_result),
        "gap_type": _infer_gap_type(case_result),
        "actual": case_result.get("actual", ""),
        "expected": case_result.get("expected", ""),
        "evidence_ref": case_result.get("evidence_ref", ""),
        "stdout_ref": case_result.get("stdout_ref", ""),
        "stderr_ref": case_result.get("stderr_ref", ""),
        "diagnostics": case_result.get("diagnostics", [])[:5],  # Cap at 5 inline
        "run_id": run_id,
        "discovered_at": now,
        "fixed_at": None,
        "verified_at": None,
        "closed_at": None,
        "resolution": None,
        "fix_commit": None,
        "duplicate_of": None,
        "resolution_reason": None,
        "re_verify_result": None,
        "resurrected_from": None,
        "strike_count": 0,
        "fix_hypothesis": None,
        "trace": [{"event": "discovered", "at": now, "run_id": run_id}],
        "manifest_ref": _resolve_manifest_ref(feat_ref, proto_ref),
    }
```

## Integration Plan

### build_bug_bundle() Upgrade (BUG-INTEG-01)

**Current implementation** (`cli/lib/test_exec_reporting.py:174-201`):
- Filters case_results for status="failed"
- Generates flat JSON per bug with: bug_id, case_id, title, actual, expected, evidence_ref
- Creates index.json listing all bugs
- Uses SHA1 hash of case_id for bug_id (no run_id or timestamp)

**Required changes:**
1. Add `gap_type` field to each bug JSON (auto-inferred)
2. Add `status: "detected"` field
3. Add `run_id` to the hash input for bug_id generation (match D-06 format)
4. Add `diagnostics` array with inline diagnostic info
5. Switch from SHA1 to MD5 hash (D-06 specifies md5_hash_6char)

**Minimal diff approach:** Modify `build_bug_bundle()` to accept an optional `run_id` parameter and add the new fields. Keep backward compatibility by defaulting `run_id=None` (falls back to current behavior).

### sync_bugs_to_registry() Implementation (BUG-INTEG-02)

**New function in `cli/lib/bug_registry.py`:**
```python
def sync_bugs_to_registry(
    workspace_root: Path,
    feat_ref: str | None,
    proto_ref: str | None,
    run_id: str,
    case_results: list[dict[str, Any]],
) -> None:
    """Sync failed cases to bug-registry.yaml. Called as on_complete callback."""
    failed = [cr for cr in case_results if cr.get("status") == "failed"]
    if not failed:
        return

    registry = load_or_create_registry(workspace_root, feat_ref, proto_ref)
    for case_result in failed:
        bug_record = _build_bug_record(case_id, run_id, case_result, feat_ref, proto_ref)
        # Upsert: if bug_id exists, skip (same run won't re-create)
        existing = _find_bug_by_case_id(registry["bugs"], case_result["case_id"])
        if existing is None:
            registry["bugs"].append(bug_record)
        # If same case failed again in a new run, the new run generates a new bug_id
        # (per D-07: different failure -> different bug_id, linked by resurrected_from)

    registry["last_synced_at"] = _timestamp()
    registry["last_sync_run_id"] = run_id
    _save_registry(workspace_root, feat_ref, proto_ref, registry)
```

### on_complete Callback Injection (test_orchestrator.py)

**Modification to `run_spec_test()` signature:**
```python
def run_spec_test(
    workspace_root: Path,
    *,
    feat_ref: str | None = None,
    proto_ref: str | None = None,
    # ... existing params ...
    on_complete: Callable[..., None] | None = None,  # NEW
) -> StepResult:
```

**Invocation point (after line 295, after update_manifest):**
```python
    # -------------------------------------------------------------------------
    # Step 4.5: on_complete callback (Phase 25 integration point)
    # -------------------------------------------------------------------------
    if on_complete is not None:
        on_complete(workspace_root, feat_ref, proto_ref, run_id, case_results)
```

**Wiring point** (in `cli/commands/skill/command.py` or wherever `run_spec_test` is called):
```python
from cli.lib.bug_registry import sync_bugs_to_registry
result = run_spec_test(..., on_complete=sync_bugs_to_registry)
```

This keeps test_orchestrator.py free of bug_registry imports (D-05).

## Code Examples

### Registry Load/Create Pattern

```python
# Source: Adapted from cli/lib/frz_registry.py:26-43

def registry_path(workspace_root: Path, feat_ref: str) -> Path:
    return workspace_root / "artifacts" / "bugs" / feat_ref / "bug-registry.yaml"

def _load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_registry()
    text = read_text(path)
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return _empty_registry()
    return data.get("bug_registry", _empty_registry())

def _save_registry(path: Path, registry: dict[str, Any]) -> None:
    """Atomic write -- verbatim pattern from frz_registry.py."""
    ensure_parent(path)
    content = yaml.dump(
        {"bug_registry": registry},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    dir_name = path.parent
    fd, temp_path = tempfile.mkstemp(dir=str(dir_name), suffix=".yaml.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, str(path))
    except BaseException:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise

def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_id": "",
        "feat_ref": "",
        "proto_ref": None,
        "version": str(uuid.uuid4()),
        "generated_at": _timestamp(),
        "last_synced_at": _timestamp(),
        "last_sync_run_id": "",
        "bugs": [],
    }
```

### gap_type Auto-Inference (from ADR-055 §2.14)

```python
def _infer_gap_type(case_result: dict[str, Any]) -> str:
    """MVP gap_type inference. Developer can override via CLI."""
    # Condition 1: check if diagnostics suggest flaky behavior
    diagnostics = case_result.get("diagnostics", [])
    for d in diagnostics:
        dl = str(d).lower()
        if any(kw in dl for kw in ("timeout", "connection reset", "flaky", "intermittent")):
            return "env_issue"

    # Condition 2: check if stack trace points to test code
    stderr = case_result.get("stderr_ref", "")
    # Simplified: if evidence is in test directories, likely test_defect
    # Full implementation would parse stack traces

    # Default: code defect
    return "code_defect"
```

### PLAN.md 6-Task Template (from ADR-055 §2.5)

```python
PLAN_TEMPLATE = """# Bug Fix Plan: {bug_id}

## Tasks

### Task 1: Root Cause Analysis
- **Type:** auto
- **Description:** Analyze bug evidence and code paths to determine root cause
- **Input:** bug-registry entry for {bug_id}, execution evidence
- **Output:** fix_hypothesis (root_cause, expected_behavior_change, affected_files)

### Task 2: Implement Fix
- **Type:** auto
- **Description:** Minimal-scope fix for the identified root cause
- **Input:** Task 1 output, affected source files
- **Output:** Code changes (diff)

### Task 3: Update Bug Status
- **Type:** auto
- **Description:** `transition_bug_status(bug_id, "fixed", fix_commit=commit_hash)`
- **Status transition:** fixing -> fixed

### Task 4: Verify Fix
- **Type:** auto
- **Description:** Run `qa-test-run --verify-bugs` targeting this bug's coverage_id
- **Status transition:** fixed -> re_verify_passed (or back to open on failure)

### Task 5: Review & Close
- **Type:** auto
- **Description:** Generate fix summary. If 2 conditions met, auto-close and notify developer
- **Status transition:** re_verify_passed -> closed

### Task 6: Update Failure Case
- **Type:** auto
- **Description:** Update `tests/defect/failure-cases/BUG-{id}.md` with root cause and fix details
"""
```

## Common Pitfalls

### Pitfall 1: Forgetting Terminal State Exception Rule
**What goes wrong:** Implementing the transition matrix as a strict dict lookup without special-casing wont_fix/duplicate, which are reachable from ANY non-terminal state.
**Why it happens:** The transition matrix in ADR-055 shows wont_fix/duplicate as separate columns with checkmarks for every row, but the natural code approach is "look up from-state in dict."
**How to avoid:** Add explicit pre-check: if new_status in {"wont_fix", "duplicate"} and current not in terminal set, allow the transition regardless of the dict.
**Warning signs:** Unit tests failing for "detected -> wont_fix" or "fixing -> duplicate" transitions.

### Pitfall 2: Modifying case_results in Place
**What goes wrong:** Mutating the case_results list during sync_bugs_to_registry(), which the caller may still reference.
**Why it happens:** Adding gap_type or bug_id fields directly to case_result dicts.
**How to avoid:** Build new bug record dicts from case_result data. Never modify the input list. Follow the immutability principle from coding-style.md.
**Warning signs:** Flaky tests where case_results carry over state between test runs.

### Pitfall 3: Version Conflicts on Every Write
**What goes wrong:** Two sequential calls to sync_bugs_to_registry() within the same test run produce a version conflict because version is read once but the file was modified.
**Why it happens:** Not re-reading the version before each write, or not using file-level locking.
**How to avoid:** sync_bugs_to_registry() should be a single atomic read-modify-write cycle. Read registry, add bugs, write registry -- all in one function call. No external state between read and write.
**Warning signs:** Spurious "Registry version conflict" errors during normal single-user operation.

### Pitfall 4: Missing feat_ref in bug-registry path
**What goes wrong:** Creating `artifacts/bugs/None/bug-registry.yaml` when feat_ref is None (E2E chain uses proto_ref).
**Why it happens:** Not handling the feat_ref=None case for E2E chains.
**How to use:** Use `feat_ref or proto_ref` as the directory name. Always validate before path construction.
**Warning signs:** Directory named "None" appearing under artifacts/bugs/.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat bug JSON per case (build_bug_bundle) | YAML registry with state machine | ADR-055 (this phase) | Bugs persist across runs; state transitions tracked; single source of truth per feat |
| No gap_type classification | 3-type MVP: code_defect / test_defect / env_issue | ADR-055 §2.14 v1.6 | Enables automatic routing (test_defect -> lightweight path, code_defect -> GSD phase) |
| Bug info lost on next test run | YAML registry in artifacts/bugs/ survives re-runs | ADR-055 §2.3 | Historical bug tracking, trend analysis |

**Deprecated/outdated:**
- build_bug_bundle() flat JSON: Still generated for backward compatibility but the YAML registry is the new SSOT for bug state
- SHA1 hash for bug_id: Replaced by MD5 per D-06 (consistent length, no security requirement)

## Risk Analysis

### Risk 1: Concurrent test runs corrupting registry
**Probability:** Medium (multiple developers, CI + local)
**Impact:** HIGH -- corrupted YAML loses all bug state
**Mitigation:** Atomic write (tempfile + os.replace) prevents partial writes. Optimistic lock (version UUID) prevents silent overwrites. If two runs race, the second gets a clear error and can retry.
**Detection:** YAML parse error on load -> auto-recover by re-running test

### Risk 2: bug_id collision from MD5 truncation
**Probability:** LOW (6 hex chars = 16^6 = 16.7M combinations)
**Impact:** MEDIUM -- two different bugs get same ID, one overwrites the other
**Mitigation:** Hash input includes case_id + run_id + timestamp, providing high entropy. Collision requires same case failing in the same millisecond across runs.
**Detection:** Duplicate bug_id check in upsert logic

### Risk 3: Stale registry accumulating detected bugs
**Probability:** HIGH (inherent to design)
**Impact:** LOW -- registry grows but does not break
**Mitigation:** Phase 26 (gate_remediation.py) handles detected->archived and not_reproducible cleanup. Phase 25 just provides the data structure; cleanup is Phase 26 responsibility.
**Detection:** Registry size monitoring (future)

### Risk 4: on_complete callback not wired in CLI
**Probability:** HIGH (plumbing work in command.py)
**Impact:** MEDIUM -- sync_bugs_to_registry never called, registry stays empty
**Mitigation:** Phase 25 must include the wiring. Test with a manual call to verify end-to-end.
**Detection:** Integration test that calls run_spec_test(on_complete=sync_bugs_to_registry) and checks registry

### Risk 5: Edge case -- same case_id fails in consecutive runs
**Probability:** HIGH (normal development workflow)
**Impact:** LOW if handled correctly
**Mitigation:** D-07 says same case different failure = different bug_id (timestamp in hash). But same case same failure should NOT create duplicate. Logic: if a bug with this case_id already exists in "detected" status from a recent run, skip creation. If previous bug is in terminal state, create new record with resurrected_from.
**Detection:** Unit test covering consecutive failures of same case

## Open Questions

1. **What is the exact behavior when case_id exists in detected state from a prior run?**
   - What we know: D-07 says different failures get different bug_ids
   - What's unclear: If the exact same case fails again before gate runs, do we create a second detected record or update the existing one?
   - Recommendation: Skip creation if a bug with the same case_id is already in detected/fixed/re_verify_passed status. Only create a new record if the prior bug is in a terminal state.

2. **How does the optimistic lock version field initialize for a new registry?**
   - What we know: test_orchestrator.py uses uuid.uuid4() for _version
   - What's unclear: Whether the version goes in the top-level registry dict or per-bug
   - Recommendation: Top-level only (same as manifest). Per-bug locking adds complexity with no MVP benefit.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | All modules | Yes | -- | -- |
| PyYAML | YAML persistence | Yes | (installed) | -- |
| pytest | Unit tests | Yes | (installed) | -- |
| hashlib (stdlib) | bug_id generation | Yes | -- | -- |
| tempfile (stdlib) | Atomic write | Yes | -- | -- |
| uuid (stdlib) | Version field | Yes | -- | -- |

**No missing dependencies.** This phase uses only stdlib and already-installed packages.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml (existing) |
| Quick run command | `pytest cli/lib/test_bug_registry.py -x -v` |
| Full suite command | `pytest cli/lib/test_bug_registry.py cli/lib/test_bug_phase_generator.py -x -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUG-REG-01 | Create/read/update YAML registry | unit | `pytest cli/lib/test_bug_registry.py::test_load_or_create -x` | No -- Wave 0 |
| BUG-REG-01 | Optimistic lock version field | unit | `pytest cli/lib/test_bug_registry.py::test_optimistic_lock -x` | No -- Wave 0 |
| BUG-REG-02 | State machine happy path transitions | unit | `pytest cli/lib/test_bug_registry.py::test_happy_path_transitions -x` | No -- Wave 0 |
| BUG-REG-02 | Invalid transition raises error | unit | `pytest cli/lib/test_bug_registry.py::test_invalid_transition -x` | No -- Wave 0 |
| BUG-REG-03 | wont_fix requires resolution_reason | unit | `pytest cli/lib/test_bug_registry.py::test_wont_fix_requires_reason -x` | No -- Wave 0 |
| BUG-REG-03 | duplicate requires duplicate_of | unit | `pytest cli/lib/test_bug_registry.py::test_duplicate_requires_ref -x` | No -- Wave 0 |
| BUG-REG-03 | not_reproducible threshold logic | unit | `pytest cli/lib/test_bug_registry.py::test_not_reproducible_thresholds -x` | No -- Wave 0 |
| BUG-REG-03 | Resurrection creates new record | unit | `pytest cli/lib/test_bug_registry.py::test_resurrection_new_record -x` | No -- Wave 0 |
| BUG-PHASE-01 | Phase directory structure generation | unit | `pytest cli/lib/test_bug_phase_generator.py::test_phase_dir_structure -x` | No -- Wave 0 |
| BUG-PHASE-02 | Mini-batch aggregation | unit | `pytest cli/lib/test_bug_phase_generator.py::test_mini_batch -x` | No -- Wave 0 |
| BUG-INTEG-01 | build_bug_bundle includes gap_type | unit | `pytest cli/lib/test_bug_registry.py::test_gap_type_inference -x` | No -- Wave 0 |
| BUG-INTEG-02 | sync_bugs_to_registry persists to YAML | unit | `pytest cli/lib/test_bug_registry.py::test_sync_persists -x` | No -- Wave 0 |

### Wave 0 Gaps
- [ ] `cli/lib/test_bug_registry.py` -- covers BUG-REG-01/02/03, BUG-INTEG-01/02
- [ ] `cli/lib/test_bug_phase_generator.py` -- covers BUG-PHASE-01/02
- [ ] Framework: none needed (pytest already installed)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | gap_type inference heuristics (timeout/keywords -> env_issue) will catch ~70% of flaky cases | gap_type inference | Low -- manual override always available |
| A2 | MD5 6-char truncation collision rate acceptable for <1000 bugs per feat | bug_id generation | Low -- 16.7M combinations, hash includes timestamp |
| A3 | on_complete callback pattern sufficient for integration (no async/queue needed) | Integration plan | Low -- test_orchestrator is synchronous |
| A4 | frz_registry.py atomic write pattern works correctly on Windows (os.replace) | YAML persistence | Low -- already tested in frz_registry |
| A5 | bug_phase_generator.py PLAN.md template defined by planner (Claude's Discretion) | Phase generation | Medium -- template content affects fix quality |

## Sources

### Primary (HIGH confidence)
- `cli/lib/frz_registry.py` -- YAML atomic write pattern, _load_registry/_save_registry
- `cli/lib/test_orchestrator.py` -- run_spec_test() flow, update_manifest() optimistic lock, _get_failed_coverage_ids()
- `cli/lib/test_exec_reporting.py` -- build_bug_bundle() existing implementation, case_results data structure
- `cli/lib/state_machine_executor.py` -- _get_valid_transitions() dict pattern (design reference)
- `cli/lib/errors.py` -- CommandError taxonomy, ensure() helper
- `cli/lib/fs.py` -- ensure_parent, read_text, write_text, write_json
- `ssot/adr/ADR-055-Bug流转闭环与GSD执行阶段集成.md` -- Complete design specification

### Secondary (MEDIUM confidence)
- `cli/lib/test_frz_registry.py` -- Test pattern for registry modules (tmp_workspace fixture, pytest.mark.unit)
- `cli/lib/contracts.py` -- StepResult dataclass definition
- `cli/lib/registry_store.py` -- CRUD API design reference (JSON-based but similar pattern)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies; all stdlib or already installed
- Architecture: HIGH -- locked decisions in CONTEXT.md + detailed ADR-055 specification
- State machine: HIGH -- complete transition matrix from ADR-055 §2.2
- Pitfalls: HIGH -- identified from code analysis and state machine edge cases
- Integration: MEDIUM -- on_complete callback wiring point in command.py not yet verified

**Research date:** 2026-04-29
**Valid until:** 2026-05-29 (30 days -- design is locked, unlikely to change)

## RESEARCH COMPLETE
