# Phase 18: 实施轴 P0 模块 - Research

**Researched:** 2026-04-24
**Domain:** Test execution runtime - run-manifest generation, scenario spec compilation, 3-state machine executor, E2E chain testing
**Confidence:** HIGH

## Summary

Phase 18 delivers the P0 implementation components for the execution axis (实施轴), completing the bridge from Phase 17. The phase requires three core modules: (1) `run_manifest_gen.py` for unique run identification with version/environment binding, (2) `scenario_spec_compile.py` for E2E spec to scenario spec compilation with A/B/C layer assertions, and (3) `state_machine_executor.py` with a 3-state model (SETUP/EXECUTE/VERIFY/COLLECT/DONE). Additionally, it includes E2E chain end-to-end testing (TEST-02, TEST-03) with `--resume` support.

Key findings: (1) Phase 17 already built `spec_adapter.py`, `environment_provision.py`, `test_orchestrator.py`, and `contracts.py` - Phase 18 extends these rather than rewriting. (2) The artifact directory structure `ssot/tests/.artifacts/runs/{run_id}/` is specified in CONTEXT.md (D-01, D-02) but does not yet exist. (3) The `test_exec_playwright.py` already has complete Playwright execution patterns that can be extended. (4) The 3-state model is simplified from the 9-node model (FR-02 deferred) - all non-DONE failures flow to COLLECT.

**Primary recommendation:** Build Phase 18 modules as thin extensions to existing Phase 17 infrastructure. `run_manifest_gen.py` writes to `ssot/tests/.artifacts/runs/{run_id}/run-manifest.yaml`, `scenario_spec_compile.py` extends `spec_adapter.py` with A/B/C layer logic, and `state_machine_executor.py` wraps the orchestrator with state persistence.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** run-manifest storage in `ssot/tests/.artifacts/runs/{run_id}/` directory
- **D-02:** Append-only storage for full audit trail, never delete
- **D-03:** C-layer assertions marked `C_MISSING` with placeholder + evidence collection
- **D-04:** C_MISSING placeholders collect both HAR + screenshot for manual review
- **D-05:** Separate `{run_id}-state.yaml` file for state persistence (not embedded in run-manifest)
- **D-06:** Step-level tracking within journeys (per-step granularity)
- **D-07:** Per-step within journey as atomic unit
- **D-08:** On step failure: stop journey, go to COLLECT state, collect evidence
- **D-09:** `qa test-run --proto-ref XXX --app-url http://localhost:3000 --api-url http://localhost:8000`
- **D-10:** `--resume` reads from `{run_id}-state.yaml` to continue from last completed step

### Claude's Discretion
- Specific implementation of run_id format (current suggestion: `e2e.run-{timestamp}-{random_suffix}`)
- Internal structure of run-manifest.yaml fields
- Internal structure of state.yaml
- Step-level tracking granularity details
- How HAR capture is implemented (Playwright built-in vs. manual)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXEC-01 | `run_manifest_gen.py` — unique run-manifest.yaml with git sha/frontend build/backend build/base_url/browser/accounts | Existing `test_exec_reporting.py` evidence patterns inform artifact structure; `environment_provision.py` provides URL fields |
| EXEC-02 | `scenario_spec_compile.py` (simplified) — e2e spec to scenario spec, A/B layers, C layer `C_MISSING` | `spec_adapter.py` provides parsing foundation; ADR-054 §3 Phase 2 specifies simplified version |
| EXEC-03 | `state_machine_executor.py` (3-state model) — SETUP/EXECUTE/VERIFY/COLLECT/DONE, non-DONE failures to COLLECT | `job_state.py` provides state transition patterns; existing state machine not present |
| TEST-02 | E2E chain E2E testing — `qa test-run --proto-ref XXX --app-url ... --api-url ...` | `test_orchestrator.py` provides CLI invocation pattern; Playwright patterns from `test_exec_playwright.py` |
| TEST-03 | `--resume` re-run failed cases | `test_orchestrator.py` already implements `_get_failed_coverage_ids()` and `_filter_test_units_by_failed()` |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| run-manifest generation | API/Backend | CLI layer | Manifest is a server-side artifact; CLI invokes via test_orchestrator |
| scenario spec compilation | API/Backend | — | Pure transformation logic; no client involvement |
| state machine execution | API/Backend | CLI layer | State transitions happen server-side; CLI reads state.yaml |
| E2E chain test invocation | CLI layer | API/Backend | CLI is the user-facing entry point; test_orchestrator handles backend |
| `--resume` logic | CLI layer | API/Backend | Resume reads state.yaml and filters units; orchestrator re-executes |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Language runtime | Project baseline |
| PyYAML | latest | YAML serialization for manifests | Existing project standard |
| pytest | 9.0.2 | Test framework | Already in use, see `tests/cli/lib/` |
| `@playwright/test` | ^1.58.2 | E2E test execution | Already used in `test_exec_playwright.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `git` Python library | — | Git SHA retrieval | EXEC-01 git sha field |
| subprocess | stdlib | Running git commands | For git sha without external dep |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| GitPython library | subprocess git command | subprocess avoids extra dependency; simpler |
| Custom state machine | `transitions` library | Built-in Python with simple states; external lib overkill |

**Installation:**
```bash
pip install pyyaml pytest
npm install @playwright/test@^1.58.2
```

**Version verification:** All core packages are already present in the project.

---

## Architecture Patterns

### System Architecture Diagram

```
CLI (qa test-run)
    │
    ├─── reads --proto-ref, --app-url, --api-url, --resume
    │
    ▼
