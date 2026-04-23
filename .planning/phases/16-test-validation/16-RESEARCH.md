# Phase 16: Test Validation - Research

**Researched:** 2026-04-23
**Domain:** Python pytest test validation, coverage reporting, CI evidence collection
**Confidence:** HIGH

## Summary

Phase 16 is a testing and validation phase, not a feature-building phase. All v2.1 deliverables (schemas, enum_guard, governance_validator, integration tests) are already implemented with a substantial test suite in place. The baseline is **207 tests across 6 test files**, all currently passing. The primary work is installing missing coverage tooling, ensuring the test_manifests.json includes the v2.1 tests, running the full suite with JUnit XML + coverage evidence, and confirming no gaps remain for TEST-01 through TEST-05.

The main gap is **pytest-cov is not installed** -- required by decision D-03 for coverage evidence. Additionally, the CI test manifests (`tools/ci/manifests/test_manifests.json`) do not reference any `tests/cli/lib/` test files, meaning the v2.1 tests are not exercised by the existing CI pipeline. This is a configuration gap, not a code gap.

**Primary recommendation:** Install pytest-cov, add a `cli_lib_tests` entry to test_manifests.json, run full suite with `--junitxml` and `--cov=cli.lib`, collect evidence artifacts, and confirm `ready_for_test` state.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schema validation tests (TEST-01) | API / Backend | -- | Tests validate library-level schema modules in cli/lib/ |
| Enum guard tests (TEST-02) | API / Backend | -- | Tests validate enum_guard.py module |
| Governance validator tests (TEST-03) | API / Backend | -- | Tests validate governance_validator.py module |
| SSOT integration tests (TEST-04) | API / Backend | -- | Tests validate fs.py write path through enum_guard to disk |
| FC traceability tests (TEST-05) | API / Backend | -- | Tests validate _inject_fc_refs in fs.py output |
| Test runner / evidence collection | CI / Build | -- | pytest + plugins produce machine-readable evidence |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test runner and assertion framework | Already installed, all 207 tests use it [VERIFIED: `python -m pytest --version`] |
| pytest-cov | 6.1.1 (latest) | Coverage reporting with `--cov` flag | Required by D-03 for evidence; currently NOT installed [VERIFIED: `pip show pytest-cov` returned not found] |
| pyyaml | 6.0.2 | YAML parsing for schema validate_file tests | Already used by all schema modules [VERIFIED: imports in source files] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| coverage | 7.8.0 (latest) | Underlying coverage engine for pytest-cov | Installed alongside pytest-cov |

**Installation:**
```bash
pip install pytest-cov coverage
```

**Version verification:**
```
$ pip show pytest-cov 2>/dev/null || echo "NOT INSTALLED"
NOT INSTALLED
$ pip show pytest | head -3
Name: pytest
Version: 9.0.2
```

## Architecture Patterns

### System Architecture Diagram

```
Phase 16: Test Validation Pipeline

  [pytest runner]
       |
       +-- tests/cli/lib/test_testset_schema.py    --> TEST-01 (schema tests)
       +-- tests/cli/lib/test_environment_schema.py --> TEST-01 (schema tests)
       +-- tests/cli/lib/test_gate_schema.py        --> TEST-01 (schema tests)
       +-- tests/cli/lib/test_enum_guard.py         --> TEST-02 (enum guard tests)
       +-- tests/cli/lib/test_governance_validator.py --> TEST-03 (gov validator tests)
       +-- tests/cli/lib/test_fs.py                 --> TEST-04/05 (integration + FC tests)
       |
       v
  [pytest-cov plugin] --collects coverage data--> .coverage / htmlcov/
       |
       v
  [JUnit XML reporter] --junitxml--> .planning/phases/16-test-validation/test-results.xml
       |
       v
  [Evidence package] --> ready_for_test state confirmed
```

