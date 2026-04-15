# Phase 5: spec-to-tests-evidence - Research

**Researched:** 2026-04-15
**Domain:** ADR-047 QA spec-driven test generation and execution (pytest + Playwright)
**Confidence:** HIGH

## Summary

Phase 5 delivers the two missing layers of ADR-047's five-layer skill architecture: the **generation layer** (spec-to-tests) and the **execution layer** (test execution with evidence collection). This closes the broken chain at ADR-047 Section 19 Connection 2: `spec -> generation -> execution -> evidence -> settlement`.

The generation skills (`ll-qa-api-spec-to-tests`, `ll-qa-e2e-spec-to-tests`) follow the Phase 2 Prompt-first pattern: LLM executor reads frozen spec YAML, generates test scripts (pytest for API, Playwright for E2E). The execution skills (`ll-qa-api-test-exec`, `ll-qa-e2e-test-exec`) are fundamentally different from Phase 2 skills -- they are **code-driven** (not Prompt-first), invoking real test runners (`pytest`, `npx playwright test`) and collecting structured evidence YAML per ADR-047 Section 6.3.

The existing `cli/lib/test_exec_runtime.py` and `cli/lib/test_exec_execution.py` provide the TESTSET-driven execution infrastructure that must be adapted for spec-driven execution. The `cli/lib/test_exec_playwright.py` module already contains Playwright project scaffolding and execution logic that can be reused for E2E execution.

**Primary recommendation:** Build 2 Prompt-first generation skills (Phase 2 pattern) + 2 code-driven execution skills (adapt existing `test_exec_*` runtime). Register all 4 in `_QA_SKILL_MAP` and `ll.py`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-GEN-01:** `ll-qa-api-spec-to-tests` input is frozen `api-test-spec` YAML (one or many), output is pytest test script files
- **D-GEN-02:** `ll-qa-e2e-spec-to-tests` input is frozen `e2e-journey-spec` YAML (one or many), output is Playwright test script files
- **D-EXEC-01:** `ll-qa-api-test-exec` executes generated pytest scripts, collects evidence YAML, backfills manifest `lifecycle_status` / `evidence_status` / `evidence_refs`
- **D-EXEC-02:** `ll-qa-e2e-test-exec` executes generated Playwright scripts, collects evidence YAML, backfills manifest `lifecycle_status` / `evidence_status` / `evidence_refs`
- **D-EVIDENCE-01:** Evidence files conform to ADR-047 Section 6.3 requirements (API: request/response snapshots, assertion results, side-effect assertions, execution log; E2E: browser trace, screenshot/video, network log, DOM assertion, persistence assertion, console error check)
- **D-CHAIN-01:** Full chain closure: `spec -> generation -> execution -> evidence -> settlement` (non-simulated for Phase 5)
- **D-CLI-01:** 4 new actions registered in `_QA_SKILL_MAP` and `cli/ll.py` skill subparser

### Claude's Discretion
- Prompt structure for generation skills (executor.md content)
- Evidence YAML schema details beyond ADR-047 Section 6.3 minimums
- How to adapt `test_exec_runtime.py` for spec-driven execution vs TESTSET-driven
- Output file naming conventions for generated test scripts
- Whether execution skills are Prompt-first or code-driven