test_orchestrator.run_spec_test()
    │
    ├─ Step 1: provision_environment() → ENV file
    ├─ Step 2: spec_to_testset() → SPEC_ADAPTER_COMPAT
    │
    ▼
[NEW] run_manifest_gen.py (EXEC-01)
    │  - generates ssot/tests/.artifacts/runs/{run_id}/run-manifest.yaml
    │  - binds git sha, frontend/backend build, URLs, browser, accounts
    │
    ▼
[NEW] scenario_spec_compile.py (EXEC-02)
    │  - compiles e2e spec → scenario spec
    │  - A-layer: UI state assertions
    │  - B-layer: network/API assertions
    │  - C-layer: C_MISSING placeholders with HAR + screenshot collection
    │
    ▼
[NEW] state_machine_executor.py (EXEC-03)
    │  - 3-state model: SETUP → EXECUTE → VERIFY → COLLECT → DONE
    │  - persists state to {run_id}-state.yaml
    │  - per-step tracking (atomic units)
    │  - on failure: stop journey → COLLECT
    │
    ▼
test_exec_playwright.py (existing)
    │  - renders Playwright test spec
    │  - executes playwright project
    │  - parses report results
    │
    ▼
{run_id}-state.yaml (persisted)
    │
    ▼
ssot/tests/.artifacts/runs/{run_id}/
    ├─ run-manifest.yaml       ← EXEC-01 output
    ├─ {run_id}-state.yaml    ← EXEC-03 output
    ├─ evidence/              ← HAR + screenshots for C_MISSING
    └─ scenario-spec/         ← EXEC-02 output
```

### Recommended Project Structure
```
cli/lib/
├── run_manifest_gen.py           # NEW: EXEC-01
├── scenario_spec_compile.py       # NEW: EXEC-02
├── state_machine_executor.py      # NEW: EXEC-03
├── spec_adapter.py                # EXISTING: extended by EXEC-02
├── test_orchestrator.py          # EXISTING: extended with state machine
└── ...

ssot/tests/.artifacts/            # EXISTING: extended structure
└── runs/                         # NEW: per-run directory
    └── {run_id}/
        ├── run-manifest.yaml
        ├── {run_id}-state.yaml
        ├── scenario-spec/
        └── evidence/
```

### Pattern 1: Run Manifest Generation
**What:** Generate a unique, immutable run-manifest.yaml per execution with full environment binding.
**When to use:** Every test execution, created before test run begins.
**Example:**
```python
# Source: based on existing test_exec_reporting.py evidence patterns
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import yaml

def generate_run_manifest(
    workspace_root: Path,
    run_id: str,
    *,
    app_url: str,
    api_url: str | None = None,
    browser: str = "chromium",
    accounts: list[str] | None = None,
) -> Path:
    """Generate run-manifest.yaml with git sha, build versions, URLs."""
    # Get git SHA
    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace_root,
        capture_output=True,
        text=True,
    ).stdout.strip() or "unknown"

    manifest = {
        "run_id": run_id,
        "run_id_format": "e2e.run-{timestamp}-{random}",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "git_sha": git_sha,
        "frontend_build": _get_build_version(workspace_root / "frontend"),
        "backend_build": _get_build_version(workspace_root / "backend"),
        "base_url": {
            "app": app_url,
            "api": api_url,
        },
        "browser": browser,
        "accounts": accounts or [],
        "artifact_version": "1.0",
    }

    runs_dir = workspace_root / "ssot/tests/.artifacts/runs" / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = runs_dir / "run-manifest.yaml"
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, allow_unicode=True, sort_keys=False)
    return manifest_path
