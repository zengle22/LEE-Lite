# Phase 16: 测试验证 - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Run the complete test suite across all v2.1 deliverables (schemas, enum_guard, governance_validator, integration tests), fill any test coverage gaps, and produce evidence that the system reaches `ready_for_test` state. This is a testing/validation phase — not building new features, but verifying everything works together.

Dependencies: Phase 12 (schemas), Phase 13 (enum_guard), Phase 14 (governance_validator), Phase 15 (integration + FC traceability).

</domain>

<decisions>
## Implementation Decisions

### Test scope strategy
- **D-01:** Run existing tests first, then identify and fill gaps — do not rewrite tests from scratch
- **D-02:** Existing tests from phases 12-15 form the baseline: test_enum_guard.py (41 tests), test_testset_schema.py, test_environment_schema.py, test_gate_schema.py, test_governance_validator.py, test_fs.py

### Evidence format
- **D-03:** CI-style output: JUnit XML (--junitxml) + coverage reports (--cov) as primary evidence
- **D-04:** Evidence files should be machine-readable and suitable for CI/CD pipeline consumption

### Test runner
- **D-05:** Use pytest with plugins (--junitxml, --cov) — leveraging existing test structure, no custom runner needed

### Integration tests (TEST-04)
- **D-06:** Integration tests cover BOTH end-to-end flows AND module connectivity
- **D-07:** End-to-end flows: write_json → enum_guard → verify persistence
- **D-08:** Module connectivity: verify all modules connect correctly without side effects

### Gap handling
- **D-09:** When tests fail, fix the underlying code or test until it passes — no skipping or marking flaky
- **D-10:** Fix before proceeding — do not document and defer

### Frozen Contract traceability tests (TEST-05)
- **D-11:** Verify FC refs in output files (each output file contains FC-001 through FC-007 references)
- **D-12:** Verify FC refs at injection points in code paths (write_json, protocol.py)

### Claude's Discretion
- Exact pytest configuration (pytest.ini vs pyproject.toml)
- Coverage threshold above 80% minimum
- Order of test execution within the suite
- Specific test file naming conventions for any new tests

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Testing — TEST-01 through TEST-05 requirements
- `.planning/ROADMAP.md` §Phase 16 — Phase goal and success criteria

### Frozen Contract
- `.planning/REQUIREMENTS.md` §Frozen Contract Traceability — FC-01 through FC-03
- `.planning/REQUIREMENTS.md` §SSOT Write Path Integration — INT-01 through INT-03

### Implementation code (for test writers)
- `cli/lib/testset_schema.py` — TESTSET schema implementation
- `cli/lib/environment_schema.py` — Environment schema implementation
- `cli/lib/gate_schema.py` — Gate schema implementation
- `cli/lib/enum_guard.py` — Enum guard implementation (6 enums)
- `cli/lib/governance_validator.py` — Governance validator (11 objects)
- `cli/lib/fs.py` — write_json with enum_guard integration + FC refs injection

### Existing tests (baseline)
- `tests/cli/lib/test_testset_schema.py` — TESTSET schema tests
- `tests/cli/lib/test_environment_schema.py` — Environment schema tests
- `tests/cli/lib/test_gate_schema.py` — Gate schema tests
- `tests/cli/lib/test_enum_guard.py` — Enum guard tests (41 tests)
- `tests/cli/lib/test_governance_validator.py` — Governance validator tests
- `tests/cli/lib/test_fs.py` — Integration tests (enum_guard + FC traceability)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/cli/lib/test_enum_guard.py` — 41 passing tests, baseline for TEST-02
- `tests/cli/lib/test_testset_schema.py` — TESTSET schema tests, baseline for TEST-01
- `tests/cli/lib/test_environment_schema.py` — Environment schema tests, baseline for TEST-01
- `tests/cli/lib/test_gate_schema.py` — Gate schema tests, baseline for TEST-01
- `tests/cli/lib/test_governance_validator.py` — Governance validator tests, baseline for TEST-03
- `tests/cli/lib/test_fs.py` — Integration tests, baseline for TEST-04/TEST-05

### Established Patterns
- pytest-based test structure (tests/cli/lib/ directory)
- Test files follow `test_<module>.py` naming convention
- Tests organized by module under tests/cli/lib/

### Integration Points
- SSOT write path: `cli/lib/fs.py` write_json → enum_guard validation → file persistence
- FC refs injection: write_json path adds FC-001 through FC-007 references to outputs
- All modules import from `cli/lib/` — tests should verify import paths work correctly

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for CI-style test output and evidence collection.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-test-validation*
*Context gathered: 2026-04-23*
