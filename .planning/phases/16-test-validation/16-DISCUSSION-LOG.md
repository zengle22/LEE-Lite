# Phase 16: 测试验证 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 16-test-validation
**Areas discussed:** Test scope, Evidence format, Test runner, Integration tests, Gap handling, FC trace tests

---

## Test scope

| Option | Description | Selected |
|--------|-------------|----------|
| Run existing + fill gaps | Run all existing tests first, then identify and fill any gaps | ✓ |
| Full re-write of test suite | Audit and rewrite all tests from scratch | |
| Evidence collection only | Just run existing tests and collect evidence | |

**User's choice:** Run existing + fill gaps
**Notes:** Existing tests from phases 12-15 form the baseline. Focus on gap-filling, not rewriting.

## Evidence format

| Option | Description | Selected |
|--------|-------------|----------|
| Test report + artifacts | Generate structured TEST-REPORT.md | |
| CI-style output | JUnit XML + coverage reports, CI/CD pipeline ready | ✓ |
| You decide | Claude decides best format | |

**User's choice:** CI-style output
**Notes:** Machine-readable evidence files suitable for CI/CD pipeline consumption.

## Test runner

| Option | Description | Selected |
|--------|-------------|----------|
| pytest + plugins | Standard pytest with --junitxml and --cov flags | ✓ |
| Custom orchestration script | Build custom test runner script | |
| You decide | Claude decides best approach | |

**User's choice:** pytest + plugins
**Notes:** Leverage existing test structure, no custom runner needed.

## Integration tests

| Option | Description | Selected |
|--------|-------------|----------|
| End-to-end flows | Validate write_json -> enum_guard -> persistence | |
| Module connectivity | Verify modules connect without side effects | |
| Both | Both end-to-end flows AND module connectivity | ✓ |

**User's choice:** Both
**Notes:** TEST-04 should cover both e2e flows and module connectivity.

## Gap handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fix before proceeding | Fix underlying code or test until it passes | ✓ |
| Document and defer | Document failures and continue | |
| Partial pass | Document failures, mark phase partial | |

**User's choice:** Fix before proceeding
**Notes:** No skipping or marking flaky — fix before proceeding.

## FC trace tests

| Option | Description | Selected |
|--------|-------------|----------|
| Trace in output files | Verify FC refs in output files | |
| Trace in code paths | Verify FC refs at injection points | |
| Both | Both output files AND injection points | ✓ |

**User's choice:** Both
**Notes:** TEST-05 should verify FC refs in both output files and code injection paths.

## Claude's Discretion

- Exact pytest configuration (pytest.ini vs pyproject.toml)
- Coverage threshold above 80% minimum
- Order of test execution within the suite
- Specific test file naming conventions for any new tests

## Deferred Ideas

None — discussion stayed within phase scope.
