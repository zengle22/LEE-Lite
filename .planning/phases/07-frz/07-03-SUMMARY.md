---
phase: 07-frz
plan: 03
subsystem: cli
tags: [frz, msc-validation, cli, argparse, yaml, adr-050]

# Dependency graph
requires:
  - phase: 07-01
    provides: FRZ schema definitions, MSCValidator, FRZPackage dataclass
  - phase: 07-02
    provides: FRZ registry persistence, anchor registry, error types
provides:
  - ll-frz-manage skill with complete directory structure (12 files)
  - Python CLI runtime with validate/freeze/list/extract subcommands
  - 20 integration tests (all passing)
  - Shell validation scripts (validate_input.sh, validate_output.sh)
  - Agent instructions (executor, supervisor)
affects: [Phase 08 semantic extraction, Phase 10 Task Pack scheduling]

# Tech tracking
tech-stack:
  added: [argparse, yaml (PyYAML), shutil]
  patterns: [workspace root discovery, YAML-safe deserialization, MSC validation gate before freeze, atomic registry writes]

key-files:
  created:
    - skills/ll-frz-manage/SKILL.md
    - skills/ll-frz-manage/scripts/frz_manage_runtime.py
    - skills/ll-frz-manage/scripts/test_frz_manage_runtime.py
    - skills/ll-frz-manage/scripts/validate_input.sh
    - skills/ll-frz-manage/scripts/validate_output.sh
  modified: []

key-decisions:
  - "Added sys.path injection in frz_manage_runtime.py for workspace-root-relative cli.lib imports when script runs standalone"
  - "Tests use patch('frz_manage_runtime.Path.cwd') for workspace isolation instead of monkey-patching registry paths"
  - "Extract mode stubbed as Phase 8 deferred — prints error and returns exit code 1"

patterns-established:
  - "Skill template pattern: ll.contract.yaml, ll.lifecycle.yaml, input/output contracts, semantic checklists, agent instructions"
  - "MSC validation gate: freeze_frz explicitly validates before registration — cannot bypass"
  - "Evidence trail: freeze copies source documents to artifacts/frz-input/{ID}/input/"

requirements-completed:
  - FRZ-04
  - FRZ-05
  - FRZ-06

# Metrics
duration: 25min
completed: 2026-04-18
---

# Phase 07 Plan 03: ll-frz-manage Skill Summary

**User-facing FRZ management CLI with MSC validation gate, freeze registry operations, and complete skill structure following ll-patch-capture template**

## Performance

- **Duration:** 25 min
- **Started:** 2026-04-18T10:00:00Z
- **Completed:** 2026-04-18T10:25:00Z
- **Tasks:** 3
- **Files modified:** 13 (new files created)

## Accomplishments
- Complete `skills/ll-frz-manage/` directory with 12 files following ll-patch-capture template
- `frz_manage_runtime.py` CLI with validate/freeze/list/extract subcommands integrating with cli.lib (frz_schema, frz_registry, anchor_registry)
- 20 integration tests covering all command functions, edge cases, and security scenarios — all passing
- Shell validation scripts for input/output verification
- Agent instructions for executor and supervisor roles

## Task Commits

Each task was committed atomically:

1. **Task 1: Create skill structure** - `b19601f` (feat)
   - SKILL.md, contracts, lifecycle, semantic checklists, agent docs, shell scripts
2. **Task 2: Create CLI runtime** - `b22a159` (feat)
   - frz_manage_runtime.py with validate/freeze/list/extract commands
3. **Task 3: Create integration tests** - `cb409ab` (test)
   - 20 pytest tests covering all commands and edge cases

**Plan metadata commit:** pending (docs: complete plan)

## Files Created/Modified
- `skills/ll-frz-manage/SKILL.md` - Skill description with execution protocol for validate/freeze/list/extract
- `skills/ll-frz-manage/ll.contract.yaml` - Skill metadata referencing ADR-050
- `skills/ll-frz-manage/ll.lifecycle.yaml` - Lifecycle states: draft, validated, frozen, superseded, archived
- `skills/ll-frz-manage/input/contract.yaml` - Input contract for validate/freeze/list
- `skills/ll-frz-manage/output/contract.yaml` - Output contract defining expected artifacts
- `skills/ll-frz-manage/input/semantic-checklist.md` - 5-item input checklist (one per MSC dimension)
- `skills/ll-frz-manage/output/semantic-checklist.md` - 5-item output validation checklist
- `skills/ll-frz-manage/agents/executor.md` - Executor agent instructions
- `skills/ll-frz-manage/agents/supervisor.md` - Supervisor agent validation steps
- `skills/ll-frz-manage/scripts/validate_input.sh` - Shell input validation
- `skills/ll-frz-manage/scripts/validate_output.sh` - Shell output validation with MSC check
- `skills/ll-frz-manage/scripts/frz_manage_runtime.py` - Python CLI runtime (506 lines)
- `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py` - Integration test suite (20 tests)

## Decisions Made
- sys.path injection for workspace root needed because frz_manage_runtime.py runs as standalone script outside Python package context
- Tests patch Path.cwd() for workspace root discovery isolation rather than passing explicit workspace paths
- FRZ YAML saved as `.yaml` (not `.json`) to maintain consistency with upstream schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added sys.path injection for cli.lib imports**
- **Found during:** Task 2 (frz_manage_runtime.py standalone execution)
- **Issue:** Running `python skills/ll-frz-manage/scripts/frz_manage_runtime.py` failed with ModuleNotFoundError for `cli.lib` imports because workspace root not on sys.path
- **Fix:** Added workspace root detection from `__file__` path and sys.path.insert at module load
- **Files modified:** `skills/ll-frz-manage/scripts/frz_manage_runtime.py`
- **Verification:** `python frz_manage_runtime.py --help` works from script directory
- **Committed in:** `b22a159` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test import paths for pytest collection**
- **Found during:** Task 3 (test execution)
- **Issue:** Tests used `from scripts.frz_manage_runtime import ...` which fails when pytest runs from project root — `scripts` is not a Python package
- **Fix:** Changed imports to `from frz_manage_runtime import ...` and added both SCRIPT_DIR and WORKSPACE_ROOT to sys.path. Also fixed all `patch("scripts.frz_manage_runtime.Path.cwd", ...)` to `patch("frz_manage_runtime.Path.cwd", ...)`
- **Files modified:** `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py`
- **Verification:** `pytest ... -v` collects and runs all 20 tests
- **Committed in:** `cb409ab` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes required for correct module resolution. No scope creep.

## Issues Encountered
- Windows-specific worktree branch base mismatch: `git reset --soft ad9eb6c` applied before execution to ensure correct commit base
- pytest collection failed initially due to import path mismatch between standalone script execution and package-relative imports — resolved by adding both directories to sys.path

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FRZ infrastructure complete: schema (07-01), registry (07-02), CLI skill (07-03)
- Ready for Phase 08: Semantic extraction chain (FRZ -> SRC -> EPIC -> FEAT)
- Extract mode stubbed — will be implemented when Phase 08 begins

---
*Phase: 07-frz*
*Completed: 2026-04-18*

## Self-Check: PASSED

All 14 created files verified present. All 3 task commits (b19601f, b22a159, cb409ab) verified in git log.
