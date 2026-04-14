# Codebase Concerns

**Analysis Date:** 2026-04-14

## Code Complexity and File Size

### God Files Exceeding Safe Limits

**`cli/commands/gate/command.py` (793 lines)**
- Issue: Single file contains 20+ private helper functions and 7 distinct action handlers
- Functions: `_package_action`, `_evaluate_action`, `_materialize_action`, `_dispatch_action`, `_release_hold_action`, `_close_action`, plus collaboration handlers
- Impact: Changes to one gate action risk breaking others; difficult to test in isolation
- Fix approach: Extract each action handler into its own module under `cli/lib/gate_actions/`

**`cli/lib/formalization_materialize.py` (1076 lines)**
- Issue: Handles all formalization materialization logic in one module
- Impact: High cognitive load for any modification; tight coupling between materialization strategies
- Fix approach: Split by materialization type (e.g., `formalization_materialize_src.py`, `formalization_materialize_feat.py`)

### Skill Scripts Exceeding 800 Lines

- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py` (2776 lines) -- critical
- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py` (1897 lines)
- `skills/ll-product-raw-to-src/scripts/raw_to_src_high_fidelity.py` (1838 lines)
- `skills/ll-gate-human-orchestrator/scripts/gate_human_orchestrator_round_support.py` (1704 lines)
- `skills/ll-dev-tech-to-impl/scripts/tech_to_impl_contract_projection.py` (1559 lines)
- `skills/ll-product-raw-to-src/scripts/raw_to_src_bridge.py` (1433 lines)
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py` (1367 lines)

These files are 2-3x the recommended maximum and should be decomposed into smaller, focused modules.

## Security Vulnerabilities

### Command Injection via `shell=True`

**`cli/lib/test_exec_playwright.py` (lines 310, 427)**
```python
result = subprocess.run(npm_command, shell=True, cwd=project_root, ...)
result = subprocess.run(playwright_command, shell=True, cwd=project_root, ...)
```
- Risk: `npm_command` and `playwright_command` come from `environment` dict which can be user-controlled through test environment configuration
- Impact: Arbitrary command execution if a malicious test environment spec is provided
- Fix: Use list-based `subprocess.run()` with explicit argument splitting. Never pass user-controlled strings through shell.

**`cli/lib/test_exec_ui_runtime_probe.py` (line 111)**
```python
result = subprocess.run(
    f'{probe_command} "{input_path}" "{output_path}"',
    shell=True, ...
)
```
- Risk: `probe_command` is interpolated directly into a shell string
- Impact: Command injection via probe_command field
- Fix: Split command into argument list; use `shell=False`

**`cli/lib/test_exec_execution.py` (line 454)**
```python
run_with_shell = True
```
- Risk: Defaults to shell execution for all test cases
- Impact: Any `command_entry` containing shell metacharacters executes in shell context
- Fix: Default to `shell=False`; only enable shell mode with explicit allowlist

### Broad Exception Swallowing

**`cli/lib/formalization_owner_merge.py` (lines 40, 271)**
```python
except Exception:
```
- Risk: All exceptions including KeyboardInterrupt, SystemExit are silently swallowed
- Impact: Masking of critical failures, making debugging nearly impossible
- Fix: Catch specific exception types; log caught exceptions

**`cli/lib/skill_invoker.py` (line 229)**
```python
except Exception as exc:
    raise CommandError("INTERNAL_ERROR", f"failed to invoke {target_skill}: {exc}") from exc
```
- Risk: Catches all exceptions including KeyboardInterrupt and MemoryError
- Fix: Use `except (FileNotFoundError, ValueError, ImportError, ModuleNotFoundError)` -- be specific

**`cli/lib/review_projection/renderer.py` (lines 28, 113)**
```python
except Exception as exc:  # line 28
except Exception:          # line 113 -- silent swallow
```
- Line 113 silently discards all exceptions -- data loss risk

### Destructive File Operations Without Safeguards

**`cli/lib/formalization_materialize.py` (line 612)**
```python
if target_dir.exists():
    shutil.rmtree(target_dir)