### Deferred Ideas (OUT OF SCOPE)
- E2E chain full pilot (REQ-10 -- v2)
- Python production CLI runtime (REQ-20 -- v2)
- CI integration with release gate (REQ-21 -- v2)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.13.3 | Runtime for all CLI commands | [VERIFIED: `python --version` on target machine] |
| pytest | 9.0.2 | API test execution framework | [VERIFIED: `pip show pytest` on target machine] -- already installed, project standard |
| PyYAML | system | YAML parsing for spec reading, evidence writing | [VERIFIED: `cli/lib/qa_schemas.py` uses `import yaml`] |
| @playwright/test | ^1.58.2 | E2E test execution framework | [VERIFIED: `cli/lib/test_exec_playwright.py` line 34 renders `package.json` with `^1.58.2`] -- NOT currently installed on target machine |
| coverage | system | Code coverage collection during test execution | [VERIFIED: `cli/lib/test_exec_reporting.py` line 11 `from coverage import Coverage`] |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| `cli/lib/qa_schemas.py` | Schema validation for spec/evidence | Every skill output validation |
| `cli/lib/qa_skill_runtime.py` | Shared QA skill runtime (`run_skill()`) | All Prompt-first QA skill invocations |
| `cli/lib/test_exec_runtime.py` | Governed test execution carrier | Adapting for spec-driven execution |
| `cli/lib/test_exec_execution.py` | Narrow execution loop, case execution | Reusing `execute_cases()`, `run_narrow_execution()` patterns |
| `cli/lib/test_exec_playwright.py` | Playwright project scaffolding + execution | E2E script execution (already generates `playwright.config.ts`, installs deps, runs tests, parses `results.json`) |
| `cli/lib/test_exec_reporting.py` | Evidence compliance, case judgment, coverage collection | Evidence validation and reporting for both API and E2E |
| `cli/commands/skill/command.py` | `_QA_SKILL_MAP` dispatch | Register 4 new actions |

### Installation
```bash
# Playwright is NOT installed on target machine -- must be installed during E2E execution
npm install @playwright/test@^1.58.2  # or let test_exec_playwright.py handle via ensure_playwright_project()
npx playwright install chromium       # browser binary installation
```

**Version verification:**
- Python 3.13.3 -- [VERIFIED: `python --version`]
- pytest 9.0.2 -- [VERIFIED: `pip show pytest`]
- @playwright/test -- NOT installed, but `test_exec_playwright.py` handles installation at runtime via `ensure_playwright_project()` which runs `npm install`
- coverage -- present (imported by `test_exec_reporting.py`)

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest for API | unittest (stdlib) | pytest has better fixtures, parametrize, plugins -- already project standard |
| Playwright for E2E | Cypress | Playwright already integrated in `test_exec_playwright.py` -- switching would require new infrastructure |
| LLM-based generation | Template-based codegen (Jinja2) | LLM handles complex spec-to-script translation (assertions, edge cases) better; template would miss spec nuance |

## Architecture Patterns

### Recommended Skill Directory Structure

Each of the 4 new skills follows the Phase 2 skeleton pattern:

```
skills/ll-qa-api-spec-to-tests/
├── SKILL.md                           # Skill description + deprecation notice
├── ll.lifecycle.yaml                  # Lifecycle states: draft -> validated -> executed -> frozen
├── ll.contract.yaml                   # Skill metadata (adr, category, chain, phase)
├── input/
│   ├── contract.yaml                  # Input contract: spec YAML path, optional output dir
│   └── semantic-checklist.md          # What to check about input
├── output/
│   ├── contract.yaml                  # Output contract: generated .py test files
│   └── semantic-checklist.md          # What to validate about output
├── agents/
│   ├── executor.md                    # LLM prompt: read spec, generate pytest script
│   └── supervisor.md                  # Validation checklist for generated scripts
├── scripts/
│   ├── run.sh                         # Entry point wrapper
│   ├── validate_input.sh              # Validate spec YAML exists and passes schema
│   └── validate_output.sh             # Validate generated .py files exist
└── evidence/
    ├── execution-evidence.schema.json # Schema for skill's own evidence
    └── supervision-evidence.schema.json

skills/ll-qa-api-test-exec/
├── SKILL.md
├── ll.lifecycle.yaml
├── ll.contract.yaml
├── input/
│   ├── contract.yaml                  # Input: generated test file paths, optional base_url
│   └── semantic-checklist.md
├── output/
│   ├── contract.yaml                  # Output: evidence YAML paths, manifest update
│   └── semantic-checklist.md
├── agents/
│   ├── executor.md                    # LLM prompt (minimal -- execution is code-driven)
│   └── supervisor.md                  # Post-execution validation checklist
├── scripts/
│   ├── run.sh                         # Entry point: invoke pytest, collect evidence
│   ├── validate_input.sh              # Validate test files exist
│   └── validate_output.sh             # Validate evidence YAML files exist and conform
└── evidence/
    ├── execution-evidence.schema.json
    └── supervision-evidence.schema.json
```

Same structure for `ll-qa-e2e-spec-to-tests` and `ll-qa-e2e-test-exec`.