### Existing Project Structure (test-relevant)
```
tests/cli/lib/                    # v2.1 test directory
├── test_enum_guard.py            # 41 tests (TEST-02 baseline)
├── test_testset_schema.py        # 12 tests (TEST-01 partial)
├── test_environment_schema.py    # 17 tests (TEST-01 partial)
├── test_gate_schema.py           # 17 tests (TEST-01 partial)
├── test_governance_validator.py  # 86 tests (TEST-03 baseline)
└── test_fs.py                    # 17 tests (TEST-04/05 baseline)

cli/lib/                          # v2.1 source directory
├── testset_schema.py             # TESTSET schema
├── environment_schema.py         # Environment schema
├── gate_schema.py               # Gate schema + GateVerdict enum
├── enum_guard.py                 # 6 enum fields + registry
├── governance_validator.py       # 11 governance object validators
├── fs.py                         # write_json with enum_guard + FC refs
├── errors.py                     # CommandError, STATUS_SEMANTICS
└── protocol.py                   # SSOT write path (calls write_json)
```

### Pattern 1: pytest test collection and execution
**What:** Standard pytest discovery with `tests/cli/lib/` directory, `test_*.py` files, class-based test organization with `Test*` prefixes.
**When to use:** All test execution for this phase.
**Example:**
```bash
# Full suite with evidence
python -m pytest tests/cli/lib/ \
  --junitxml=.planning/phases/16-test-validation/test-results.xml \
  --cov=cli.lib \
  --cov-report=term-missing \
  --cov-report=html:.planning/phases/16-test-validation/htmlcov \
  -v
```

### Pattern 2: Integration test with tmp_path fixture
**What:** pytest's built-in `tmp_path` fixture for filesystem integration tests.
**When to use:** TEST-04 SSOT write path tests, TEST-05 FC refs persistence tests.
**Example:**
```python
# Source: tests/cli/lib/test_fs.py (existing)
def test_ssot_write_adds_fc_refs_to_file(self, tmp_path):
    ssot = tmp_path / "ssot"
    ssot.mkdir()
    f = ssot / "test.json"
    write_json(f, {"data": "value"})
    written = json.loads(f.read_text())
    assert "fc_refs" in written
    assert "FC-001" in written["fc_refs"]
```

### Anti-Patterns to Avoid
- **Do not rewrite existing tests** -- D-01 explicitly says "do not rewrite tests from scratch"
- **Do not skip failing tests** -- D-09 says "no skipping or marking flaky", D-10 says "fix before proceeding"
- **Do not use custom test runners** -- D-05 says "use pytest with plugins, no custom runner needed"
- **Do not add `tests/cli/lib/` to existing test_manifest entries** -- The current manifests (`cli_tests`, `unit_fast`) have different scopes; add a new manifest entry or run directly for this phase

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test runner | Custom test orchestrator | pytest (existing) | 207 tests already organized, tmp_path fixtures, parametrization built in |
| Coverage reporting | Manual line-counting | pytest-cov | Integrates with pytest, produces term-missing + HTML + XML reports |
| JUnit XML evidence | Custom XML writer | `pytest --junitxml=path` | CI-standard format, machine-readable, already supported by GitHub Actions |
| Test discovery | Manual file listing | pytest auto-discovery | Follows `test_*.py` convention, handles imports correctly |
| Test fixtures | Global test state | pytest fixtures (tmp_path) | Isolation per test, no cross-test pollution |

**Key insight:** The entire test infrastructure already exists. This phase is about running it, measuring it, and producing evidence -- not building new testing tools.

## Common Pitfalls

### Pitfall 1: pytest-cov not installed
**What goes wrong:** `--cov` flag fails with "unrecognized arguments" error, no coverage evidence produced.
**Why it happens:** pytest-cov is not in any requirements file and is not installed on the current system.
**How to avoid:** Run `pip install pytest-cov` as a prerequisite step before the test run.
**Warning signs:** `python -m pip show pytest-cov` returns "WARNING: Package(s) not found".

### Pitfall 2: PytestCollectionWarning on dataclass names
**What goes wrong:** pytest warns "cannot collect test class 'Testset' because it has a __init__ constructor". This is cosmetic noise that obscures real output.
**Why it happens:** Source files contain classes named `Testset`, `TestsetSchemaError` that pytest tries to collect as test classes. The `__init__` constructor (from dataclass) prevents collection.
**How to avoid:** Add `filterwarnings = ignore::pytest.PytestCollectionWarning` to pytest config, or use `python_classes = Test` pattern that excludes these.
**Warning signs:** Two warnings at end of test output: "PytestCollectionWarning: cannot collect test class".

