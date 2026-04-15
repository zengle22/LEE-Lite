---
phase: "05-spec-to-tests-evidence"
plan: 04
subsystem: testing
tags: [playwright, typescript, e2e, spec-to-tests, evidence-collection, adr-047]

# Dependency graph
requires:
  - phase: 05-01
    provides: e2e_journey_spec schema in spec.yaml, validate_e2e_spec() in qa_schemas.py
provides:
  - ll-qa-e2e-spec-to-tests skill (14 files) for E2E spec-to-Playwright generation
  - executor.md LLM prompt for frozen e2e-journey-spec to Playwright .spec.ts conversion
  - supervisor.md 11-item validation checklist for generated Playwright scripts
  - Input validation via qa_schemas --type e2e_spec
  - Output validation checking .spec.ts files contain @playwright/test imports
affects: [05-05-e2e-test-exec, downstream E2E chain pilot]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase 2 Prompt-first skeleton pattern adapted for Playwright TypeScript output"
    - "E2E evidence collection hooks embedded in generated test scripts (page.screenshot, page.on response, console listener)"
    - "Run-scoped evidence directories with run_id collision avoidance"

key-files:
  created:
    - skills/ll-qa-e2e-spec-to-tests/SKILL.md
    - skills/ll-qa-e2e-spec-to-tests/agents/executor.md
    - skills/ll-qa-e2e-spec-to-tests/agents/supervisor.md
    - skills/ll-qa-e2e-spec-to-tests/scripts/run.sh
    - skills/ll-qa-e2e-spec-to-tests/scripts/validate_input.sh
    - skills/ll-qa-e2e-spec-to-tests/scripts/validate_output.sh
  modified: []

key-decisions:
  - "Mirrored ll-qa-api-spec-gen Phase 2 pattern (not ll-qa-api-spec-to-tests which does not exist) for skeleton structure"
  - "Adapted validate_output.sh to check for @playwright/test import instead of Python pytest patterns"
  - "Evidence directory forced-added via git add -f due to .gitignore global evidence/ rule"

patterns-established:
  - "E2E spec-to-tests generation follows same Prompt-first pattern as API spec-to-tests"
  - "Generated Playwright scripts write their own evidence YAML during execution (per ADR-047 Section 6.3)"
  - "Input validation uses qa_schemas --type e2e_spec, output validation checks TypeScript imports"

requirements-completed: [REQ-07]

# Metrics
duration: 8min
completed: 2026-04-15
---

# Phase 05 Plan 04: E2E Spec-to-Tests Generation Summary

**14-file Prompt-first skill converting frozen e2e-journey-spec YAML into executable Playwright TypeScript test scripts with embedded evidence collection per ADR-047 Section 6.3**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T13:00:00Z
- **Completed:** 2026-04-15T13:08:00Z
- **Tasks:** 2
- **Files modified:** 14 created

## Accomplishments
- Created complete ll-qa-e2e-spec-to-tests skill skeleton (12 files) following Phase 2 Prompt-first pattern
- Added executor.md and supervisor.md LLM agent prompts (2 files) adapted for Playwright TypeScript output
- Input validation pipeline: validate_input.sh calls qa_schemas --type e2e_spec
- Output validation pipeline: validate_output.sh verifies .spec.ts files contain @playwright/test imports
- Evidence collection hooks embedded in executor instructions: page.screenshot, network interception, console error listener, DOM assertions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ll-qa-e2e-spec-to-tests skill skeleton (12 files)** - `749b4e3` (feat)
2. **Task 2: Create executor.md and supervisor.md for E2E LLM agents** - `2221c92` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created