### Pattern 1: Prompt-first Generation (API Spec-to-Tests)

**What:** LLM reads frozen `api-test-spec` YAML, generates pytest test script with proper fixtures, assertions, and evidence collection hooks.

**When to use:** For both generation skills (`ll-qa-api-spec-to-tests`, `ll-qa-e2e-spec-to-tests`).

**Input contract (verified from `ssot/schemas/qa/spec.yaml`):**
```yaml
api_test_spec:
  case_id: string           # e.g., api_case.plan.create.invalid-date-range
  coverage_id: string       # links to manifest
  endpoint: string          # HTTP method + path
  capability: string
  preconditions: [string]
  request:
    method: string | null
    path_params: object | null
    query_params: object | null
    headers: object | null
    body: object | null
  expected:
    status_code: integer
    response_assertions: [string]
    side_effect_assertions: [string]
    response_schema: object | null
  cleanup: [string]
  evidence_required: [string]  # e.g., request_snapshot, response_snapshot, db_assertion_result
```

**Generated output pattern (pytest):**
```python
# Source: derived from ADR-047 Section 4.1.5 C spec schema
import pytest
import yaml
from pathlib import Path

EVIDENCE_DIR = Path("ssot/tests/.artifacts/evidence")

class TestAPICase:
    """Test: {case_id} | Coverage: {coverage_id}"""

    def test_{capability}_{scenario}(self, api_client):
        """Execute spec contract for {case_id}"""
        # 1. Setup preconditions
        # ...

        # 2. Build request from spec
        request_data = {body_from_spec}

        # 3. Execute and collect request snapshot
        request_snapshot = {"method": "POST", "url": endpoint, "body": request_data}

        # 4. Assert response
        response = api_client.post(endpoint, json=request_data)
        assert response.status_code == {status_code}

        # 5. Verify assertions from spec
        for assertion in spec.expected.response_assertions:
            # ... evaluate assertion expression

        # 6. Collect evidence
        evidence = {
            "evidence_record": {
                "case_id": "{case_id}",
                "coverage_id": "{coverage_id}",
                "executed_at": "<timestamp>",
                "run_id": "<run_id>",
                "evidence": {
                    "request_snapshot": request_snapshot,
                    "response_snapshot": {"status_code": response.status_code, "body": response.json()},
                    "assertion_results": [...]
                },
                "side_effects": [...],
                "execution_status": "success"
            }
        }
        evidence_file = EVIDENCE_DIR / "{coverage_id}.evidence.yaml"
        evidence_file.parent.mkdir(parents=True, exist_ok=True)
        evidence_file.write_text(yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True))
```

### Pattern 2: Code-driven Execution (API Test Exec)

**What:** Execute pytest scripts programmatically, parse results, collect evidence YAML, update manifest. This is NOT Prompt-first -- it uses Python subprocess to run pytest and collects structured output.

**When to use:** For both execution skills (`ll-qa-api-test-exec`, `ll-qa-e2e-test-exec`).

**Execution flow (adapted from `test_exec_execution.py`):**
```
1. Load spec YAML(s) from input path
2. Discover generated test files (or use explicit test_paths from payload)
3. Run pytest with --json or --junitxml output
4. Parse test results (pass/fail/error per case)
5. For each test case:
   a. Read evidence YAML produced by the test itself (during execution)
   b. Validate evidence contains all items from spec.evidence_required
   c. Update manifest item: lifecycle_status, evidence_status, evidence_refs
6. Write execution summary JSON
```

**Key insight:** The generated test scripts (from Pattern 1) are responsible for writing their own evidence YAML during pytest execution. The execution skill's job is to:
1. Run pytest
2. Verify evidence files were created
3. Validate evidence completeness (all `evidence_required` items present)
4. Update the coverage manifest
5. Return evidence refs for downstream settlement

### Pattern 3: Manifest Backfill Pattern

**What:** After execution, update the coverage manifest with execution results.