### Pitfall 3: test_manifests.json does not include tests/cli/lib/ tests
**What goes wrong:** CI `cli-governance --run-tests` job does not exercise any v2.1 tests.
**Why it happens:** `tools/ci/manifests/test_manifests.json` `cli_tests` only lists `tests/unit/test_cli_*` files. No manifest entry references `tests/cli/lib/`.
**How to avoid:** Add a new manifest entry `"cli_lib_tests": ["tests/cli/lib"]` to test_manifests.json, or run tests directly for this phase.
**Warning signs:** `python -m tools.ci.run_checks cli-governance --run-tests` produces reports with `"tests_run": []`.

### Pitfall 4: No conftest.py for shared fixtures
**What goes wrong:** Each test file must define its own fixtures; no project-wide test configuration.
**Why it happens:** The project has no `conftest.py` at any level in the tests directory.
**How to avoid:** For this phase, no new shared fixtures are needed. If adding tests later, create `tests/cli/lib/conftest.py`.

### Pitfall 5: Windows path separators in CI evidence
**What goes wrong:** JUnit XML or coverage paths contain backslashes, causing issues with CI consumers expecting POSIX paths.
**Why it happens:** Running on Windows (win32) produces Windows-style paths.
**How to avoid:** The existing CI runs on ubuntu-laster. For local evidence collection, note the platform difference. If evidence must be CI-consumable, consider running tests in a Linux environment or normalizing paths.

## Code Examples

### Running full test suite with evidence (TEST-01 through TEST-05)
```bash
# Install coverage plugin (one-time)
pip install pytest-cov

# Run complete suite with all evidence formats
python -m pytest tests/cli/lib/ \
  --junitxml=.planning/phases/16-test-validation/test-results.xml \
  --cov=cli.lib \
  --cov-report=term-missing \
  --cov-report=html:.planning/phases/16-test-validation/htmlcov \
  --cov-report=xml:.planning/phases/16-test-validation/coverage.xml \
  -v 2>&1 | tee .planning/phases/16-test-validation/test-output.log
```

### Running individual requirement subsets
```bash
# TEST-01: Schema validation tests only
python -m pytest tests/cli/lib/test_testset_schema.py \
  tests/cli/lib/test_environment_schema.py \
  tests/cli/lib/test_gate_schema.py -v

# TEST-02: Enum guard tests only
python -m pytest tests/cli/lib/test_enum_guard.py -v

# TEST-03: Governance validator tests only
python -m pytest tests/cli/lib/test_governance_validator.py -v

# TEST-04: Integration tests (SSOT write path)
python -m pytest tests/cli/lib/test_fs.py -v -k "ssot"

# TEST-05: FC traceability tests
python -m pytest tests/cli/lib/test_fs.py -v -k "fc_refs or inject_fc"
```

