# Testing Patterns

**Analysis Date:** 2026-04-14

## Test Framework

**Runner:**
- `unittest` (Python standard library) -- all tests use `unittest.TestCase`
- `pytest` used as test runner via CI (invoked through `python -m pytest`)
- Config: `.pytest_cache/` present in `tests/unit/`; no `pytest.ini`, `pyproject.toml`, or `setup.cfg` with pytest config

**Assertion Library:**
- `unittest.TestCase` assertion methods: `assertEqual`, `assertTrue`, `assertFalse`, `assertIn`, `assertRaises`, `assertGreater`

**Run Commands:**
```bash
python -m pytest tests/unit/                          # Run all unit tests
python -m pytest tests/unit/test_cli_runner_monitor.py  # Run single test file
python -m tools.ci.run_checks run-test-manifest unit_fast --output-dir .artifacts/ci/unit-fast  # CI run
```

## Test File Organization

**Location:**
- Co-located test pattern: tests live in `tests/unit/` directory, separate from source
- Test support modules prefixed with underscore: `tests/unit/_test_exec_skill_support.py`
- Test support modules without `test_` prefix: `tests/unit/support_feat_to_testset.py`, `tests/unit/gate_human_orchestrator_test_support.py`
- Integration tests in `tests/integration/`: `tests/integration/test_product_review_phase1_alignment.py`
- Skill-local tests: `skills/ll-product-src-to-epic/tests/`, `skills/ll-product-raw-to-src/tests/`, etc.
- Golden fixtures in `tests/golden/`
- Test fixtures in `tests/fixtures/`
- Defect tracking in `tests/defect/failure-cases/`

**Naming:**
- Test files: `test_<module_under_test>.py` (e.g., `test_cli_runner_monitor.py`, `test_review_projection.py`)
- Skill integration tests: `test_lee_<skill_name>.py` (e.g., `test_lee_product_src_to_epic.py`, `test_lee_dev_tech_to_impl.py`)
- Test classes: `<ModuleUnderTest>Test` or `<Feature>Tests` (e.g., `CliRunnerMonitorTest`, `SrcToEpicWorkflowTests`)
- Test methods: `test_<description_in_snake_case>` (e.g., `test_show_status_aggregates_operator_facing_summary`)

**Structure:**
```
tests/
├── __init__.py
├── unit/                    # Unit tests (59+ files)
│   ├── __init__.py
│   ├── test_*.py           # Individual test modules
│   ├── support_*.py        # Shared test data/builders
│   └── *_test_support.py   # Test helper classes
├── integration/             # Integration tests
│   └── test_*.py
├── fixtures/                # Test fixture data
│   └── raw-to-src/
├── golden/                  # Golden file expectations
├── qa/                      # QA analysis and review artifacts
│   ├── analysis/
│   ├── review/
│   ├── strategy/
│   └── validation/
└── defect/                  # Recorded failure cases
    └── failure-cases/
```

## Test Structure

**Suite Organization:**
Standard `unittest.TestCase` pattern with setUp/tearDown:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli.ll import main


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CliRunnerMonitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tempdir.name)
        (self.workspace / "artifacts").mkdir()
        (self.workspace / "contracts" / "input").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_show_status_aggregates_operator_facing_summary(self) -> None:
        # ... arrange, act, assert
```

**Setup pattern:**
- `tempfile.TemporaryDirectory()` for isolated workspace
- Workspace directory structure created in `setUp()`
- Helper methods for test data creation: `write_json()`, `read_json()`, `build_request()`, `create_job()`

**Teardown pattern:**
- `self.tempdir.cleanup()` in `tearDown()`

**Assertion pattern:**
- Direct assertion on response payload fields
- JSON file existence checks via `path.exists()`
- Return code validation: `self.assertEqual(self.run_cli(...), 0)`
- Type assertions: `self.assertTrue(...)`, `self.assertFalse(...)`, `self.assertIn(...)`

## Mocking

**Framework:** `unittest.mock.patch`

**Patterns:**
```python
# Mocking a specific function
with patch(
    "cli.lib.execution_runner.invoke_target",
    return_value={"ok": True, "target_skill": "workflow.dev.feat_to_tech", "result": {"ok": True}},
):
    self.assertEqual(self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)), 0)