**Verified from ADR-047 Section 15 (Manifest State Machine):**
```yaml
# Before execution:
lifecycle_status: generated    # or executable
mapping_status: mapped
evidence_status: missing
waiver_status: none

# After passed execution:
lifecycle_status: passed
mapping_status: mapped
evidence_status: complete
waiver_status: none
evidence_refs:
  - ssot/tests/.artifacts/evidence/{coverage_id}.evidence.yaml
rerun_count: 0
last_run_id: run-{timestamp}-{pid}

# After failed execution:
lifecycle_status: failed
mapping_status: mapped
evidence_status: complete
waiver_status: none
evidence_refs:
  - ssot/tests/.artifacts/evidence/{coverage_id}.evidence.yaml
```

### Anti-Patterns to Avoid
- **Hand-rolling pytest assertion parsing:** Use `pytest-json-report` or `--junitxml` to parse results programmatically. Do not regex-parse pytest stdout.
- **Mutating spec files during execution:** Specs are frozen contracts. Execution reads specs, never modifies them. Only manifest and evidence are written during execution.
- **Narrative evidence files:** Evidence must be structured YAML conforming to ADR-047 Section 6.3, not markdown reports.
- **Skipping evidence validation:** Every evidence file must be checked against the `evidence_required` list in the spec before marking `evidence_status: complete`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test execution | Custom subprocess orchestration | `pytest.main()` or `subprocess.run(["pytest", ...])` + `--junitxml` | pytest handles fixtures, parametrization, teardown, reporting |
| Playwright project setup | Manual Playwright config writing | `cli/lib/test_exec_playwright.py` (already renders `playwright.config.ts`, `package.json`, `tsconfig.json`, test spec) | Battle-tested in existing codebase, handles browser detection, timeout config, reporter setup |
| Schema validation | Custom YAML validators | `cli/lib/qa_schemas.py validate_file()` | Already implements all 5 schema types with enum checks |
| Evidence YAML structure | Ad-hoc dict serialization | Follow Phase 4 evidence pattern (`evidence_record` root key) | Existing settlement skill consumes this format |
| Coverage manifest update | Manual YAML editing | Read-manifest -> update items -> write-manifest (atomic) | Prevents partial updates, maintains state machine integrity |
| Playwright result parsing | Custom stdout regex parsing | `cli/lib/test_exec_playwright.py.parse_playwright_report()` (reads `results.json`) | Already parses Playwright JSON report, extracts case IDs, status, errors |

**Key insight:** The project already has ~14 `test_exec_*.py` modules in `cli/lib/`. The execution skills should reuse these rather than building new execution infrastructure. The main adaptation needed is changing the input from TESTSET-driven to spec-driven.

## Runtime State Inventory

N/A -- This is not a rename/refactor/migration phase. No existing runtime state needs updating.

**Note on existing execution infrastructure:**
- `cli/lib/test_exec_runtime.py` -- Currently handles `test-exec-cli` and `test-exec-web-e2e` actions. These are marked as superseded by ADR-047 spec-driven execution. The new execution skills will either adapt this runtime or create a new spec-driven execution path.
- `cli/lib/test_exec_execution.py` -- Contains `run_narrow_execution()`, `execute_case()`, `execute_cases()`. These are TESTSET-driven and expect `TestCasePack`/`ScriptPack` payloads. The spec-driven execution skills will need a different entry point that starts from spec YAML instead.
- `ssot/tests/.artifacts/evidence/` -- Contains 8 evidence YAML files from Phase 4 pilot (simulated execution). These serve as the evidence format reference.

## Common Pitfalls