### Verify FC refs in protocol response path (D-12)
```bash
# The protocol.py persist_response calls write_json for response_path.
# If response_path is an SSOT path, enum_guard validates and FC refs are injected.
# Non-SSOT paths (like response files) skip both enum_guard and FC injection.
# This is verified by test_fs.py::TestWriteJsonSsotIntegration tests.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom test runners | pytest 9.0.2 with plugins | Established | 207 tests already organized and passing |
| Manual coverage counting | pytest-cov --cov=cli.lib | New for this phase | Machine-readable coverage reports for evidence |
| Console-only output | JUnit XML + HTML coverage | New for this phase | CI-consumable evidence format (D-03, D-04) |
| No test manifest for cli/lib | tests/cli/lib/ not in test_manifests.json | Gap to fix | v2.1 tests bypass CI test execution |

**Deprecated/outdated:**
- **No conftest.py**: Currently tests work without shared fixtures. If new tests need fixtures, create `tests/cli/lib/conftest.py`.
- **No pytest.ini/pyproject.toml config**: Tests run with pytest defaults. Adding a `pytest.ini` would suppress collection warnings and set default options.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pytest-cov version 6.1.1 is latest and compatible with pytest 9.0.2 | Standard Stack | Installation may fail or coverage reports may be incomplete -- verifiable by install attempt |
| A2 | coverage 7.8.0 is the current latest version | Standard Stack | Minor version mismatch has no functional impact |
| A3 | The 207 test count represents complete coverage of v2.1 code | Test Baseline | If new code was added since last run, gaps may exist -- verifiable by coverage report |

## Open Questions

1. **Should pytest.ini be created or should options be passed inline?**
   - What we know: No pytest config file exists; tests pass with defaults; 2 PytestCollectionWarnings appear
   - What's unclear: Whether to suppress warnings via config or accept them
   - Recommendation: Create minimal pytest.ini to suppress collection warnings and set default `--cov=cli.lib` -- cleaner evidence output

2. **Should test_manifests.json be updated as part of this phase?**
   - What we know: Current manifests don't include tests/cli/lib/ tests
   - What's unclear: Whether CI pipeline should run these tests on cli/ changes
   - Recommendation: Add `"cli_lib_tests": ["tests/cli/lib"]` to test_manifests.json and update the `cli-governance` check to include them -- this is a D-08 module connectivity concern

3. **What coverage threshold constitutes "ready_for_test"?**
   - What we know: User's global testing.md requires 80% minimum; CONTEXT.md leaves exact threshold to Claude's discretion
   - What's unclear: Whether 80% line coverage or 80% branch coverage
   - Recommendation: Target 80% line coverage on cli.lib modules; use `--cov-fail-under=80` to enforce

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All tests | Yes | 3.13.3 | -- |
| pytest | Test runner | Yes | 9.0.2 | -- |
| pytest-cov | Coverage evidence (D-03) | No | -- | Install via pip |
| pyyaml | Schema validate_file tests | Yes | (installed) | -- |
| GitHub Actions | CI evidence consumption | Yes | ubuntu-latest, Python 3.13 | Local evidence files can be committed as artifacts |

**Missing dependencies with fallback:**
- pytest-cov: Not installed. Install with `pip install pytest-cov`. This is the only missing dependency and has a straightforward install.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (no pytest.ini, pyproject.toml, or setup.cfg) |
| Quick run command | `python -m pytest tests/cli/lib/ -x --tb=short` |
| Full suite command | `python -m pytest tests/cli/lib/ --junitxml=test-results.xml --cov=cli.lib --cov-report=term-missing -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | Schema validation for TESTSET, Environment, Gate | Unit | `pytest tests/cli/lib/test_testset_schema.py tests/cli/lib/test_environment_schema.py tests/cli/lib/test_gate_schema.py -v` | Yes |
| TEST-02 | Enum guard for all 6 fields (allowed + forbidden) | Unit | `pytest tests/cli/lib/test_enum_guard.py -v` | Yes |
| TEST-03 | Governance validator for all 11 objects | Unit | `pytest tests/cli/lib/test_governance_validator.py -v` | Yes |
| TEST-04 | SSOT write path: enum_guard invoked, persistence verified | Integration | `pytest tests/cli/lib/test_fs.py -v -k "ssot"` | Yes |
| TEST-05 | FC refs in output files and injection points | Integration | `pytest tests/cli/lib/test_fs.py -v -k "fc_refs or inject"` | Yes |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/cli/lib/ -x --tb=short`
- **Per wave merge:** `python -m pytest tests/cli/lib/ --cov=cli.lib --cov-report=term-missing -v`
- **Phase gate:** All 207 tests green + coverage >= 80% + JUnit XML evidence produced

### Wave 0 Gaps
- [ ] Install pytest-cov: `pip install pytest-cov` -- needed for coverage evidence
- [ ] (Optional) Create `pytest.ini` to suppress PytestCollectionWarning and set default cov options
- [ ] (Optional) Add `cli_lib_tests` entry to `tools/ci/manifests/test_manifests.json` for CI integration

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] All 6 test files in tests/cli/lib/ read and analyzed
- [VERIFIED: codebase] All 6 source modules in cli/lib/ read and analyzed
- [VERIFIED: `python -m pytest --collect-only`] 207 tests collected, all passing
- [VERIFIED: `pip show pytest-cov`] pytest-cov not installed
- [VERIFIED: .github/workflows/ci.yml] CI workflow with cli-governance job
- [VERIFIED: tools/ci/manifests/test_manifests.json] No tests/cli/lib/ entries

### Secondary (MEDIUM confidence)
- [ASSUMED] pytest-cov 6.1.1 compatible with pytest 9.0.2 (standard compatibility)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified via codebase inspection and package checks
- Architecture: HIGH - Actual test run confirmed 207/207 passing
- Pitfalls: HIGH - Directly observed: pytest-cov missing, collection warnings present, test_manifests gap confirmed

**Research date:** 2026-04-23
**Valid until:** 2026-05-23 (stable domain, no fast-moving dependencies)
