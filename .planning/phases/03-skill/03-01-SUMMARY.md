---
plan: "03-01"
phase: "03-skill"
status: complete
completed_at: "2026-04-16T22:50:00Z"
---

# Plan 03-01 Summary: Skill Skeleton

## What was built

Created 7 skeleton files for `ll-experience-patch-settle` following the `ll-patch-capture` pattern:

- `SKILL.md` — Settlement skill overview with backwrite mapping, escalation conditions, workflow boundaries
- `ll.contract.yaml` — Skill metadata (chain: patch-settle, phase: settlement)
- `ll.lifecycle.yaml` — 8 lifecycle states including retain_in_code, upgraded_to_src, backwritten
- `input/contract.yaml` — feat_id + workspace required inputs, change_class_filter optional
- `output/contract.yaml` — resolved_patches.yaml, delta files, SRC candidates, integrity constraints
- `input/semantic-checklist.md` — 8 pre-settlement validation items
- `output/semantic-checklist.md` — 13 post-settlement validation items

## Key decisions

- Independent skill per D-01 (not extending ll-qa-settlement)
- Lifecycle states include all settlement-relevant states from ADR-049 Section 6.1

## Acceptance criteria

- [x] All 7 files exist
- [x] SKILL.md contains "ll-experience-patch-settle", "ADR-049", "pending_backwrite"
- [x] ll.contract.yaml contains skill: ll-experience-patch-settle and chain: patch-settle
- [x] ll.lifecycle.yaml contains retain_in_code and upgraded_to_src
- [x] input/contract.yaml contains feat_id and workspace as required fields
- [x] output/contract.yaml contains resolved_patches.yaml and delta file references
- [x] No references to extending ll-qa-settlement

## Commits

- 2972d85 feat(03-01): create ll-experience-patch-settle skill skeleton