### Pitfall 1: Execution Skills Need Runtime Infrastructure (Not Just Prompts)
**What goes wrong:** Following the Phase 2 Prompt-first pattern for execution skills would leave no actual test execution happening. The LLM prompt writes the prompt file and returns without running tests.
**Why it happens:** `qa_skill_runtime.py._run_llm_executor()` only writes the prompt to a temp file (verified from Phase 4 research, Pitfall #5). It does NOT invoke Claude subprocess.
**How to avoid:** Execution skills must have **code-driven** `run.sh` scripts that actually invoke `pytest` or `npx playwright test`. The `agents/executor.md` for execution skills should be minimal (supervisory role only), not the primary execution mechanism.
**Warning signs:** `run.sh` calls `python -m cli skill <action>` which writes `_executor_prompt.md` and returns without executing any tests.

### Pitfall 2: Playwright Not Installed on Target Machine
**What goes wrong:** E2E execution skills will fail because `@playwright/test` npm package and browser binaries are not installed.
**Why it happens:** Verified via `npm list @playwright/test` -- empty. The existing `test_exec_playwright.py` handles installation via `ensure_playwright_project()` which runs `npm install`, but `npx playwright install chromium` is needed for browser binaries.
**How to avoid:** The E2E execution skill's `run.sh` must ensure Playwright is installed before running tests. Reuse `ensure_playwright_project()` from `test_exec_playwright.py` which already handles `npm install`. Browser installation (`npx playwright install`) must be added.
**Warning signs:** `Error: browserType.launch: Executable doesn't exist at ...`

### Pitfall 3: Evidence File Naming Collision
**What goes wrong:** Multiple test runs produce evidence files with the same name (`{coverage_id}.evidence.yaml`), overwriting previous evidence.
**Why it happens:** Phase 4 evidence files are named `{coverage_id}.evidence.yaml` (verified from `ssot/tests/.artifacts/evidence/`). No run_id or timestamp in the filename.
**How to avoid:** Either (a) include run_id in filename: `{coverage_id}.{run_id}.evidence.yaml`, or (b) write to run-scoped directories: `ssot/tests/.artifacts/evidence/{run_id}/{coverage_id}.evidence.yaml`. Recommendation: use run-scoped directories to keep evidence grouped by execution run.
**Warning signs:** Evidence file timestamps don't match current run, evidence shows stale data.

### Pitfall 4: Generated Test Scripts May Not Write Evidence
**What goes wrong:** LLM-generated test scripts may not include the evidence-writing code, resulting in missing evidence files after execution.
**Why it happens:** The executor prompt (`agents/executor.md`) must explicitly instruct the LLM to write evidence YAML during test execution. If the prompt only says "generate a pytest script", the LLM may produce a script that asserts but doesn't collect evidence.
**How to avoid:** The generation skill's executor prompt must include:
1. A template showing the evidence-writing pattern
2. A supervisor checklist item: "Generated script writes evidence YAML for every `evidence_required` item"
3. The execution skill must verify evidence file existence after pytest completes
**Warning signs:** pytest passes but no evidence files exist in `ssot/tests/.artifacts/evidence/`.

### Pitfall 5: Manifest Update Must Be Atomic
**What goes wrong:** Partial manifest updates (some items updated, others not) leave the manifest in an inconsistent state.
**Why it happens:** If execution fails midway through updating manifest items, some items show `lifecycle_status: passed` while others still show `lifecycle_status: generated`.
**How to avoid:** Read the full manifest, update all items in memory, then write back atomically. If any step fails, do not write the manifest. Use a temp file + rename pattern.
**Warning signs:** Manifest items have mixed lifecycle statuses that don't match the execution run's actual results.

### Pitfall 6: E2E Spec Format Differs from API Spec Format
**What goes wrong:** The E2E generation skill expects `e2e_journey_spec` top-level key but receives `api_test_spec` format.
**Why it happens:** The project only has `ssot/schemas/qa/spec.yaml` which defines `api_test_spec`. There is no `e2e_journey_spec` schema file yet. ADR-047 Section 4.2.5 C defines the E2E spec structure in prose but not as a schema file.
**How to avoid:** Phase 5 should either (a) extend `ssot/schemas/qa/spec.yaml` to include both API and E2E spec schemas, or (b) create a new `ssot/schemas/qa/e2e_spec.yaml`. The `qa_schemas.py` validator needs a new `validate_e2e_spec()` function and a new entry in `_VALIDATORS`. This is a prerequisite for the E2E generation skill.

## Code Examples

### CLI Registration Pattern (verified from `cli/commands/skill/command.py`)

The `_QA_SKILL_MAP` must be extended with 4 new entries:
```python
_QA_SKILL_MAP = {
    # ... existing 9 entries ...
    "api-spec-to-tests": ("ll-qa-api-spec-to-tests", "qa_skill_runtime"),
    "e2e-spec-to-tests": ("ll-qa-e2e-spec-to-tests", "qa_skill_runtime"),
    "api-test-exec": ("ll-qa-api-test-exec", "api_test_exec"),
    "e2e-test-exec": ("ll-qa-e2e-test-exec", "e2e_test_exec"),
}
```

The `ll.py` skill subparser must be extended (verified from `cli/ll.py` line 81):
```python
for action in (
    # ... existing 16 actions ...
    "api-spec-to-tests",
    "e2e-spec-to-tests",
    "api-test-exec",
    "e2e-test-exec",
):
    _add_action_parser(skill_sub, action)
```

### Evidence YAML Format (verified from Phase 4 pilot evidence files)

API evidence (from `ssot/tests/.artifacts/evidence/api.training_plan.create.happy.evidence.yaml`):
```yaml
evidence_record:
  case_id: "api_case.plan.create.happy"
  coverage_id: "api.training_plan.create.happy"
  executed_at: "2026-04-15T12:05:00Z"
  run_id: "run-pilot-001"
  evidence:
    request_snapshot:
      method: "POST"
      url: "/api/v1/training-plans"
      body: { ... }
    response_snapshot:
      status_code: 201
      body: { ... }
    assertion_results:
      - assertion: "response.id is not null"
        result: "pass"
  side_effects: []
  execution_status: "simulated"
```

E2E evidence (ADR-047 Section 6.3 minimum, not yet implemented):
```yaml
evidence_record:
  case_id: "e2e_case.onboarding.create-plan.main"
  coverage_id: "e2e.onboarding.create-plan.main"
  executed_at: "2026-04-15T12:05:00Z"
  run_id: "run-001"
  evidence:
    browser_trace: "artifacts/tests/e2e/evidence/{run_id}/trace.zip"
    screenshot_final: "artifacts/tests/e2e/evidence/{run_id}/final.png"
    network_log: "artifacts/tests/e2e/evidence/{run_id}/network.json"
    dom_assertions:
      - selector: "h1"
        expected: "Training Plan"
        result: "pass"
    persistence_assertion:
      - check: "reload_page_keeps_generated_plan"
        result: "pass"
    console_errors: []
  execution_status: "success"
```

### run.sh Pattern for Execution Skill (code-driven, not Prompt-first)

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_PATH=""
TEST_DIR=""
OUTPUT_DIR=""
WORKSPACE="${PWD}"
RUN_ID="run-$(date +%s)-$$"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --spec-path) SPEC_PATH="$2"; shift 2;;
    --test-dir) TEST_DIR="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) shift;;
  esac