```
- Risk: Unconditionally deletes entire target directory before copying
- Impact: If `target_dir` resolves to an unexpected path (e.g., via path traversal), could delete unintended content
- Fix: Add path validation against workspace root; use atomic rename pattern; add confirmation check

Similar patterns in:
- `skills/ll-dev-feat-to-proto/scripts/feat_to_proto.py` (line 386)
- `skills/ll-skill-install/scripts/install_adapter.py` (line 419)
- `skills/l3/ll-governance-failure-capture/scripts/install_profile.py` (line 57)
- `skills/ll-meta-skill-creator/scripts/install_profile.py` (line 57)

## Runtime Path Manipulation (sys.path Injection)

**30+ instances of `sys.path.insert(0, ...)` across the codebase**

This pattern modifies Python's import resolution at runtime, which creates:

1. **Import order fragility**: Modules from different skills with the same name can collide
   - Multiple skills contain `feat_to_ui.py`, `feat_to_ui_spec.py`, `workflow_runtime.py`
   - `skills/ll-dev-feat-to-ui/scripts/feat_to_ui.py` vs `skills/ll-dev-proto-to-ui/scripts/feat_to_ui.py` vs `skills/ll-dev-feat-to-proto/scripts/feat_to_ui.py`

2. **Thread-unsafe mutation**: `sys.path` is global state; concurrent invocations race on path modification

3. **Cleanup risk**: The `finally` block cleanup in `cli/lib/skill_invoker.py` (line 26) and `cli/commands/skill/command.py` (lines 93-94) can fail if the path was already modified elsewhere

**Central managed pattern exists but is not universally used:**
- `cli/lib/skill_invoker.py` has `_prepend_sys_path()` context manager (lines 15-26) -- this is the correct pattern
- `cli/commands/skill/command.py` does manual insert/remove (lines 76-94) -- should use the context manager

**Locations with direct sys.path manipulation outside the context manager:**
- `skills/ll-product-src-to-epic/scripts/src_to_epic_runtime.py` (line 16) -- module-level, never cleaned up
- `skills/ll-dev-proto-to-ui/scripts/proto_to_ui.py` (line 13)
- `skills/ll-dev-proto-to-ui/scripts/feat_to_ui.py` (line 13)
- `skills/ll-dev-feat-to-ui/scripts/feat_to_ui.py`
- `skills/ll-product-raw-to-src/scripts/raw_to_src.py` (line 15)
- `skills/ll-product-raw-to-src/scripts/raw_to_src_gate_integration.py` (line 61)
- `skills/ll-product-raw-to-src/scripts/raw_to_src_cli_integration.py` (lines 27, 80)
- `skills/ll-product-raw-to-src/scripts/raw_to_src_revision.py` (line 13)
- `skills/ll-product-src-to-epic/scripts/src_to_epic_review_phase1.py` (line 14)
- `skills/ll-product-src-to-epic/scripts/src_to_epic_gate_integration.py` (line 98)
- `skills/ll-product-src-to-epic/scripts/src_to_epic_common.py` (lines 163, 194)
- `skills/ll-product-src-to-epic/scripts/src_to_epic_cli_integration.py` (line 25)
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_runtime.py` (line 15)
- `skills/ll-qa-feat-to-testset/scripts/feat_to_testset_gate_integration.py` (line 101)

Fix approach: Consolidate all dynamic imports through the `_prepend_sys_path()` context manager or migrate skills to proper Python packages with `setup.py`/`pyproject.toml`.

## Test Coverage Gaps

### Skills With Zero Test Coverage

| Skill | Python Files | Test Files | Risk |
|-------|-------------|------------|------|
| `ll-dev-feat-to-tech` | 18 | 0 | High -- core dev workflow |
| `ll-qa-feat-to-testset` | 18 | 0 | High -- QA test generation |
| `ll-gate-human-orchestrator` | 8 | 0 | High -- human-in-the-loop gating |
| `ll-meta-skill-creator` | 5 | 0 | Medium -- scaffolding tool |
| `ll-skill-install` | 1 | 0 | Medium -- adapter installation |
| `ll-test-exec-web-e2e` | 2 | 0 | High -- e2e test execution |
| `l3/ll-governance-failure-capture` | 4 | 0 | Medium -- failure tracking |
| `ll-project-init` | 1 | 0 | Low -- project bootstrap |

### Empty Skeleton Skills (Planned but Not Implemented)

The following skill directories exist but contain zero Python files, representing unfinished work that may be referenced by downstream code:

- `ll-qa-api-manifest-init`
- `ll-qa-api-spec-gen`
- `ll-qa-e2e-manifest-init`
- `ll-qa-e2e-spec-gen`
- `ll-qa-feat-to-apiplan`
- `ll-qa-gate-evaluate`
- `ll-qa-prototype-to-e2eplan`
- `ll-qa-settlement`

