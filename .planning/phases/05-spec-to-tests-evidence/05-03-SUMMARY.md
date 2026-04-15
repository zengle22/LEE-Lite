---
phase: 05-spec-to-tests-evidence
plan: 03
subsystem: testing
tags: [pytest, junitxml, evidence-yaml, manifest-backfill, code-driven, qa-execution]

# Dependency graph
requires:
  - phase: 05-spec-to-tests-evidence
    provides: "qa_schemas.py validate_spec/validate_evidence, qa_manifest_backfill.py backfill_manifest (Plan 05-01)"
  - phase: 05-spec-to-tests-evidence
    provides: "Generated pytest test scripts from api-test-spec YAML (Plan 05-02)"
provides:
  - "ll-qa-api-test-exec skill directory (14 files): code-driven execution skill skeleton"
  - "cli/lib/api_test_exec.py: pytest subprocess runner, junitxml parser, evidence validator, manifest backfiller"
  - "Execution pipeline: spec -> pytest -> junitxml -> evidence validation -> atomic manifest update"
affects: ["05-04", "05-05", "settlement", "gate-evaluation"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Code-driven skill execution (subprocess pytest vs LLM prompt-first)"
    - "junitxml parsing with xml.etree.ElementTree for structured test results"
    - "Evidence validation before manifest backfill (fail-fast on missing evidence_required items)"
    - "Atomic manifest update via backfill_manifest (temp file + os.replace)"

key-files:
  created:
    - skills/ll-qa-api-test-exec/SKILL.md
    - skills/ll-qa-api-test-exec/scripts/run.sh
    - skills/ll-qa-api-test-exec/scripts/validate_input.sh
    - skills/ll-qa-api-test-exec/scripts/validate_output.sh
    - skills/ll-qa-api-test-exec/agents/executor.md
    - skills/ll-qa-api-test-exec/agents/supervisor.md
    - cli/lib/api_test_exec.py
  modified: []

key-decisions:
  - "Evidence directory (.evidence/) is .gitignored -- schema files force-added as skill definition artifacts"
  - "pytest non-zero exit codes for test failures treated as expected behavior (returncode >= 4 = crash)"
  - "Evidence files named {coverage_id}.evidence.yaml (no run_id in filename, grouped by run-scoped directory)"

patterns-established:
  - "Code-driven execution skills: run.sh invokes Python module, not LLM"
  - "Evidence validation gate: validate_evidence() called for each evidence file before manifest backfill"
  - "Structured test result parsing via junitxml (not regex-parsing pytest stdout)"

requirements-completed: [REQ-07]

# Metrics
duration: 12min
completed: 2026-04-15T08:59:00Z
---

# Phase 05 Plan 03: API Test Execution Skill Summary

**Code-driven ll-qa-api-test-exec execution skill: pytest subprocess runner with junitxml parsing, evidence YAML validation, and atomic manifest backfill via qa_manifest_backfill**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-15T08:47:09Z
- **Completed:** 2026-04-15T08:59:00Z
- **Tasks:** 3
- **Files created:** 15 (14 skill files + 1 Python module)

## Accomplishments

- Complete 14-file `ll-qa-api-test-exec` skill skeleton with code-driven execution model
- `api_test_exec.py` module: runs pytest via subprocess, parses junitxml, validates evidence, backfills manifest
- `run.sh` entry point invokes `api_test_exec.run_api_test_exec()` (not LLM)
- Input/output validation scripts verify spec, test files, manifest, and evidence files
- Executor and supervisor agent docs document code-driven execution model

## Task Commits

Each task was committed atomically:

1. **Task 1: Create skill skeleton (12 files)** - `6635ebe` (feat)
   - SKILL.md, lifecycle/contract YAMLs, input/output contracts, scripts, evidence schemas
2. **Task 2: Create cli/lib/api_test_exec.py module** - `75336e2` (feat)
   - run_api_test_exec() with pytest subprocess, junitxml parsing, evidence validation, manifest backfill
3. **Task 3: Create executor.md and supervisor.md** - `ad03116` (feat)
   - Code-driven execution model documented, 8-point supervisor validation checklist

**Plan metadata commit:** pending (docs: complete plan)

## Files Created/Modified

- `skills/ll-qa-api-test-exec/SKILL.md` - Code-driven execution skill description
- `skills/ll-qa-api-test-exec/ll.lifecycle.yaml` - Lifecycle states (draft/validated/executed/frozen)
- `skills/ll-qa-api-test-exec/ll.contract.yaml` - Skill metadata (category: execution, chain: api)
- `skills/ll-qa-api-test-exec/input/contract.yaml` - Input contract for spec_path, test_dir, manifest_path
- `skills/ll-qa-api-test-exec/input/semantic-checklist.md` - Input validation checklist
- `skills/ll-qa-api-test-exec/output/contract.yaml` - Output contract with evidence format
- `skills/ll-qa-api-test-exec/output/semantic-checklist.md` - Output validation checklist
- `skills/ll-qa-api-test-exec/scripts/run.sh` - Code-driven entry point invoking api_test_exec.py
- `skills/ll-qa-api-test-exec/scripts/validate_input.sh` - Input validation (spec, tests, manifest)
- `skills/ll-qa-api-test-exec/scripts/validate_output.sh` - Evidence file validation
- `skills/ll-qa-api-test-exec/evidence/execution-evidence.schema.json` - Execution evidence JSON schema
- `skills/ll-qa-api-test-exec/evidence/supervision-evidence.schema.json` - Supervision evidence JSON schema
- `skills/ll-qa-api-test-exec/agents/executor.md` - Supervisory executor prompt (code-driven model)
- `skills/ll-qa-api-test-exec/agents/supervisor.md` - Post-execution validation checklist
- `cli/lib/api_test_exec.py` - Core execution module with run_api_test_exec()

## Decisions Made

- Evidence directory is .gitignored but schema JSON files are skill definition artifacts -- force-added to track skill skeleton
- pytest subprocess treats returncode 0-3 as expected (0=all pass, 1=tests failed, 2=interrupted, 3=internal error) and >= 4 as crash
- Evidence files use run-scoped directories to avoid filename collision (Pattern 3 from 05-RESEARCH.md)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Force-added evidence schema files past .gitignore**
- **Found during:** Task 1 (skill skeleton creation)
- **Issue:** `.gitignore` blocks `evidence/` directories (line 95), preventing `git add` of skill schema JSON files
- **Fix:** Used `git add -f` for the two evidence JSON schema files since they are skill definition artifacts, not runtime evidence data
- **Files modified:** skills/ll-qa-api-test-exec/evidence/execution-evidence.schema.json, skills/ll-qa-api-test-exec/evidence/supervision-evidence.schema.json
- **Verification:** Both files committed successfully in Task 1 commit
- **Committed in:** 6635ebe (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking .gitignore override)
**Impact on plan:** Evidence schema files are now tracked as skill definition artifacts. No scope creep.

## Issues Encountered

- None - plan executed exactly as written after .gitignore deviation handled

## Known Stubs

None - all files are complete with substantive content.

## Next Phase Readiness

- `ll-qa-api-test-exec` skill skeleton complete with 14 files + api_test_exec.py module
- Ready for integration with Plan 05-02 (spec-to-tests generation) and Plan 05-04/05-05 (E2E execution)
- `run_api_test_exec()` can be invoked directly from CLI or via `run.sh` entry point

---

## Self-Check: PASSED

**Files verified:**
- `skills/ll-qa-api-test-exec/` has 14 files: PASSED
- `cli/lib/api_test_exec.py` exists and imports: PASSED
- `run.sh` contains `api_test_exec` reference: PASSED

**Commits verified:**
- `6635ebe` Task 1 skeleton: FOUND
- `75336e2` Task 2 module: FOUND
- `ad03116` Task 3 agents: FOUND

---

*Phase: 05-spec-to-tests-evidence*
*Completed: 2026-04-15*
