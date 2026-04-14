---
phase: 03-settlement-exec
plan: 01
type: execute
wave: 1
status: complete
---

# Plan 03-01 Summary: ll-qa-settlement Prompt-first Runtime Infrastructure

## Objective

Add Prompt-first runtime infrastructure to the `ll-qa-settlement` skill, creating 5 standard infrastructure files that make it executable via the CLI protocol established in Phase 2.

## Tasks Completed

### Task 1: Create runtime scripts (3 files)

**Commit:** `3236b46` — feat(settlement): add runtime scripts for ll-qa-settlement skill

| File | Purpose |
|------|---------|
| `skills/ll-qa-settlement/scripts/run.sh` | Entry point — parses `--manifest-path`, `--chain`, `--output-dir`, `--workspace` args; validates input; invokes `python -m cli skill settlement`; validates output |
| `skills/ll-qa-settlement/scripts/validate_input.sh` | Input validation — checks manifest file existence and validates against manifest schema via `qa_schemas.py` |
| `skills/ll-qa-settlement/scripts/validate_output.sh` | Output validation — checks settlement report file existence and validates against settlement schema via `qa_schemas.py` |

### Task 2: Create lifecycle and evidence schema (2 files)

**Commit:** `ea787be` — feat(settlement): add lifecycle state machine and evidence schema

| File | Purpose |
|------|---------|
| `skills/ll-qa-settlement/ll.lifecycle.yaml` | Lifecycle state machine with states: draft, validated, executed, frozen |
| `skills/ll-qa-settlement/evidence/settlement.schema.json` | JSON Schema defining settlement evidence artifacts (chain, manifest_path, settlement_report_path, generated_at, summary stats, gap_list, waiver_list) |

## Verification Results

- All 3 scripts pass `bash -n` syntax check
- `settlement.schema.json` validates as correct JSON
- All scripts follow Phase 2 reference patterns (matched against `ll-qa-feat-to-apiplan`, `ll-qa-api-manifest-init`, `ll-qa-api-spec-gen`)
- All scripts are executable (`chmod +x`)

## Acceptance Criteria Met

- [x] `scripts/run.sh` contains `set -euo pipefail`
- [x] `scripts/run.sh` contains `--manifest-path` argument parsing
- [x] `scripts/run.sh` contains `--chain` argument parsing with default `api`
- [x] `scripts/run.sh` contains `python -m cli skill settlement`
- [x] `scripts/run.sh` calls `validate_input.sh` before CLI invocation
- [x] `scripts/run.sh` calls `validate_output.sh` after CLI invocation
- [x] `scripts/validate_input.sh` calls `python -m cli.lib.qa_schemas --type manifest`
- [x] `scripts/validate_output.sh` calls `python -m cli.lib.qa_schemas --type settlement`
- [x] All 3 scripts pass `bash -n` syntax check
- [x] `ll.lifecycle.yaml` contains `skill: ll-qa-settlement` with correct lifecycle states
- [x] `evidence/settlement.schema.json` is valid JSON with `chain` in required properties