done

if [[ -z "${SPEC_PATH}" ]]; then echo "Error: --spec-path required"; exit 1; fi
bash "${SCRIPT_DIR}/validate_input.sh" "${SPEC_PATH}"

EVIDENCE_DIR="${OUTPUT_DIR:-${WORKSPACE}/.artifacts/tests/api/evidence/${RUN_ID}}"
mkdir -p "${EVIDENCE_DIR}"

# Run pytest (API execution)
pytest "${TEST_DIR}" \
  --junitxml="${EVIDENCE_DIR}/results.xml" \
  --json-report --json-report-file="${EVIDENCE_DIR}/results.json" \
  --tb=short \
  --evidence-dir="${EVIDENCE_DIR}" \
  || true  # Don't fail the script on test failures -- we report them

# Validate evidence files exist
bash "${SCRIPT_DIR}/validate_output.sh" "${EVIDENCE_DIR}"

# Update manifest
python -c "
import sys; sys.path.insert(0, '${WORKSPACE}/cli/lib')
from qa_schemas import validate_file
# ... manifest backfill logic
"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TESTSET-driven execution | Spec-driven execution (ADR-047 Section 6.4) | ADR-047 v1.4 (2026-04-10) | Execution skills read `api-test-spec`/`e2e-journey-spec`, not TESTSET |
| ll-test-exec-cli / ll-test-exec-web-e2e | New `ll-qa-api-test-exec` / `ll-qa-e2e-test-exec` | Phase 3 (2026-04-15) | Old skills marked DEPRECATED; new skills are spec-driven |
| Narrative test reports | Structured evidence YAML | ADR-047 Section 6.3 | Evidence must be machine-readable, not prose |
| Free-form test generation | Spec-driven generation | ADR-047 Section 3.8 Step 2 | Generation consumes frozen spec, not prose docs |
| Single `status` field | Layered status (`lifecycle_status`/`mapping_status`/`evidence_status`/`waiver_status`) | ADR-047 v1.2 | Manifest updates must set all 4 fields correctly |

