---
phase: "02-patch-skill"
plan: "02"
type: execute
wave: 1
subsystem: ll-patch-capture
tags: [agent-prompts, executor-supervisor, dual-path-routing, patch-yaml]
dependency_graph:
  requires: []
  provides: [REQ-PATCH-02]
  affects: [02-03, 02-04]
tech-stack:
  added: []
  patterns: [executor-supervisor-split, dual-path-routing, four-layer-validation]
key-files:
  created:
    - skills/ll-patch-capture/agents/executor.md
    - skills/ll-patch-capture/agents/supervisor.md
  modified: []
decisions:
  - "Executor outputs YAML only; runtime is sole patch_registry.json writer (prevents double-write corruption)"
  - "Supervisor Layer 1 uses python -m cli.lib.patch_schema for mechanical validation, not LLM judgment"
  - "Auto-pass requires ALL conditions: schema valid + no conflict + confidence high + non-semantic"
  - "Six escalation triggers defined per D-09: schema fail, low confidence, conflict, semantic, first-patch, disputed test_impact"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-16T15:55:00Z"
  tasks_completed: 2
  files_created: 2
  lines_added: 202
---

# Phase 02 Plan 02: Executor & Supervisor Agent Prompts Summary

**One-liner:** Two-agent prompt model for ll-patch-capture skill — Executor generates Patch YAML from user input via dual-path routing, Supervisor validates with four-layer checks and auto-pass/escalate decision logic.

## Objective

Create the Executor and Supervisor Agent prompt files for ll-patch-capture. The Executor generates Patch YAML from user input; the Supervisor validates it and decides whether to auto-pass or escalate to human confirmation. Implements the two-agent model that all 29 governed skills use, adapted for patch capture with dual-path routing and schema validation.

## Tasks Completed

### Task 1: Create Executor Agent prompt (agents/executor.md)

**Commit:** `1cd1a74`
**File:** `skills/ll-patch-capture/agents/executor.md` (113 lines)

Created the Executor Agent prompt with:
- **Dual-path routing**: Prompt-to-Patch (free-form text to YAML) and Document-to-SRC (structured document delegation to ll-product-raw-to-src)
- **ADR-049 section 2.4 decision tree**: Three-gate classification for change_class (visual/interaction/semantic)
- **All enum values inlined**: PatchStatus, ChangeClass, Severity, SourceActor, BackwriteStatus from cli/lib/patch_schema.py
- **Complete field specifications**: Required and optional fields per ssot/schemas/qa/patch.yaml
- **test_impact pre-fill rules**: interaction/semantic default to true; visual defaults to false
- **backwrite_targets mapping**: Per ADR-049 section 4.4 (visual, interaction, semantic targets)
- **Critical constraint**: Python runtime is sole patch_registry.json writer — Executor only produces YAML output

### Task 2: Create Supervisor Agent prompt (agents/supervisor.md)

**Commit:** `c1379c3`
**File:** `skills/ll-patch-capture/agents/supervisor.md` (89 lines)

Created the Supervisor Agent prompt with:
- **Layer 1 (Mechanical)**: Calls `python -m cli.lib.patch_schema --type patch <file>` for schema validation
- **Layer 2 (Semantic)**: 9-item validation checklist (schema, required fields, source, scope, change_class, status, enum values, timestamps, test_impact)
- **Layer 3 (Conflict Detection)**: Scans existing active patches for overlapping changed_files and same-target conflicts
- **Layer 4 (Escalation Decision)**: Auto-pass requires ALL conditions; ANY of 6 triggers causes escalation
- **Auto-pass Action**: Confirms registry update, emits success notification
- **Escalation Action**: Sets draft status, presents structured review checklist, waits for human decision

## Decisions Made

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Executor outputs YAML only; runtime writes registry | Prevents double-write corruption (from .continue-here.md constraint) | Implemented |
| Layer 1 uses Python validator, not LLM | Mechanical check is authoritative for schema compliance | Implemented |
| Auto-pass requires all conditions | Prevents invalid patches from auto-registering (T-02-06 mitigation) | Implemented |
| First-patch-for-FEAT triggers escalation | Inaugural patches warrant human review | Implemented |

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. Both agent prompts are complete with full instructions, no placeholder values.

## Threat Flags

All threats from the plan's threat_model are mitigated in implementation:

| Threat ID | Category | Mitigation |
|-----------|----------|------------|
| T-02-05 | Tampering | Supervisor Layer 1 calls Python `validate_file()` — mechanical check, not LLM judgment |
| T-02-06 | Elevation of Privilege | Auto-pass requires ALL conditions (schema valid + no conflict + confidence high + non-semantic) |
| T-02-07 | Repudiation | CLI protocol `request_id` logged in source.session field; Supervisor validation results recorded |

## Commits

- `1cd1a74`: feat(02-02): create Executor Agent prompt for ll-patch-capture
- `c1379c3`: feat(02-02): create Supervisor Agent prompt for ll-patch-capture

## Self-Check

### Created files
- FOUND: skills/ll-patch-capture/agents/executor.md (113 lines)
- FOUND: skills/ll-patch-capture/agents/supervisor.md (89 lines)

### Commits
- FOUND: 1cd1a74 (executor.md)
- FOUND: c1379c3 (supervisor.md)

### Acceptance criteria (executor.md)
- PASS: Contains "# Executor Agent: ll-patch-capture" heading
- PASS: Contains "## Role" section
- PASS: Contains "## Instructions" section with 4+ numbered steps
- PASS: Contains change_class enum values: "visual", "interaction", "semantic"
- PASS: Contains "human_confirmed_class" instruction (must never be null)
- PASS: Contains "patch_registry.json" reference (runtime sole writer)
- PASS: Contains "UXPATCH-NNNN" format specification
- PASS: Contains ADR-049 section 2.4 decision tree reference
- PASS: Contains test_impact pre-fill rules
- PASS: Contains backwrite_targets mapping per ADR-049 section 4.4
- PASS: Minimum 30 lines (113 lines)

### Acceptance criteria (supervisor.md)
- PASS: Contains "# Supervisor Agent: ll-patch-capture" heading
- PASS: Contains "## Role" section
- PASS: Contains "## Validation Protocol" section
- PASS: Contains "Layer 1: Mechanical Schema Validation" with python command
- PASS: Contains "Layer 2: Semantic Validation Checklist" with 9 items (>= 5 required)
- PASS: Contains "Layer 3: Conflict Detection" with file overlap scanning
- PASS: Contains "Layer 4: Escalation Decision" section
- PASS: Contains Auto-pass conditions
- PASS: Contains Escalation triggers (6 triggers)
- PASS: Contains Auto-pass Action and Escalation Action sections
- PASS: Minimum 30 lines (89 lines)

## Self-Check: PASSED
