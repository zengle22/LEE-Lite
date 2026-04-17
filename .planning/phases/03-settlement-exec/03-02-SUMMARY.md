---
phase: 03-settlement-exec
plan: 02
subsystem: testing
tags: gate-evaluate, qa, cli, shell-scripts, json-schema

# Dependency graph
requires:
  - phase: 02-design-skill-completion
    provides: SKILL.md, ll.contract.yaml, agents/executor.md, agents/supervisor.md, input/output contracts for ll-qa-gate-evaluate
provides:
  - Executable CLI protocol for ll-qa-gate-evaluate skill via run.sh
  - Input validation for all 5 artifacts (2 manifests, 2 settlements, waivers)
  - Output validation for release_gate_input.yaml with gate-specific checks
  - Lifecycle state machine configuration
  - Evidence JSON schema for gate evaluation artifacts
affects:
  - 03-settlement-exec (downstream plans need gate-evaluate executable)
  - 04-api-chain-pilot (requires gate-evaluate skill to run end-to-end)

# Tech tracking
tech-stack:
  added: none
  patterns: Phase 2 shell script pattern (run.sh -> validate_input -> CLI -> validate_output)

key-files:
  created:
    - skills/ll-qa-gate-evaluate/scripts/run.sh
    - skills/ll-qa-gate-evaluate/scripts/validate_input.sh
    - skills/ll-qa-gate-evaluate/scripts/validate_output.sh
    - skills/ll-qa-gate-evaluate/ll.lifecycle.yaml
    - skills/ll-qa-gate-evaluate/evidence/gate-eval.schema.json
  modified: []

key-decisions:
  - "Used force-add for evidence/gate-eval.schema.json since evidence/ is in .gitignore; schema is a tracked definition file, not runtime output"
  - "validate_output.sh uses inline Python for YAML parsing since gate_evaluation is not one of the 4 schema types in qa_schemas.py _VALIDATORS"

patterns-established:
  - "run.sh pattern: parse 5 args -> validate_input.sh -> python -m cli skill -> validate_output.sh"
  - "validate_input.sh: explicit per-file existence checks + schema validation via qa_schemas module"
  - "validate_output.sh: inline Python for custom schema validation when qa_schemas does not cover the type"

requirements-completed: [REQ-03]

# Metrics
duration: 5min
completed: 2026-04-15
---

# Phase 03 Plan 02: ll-qa-gate-evaluate Prompt-first Runtime Infrastructure

**Prompt-first runtime infrastructure for ll-qa-gate-evaluate skill: 3 shell scripts, lifecycle config, and evidence JSON schema**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-14T16:00:00Z
- **Completed:** 2026-04-15T00:10:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created executable CLI protocol (run.sh) that parses 5 input arguments, validates inputs, invokes the gate-evaluate skill, and validates output
- Created input validation script (validate_input.sh) checking all 5 artifact files exist and conform to schemas
- Created output validation script (validate_output.sh) checking gate evaluation structure, final_decision enum, SHA-256 evidence_hash format, and all 7 anti-laziness checks
- Created lifecycle state machine config matching Phase 2 pattern
- Created JSON evidence schema with all required gate evaluation properties

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ll-qa-gate-evaluate scripts** - `d0d8f1c` (feat)
2. **Task 2: Create ll.lifecycle.yaml and evidence schema** - `dd5b1f6` (feat)

## Files Created/Modified
- `skills/ll-qa-gate-evaluate/scripts/run.sh` - Entry point: parses 5 input args, validates, invokes CLI, validates output
- `skills/ll-qa-gate-evaluate/scripts/validate_input.sh` - Validates 5 input files: manifests via `--type manifest`, settlements via `--type settlement`, waivers via yaml.safe_load
- `skills/ll-qa-gate-evaluate/scripts/validate_output.sh` - Validates release_gate_input.yaml: top-level `gate_evaluation` key, `final_decision` enum, `evidence_hash` format, 7 anti_laziness_checks
- `skills/ll-qa-gate-evaluate/ll.lifecycle.yaml` - Lifecycle state machine (draft, validated, executed, frozen)
- `skills/ll-qa-gate-evaluate/evidence/gate-eval.schema.json` - JSON Schema for gate evaluation evidence artifacts

## Decisions Made
- Used force-add (`git add -f`) for evidence schema since `evidence/` is in .gitignore — the schema is a tracked definition file, not runtime-generated output
- validate_output.sh uses inline Python instead of qa_schemas.py since gate_evaluation is not one of the 4 registered schema types

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] evidence/ directory blocked by .gitignore**
- **Found during:** Task 2 (evidence schema creation)
- **Issue:** `skills/ll-qa-gate-evaluate/evidence/` is matched by `.gitignore` line 95 (`evidence/`)
- **Fix:** Used `git add -f` to force-add the schema definition file
- **Files modified:** skills/ll-qa-gate-evaluate/evidence/gate-eval.schema.json
- **Verification:** File added to staging, committed successfully
- **Committed in:** dd5b1f6 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Force-add was necessary for correctness; the schema is a tracked definition, not runtime output. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ll-qa-gate-evaluate skill now has all 6 infrastructure files (3 scripts + lifecycle + evidence schema + existing SKILL.md/ll.contract.yaml/agents)
- Ready for downstream plans that depend on gate-evaluate being executable

---
*Phase: 03-settlement-exec*
*Completed: 2026-04-15*