**Deprecated/outdated:**
- `ll-test-exec-cli` -- marked DEPRECATED in Phase 3, superseded by spec-driven execution
- `ll-test-exec-web-e2e` -- marked DEPRECATED in Phase 3, superseded by spec-driven execution
- TESTSET-driven execution flow (`test_exec_runtime.py` current behavior) -- must be adapted for spec-driven

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Execution skills should be code-driven (not Prompt-first), because `_run_llm_executor()` does not actually invoke tests | Pattern 2, Pitfall #1 | HIGH -- If execution skills are Prompt-first, no real tests will run |
| A2 | `ssot/schemas/qa/spec.yaml` only defines `api_test_spec` -- no E2E spec schema exists yet | Pitfall #6 | MEDIUM -- E2E generation skill needs a schema to validate against |
| A3 | Generated test scripts should write their own evidence YAML during pytest execution | Pattern 2 | MEDIUM -- Alternative: execution skill collects evidence post-hoc from pytest output |
| A4 | `pytest-json-report` plugin or `--junitxml` is available for programmatic result parsing | Code-driven Execution | LOW -- If not available, must install as additional dependency |
| A5 | The `test_exec_playwright.py` module can be reused for E2E execution with minimal adaptation | Supporting table | LOW -- If the module is tightly coupled to TESTSET format, significant refactoring needed |
| A6 | No API backend exists for real API test execution (from Phase 4 research) | Summary | HIGH -- If a backend exists, Phase 5 should connect to it; otherwise execution remains simulated or uses mocks |

## Open Questions

1. **E2E spec schema missing**: <!-- RESOLVED by Plan 05-01 Task 1: Extended spec.yaml with e2e_journey_spec schema; Plan 05-01 Task 2: Added validate_e2e_spec() to qa_schemas.py --> The project has `ssot/schemas/qa/spec.yaml` for API test specs but no schema file for `e2e_journey_spec`. ADR-047 Section 4.2.5 C defines the structure in prose.
   - What we know: ADR-047 defines `e2e_journey_spec` fields (case_id, coverage_id, journey_id, entry_point, preconditions, user_steps, expected_ui_states, expected_network_events, expected_persistence, anti_false_pass_checks, evidence_required).
   - **Resolution**: Plan 05-01 Task 1 extends spec.yaml with e2e_journey_spec schema; Plan 05-01 Task 2 adds validate_e2e_spec() dataclass and validator to qa_schemas.py.

2. **Evidence schema needs formalization**: <!-- RESOLVED by Plan 05-01 Task 2: Created ssot/schemas/qa/evidence.yaml and added validate_evidence() to qa_schemas.py --> Phase 4 evidence files use an ad-hoc `evidence_record` format. ADR-047 Section 6.3 defines minimum fields but no formal schema.
   - What we know: 8 evidence YAML files exist in `ssot/tests/.artifacts/evidence/` from Phase 4 pilot, all with `evidence_record` root key.
   - **Resolution**: Plan 05-01 Task 2 creates ssot/schemas/qa/evidence.yaml with evidence_record schema; adds EvidenceRecord dataclass and validate_evidence() function to qa_schemas.py.

3. **Manifest backfill: which Python module owns it?** <!-- RESOLVED by Plan 05-01 Task 3: Created cli/lib/qa_manifest_backfill.py with backfill_manifest() -->
   - What we know: No existing module updates the manifest after execution. Phase 4 manually updated manifest states.
   - **Resolution**: Plan 05-01 Task 3 creates dedicated cli/lib/qa_manifest_backfill.py with backfill_manifest() function that atomically updates manifest items. Execution skills (05-03, 05-05) call this module.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13.3 | All CLI commands, schema validation, execution skills | Yes | 3.13.3 | -- |