Risk: Code may reference these skills expecting them to exist, causing PRECONDITION_FAILED errors at runtime.

### No Test Configuration

- No `conftest.py` in project root or any test directory
- No `pytest.ini`, `pyproject.toml` with pytest config
- Tests rely on ad-hoc setup in individual test files
- No shared fixtures, no centralized test utilities across the 59 test files

### No Code Coverage Enforcement

- CI installs `coverage` package but no coverage threshold is configured
- No `.coveragerc` or coverage configuration file
- No coverage reports generated in CI pipeline

## Dependency Management

### No Python Dependency Manifest

- No `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg`, `Pipfile`, or `poetry.lock`
- CI installs `pip install --upgrade pip pytest pyyaml coverage` inline (`.github/workflows/ci.yml`)
- Dependencies are implicit and scattered across the CI workflow
- Risk: Reproducible builds are not guaranteed; local dev environment may differ from CI

### Minimal package.json

Only contains `playwright` as a dependency (`package.json`):
```json
{"dependencies": {"playwright": "^1.58.2"}}
```
- No lockfile for Python dependencies
- No Node.js lockfile (package-lock.json exists but is minimal)

### No Linting or Formatting Configuration

- No `.ruff.toml`, `ruff.toml`, `.flake8`, `pylintrc`, `mypy.ini`
- No `.prettierrc`, `.eslintrc*`
- No code quality enforcement in CI beyond custom governance checks
- Risk: Inconsistent code style across the 142 skill Python files and 86 CLI library files

## Duplicate Code

### Identical-Named Files Across Skills

Multiple skills contain files with the same name, creating import collision risk when `sys.path` manipulation is used:

- `feat_to_ui.py` exists in 3 skills: `ll-dev-feat-to-proto`, `ll-dev-feat-to-ui`, `ll-dev-proto-to-ui`
- `feat_to_ui_spec.py` exists in 3 skills: same as above
- `workflow_runtime.py` exists in 4 skills: `l3/ll-governance-failure-capture`, `l3/ll-governance-spec-reconcile`, `ll-dev-feat-to-tech`, `ll-project-init`

### Output Templates Are Boilerplate Duplicates

All skill `output/template.md` files follow the same TODO-placeholder pattern:
- `skills/ll-dev-feat-to-tech/output/template.md`
- `skills/ll-dev-feat-to-ui/output/template.md`
- `skills/ll-dev-feat-to-proto/output/template.md`
- `skills/ll-dev-proto-to-ui/output/template.md`
- `skills/ll-qa-feat-to-testset/output/template.md`
- `skills/ll-product-epic-to-feat/output/template.md`
- etc.

These should be generated from a shared template with skill-specific variables.

## Incomplete Code

### TODO in Runtime Code

**`skills/ll-dev-feat-to-tech/scripts/workflow_runtime.py` (line 4)**
```
Replace the TODO sections with workflow-specific transformation logic.
```
This is a workflow_runtime file that still contains placeholder text suggesting incomplete implementation.

**`skills/ll-meta-skill-creator/scripts/init_lee_workflow_skill.py` (line 650)**
Same TODO pattern in the skill creator itself.

## No Type Checking

- No `mypy.ini` or `pyrightconfig.json`
- No type checking in CI pipeline
- While type annotations are used (`from __future__ import annotations`, type hints on signatures), they are not validated
- Risk: Type annotation drift -- annotations may not match actual usage

## CI Pipeline Limitations

### No Matrix Testing

CI runs only on `ubuntu-latest` with Python 3.13 (`.github/workflows/ci.yml`)
- No testing against multiple Python versions
- No Windows or macOS CI runs despite Windows user base

### No Integration Tests in CI

CI runs: `unit_fast`, `repo-hygiene`, `ssot-governance`, `code-size-governance`, `skill-governance`, `cli-governance`, `cross-domain-compat`
- No end-to-end integration tests
- No test of actual CLI workflows end-to-end

### No Security Scanning

- No `bandit` or similar static security analysis in CI
- No dependency vulnerability scanning
- No secret scanning configuration

## Fragile Patterns

### Deprecated Skill Still in Router

**`cli/lib/skill_invoker.py` (lines 46-50)**
```python
def _invoke_feat_to_ui(workspace_root: Path, job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    raise CommandError(
        "PRECONDITION_FAILED",
        "workflow.dev.feat_to_ui is deprecated and disabled; use workflow.dev.feat_to_proto first, ...",
    )
```
- The deprecated skill is still in the dispatch table; any job referencing it will fail at runtime
- Risk: Stale job records or downstream dispatch targeting this skill will fail with opaque errors

