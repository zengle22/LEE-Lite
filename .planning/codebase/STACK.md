# Technology Stack

**Analysis Date:** 2026-04-14

## Languages

**Primary:**
- Python 3.13 - Core CLI runtime, skill scripts, CI tooling, and test infrastructure. Target version confirmed in `.github/workflows/ci.yml` (`python-version: "3.13"`). Pycache bytecode confirms CPython 3.13 runtime (`__pycache__/*.cpython-313.pyc`).

**Secondary:**
- TypeScript 5.x - Used only within dynamically generated Playwright test projects for E2E test execution (`cli/lib/test_exec_playwright.py` renders `package.json` with `"typescript": "^5.0.0"`).
- YAML - Configuration and contract definition format used throughout SSOT objects, skill contracts, and CI manifests.
- Markdown - Primary documentation format for ADRs, skills, specifications, and governance artifacts.

## Runtime

**Environment:**
- CPython 3.13

**Package Manager:**
- pip (used directly in CI: `python -m pip install --upgrade pip pytest pyyaml coverage`)
- npm (used for Playwright E2E test project scaffolding via `npm install --no-fund --no-audit`)
- No lockfile for Python dependencies (no `requirements.txt`, `pyproject.toml`, `Pipfile`, `poetry.lock`, or `uv.lock` detected)
- Node.js lockfile: `package-lock.json` present but tracked in `.gitignore`

## Frameworks

**Core:**
- `argparse` (stdlib) - CLI command parsing and subcommand routing (`cli/ll.py`)
- No web framework (this is a CLI-first file-based runtime, not a web application)

**Testing:**
- pytest - Unit and integration test runner (`tools/ci/common.py` invokes `python -m pytest`)
- unittest (stdlib) - Some test support files use `unittest.TestCase` as base class
- Playwright - E2E browser test execution (`cli/lib/test_exec_playwright.py`, `skills/ll-test-exec-web-e2e/`)

**Build/Dev:**
- GitHub Actions - CI pipeline (`.github/workflows/ci.yml`)
- No dedicated linter/formatter configuration detected (no `.pre-commit-config`, `ruff.toml`, `pyproject.toml`, or `pyrightconfig.json`)

## Key Dependencies

**Critical:**
- `pyyaml` - YAML parsing for SSOT objects, skill contracts, CI manifests, and configuration files. Imported in `tools/ci/common.py` and test files.
- `coverage` - Test coverage reporting (installed in CI, used for test manifest execution)
- `pytest` - Test runner for all test suites (unit, integration, skill-governance)

**Infrastructure:**
- `@playwright/test` ^1.58.2 - E2E test execution framework, dynamically scaffolded at runtime (`cli/lib/test_exec_playwright.py` renders a temporary Playwright project)
- `playwright` ^1.58.2 - Root `package.json` dependency for Playwright browser automation

**Standard Library Heavy Usage:**
- `pathlib` - File path operations throughout all modules
- `subprocess` - External process invocation (git commands, skill scripts, Playwright, npm)
- `json` - JSON serialization/deserialization for artifacts, job records, registry entries
- `dataclasses` - Data structures (`@dataclass` for `CommandError`, `Violation`, job state records)
- `typing` - Type annotations across all modules (`from __future__ import annotations` pattern)
- `ast` - Python AST parsing for CI code size governance checks (`tools/ci/common.py`)

## Configuration

**Environment:**
- `.env.example` present with three variables: `LL_RUNTIME_HOME`, `LL_CACHE_HOME`, `LL_SESSION_HOME`
- `.env` gitignored - environment configuration loaded at runtime, not committed
- `.lee/config.yaml` - LEE executor configuration (`default_type: claude_code`, project name, spec root)
- `.lee/repos.yaml` - Repository metadata (git repo URL: `https://github.com/zengle22/LEE-Lite.git`)
- `openspec/config.yaml` - Spec-driven schema configuration

**Build:**
- `.github/workflows/ci.yml` - GitHub Actions CI with 6 parallel jobs
- `.editorconfig` - Editor configuration (UTF-8, LF, 2-space indent)
- `Makefile` - Minimal skeleton (only `tree` target)
- `tools/ci/run_checks.py` - Custom CI check runner with 7 check types:
  - `repo-hygiene` - Repository structure validation
  - `ssot-governance` - SSOT object registry compliance
  - `code-size-governance` - Code size and function length limits
  - `skill-governance` - Skill file structure and contract compliance
  - `cli-governance` - CLI surface and runtime validation
  - `cross-domain-compat` - Cross-domain compatibility checks
  - `run-test-manifest` - Test manifest execution

## Platform Requirements

**Development:**
- Python 3.13+
- Git
- Node.js (for Playwright E2E test execution)
- npm

**Production:**
- No containerization detected (no Dockerfile, docker-compose)
- No cloud deployment target identified
- File-based runtime: operates on local filesystem with JSON/YAML artifacts
- `.workflow/orchestrator.db` - SQLite database for workflow orchestration state (557KB)
- Runtime state directories intentionally excluded from repo (`.gitignore` excludes `.lee/`, `.artifacts/`, `.project/`)

## Codebase Scale

- CLI: ~10 command modules in `cli/commands/`, ~70 library modules in `cli/lib/`
- Skills: 28 skill directories under `skills/`
- Tests: ~40 test files under `tests/` (unit, integration, fixtures, golden, qa, defect)
- SSOT: 25+ ADR documents under `ssot/adr/`
- CI: 6 parallel CI jobs covering repo hygiene, unit tests, governance checks

---

*Stack analysis: 2026-04-14*
