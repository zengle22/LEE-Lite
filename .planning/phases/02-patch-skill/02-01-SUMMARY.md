---
phase: "02-patch-skill"
plan: "01"
subsystem: skill-skeleton
tags: [adr-049, experience-patch, skill-skeleton, yaml-contracts, semantic-checklists]

# Dependency graph
requires:
  - phase: "01-patch-schema"
    provides: "Patch YAML schema at ssot/schemas/qa/patch.yaml, ADR-049 frozen design"
provides:
  - "ll-patch-capture skill skeleton with 7 files"
  - "Dual-path execution protocol (Prompt-to-Patch + Document-to-SRC)"
  - "Input/output contract boundaries with semantic checklists"
  - "Lifecycle state machine definition (6 states)"
affects: ["agent-prompts", "cli-registration", "patch-runtime", "patch-settlement"]

# Tech tracking
tech-stack:
  added: []
  patterns: ["ll-qa-settlement template replication for skill skeletons", "input/output contract pattern", "semantic checklist pattern"]

key-files:
  created:
    - "skills/ll-patch-capture/SKILL.md"
    - "skills/ll-patch-capture/ll.contract.yaml"
    - "skills/ll-patch-capture/ll.lifecycle.yaml"
    - "skills/ll-patch-capture/input/contract.yaml"
    - "skills/ll-patch-capture/input/semantic-checklist.md"
    - "skills/ll-patch-capture/output/contract.yaml"
    - "skills/ll-patch-capture/output/semantic-checklist.md"
  modified: []

key-decisions:
  - "Followed ll-qa-settlement skeleton pattern exactly for consistency with 29 existing skills"
  - "Lifecycle states adapted from PatchStatus enum (patch_schema.py) rather than qa-settlement states"

patterns-established:
  - "Skill skeleton: SKILL.md + ll.contract.yaml + ll.lifecycle.yaml + input/ + output/ contracts"
  - "Dual-path routing documented in SKILL.md Execution Protocol"

requirements-completed: [REQ-PATCH-02]

# Metrics
duration: 12min
completed: 2026-04-16
---

# Phase 02 Plan 01: ll-patch-capture Skill Skeleton Summary

**ADR-049 governed skill skeleton with dual-path execution protocol, contract boundaries, and semantic checklists -- 7 files following ll-qa-settlement template pattern**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-16T08:00:00Z
- **Completed:** 2026-04-16T08:12:00Z
- **Tasks:** 3
- **Files created:** 7

## Accomplishments
- Created ll-patch-capture skill directory with complete skeleton (7 files)
- SKILL.md (88 lines) documents dual-path execution: Prompt-to-Patch for small UX changes, Document-to-SRC for large changes
- ll.contract.yaml references ADR-049 with experience category and patch-capture chain
- ll.lifecycle.yaml defines 6 patch-appropriate states matching PatchStatus enum
- Input/output contracts define clear boundaries with feat_id, input_type classification, and patch registry update requirements
- Semantic checklists provide 6 input and 11 output human-verifiable items

## Task Commits

Each task was committed atomically:

1. **Task 1: Create skill metadata and lifecycle files** - `ccdc1c2` (feat)
2. **Task 2: Create SKILL.md with dual-path execution protocol** - `289623d` (feat)
3. **Task 3: Create input/output contracts and semantic checklists** - `4219405` (feat)

## Files Created/Modified
- `skills/ll-patch-capture/SKILL.md` - Skill entry point with dual-path execution protocol (88 lines)
- `skills/ll-patch-capture/ll.contract.yaml` - Skill metadata (adr: ADR-049, category: experience)
- `skills/ll-patch-capture/ll.lifecycle.yaml` - Lifecycle state machine (6 states)
- `skills/ll-patch-capture/input/contract.yaml` - Input schema (feat_id, input_type, input_value)
- `skills/ll-patch-capture/input/semantic-checklist.md` - 6 input validation items
- `skills/ll-patch-capture/output/contract.yaml` - Output schema referencing patch.yaml and registry
- `skills/ll-patch-capture/output/semantic-checklist.md` - 11 output validation items

## Decisions Made
- Followed ll-qa-settlement skeleton pattern exactly for consistency across all 29+ skills
- Lifecycle states adapted from PatchStatus enum in cli/lib/patch_schema.py (draft, active, validated, pending_backwrite, resolved, archived) rather than qa-settlement's draft/validated/executed/frozen

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Skill skeleton ready for downstream plans: agent prompts (executor.md, supervisor.md already exist), runtime integration, CLI registration
- Pre-existing agents/executor.md and agents/supervisor.md files present in directory (from prior plan)

---
*Phase: 02-patch-skill*
*Completed: 2026-04-16*

## Self-Check: PASSED