- `skills/ll-qa-e2e-spec-to-tests/SKILL.md` - Skill description, execution protocol, non-negotiable rules
- `skills/ll-qa-e2e-spec-to-tests/ll.lifecycle.yaml` - Lifecycle states: draft/validated/executed/frozen
- `skills/ll-qa-e2e-spec-to-tests/ll.contract.yaml` - Skill metadata: adr=ADR-047, category=generation, chain=e2e, phase=5
- `skills/ll-qa-e2e-spec-to-tests/input/contract.yaml` - Input contract: spec_path, output_dir
- `skills/ll-qa-e2e-spec-to-tests/input/semantic-checklist.md` - 9-item input validation checklist
- `skills/ll-qa-e2e-spec-to-tests/output/contract.yaml` - Output contract: test_files array with paths and IDs
- `skills/ll-qa-e2e-spec-to-tests/output/semantic-checklist.md` - 12-item output validation checklist
- `skills/ll-qa-e2e-spec-to-tests/scripts/run.sh` - Entry point wrapper calling qa_skill_runtime
- `skills/ll-qa-e2e-spec-to-tests/scripts/validate_input.sh` - Validates e2e_spec via qa_schemas
- `skills/ll-qa-e2e-spec-to-tests/scripts/validate_output.sh` - Validates .spec.ts files with Playwright imports
- `skills/ll-qa-e2e-spec-to-tests/evidence/execution-evidence.schema.json` - Skill execution evidence schema
- `skills/ll-qa-e2e-spec-to-tests/evidence/supervision-evidence.schema.json` - Supervision evidence schema
- `skills/ll-qa-e2e-spec-to-tests/agents/executor.md` - 153-line LLM prompt for E2E spec-to-Playwright generation with evidence collection
- `skills/ll-qa-e2e-spec-to-tests/agents/supervisor.md` - 11-item validation checklist for generated Playwright scripts

## Decisions Made

1. Used ll-qa-api-spec-gen as the Phase 2 reference pattern since ll-qa-api-spec-to-tests (referenced in plan) does not exist yet
2. Adapted all validation scripts for Playwright TypeScript instead of pytest Python
3. Forced git add for evidence/ directory files due to global .gitignore rule (these are schema files, not runtime evidence)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Evidence directory gitignored**
- **Found during:** Task 1 (skill skeleton creation)
- **Issue:** Global .gitignore contains `evidence/` rule, preventing `git add` of evidence schema JSON files
- **Fix:** Used `git add -f` to force-add the two evidence schema files (execution-evidence.schema.json, supervision-evidence.schema.json)
- **Files modified:** skills/ll-qa-e2e-spec-to-tests/evidence/execution-evidence.schema.json, skills/ll-qa-e2e-spec-to-tests/evidence/supervision-evidence.schema.json
- **Verification:** Both files committed and tracked in git
- **Committed in:** 749b4e3 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to track schema files; no scope creep.

## Issues Encountered
- None beyond the gitignore issue documented above.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag:injection | skills/ll-qa-e2e-spec-to-tests/agents/executor.md | LLM prompt instructs generation of executable TypeScript from spec data; validate_input.sh mitigates by running qa_schemas validate_e2e_spec before LLM invocation |
| threat_flag:tampering | skills/ll-qa-e2e-spec-to-tests/scripts/validate_output.sh | Generated .spec.ts files checked for @playwright/test import; supervisor checklist validates Playwright API usage |
| threat_flag:repudiation | skills/ll-qa-e2e-spec-to-tests/agents/executor.md | Evidence YAML required with case_id, coverage_id, executed_at, run_id for every evidence_required item |

## Known Stubs
None - all files are structural skeleton/prompt definitions. No data stubs or placeholder values that flow to UI rendering.

## Next Phase Readiness
- E2E generation skill complete, ready for 05-05 (E2E test execution skill) to consume generated .spec.ts files
- Depends on ll-qa-e2e-spec-gen producing frozen e2e-journey-spec YAML files as input
- CLI registration (e2e-spec-to-tests action in _QA_SKILL_MAP) required before skill is invokable

---
*Phase: 05-spec-to-tests-evidence*
*Completed: 2026-04-15*
