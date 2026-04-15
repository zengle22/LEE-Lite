---
phase: "05"
plan: 02
type: execute
subsystem: generation-layer
tags: [spec-to-tests, pytest, evidence-collection, ADR-047]

dependency_graph:
  requires:
    - phase-05-plan-01 (qa_schemas.py spec validation infrastructure)
    - skills/ll-qa-api-spec-gen (Phase 2 skeleton pattern reference)
  provides:
    - Complete ll-qa-api-spec-to-tests skill (14 files)
    - executor.md prompt for spec-to-pytest generation
    - supervisor.md validation checklist
  affects:
    - downstream: ll-qa-api-test-exec (Plan 05-03)
    - upstream: ll-qa-api-spec-gen (generates specs this skill consumes)

tech_stack:
  added: []
  patterns:
    - Prompt-first LLM execution (Phase 2 pattern)
    - Input/output contract YAML files
    - Shell script validation pipeline
    - JSON Schema for evidence records
  key_files_created:
    - skills/ll-qa-api-spec-to-tests/SKILL.md
    - skills/ll-qa-api-spec-to-tests/ll.lifecycle.yaml
    - skills/ll-qa-api-spec-to-tests/ll.contract.yaml
    - skills/ll-qa-api-spec-to-tests/input/contract.yaml
    - skills/ll-qa-api-spec-to-tests/input/semantic-checklist.md
    - skills/ll-qa-api-spec-to-tests/output/contract.yaml
    - skills/ll-qa-api-spec-to-tests/output/semantic-checklist.md
    - skills/ll-qa-api-spec-to-tests/scripts/run.sh
    - skills/ll-qa-api-spec-to-tests/scripts/validate_input.sh
    - skills/ll-qa-api-spec-to-tests/scripts/validate_output.sh
    - skills/ll-qa-api-spec-to-tests/evidence/execution-evidence.schema.json
    - skills/ll-qa-api-spec-to-tests/evidence/supervision-evidence.schema.json
    - skills/ll-qa-api-spec-to-tests/agents/executor.md
    - skills/ll-qa-api-spec-to-tests/agents/supervisor.md

key_files:
  created: 14
  modified: 0

decisions:
  - "Followed Phase 2 skeleton pattern from ll-qa-api-spec-gen verbatim for directory structure and shell script protocols"
  - "validate_input.sh calls qa_schemas --type spec for schema validation (not custom validation)"
  - "validate_output.sh uses py_compile on all generated .py files (plan spec requires this)"
  - "executor.md includes evidence_record dict template with run_id-scoped output path to prevent collision"
  - "supervisor.md has 17-item checklist (7 more than plan minimum) for thorough validation"

metrics:
  duration_minutes: 2
  completed_date: "2026-04-15T16:39:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 14
---

# Phase 5 Plan 02: ll-qa-api-spec-to-tests Generation Skill Summary

One-liner: Created `ll-qa-api-spec-to-tests` Prompt-first generation skill (14 files) that converts frozen api-test-spec YAML into executable pytest test scripts with embedded ADR-047 §6.3 evidence collection.

## Tasks Completed

| # | Task | Type | Commit | Files Created |
|---|------|------|--------|---------------|
| 1 | Create skill skeleton (12 files) | auto | `1d32094` | SKILL.md, ll.lifecycle.yaml, ll.contract.yaml, input/*, output/*, scripts/*, evidence/* |
| 2 | Create executor.md and supervisor.md | auto | `9e104a1` | agents/executor.md (80 lines), agents/supervisor.md (43 lines) |

## Task 1: Skill Skeleton

Created 12-file skeleton following Phase 2 pattern from `skills/ll-qa-api-spec-gen/`:

- **SKILL.md**: Full skill description with execution protocol, workflow boundary, non-negotiable rules
- **ll.lifecycle.yaml**: 4-state lifecycle (draft → validated → executed → frozen)
- **ll.contract.yaml**: Skill metadata (category: generation, chain: api, phase: 5)
- **input/contract.yaml**: Input contract defining api-test-spec YAML structure
- **input/semantic-checklist.md**: 9-item input validation checklist
- **output/contract.yaml**: Output contract defining generated pytest file structure and evidence format
- **output/semantic-checklist.md**: 10-item output validation checklist
- **scripts/run.sh**: Entry point with --spec-path, --output-dir, --workspace args; calls validate_input.sh, invokes qa_skill_runtime, calls validate_output.sh
- **scripts/validate_input.sh**: Runs `python -m cli.lib.qa_schemas --type spec` on input spec
- **scripts/validate_output.sh**: Finds all .py files in output dir, runs `python -m py_compile` on each
- **evidence/execution-evidence.schema.json**: JSON schema for skill execution evidence
- **evidence/supervision-evidence.schema.json**: JSON schema for supervisor validation evidence

## Task 2: LLM Agent Prompts

- **agents/executor.md** (80 lines): Complete LLM prompt for spec-to-pytest generation with:
  - Detailed evidence_record dict construction template
  - yaml.safe_dump evidence writing with run_id-scoped directory
  - try/except error handling that writes evidence on failure
  - Anti-false-pass guarantees
  - 15 mentions of "evidence", 3 mentions of "evidence_record", 2 mentions of "run_id"

- **agents/supervisor.md** (43 lines): 17-item validation checklist covering:
  - File existence and py_compile validation
  - Import verification (pytest, yaml, pathlib)
  - Evidence structure validation (evidence_record, yaml.safe_dump, run_id path)
  - Frozen spec integrity (no modification of input spec)
  - Error handling verification
  - Assertion coverage (response_assertions, side_effect_assertions)

## Acceptance Criteria Verification

All 7 acceptance criteria passed:

- [x] `ls skills/ll-qa-api-spec-to-tests/` shows SKILL.md, ll.lifecycle.yaml, ll.contract.yaml, input/, output/, agents/, scripts/, evidence/
- [x] `grep "ll-qa-api-spec-to-tests"` in ll.lifecycle.yaml returns 1 match
- [x] `grep "generation"` in ll.contract.yaml returns 1 match
- [x] `grep "qa_schemas"` in validate_input.sh returns 1 match
- [x] `grep "py_compile"` in validate_output.sh returns 2 matches
- [x] `grep "--type spec"` in validate_input.sh returns 1 match
- [x] `find skills/ll-qa-api-spec-to-tests -type f | wc -l` outputs 14 (>= 12)

Agent criteria:
- [x] `grep "evidence_record"` in executor.md returns 3 matches (>= 2)
- [x] `grep "yaml.safe_dump"` in executor.md returns 1 match (>= 1)
- [x] `grep "run_id"` in executor.md returns 2 matches (>= 2)
- [x] `grep "py_compile"` in supervisor.md returns 1 match (>= 1)
- [x] `grep "evidence_required"` in supervisor.md returns 1 match (>= 1)
- [x] `grep "api-test-spec"` in executor.md returns 2 matches (>= 2)
- [x] `wc -l executor.md` outputs 80 (>= 20)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. All files are complete with full content (no TODOs, no placeholder text).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag:injection | skills/ll-qa-api-spec-to-tests/scripts/validate_input.sh | Untrusted spec YAML flows into LLM prompt; mitigated by qa_schemas validation before execution |
| threat_flag:tampering | skills/ll-qa-api-spec-to-tests/scripts/validate_output.sh | LLM-generated Python written to filesystem; mitigated by py_compile and supervisor checklist |

## Self-Check: PASSED

All 14 files exist in skills/ll-qa-api-spec-to-tests/. Both commits (1d32094, 9e104a1) verified in git log.