```

### Pattern 2: Scenario Spec Compilation with A/B/C Layers
**What:** Convert e2e-journey-spec to scenario spec with three assertion layers.
**When to use:** Before E2E test execution, to organize assertions by type.
**Example:**
```python
# Source: based on spec_adapter.py patterns + ADR-054 §3 Phase 2
@dataclass
class ScenarioSpec:
    journey_id: str
    spec_id: str
    steps: list[ScenarioStep]
    assertions: ScenarioAssertions

@dataclass
class ScenarioAssertions:
    a_layer: list[str]  # UI state assertions (visible, text, etc.)
    b_layer: list[str]  # Network/API assertions (HAR-verified)
    c_layer: list[CLayerAssertion]  # Business state (C_MISSING placeholder)

@dataclass
class CLayerAssertion:
    type: Literal["C_MISSING"]
    description: str
    evidence_required: list[str]  # ["har", "screenshot"]
    placeholder: str = "C_MISSING: Business state verification pending"

def compile_scenario_spec(e2e_spec: dict[str, Any]) -> ScenarioSpec:
    """Compile e2e spec to scenario spec with A/B/C layers."""
    # A-layer: from Expected UI States
    a_layer = [line for line in e2e_spec.get("expected_ui_states", [])]

    # B-layer: from Expected Network Events
    b_layer = [line for line in e2e_spec.get("expected_network_events", [])]

    # C-layer: business state assertions → C_MISSING
    c_layer = [
        CLayerAssertion(
            type="C_MISSING",
            description=line,
            evidence_required=["har", "screenshot"],
        )
        for line in e2e_spec.get("expected_persistence", [])
    ]

    return ScenarioSpec(
        journey_id=e2e_spec.get("journey_id", ""),
        spec_id=e2e_spec.get("coverage_id", ""),
        steps=[...],
        assertions=ScenarioAssertions(
            a_layer=a_layer,
            b_layer=b_layer,
            c_layer=c_layer,
        ),
    )
```

### Pattern 3: 3-State Machine Executor
**What:** Execute tests with state persistence, supporting resume and failure collection.
**When to use:** E2E test execution with per-step tracking.
**Example:**
```python
# Source: based on job_state.py patterns + CONTEXT.md D-05 to D-08
from enum import Enum

class StateMachineState(str, Enum):
    SETUP = "SETUP"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    COLLECT = "COLLECT"
    DONE = "DONE"

@dataclass
class ExecutionState:
    run_id: str
    current_state: StateMachineState
    current_journey: str | None
    current_step_index: int
    completed_steps: list[CompletedStep]
    failed_journeys: list[str]
    created_at: str
    updated_at: str

@dataclass
class CompletedStep:
    journey_id: str
    step_index: int
    step_name: str
    status: str  # "passed", "failed"
    error: str | None = None

