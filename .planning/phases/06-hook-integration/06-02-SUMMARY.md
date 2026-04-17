---
phase: 6
plan: "06-02"
name: "CLAUDE.md rules update + experience-patches directory + template"
type: execute
subsystem: hook-integration
tags: [patch-awareness, claude-md, experience-patch, adr-049]
dependency:
  requires: [phase-5-patch-awareness-skill]
  provides: [patch-context-rules, patch-template, patch-directory]
  affects: [CLAUDE.md, ssot/experience-patches/]
tech-stack:
  added: []
  patterns: [declarative-rules, yaml-template]
key-files:
  created:
    - CLAUDE.md
    - ssot/experience-patches/.gitkeep
    - ssot/experience-patches/TEMPLATE.yaml
  modified: []
decisions:
  - "CLAUDE.md did not exist at base commit, created fresh with ADR-049 section"
  - "Worktree branch reset from cb6a11a to d224ba3 to match correct base commit"
metrics:
  tasks_completed: 2
  tasks_total: 2
  duration: "~15min"
  completed_at: "2026-04-17T20:55:00Z"
---

# Phase 6 Plan 02: CLAUDE.md rules update + experience-patches directory + template

## One-liner

Added ADR-049 patch context injection and auto-registration rules to CLAUDE.md, created experience-patches directory structure with full YAML template matching ADR-049 §5.3 schema.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Update CLAUDE.md with patch injection + auto-registration rules | `fe343ec` | `CLAUDE.md` (created) |
| 2 | Create experience-patches directory with template | `20dd6ab` | `ssot/experience-patches/.gitkeep`, `ssot/experience-patches/TEMPLATE.yaml` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree branch mismatch**
- **Found during:** Task 1
- **Issue:** `git merge-base HEAD d224ba3` returned `cb6a11a` instead of `d224ba3`, worktree was based on wrong commit
- **Fix:** Reset worktree branch to `d224ba3` (correct base per execution_context)
- **Files modified:** git branch state

**2. [Rule 3 - Blocking] CLAUDE.md did not exist at target base commit**
- **Found during:** Task 1
- **Issue:** Plan said "append to CLAUDE.md" but CLAUDE.md did not exist in the repo at `d224ba3`
- **Fix:** Created CLAUDE.md as new file with ADR-049 section (equivalent to appending to empty file)
- **Files modified:** `CLAUDE.md` (created)

None — plan executed as written after deviations handled.

## Commits

- `fe343ec`: docs(06-02): add ADR-049 patch context rules to CLAUDE.md
- `20dd6ab`: chore(06-02): create experience-patches directory and YAML template

## Self-Check: PASSED