| pytest | API test execution (`ll-qa-api-test-exec`) | Yes | 9.0.2 | -- |
| PyYAML | YAML parsing for all skills | Yes | system | -- |
| @playwright/test | E2E test execution (`ll-qa-e2e-test-exec`) | No | -- | `npm install` at runtime (handled by `test_exec_playwright.py`) |
| Playwright browser binaries | E2E test execution | No | -- | `npx playwright install chromium` at runtime |
| pytest-json-report | Programmatic pytest result parsing | Unknown | -- | Use `--junitxml` (stdlib) as fallback |
| coverage | Coverage collection during execution | Yes (importable) | system | -- |

**Missing dependencies with fallback:**
- @playwright/test -- not installed, but `test_exec_playwright.py` has `ensure_playwright_project()` that runs `npm install`. Browser binaries need `npx playwright install` added.
- pytest-json-report -- status unknown. If not installed, use `--junitxml` output which pytest includes by default.

## Validation Architecture

> Skipped: `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Test execution does not handle auth directly |
| V3 Session Management | No | No session handling in test execution |
| V4 Access Control | No | Test execution is local, no access control |
| V5 Input Validation | Yes | `qa_schemas.py` validators + `validate_input.sh` scripts for spec validation |
| V6 Cryptography | No | No cryptographic operations in generation/execution |

### Known Threat Patterns for Test Execution

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Test script injection (malicious generated code) | Tampering | Generated scripts are from trusted LLM prompts with spec-bounded input; supervisor validates output structure |
| Evidence fabrication | Repudiation | Execution skill validates evidence file existence and completeness against spec.evidence_required |
| Manifest state manipulation | Tampering | Atomic manifest updates; settlement statistics self-consistency check (Phase 3) |
| Command injection via spec body | Injection | Spec YAML values are data, not executable code; pytest treats them as test parameters |

## Sources

### Primary (HIGH confidence)
- Codebase files read directly:
  - `cli/lib/qa_schemas.py` -- all 5 schema validators (plan/manifest/spec/settlement/gate)
  - `cli/lib/qa_skill_runtime.py` -- Prompt-first skill runtime
  - `cli/lib/test_exec_runtime.py` -- governed test execution carrier
  - `cli/lib/test_exec_execution.py` -- narrow execution loop (641 lines)
  - `cli/lib/test_exec_playwright.py` -- Playwright scaffolding and execution (443 lines)
  - `cli/lib/test_exec_reporting.py` -- reporting and validation (460 lines)
  - `cli/commands/skill/command.py` -- `_QA_SKILL_MAP` dispatch
  - `cli/ll.py` -- CLI subparser definition
  - `cli/lib/skill_runtime_paths.py` -- skill directory resolution
  - `ssot/schemas/qa/spec.yaml` -- API test spec schema
  - `ssot/schemas/qa/manifest.yaml` -- coverage manifest schema
  - `ssot/schemas/qa/settlement.yaml` -- settlement report schema
  - `ssot/schemas/qa/plan.yaml` -- API test plan schema
  - `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` -- full ADR (1599 lines)
  - `ssot/tests/.artifacts/evidence/*.yaml` -- 8 Phase 4 pilot evidence files
  - Phase 2 skills: `ll-qa-api-spec-gen/`, `ll-qa-e2e-spec-gen/` (directory structure, executor prompts)
  - Phase 4 research: `.planning/phases/04-api/04-RESEARCH.md`

### Secondary (MEDIUM confidence)
- ADR-047 section references for generation layer (Section 11.1), execution layer (Section 6.4), evidence requirements (Section 6.3), manifest state machine (Section 15)
- `test_exec_playwright.py` Playwright version `^1.58.2` (rendered in `render_package_json()`)

### Tertiary (LOW confidence)
- A6: No API backend exists (from Phase 4 research, not independently verified in this session)
- A4: `pytest-json-report` plugin availability (not checked via `pip list`)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified from codebase or target machine
- Architecture: HIGH -- skill directories, CLI protocol, execution runtime verified from source
- Pitfalls: MEDIUM -- identified from code analysis, not runtime-tested
- Evidence format: HIGH -- 8 Phase 4 evidence files read directly

**Research date:** 2026-04-15
**Valid until:** 2026-05-15 (stable domain, no fast-moving dependencies)
