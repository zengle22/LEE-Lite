# External Integrations

**Analysis Date:** 2026-04-14

## APIs & External Services

**AI/LLM Integration:**
- Claude Code - Primary AI executor for skill workflows. Configured in `.lee/config.yaml` as `executor.default_type: claude_code`. Skills invoke Claude Code sessions to generate governed artifacts (specs, designs, implementations, tests).
- No direct OpenAI, Anthropic, or other LLM SDK imports detected in the codebase. LLM interaction is mediated through the Claude Code CLI subprocess, not direct API calls.

**Version Control:**
- GitHub - Repository hosted at `https://github.com/zengle22/LEE-Lite.git` (from `.lee/repos.yaml`)
- Git CLI - Used extensively via `subprocess.run` for:
  - Changed file detection (`tools/ci/write_changed_files.py`)
  - File retrieval at revisions (`tools/ci/common.py` `git_show_file()`)
  - Temporary repo initialization in CI tests (`tests/unit/test_ci_validators.py`)

## Data Storage

**Databases:**
- SQLite - Local workflow orchestration database
  - Location: `.workflow/orchestrator.db` (557KB)
  - Client: Not directly accessed via SQLAlchemy or similar ORM; managed by the workflow orchestration layer
  - Purpose: Stores workflow run state, events, approvals, and orchestration metadata

**File Storage:**
- Local filesystem - Primary storage mechanism
  - JSON files: Job records, registry entries, artifacts, evidence bundles, gate decisions
  - YAML files: SSOT objects, skill contracts, configuration files
  - Markdown files: ADRs, specifications, skill documentation
  - Storage locations:
    - `ssot/` - Single source of truth objects (specs, architecture, features, implementations)
    - `artifacts/` - Generated outputs, reports, evidence, lineage tracking
    - `.artifacts/` - CI artifact outputs
    - `.workflow/` - Workflow runtime state (approvals, blobs, cache, runs, traces)

**Caching:**
- Filesystem-based caching only
  - `.workflow/cache/` - Workflow cache directory
  - `__pycache__/` - Python bytecode cache (gitignored)
  - No Redis, Memcached, or distributed caching detected

## Authentication & Identity

**Auth Provider:**
- None at the application level - This is a CLI tool operating on local files
- GitHub authentication handled by the `gh` CLI and git credential manager (external to this codebase)
- Claude Code authentication managed by the Claude Code CLI (external)

**Secrets Management:**
- Environment variables via `.env` file (gitignored)
- Three runtime home variables: `LL_RUNTIME_HOME`, `LL_CACHE_HOME`, `LL_SESSION_HOME`
- No hardcoded secrets detected in the codebase

## Monitoring & Observability

**Error Tracking:**
- No external error tracking service (no Sentry, Rollbar, etc.)
- Structured error handling via `CommandError` dataclass with status codes (`cli/lib/errors.py`):
  - `OK`, `INVALID_REQUEST`, `POLICY_DENIED`, `REGISTRY_MISS`, `ELIGIBILITY_DENIED`, `PRECONDITION_FAILED`, `PROVISIONAL_SLICE_DISABLED`, `INVARIANT_VIOLATION`, `INTERNAL_ERROR`
  - Each maps to exit codes (0-10) and semantic result categories

**Logs:**
- stdout/stderr via `subprocess.run` output capture
- CI log output printed during test execution (`tools/ci/common.py` `run_pytest()`)
- `.workflow/events.jsonl` - JSONL event log for workflow orchestration (11KB)
- Evidence bundles stored in `artifacts/reports/` and `.workflow/evidence/`

## CI/CD & Deployment

**Hosting:**
- GitHub repository (no external hosting platform detected)
- No Docker or container configuration
- No server deployment - CLI tool runs locally

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`)
- Triggers: `pull_request`, `push` to `main`, `master`, `codex/**` branches
- 6 parallel jobs:
  1. `repo-hygiene` - Repository structure validation
  2. `unit-fast` - Fast unit test suite (`tests/unit`)
  3. `ssot-governance` - SSOT object compliance
  4. `code-size-governance` - Code size/function length limits
  5. `skill-governance` - Skill file structure with optional test execution
  6. `cli-governance` - CLI surface validation with optional test execution
  7. `cross-domain-compat` - Cross-domain compatibility with optional test execution
- Python 3.13 on `ubuntu-latest`
- Dependencies installed per-job: `pip install --upgrade pip pytest pyyaml coverage`
- Artifacts output to `.artifacts/ci/` subdirectories

## Environment Configuration

**Required env vars:**
- `LL_RUNTIME_HOME` - LEE runtime home directory
- `LL_CACHE_HOME` - LEE cache directory
- `LL_SESSION_HOME` - LEE session directory

**Secrets location:**
- Local `.env` file (gitignored) - no committed secrets
- GitHub repository secrets for CI (if any, not detected in workflow file)

## Webhooks & Callbacks

**Incoming:**
- GitHub Actions webhook triggers on push/PR events

**Outgoing:**
- None detected - this is a local CLI tool that operates on files

## Third-Party Tool Integrations

**BMAD Framework:**
- `_bmad/` directory contains BMAD (Build-Measure-Adapt-Deploy) modules:
  - `_config/`, `bmb/`, `bmm/`, `cis/`, `core/`, `tea/`, `wds/`
  - Third-party skills auto-downloaded to `.claude/skills/bmad-*` and `.claude/skills/wds-*` (gitignored)

**OpenSpec:**
- `openspec/` directory with `config.yaml` using `spec-driven` schema
- Contains `changes/` and `specs/` subdirectories for specification management

**Oh-My-ClaudeCode (OMC):**
- `.omc/` directory for OMC orchestration state (gitignored)
- Multi-agent coordination layer for Claude Code sessions

**Playwright E2E:**
- Dynamic Playwright project generation via `cli/lib/test_exec_playwright.py`:
  - Creates temporary `playwright-project/` with `package.json`, `tsconfig.json`, `playwright.config.ts`
  - Runs `npm install` and `npx playwright test` as subprocess commands
  - Supports browser selection (chromium, firefox, webkit) via environment config

---

*Integration audit: 2026-04-14*