def execute_with_state_machine(
    workspace_root: Path,
    run_id: str,
    spec: ScenarioSpec,
    *,
    resume: bool = False,
) -> ExecutionState:
    """Execute scenario with 3-state machine and state persistence."""
    state_path = workspace_root / f"ssot/tests/.artifacts/runs/{run_id}/{run_id}-state.yaml"

    if resume and state_path.exists():
        state = _load_state(state_path)
        # Resume from last completed step
        start_journey = state.current_journey
        start_step = state.current_step_index + 1
    else:
        state = ExecutionState(
            run_id=run_id,
            current_state=StateMachineState.SETUP,
            current_journey=None,
            current_step_index=0,
            completed_steps=[],
            failed_journeys=[],
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    # State transitions
    _transition_state(state, StateMachineState.SETUP)

    for journey in spec.journeys:
        state.current_journey = journey.journey_id
        state.current_state = StateMachineState.EXECUTE

        for step_idx, step in enumerate(journey.steps):
            if resume and _is_step_completed(state, journey.journey_id, step_idx):
                continue

            try:
                _execute_step(step)
                state.completed_steps.append(CompletedStep(
                    journey_id=journey.journey_id,
                    step_index=step_idx,
                    step_name=step.name,
                    status="passed",
                ))
            except StepError as e:
                # Per D-07: stop journey, go to COLLECT
                state.completed_steps.append(CompletedStep(
                    journey_id=journey.journey_id,
                    step_index=step_idx,
                    step_name=step.name,
                    status="failed",
                    error=str(e),
                ))
                state.failed_journeys.append(journey.journey_id)
                state.current_state = StateMachineState.COLLECT
                _collect_evidence(workspace_root, run_id, journey)
                break  # Stop journey, move to next

        if state.current_state != StateMachineState.COLLECT:
            state.current_state = StateMachineState.VERIFY

    # Final transition
    if state.failed_journeys:
        state.current_state = StateMachineState.COLLECT
    else:
        state.current_state = StateMachineState.DONE

    _save_state(state_path, state)
    return state
```

### Anti-Patterns to Avoid
- **In-memory state storage:** Per D-05, state MUST be in `{run_id}-state.yaml`. Do not store state in memory or in run-manifest.
- **Deleting old run artifacts:** Per D-02, artifacts are append-only. Never delete `runs/{run_id}` after creation.
- **Blocking all journeys on one failure:** Per D-08, only the failed journey stops. Other journeys continue.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Playwright execution | Custom test runner | `test_exec_playwright.py` + `test_orchestrator.run_spec_test()` | Already battle-tested, handles report parsing |
| State persistence format | Custom JSON/XML format | YAML (consistent with project) | Project uses YAML everywhere |
| Git SHA retrieval | GitPython library | subprocess `git rev-parse HEAD` | Avoids extra dependency; simple |
| State machine transitions | Custom enum/if-else | `job_state.py` patterns | Consistent with existing job state logic |

**Key insight:** Phase 17 already built the infrastructure. Phase 18 extends it rather than rebuilding.

---

## Runtime State Inventory

> Not a rename/refactor/migration phase - this is a new implementation. Skipping runtime state inventory.

Step 2.5: SKIPPED (not a rename/refactor/migration phase)

---

## Common Pitfalls

### Pitfall 1: Inconsistent run_id Format
**What goes wrong:** Different modules generate run_id with different formats, breaking resume functionality.
**Why it happens:** No central run_id generation; each module invents its own format.
**How to avoid:** Centralize run_id generation in a shared constant or function. Suggested format: `e2e.run-{timestamp}-{random_suffix}`.
**Warning signs:** Resume fails with "run_id not found" or mismatches between state.yaml and manifest.

### Pitfall 2: State File Missing on Resume
**What goes wrong:** `--resume` specified but `{run_id}-state.yaml` does not exist.
**Why it happens:** Resume specified for a fresh run (no previous state).
**How to avoid:** Validate state file exists before resume; fail fast with clear message.
**Warning signs:** `FileNotFoundError` during resume or "No state file found" errors.

### Pitfall 3: HAR Capture Without Page Context
**What goes wrong:** C_MISSING evidence collection tries to capture HAR without proper Playwright page context.
**Why it happens:** HAR capture requires page.route interception which needs active page context.
**How to avoid:** Ensure HAR capture happens within Playwright test execution context, not as a post-processing step.
**Warning signs:** Empty HAR files or "No active page context" errors.

### Pitfall 4: Missing accounts Field
**What goes wrong:** run-manifest.yaml generated without accounts field, violating EXEC-01.
**Why it happens:** accounts parameter not passed through the CLI chain.
**How to avoid:** Ensure `--accounts` parameter flows from CLI → test_orchestrator → run_manifest_gen.
**Warning signs:** Manifest files missing the `accounts` key.

### Pitfall 5: State File Overwrites on Resume
**What goes wrong:** Resume overwrites existing state.yaml instead of reading and continuing.
**Why it happens:** `_save_state()` called unconditionally after resume load.
**How to avoid:** Only save state after a step completes or fails, not at resume initialization.
**Warning signs:** State resets to SETUP on resume instead of continuing from last point.

---

## Code Examples

### run-manifest.yaml Structure
```yaml
# Source: based on ADR-054 §3 Phase 2 + CONTEXT.md D-01
run_id: e2e.run-20260424-A1B2C3D4
run_id_format: "e2e.run-{timestamp}-{random}"
created_at: "2026-04-24T10:30:00Z"
git_sha: "78e3b62d8f..."
frontend_build: "unknown"
backend_build: "unknown"
base_url:
  app: "http://localhost:3000"
  api: "http://localhost:8000"
browser: "chromium"
accounts:
  - "test-account-1@example.com"
artifact_version: "1.0"
```

### {run_id}-state.yaml Structure
```yaml
# Source: based on CONTEXT.md D-05, D-06
run_id: e2e.run-20260424-A1B2C3D4
current_state: "EXECUTE"
current_journey: "JOURNEY-MAIN-001"
current_step_index: 3
completed_steps:
  - journey_id: "JOURNEY-MAIN-001"
    step_index: 0
    step_name: "navigate_to_submit_page"
    status: "passed"
  - journey_id: "JOURNEY-MAIN-001"
    step_index: 1
    step_name: "fill_package_id"
    status: "passed"
  - journey_id: "JOURNEY-MAIN-001"
    step_index: 2
    step_name: "fill_proposal_ref"
    status: "passed"
  - journey_id: "JOURNEY-MAIN-001"
    step_index: 3
    step_name: "submit_form"
    status: "failed"
    error: "net::ERR_CONNECTION_REFUSED"
failed_journeys:
  - "JOURNEY-MAIN-001"
created_at: "2026-04-24T10:30:00Z"
updated_at: "2026-04-24T10:31:15Z"
```

### scenario-spec.yaml Structure (A/B/C Layers)
```yaml
# Source: based on ADR-054 §3 Phase 2
journey_id: "JOURNEY-MAIN-001"
spec_id: "e2e.journey.main.happy"
steps:
  - action: "goto"
    target: "/candidate-submit"
  - action: "fill"
    selector: "#package-id"
    value: "pkg-e2e-001"
  # ...

assertions:
  a_layer:
    - "Step 6: 显示 '提交成功' 提示"
    - "Step 7: 显示 handoff_id"
  b_layer:
    - "POST /api/v1/candidate-packages/submit called once"
    - "GET /api/v1/handoffs/{id} called after create"
  c_layer:
    - type: "C_MISSING"
      description: "reload_page_keeps_handoff_status == true"
      evidence_required:
        - "har"
        - "screenshot"
      placeholder: "C_MISSING: Business state verification pending"
    - type: "C_MISSING"
      description: "backend_handoff_exists_for_user == true"
      evidence_required:
        - "har"
        - "screenshot"
      placeholder: "C_MISSING: Business state verification pending"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No run-manifest | Append-only run-manifest per execution | Phase 18 | Full audit trail, debuggable failures |
| Single assertions layer | A/B/C layer separation | Phase 18 | Clearer test contract, C_MISSING for Phase 3 |
| In-memory state | Persisted `{run_id}-state.yaml` | Phase 18 | Resume support, failure recovery |
| 9-node state machine | Simplified 5-node model | Phase 18 | Faster implementation, Phase 3 complexity deferred |

**Deprecated/outdated:**
- Inline state in run-manifest: Now separate `{run_id}-state.yaml` per D-05
- Hardcoded manifest path: Now `ssot/tests/.artifacts/runs/{run_id}/` per D-01

---

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | run_id format `e2e.run-{timestamp}-{random}` is acceptable | run-manifest-gen | If user expects different format, code changes needed |
| A2 | `frontend_build` and `backend_build` can be "unknown" if no build artifacts exist | run-manifest-gen | If strict versioning required, CI pipeline needs to pass these |
| A3 | `--accounts` parameter will be added to CLI interface | run-manifest-gen | If accounts not in CLI, manifest will have empty accounts list |
| A4 | HAR capture uses Playwright's built-in `page.route` interception | C-layer evidence | If different HAR capture method preferred, implementation changes |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **run_id format for API chain vs E2E chain**
   - What we know: E2E suggestion is `e2e.run-{timestamp}-{random}`, API likely `api.run-{timestamp}-{random}`
   - What's unclear: Should format be chain-agnostic or chain-specific?
   - Recommendation: Use chain-agnostic `run-{timestamp}-{random}` in base, with chain prefix in subdirectory (e.g., `runs/e2e/run-xxx`, `runs/api/run-xxx`)

2. **accounts parameter sourcing**
   - What we know: EXEC-01 requires `accounts` field in run-manifest
   - What's unclear: Where do accounts come from — CLI parameter, config file, environment?
   - Recommendation: Add `--account` CLI parameter (repeatable), default to empty list

3. **C-layer evidence: HAR + screenshot timing**
   - What we know: Per D-04, C_MISSING collects HAR + screenshot
   - What's unclear: Is HAR capture per-step or per-journey? When is screenshot taken?
   - Recommendation: HAR capture per-journey (start → end), screenshot at step failure point

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All modules | ✓ | 3.11+ | — |
| pytest | TEST-02, TEST-03 | ✓ | 9.0.2 | — |
| PyYAML | YAML serialization | ✓ | latest | — |
| Node.js | Playwright | ✓ | 22.15.0 | — |
| npm | Playwright install | ✓ | 11.3.0 | — |
| @playwright/test | E2E execution | ✓ | ^1.58.2 | — |
| git | run_manifest_gen | ✓ | system git | subprocess fallback |

**Missing dependencies with no fallback:**
- None identified — all required tools are available.

**Missing dependencies with fallback:**
- GitPython library — use subprocess `git rev-parse HEAD` instead.

---

## Validation Architecture

> Per planning config, `workflow.nyquist_validation` is enabled. Include test framework mapping.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` (if exists) or `pyproject.toml` |
| Quick run command | `pytest tests/cli/lib/ -x -q` |
| Full suite command | `pytest tests/ -x -q --ignore=tests/e2e` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXEC-01 | run_manifest_gen generates unique manifest with all required fields | unit | `pytest tests/cli/lib/test_run_manifest_gen.py -x` | ❌ Wave 0 |
| EXEC-02 | scenario_spec_compile produces A/B/C layer assertions | unit | `pytest tests/cli/lib/test_scenario_spec_compile.py -x` | ❌ Wave 0 |
| EXEC-03 | state_machine_executor transitions correctly, persists state | unit | `pytest tests/cli/lib/test_state_machine_executor.py -x` | ❌ Wave 0 |
| TEST-02 | E2E chain test-run with app-url/api-url | integration | `pytest tests/integration/test_e2e_chain.py -x` | ❌ Wave 0 |
| TEST-03 | --resume re-runs failed cases | integration | `pytest tests/integration/test_resume.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/cli/lib/test_run_manifest_gen.py -x -q`
- **Per wave merge:** `pytest tests/cli/lib/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/cli/lib/test_run_manifest_gen.py` — covers EXEC-01
- [ ] `tests/cli/lib/test_scenario_spec_compile.py` — covers EXEC-02
- [ ] `tests/cli/lib/test_state_machine_executor.py` — covers EXEC-03
- [ ] `tests/integration/test_e2e_chain.py` — covers TEST-02
- [ ] `tests/integration/test_resume.py` — covers TEST-03
- [ ] `tests/conftest.py` — shared fixtures (if not already exists)

---

## Security Domain

> `security_enforcement` is enabled (absent = enabled). Include security considerations.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | No hardcoded credentials; accounts from CLI/env only |
| V5 Input Validation | yes | Validate run_id format, URL formats for --app-url/--api-url |
| V10 File Integrity | partial | Append-only artifacts; no deletion of run artifacts |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in run_id | Tampering | Validate run_id format; reject `../` patterns |
| Malformed YAML in state file | Denial | Wrap YAML load in try/except; validate structure on read |
| Empty accounts list (security gap) | Information Disclosure | Log warning if no accounts provided; require explicit flag |

---

## Sources

### Primary (HIGH confidence)
- `cli/lib/test_exec_runtime.py` — existing execution runtime patterns
- `cli/lib/execution_runner.py` — job state transitions
- `cli/lib/test_exec_playwright.py` — Playwright execution patterns
- `cli/lib/job_state.py` — state transition patterns
- `cli/lib/contracts.py` — StepResult dataclass
- `cli/lib/spec_adapter.py` — spec parsing foundation
- `cli/lib/environment_provision.py` — ENV file generation
- `cli/lib/test_orchestrator.py` — orchestrator integration

### Secondary (MEDIUM confidence)
- `ssot/adr/ADR-054-实施轴接入需求轴-双链桥接与执行闭环.md` — ADR design document
- `.planning/REQUIREMENTS.md` — requirements specification

### Tertiary (LOW confidence)
- `ssot/tests/.artifacts/evidence/e2e/run-*/` — existing evidence structure (sample only)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in existing codebase
- Architecture: HIGH — patterns derived from existing code with ADR-054 design
- Pitfalls: MEDIUM — identified through reasoning, not verified with implementation history

**Research date:** 2026-04-24
**Valid until:** 2026-05-24 (30 days for stable architecture; Phase 17 context is current)