### Hardcoded Artifact Paths

**`cli/commands/gate/command.py` (lines 80-85)**
```python
"brief": f"artifacts/active/gates/briefs/{key}-brief-record.json",
"pending": f"artifacts/active/gates/pending-human/{key}-pending-human-decision.json",
```
- Artifact paths are hardcoded as string constants scattered across the codebase
- Risk: Changing the artifact layout requires updating dozens of references
- Fix: Centralize path construction in a single `ArtifactPaths` class

### Runtime Environment Not Configured

**`cli/ll.py` (lines 1-4)**
```python
LL_RUNTIME_HOME=
LL_CACHE_HOME=
LL_SESSION_HOME=
```
- Runtime home directories are empty/undefined
- `.env.example` exists but has no actual configuration
- Risk: Runtime behavior depends on implicit defaults; no way to configure for different environments

## Data Safety

### Path Traversal Mitigation Exists But Is Inconsistent

**`cli/lib/formalization_materialize.py` (lines 632-635)** has proper path escape validation:
```python
try:
    candidate_path.relative_to(resolved_root)
except ValueError:
    ensure(False, "PRECONDITION_FAILED", f"prototype package ref escapes package root: {relative_ref}")
```

But **`cli/lib/fs.py` `canonical_to_path()` (lines 55-57)** does not validate against workspace root:
```python
def canonical_to_path(canonical_path: str, workspace_root: Path) -> Path:
    path = Path(canonical_path)
    return path if path.is_absolute() else (workspace_root / path)
```
- An absolute path in `canonical_path` bypasses the workspace root entirely
- This function is called 50+ times across the codebase
- Risk: Path traversal if a malicious response or request contains an absolute path

## Scalability Limitations

### File-Based State Management

The entire system uses JSON files on disk as its state store:
- Jobs: `artifacts/jobs/`
- Gates: `artifacts/active/gates/`
- Registry: resolved via `cli/lib/registry_store.py`

No database layer exists. This works for single-developer workflows but:
- No concurrent access protection
- No atomic transactions
- No query capability beyond glob + load
- No pagination for job lists (see `cli/lib/job_queue.py`)

### No Rate Limiting

- No rate limiting on skill invocations
- No backpressure mechanism when multiple jobs target the same skill
- CI pipeline has no concurrency controls

## Legacy Artifacts

### `.workflow/` Directory Contains Session Logs

The `.workflow/claude-code/` directory contains conversation logs and input snapshots from prior AI coding sessions. These are:
- Not tracked in `.gitignore` (verified)
- Potentially contain sensitive project context
- Add repository bloat

### `legacy/evidence/` Directory

The `legacy/` directory contains an `evidence/` subdirectory but appears otherwise empty. This is dead space that should be cleaned up or properly documented.

## Summary of High-Priority Items

| Priority | Concern | Files | Recommended Action |
|----------|---------|-------|-------------------|
| High | Command injection via shell=True | `cli/lib/test_exec_playwright.py`, `cli/lib/test_exec_ui_runtime_probe.py`, `cli/lib/test_exec_execution.py` | Switch to list-based subprocess calls |
| High | Silent exception swallowing | `cli/lib/formalization_owner_merge.py`, `cli/lib/review_projection/renderer.py` | Catch specific exceptions, log errors |
| High | No test coverage for core skills | 8 skills with 0 tests | Add unit tests for ll-dev-feat-to-tech, ll-qa-feat-to-testset, ll-gate-human-orchestrator |
| High | God files (793-2776 lines) | `cli/commands/gate/command.py`, `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py` | Decompose into smaller modules |
| High | Destructive rmtree without validation | `cli/lib/formalization_materialize.py` | Add workspace root validation |
| Medium | No dependency manifest | Entire project | Create pyproject.toml |
| Medium | sys.path manipulation fragility | 30+ files | Consolidate through context manager |
| Medium | No linting/type checking config | Entire project | Add ruff + mypy configuration |
| Medium | Path traversal in canonical_to_path | `cli/lib/fs.py` | Validate absolute paths against workspace root |
| Low | Empty skeleton skills | 8 ll-qa-* skills | Implement or remove |
| Low | Duplicate output templates | All skills | Generate from shared template |
| Low | No CI security scanning | `.github/workflows/ci.yml` | Add bandit, dependency scanning |

---

*Concerns audit: 2026-04-14*
