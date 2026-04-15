---
phase: 02-design-skills
plan: 05
type: execute
wave: 1
status: complete
---

# Plan 02-05 Summary: ll-qa-api-spec-gen

## Skill Purpose

manifest → api-test-spec compilation. Reads an API coverage manifest, compiles detailed test specifications for each coverage item.

## Infrastructure Files

| File | Path | Status |
|------|------|--------|
| run.sh | `skills/ll-qa-api-spec-gen/scripts/run.sh` | Created |
| validate_input.sh | `skills/ll-qa-api-spec-gen/scripts/validate_input.sh` | Created |
| validate_output.sh | `skills/ll-qa-api-spec-gen/scripts/validate_output.sh` | Created |
| executor.md | `skills/ll-qa-api-spec-gen/agents/executor.md` | Created |
| supervisor.md | `skills/ll-qa-api-spec-gen/agents/supervisor.md` | Created |
| ll.lifecycle.yaml | `skills/ll-qa-api-spec-gen/ll.lifecycle.yaml` | Created |
| evidence schemas | `skills/ll-qa-api-spec-gen/evidence/*.schema.json` | Created (2 files) |

## CLI Registration

Action: `api-spec-gen` in `_QA_SKILL_MAP`

## Pilot Validation

Phase 4 pilot successfully invoked this skill: `api-coverage-manifest.yaml` → 8 `api-test-spec/*.yaml` files (schema: PASS)
