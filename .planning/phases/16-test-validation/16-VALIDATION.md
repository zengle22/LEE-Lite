---
phase: 16
slug: test-validation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-23
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pytest.ini (Wave 1 creates) |
| **Quick run command** | `python -m pytest tests/cli/lib/ -x --tb=short` |
| **Full suite command** | `python -m pytest tests/cli/lib/ --junitxml=test-results.xml --cov=cli.lib --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/cli/lib/ -x --tb=short`
- **After every plan wave:** Run `python -m pytest tests/cli/lib/ --junitxml=test-results.xml --cov=cli.lib --cov-report=term-missing -v`
- **Before `/gsd-verify-work`:** Full suite must be green (207+ tests, coverage >= 80%)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | TEST-01~05 | — | pytest-cov installed | unit | `pip show pytest-cov` | ❌ W0 | ⬜ pending |
| 16-01-02 | 01 | 1 | TEST-01~05 | — | pytest config suppresses warnings | unit | `pytest --collect-only -q` | ❌ W0 | ⬜ pending |
| 16-01-03 | 01 | 1 | TEST-04 | — | test_manifests.json includes cli_lib_tests | config | `python -c "import json; d=json.load(open('tools/ci/manifests/test_manifests.json')); assert 'cli_lib_tests' in d"` | ✅ | ⬜ pending |
| 16-02-01 | 02 | 2 | TEST-01~05 | — | All tests pass, evidence produced | integration | `python -m pytest tests/cli/lib/ --junitxml=test-results.xml --cov=cli.lib --cov-report=xml:coverage.xml --cov-report=html:htmlcov -v` | ✅ | ⬜ pending |
| 16-02-02 | 02 | 2 | TEST-01~05 | — | Evidence files exist and contain expected content | verification | `grep -c "<testcase" test-results.xml && grep "passed" test-output.log` | ✅ | ⬜ pending |
| 16-03-01 | 03 | 3 | TEST-01~05 | — | CI workflow includes pytest-cov | config | `python -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); assert 'pytest-cov' in str(d)"` | ✅ | ⬜ pending |
| 16-03-02 | 03 | 3 | TEST-01~05 | — | ROADMAP.md marks phase success criteria as done | verification | `grep -c "\[x\]" ROADMAP.md && test -f 16-03-SUMMARY.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Install pytest-cov via `pip install pytest-cov`
- [ ] Create pytest.ini with testpaths and python_files config
- [ ] Add cli_lib_tests entry to test_manifests.json

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual inspection of coverage report | TEST-01~05 | Coverage HTML report requires human review to confirm module coverage distribution | Open htmlcov/index.html, verify cli/lib/ modules show >= 80% coverage |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