```

**What to Mock:**
- External skill invocations (`invoke_target`)
- Subprocess calls in CI checks

**What NOT to Mock:**
- Filesystem operations (tests use real temp directories)
- CLI entry point (`main()` called directly)
- Protocol handling (request/response lifecycle tested end-to-end)

## Fixtures and Factories

**Test Data:**
Tests create their own fixtures inline. Common patterns:

```python
# CLI request builder (from tests/unit/_test_exec_skill_support.py)
def build_request(self, command: str, payload: dict) -> dict:
    return {
        "api_version": "v1",
        "command": command,
        "request_id": f"req-{command.replace('.', '-')}",
        "workspace_root": self.workspace.as_posix(),
        "actor_ref": "test-suite",
        "trace": {"run_ref": "RUN-TEST-EXEC"},
        "payload": payload,
    }

# Job fixture (from tests/unit/test_cli_runner_monitor.py)
def create_job(self, *, status: str, name: str, target_skill: str, created_at: str, ...) -> str:
    directory = {
        "ready": "artifacts/jobs/ready",
        "claimed": "artifacts/jobs/running",
        "running": "artifacts/jobs/running",
        "done": "artifacts/jobs/done",
        "failed": "artifacts/jobs/failed",
        "waiting-human": "artifacts/jobs/waiting-human",
        "deadletter": "artifacts/jobs/deadletter",
    }[status]
    # ... write job JSON
```

**Location:**
- `tests/fixtures/raw-to-src/` -- raw-to-src sample data
- `tests/golden/` -- golden file expectations
- `tests/qa/` -- QA strategy, analysis, and review artifacts organized by test set

**Shared support modules:**
- `tests/unit/_test_exec_skill_support.py` -- `SkillRuntimeHarness` base class with comprehensive test utilities
- `tests/unit/support_feat_to_testset.py` -- test data builders for feat-to-testset skill
- `tests/unit/gate_human_orchestrator_test_support.py` -- gate orchestrator fixtures

## Coverage

**Requirements:** 80% minimum (per project coding rules); not enforced by tooling

**View Coverage:**
```bash
python -m pytest --cov=cli --cov-report=term-missing tests/unit/
```

**Coverage in CI:**
- CI installs `coverage` package but does not currently run coverage reporting
- Test execution goes through `run_test_manifest` in `tools/ci/tests.py`:
```python
def run_test_manifest(name: str, output_dir: Path) -> int:
    manifest = load_json(MANIFEST_DIR / "test_manifests.json")
    tests = manifest[name]
    exit_code, _ = run_pytest(tests, output_dir / f"{name}-pytest-report.json")
    return exit_code
