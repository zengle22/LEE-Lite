---
phase: 03-settlement-exec
plan: 04
subsystem: testing
tags: [qa-schemas, cli-routing, skill-deprecation, gate-validation]

# Dependency graph
requires:
  - phase: 03-settlement-exec
    provides: Plans 01-03 created new QA skills (settlement, gate-evaluate, render-testset-view)
provides:
  - CLI registration for 3 new skill actions (settlement, gate-evaluate, render-testset-view)
  - Runtime mappings in qa_skill_runtime.py across all 4 mapping dicts
  - Gate output validator (validate_gate) in qa_schemas.py
  - Deprecation notices for legacy ADR-035 skills (ll-test-exec-cli, ll-test-exec-web-e2e)
affects: [03-settlement-exec, 04-api-chain-pilot]

# Tech tracking
tech-stack:
  added: []
  patterns: [QA skill action routing via _QA_SKILL_MAP + 4-dict runtime mapping, gate validation using _require/_enum_check pattern]

key-files:
  created: []
  modified:
    - cli/commands/skill/command.py
    - cli/lib/qa_skill_runtime.py
    - cli/lib/qa_schemas.py
    - skills/ll-test-exec-cli/SKILL.md
    - skills/ll-test-exec-cli/ll.lifecycle.yaml
    - skills/ll-test-exec-web-e2e/SKILL.md
    - skills/ll-test-exec-web-e2e/ll.lifecycle.yaml

key-decisions:
  - "Deprecated skills retain execution files; only SKILL.md and ll.lifecycle.yaml modified"
  - "render-testset-view maps to None in _action_to_schema_type (no schema validation)"

patterns-established:
  - "QA skill registration: ensure() allowlist + _QA_SKILL_MAP entry"
  - "Runtime mapping: extend all 4 dicts (action_to_skill, input_keys, output_keys, _action_to_schema_type) consistently"

requirements-completed: [REQ-03]

# Metrics
duration: ~5min
completed: 2026-04-14
---

# Phase 03 Plan 04: CLI Registration + Gate Validator + Deprecation Summary

**Registered 3 new QA skill actions in CLI handler, added gate output validator, and deprecated 2 legacy ADR-035 skills**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-14T16:14:00Z
- **Completed:** 2026-04-14T16:18:53Z
- **Tasks:** 3 completed
- **Files modified:** 6

## Accomplishments
- CLI handler (`command.py`) now accepts settlement, gate-evaluate, and render-testset-view actions
- `qa_skill_runtime.py` extended with all 4 mapping dicts for the 3 new actions
- `qa_schemas.py` gained `validate_gate()` function with full field validation for release_gate_input.yaml
- Two legacy ADR-035 skills (ll-test-exec-cli, ll-test-exec-web-e2e) marked deprecated with visible notices

## Task Commits

Each task was committed atomically:

1. **Task 1: Register new actions + extend runtime mappings** - `84c1b49` (feat)
2. **Task 2: Add validate_gate() to qa_schemas.py** - `8a8c7ca` (feat)
3. **Task 3: Deprecate legacy skills** - `d279a69` (docs)

## Files Created/Modified
- `cli/commands/skill/command.py` - Added 3 actions to ensure() allowlist and _QA_SKILL_MAP
- `cli/lib/qa_skill_runtime.py` - Extended action_to_skill, input_keys, output_keys, _action_to_schema_type dicts
- `cli/lib/qa_schemas.py` - Added validate_gate() function and "gate" entry in _VALIDATORS
- `skills/ll-test-exec-cli/SKILL.md` - Added deprecation notice in frontmatter and body
- `skills/ll-test-exec-cli/ll.lifecycle.yaml` - Added deprecated fields, changed state
- `skills/ll-test-exec-web-e2e/SKILL.md` - Added deprecation notice in frontmatter and body
- `skills/ll-test-exec-web-e2e/ll.lifecycle.yaml` - Added deprecated fields, changed state

## Decisions Made
- Deprecated skills retain all execution files (scripts, agents, etc.) -- only SKILL.md and ll.lifecycle.yaml modified for backward compatibility
- `render-testset-view` maps to `None` in `_action_to_schema_type` since it produces a view artifact, not a schema-conformant output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 new skill actions registered and verified via Python import tests
- Gate validator tested with sample data passing all field checks
- Legacy skills visibly deprecated without breaking existing functionality
- Phase 03 settlement-exec wave 2 complete; ready for next plan or phase

---
*Phase: 03-settlement-exec*
*Completed: 2026-04-14*
