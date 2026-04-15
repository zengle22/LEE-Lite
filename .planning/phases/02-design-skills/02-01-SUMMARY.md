---
phase: 02-design-skills
plan: 01
type: execute
wave: 1
status: complete
---

# Plan 02-01 Summary: ll-qa-feat-to-apiplan

## Skill Purpose

feat → api-test-plan + manifest draft. Reads a minimal feat YAML, produces an API test plan with object/capability decomposition and priority assignment.

## Infrastructure Files

| File | Path | Status |
|------|------|--------|
| run.sh | `skills/ll-qa-feat-to-apiplan/scripts/run.sh` | Created |
| validate_input.sh | `skills/ll-qa-feat-to-apiplan/scripts/validate_input.sh` | Created |
| validate_output.sh | `skills/ll-qa-feat-to-apiplan/scripts/validate_output.sh` | Created |
| executor.md | `skills/ll-qa-feat-to-apiplan/agents/executor.md` | Created |
| supervisor.md | `skills/ll-qa-feat-to-apiplan/agents/supervisor.md` | Created |
| ll.lifecycle.yaml | `skills/ll-qa-feat-to-apiplan/ll.lifecycle.yaml` | Created |
| evidence schemas | `skills/ll-qa-feat-to-apiplan/evidence/*.schema.json` | Created (2 files) |

## CLI Registration

Action: `feat-to-apiplan` in `_QA_SKILL_MAP`

## Pilot Validation

Phase 4 pilot successfully invoked this skill: `feat-pilot.yaml` → `api-test-plan.yaml` (schema: PASS)