```

**Test manifests** (`tools/ci/manifests/test_manifests.json`) define test groupings:
- `unit_fast`: runs entire `tests/unit/` directory
- `cli_tests`: specific CLI test files (8 files)
- `skill_test_map`: maps skill names to their test files

## Test Types

**Unit Tests:**
- Scope: individual CLI commands, library functions, protocol handling
- Location: `tests/unit/` (59+ test files)
- Approach: each test creates isolated temp workspace, invokes CLI via `main()`, asserts on JSON response files
- Pattern: arrange (create fixtures) -> act (run CLI command) -> assert (read response JSON, verify fields)

**Integration Tests:**
- Scope: cross-skill contract alignment, review phase consistency
- Location: `tests/integration/`
- Approach: dynamically loads skill modules via `importlib.util`, verifies contract alignment across skills
- Example: `tests/integration/test_product_review_phase1_alignment.py` verifies `review_phase1` contracts stay aligned across raw-to-src, src-to-epic, and epic-to-feat skills

**E2E Tests:**
- Playwright-based web E2E tests generated by `skill.qa.test_exec_web_e2e` skill
- Configurations stored in `.local/smoke/adr007-test-exec-web-playwright/artifacts/active/qa/executions/`
- Each E2E execution has its own `playwright.config.ts` and `tsconfig.json`
- Fake npm/playwright scripts used for test harness: `.local/smoke/adr007-test-exec-web-ui-flow-v5/tools/fake_playwright.py`

**Skill-Local Tests:**
- Individual skills have their own test directories:
  - `skills/ll-product-src-to-epic/tests/` -- `test_src_to_epic_semantic_lock.py`, `test_src_to_epic_review_phase1.py`
  - `skills/ll-product-raw-to-src/tests/` -- `test_raw_to_src_regressions.py`, `test_raw_to_src_bridge_regressions.py`
  - `skills/ll-product-epic-to-feat/tests/` -- `test_epic_to_feat_semantic_lock.py`
  - `skills/ll-dev-tech-to-impl/tests/` -- `test_tech_to_impl_surface_map.py`
  - `skills/ll-qa-impl-spec-test/tests/` -- `test_impl_spec_test_surface_map.py`

**CI Governance Tests:**
- `tools/ci/tests.py` -- test manifest runner
- `tools/ci/checks_code.py` -- code size governance with function-level metrics
- `tools/ci/checks_repo.py` -- repo hygiene and SSOT governance
- `tools/ci/checks_runtime.py` -- CLI surface snapshot, skill governance, cross-domain compatibility

## Common Patterns

**CLI Integration Testing:**
The dominant testing pattern invokes the full CLI stack:

```python
def run_cli(self, *argv: str) -> int:
    return main(list(argv))

def test_show_status_aggregates_operator_facing_summary(self) -> None:
    # Arrange: create job files in temp workspace
    self.create_job(status="ready", name="job-ready.json", target_skill="workflow.dev.feat_to_tech", ...)

    # Act: run CLI command
    request = self.build_request("loop.show-status", {})
    write_json(request_path, request)
    exit_code = self.run_cli("loop", "show-status", "--request", str(request_path), "--response-out", str(response_path))

    # Assert: read response JSON, verify fields
    self.assertEqual(exit_code, 0)
    payload = read_json(response_path)["data"]
    self.assertEqual(payload["counts"]["ready"], 1)
```

**Async Testing:**
- Not applicable; synchronous `unittest` throughout

**Error Testing:**
```python
def test_run_execution_rejects_non_integer_max_jobs(self) -> None:
    request = self.build_request("loop.run-execution", {"max_jobs": "oops"})
    write_json(request_path, request)

    self.assertEqual(
        self.run_cli("loop", "run-execution", "--request", str(request_path), "--response-out", str(response_path)),
        2,  # INVALID_REQUEST exit code
    )
    payload = read_json(response_path)
    self.assertEqual(payload["status_code"], "INVALID_REQUEST")
    self.assertEqual(payload["message"], "max_jobs must be an integer")
```

**Exception Testing:**
```python
def test_writeback_mapping_failure_and_missing_regeneration_input(self) -> None:
    with self.assertRaises(ProjectionWritebackError):
        writeback_projection_comment(self.workspace, projection["projection_ref"], "comment-unknown", ...)

    with self.assertRaises(ProjectionRegenerationError):
        request_projection_regeneration(self.workspace, comment["revision_request_ref"], "missing-updated-ssot.json")
```

**Subprocess Testing (workflow scripts):**
```python
class SrcToEpicWorkflowTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_standard_src_stays_single_epic_without_rollout_feat_track(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            input_dir = self.make_src_package(repo_root, "src-basic", candidate)
            result = self.run_cmd("run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "epic-basic")
            self.assertEqual(result.returncode, 0, result.stderr)
```

## CI Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):
- Triggers: `pull_request`, `push` to `main`/`master`/`codex/**`
- Python 3.13
- Parallel jobs:
  - `repo-hygiene` -- repository hygiene checks
  - `unit-fast` -- runs all `tests/unit/` via test manifest
  - `ssot-governance` -- SSOT object governance validation
  - `code-size-governance` -- file/function size limits (500 lines / 80 lines)
  - `skill-governance` -- skill contract validation + tests
  - `cli-governance` -- CLI surface validation + tests
  - `cross-domain-compat` -- cross-domain compatibility checks + tests

---

*Testing analysis: 2026-04-14*
