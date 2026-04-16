---
phase: 03-skill
plan: "03"
type: execute
autonomous: true
wave: 2
depends_on:
  - "03-01"
requirements:
  - REQ-PATCH-03
tags:
  - cli-wrappers
  - agent-prompts
  - ll-experience-patch-settle
dependency_graph:
  requires:
    - "03-01 (skill skeleton + contract files)"
    - "03-02 (settle_runtime.py Python runtime)"
  provides:
    - "CLI entry points for patch-settle skill"
    - "LLM executor prompt for delta/SRC generation"
    - "LLM supervisor prompt for settlement validation"
  affects:
    - "skills/ll-experience-patch-settle/scripts/"
    - "skills/ll-experience-patch-settle/agents/"
tech_stack:
  added: []
  patterns:
    - "bash wrapper with Python json.dumps payload construction (security)"
    - "feat_id regex validation before filesystem operations"
    - "executor/supervisor agent pattern (established ll-* convention)"
key_files:
  created:
    - path: "skills/ll-experience-patch-settle/scripts/run.sh"
      description: "CLI entry wrapper with --feat-id/--workspace/--change-class/--auto-approve args"
    - path: "skills/ll-experience-patch-settle/scripts/validate_input.sh"
      description: "Pre-settlement validation: feat_dir, registry, patch files"
    - path: "skills/ll-experience-patch-settle/scripts/validate_output.sh"
      description: "Post-settlement validation: YAML structure, settlement_report content"
    - path: "skills/ll-experience-patch-settle/agents/executor.md"
      description: "LLM prompt for delta/SRC content generation (134 lines)"
    - path: "skills/ll-experience-patch-settle/agents/supervisor.md"
      description: "LLM validation checklist for settlement output (83 lines)"
  modified: []
decisions:
  - "Followed ll-patch-capture and ll-qa-settlement patterns exactly for consistency"
  - "Used Python json.dumps for JSON payload construction (security per T-03-09)"
  - "Passed file paths via sys.argv to embedded Python (not string interpolation)"
metrics:
  duration: "~5 minutes"
  completed_date: "2026-04-16"
  tasks_completed: 3
  files_created: 5
---

# Phase 3 Plan 3: CLI Wrappers + LLM Agent Prompts Summary

**One-liner:** CLI entry wrappers (run.sh, validate_input.sh, validate_output.sh) and LLM agent prompts (executor.md, supervisor.md) completing the ll-experience-patch-settle skill's executable boundary.

## Tasks Completed

### Task 1: CLI wrapper scripts (run.sh, validate_input.sh, validate_output.sh)

Created 3 shell scripts following the exact patterns from ll-patch-capture and ll-qa-settlement:

- **run.sh** — Entry wrapper accepting `--feat-id`, `--workspace`, `--change-class`, `--auto-approve` arguments. Constructs JSON payload via Python `json.dumps()` (security: avoids bash string interpolation injection). Validates `feat_id` against regex `^[a-zA-Z0-9][a-zA-Z0-9._-]*$` before any filesystem operations. Invokes `python -m cli skill patch-settle` via CLI protocol. Runs validate_input.sh before settlement, validate_output.sh after.
- **validate_input.sh** — Checks feat_dir exists, patch_registry.json exists and is valid JSON, at least one UXPATCH-*.yaml file present.
- **validate_output.sh** — Checks resolved_patches.yaml exists, is valid YAML, has `settlement_report` top-level key with `generated_at`, `total_settled > 0`, and `results` list matching count.

**Commit:** `a963d31`

### Task 2: executor.md agent prompt

Created LLM prompt for generating delta drafts and SRC candidates from grouped pending_backwrite patches. Covers all 3 change_class types:

- **visual** (D-02): retain_in_code — NO delta files generated
- **interaction** (D-03): 3 delta files — ui-spec-delta.yaml (with original_text), flow-spec-delta.yaml (with original_flow), test-impact-draft.yaml (with impacts_user_path)
- **semantic** (D-04): SRC-XXXX__{slug}.yaml candidates with requires_gate_approval: true

Enforces D-05 (no SSOT modification), D-06 (original text quoting), and D-02 (visual = no deltas).

**Commit:** `995b34d`

### Task 3: supervisor.md agent prompt

Created LLM validation checklist with 7 numbered sections covering:

1. Settlement report structure and consistency
2. Action correctness per change_class (retain_in_code, backwritten, upgraded_to_src)
3. Delta file completeness for interaction patches
4. SRC candidate completeness for semantic patches
5. Patch status updates from pending_backwrite to terminal state
6. SSOT integrity (D-05)
7. Escalation conditions (D-10): conflicts, ambiguity, test_impact uncertainty

Defines supervisor_validation YAML output format with pass/fail tracking and escalation support.

**Commit:** `f00d3a5`

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: input_injection | scripts/run.sh | feat_id validated via regex before filesystem operations; JSON payload constructed via Python json.dumps() (T-03-09 mitigation) |
| threat_flag: path_traversal | scripts/run.sh, settle_runtime.py | FEAT directory resolved via path containment check against base_dir |

## Self-Check: PASSED

All 5 files verified present:
- `E:\ai\LEE-Lite-skill-first\skills\ll-experience-patch-settle\scripts\run.sh` — FOUND
- `E:\ai\LEE-Lite-skill-first\skills\ll-experience-patch-settle\scripts\validate_input.sh` — FOUND
- `E:\ai\LEE-Lite-skill-first\skills\ll-experience-patch-settle\scripts\validate_output.sh` — FOUND
- `E:\ai\LEE-Lite-skill-first\skills\ll-experience-patch-settle\agents\executor.md` — FOUND (134 lines)
- `E:\ai\LEE-Lite-skill-first\skills\ll-experience-patch-settle\agents\supervisor.md` — FOUND (83 lines)

All 3 commits verified:
- `a963d31` — feat(03-03): create CLI wrapper scripts
- `995b34d` — feat(03-03): create executor agent prompt
- `f00d3a5` — feat(03-03): create supervisor agent prompt
