---
phase: 02-design-skills
plan: 06
type: execute
wave: 1
status: complete
---

# Plan 02-06 Summary: ll-qa-e2e-spec-gen

## Skill Purpose

manifest → e2e-journey-spec compilation. Reads an E2E coverage manifest, compiles detailed E2E journey specifications for each coverage item.

## Infrastructure Files

| File | Path | Status |
|------|------|--------|
| run.sh | `skills/ll-qa-e2e-spec-gen/scripts/run.sh` | Created |
| validate_input.sh | `skills/ll-qa-e2e-spec-gen/scripts/validate_input.sh` | Created |
| validate_output.sh | `skills/ll-qa-e2e-spec-gen/scripts/validate_output.sh` | Created |
| executor.md | `skills/ll-qa-e2e-spec-gen/agents/executor.md` | Created |
| supervisor.md | `skills/ll-qa-e2e-spec-gen/agents/supervisor.md` | Created |
| ll.lifecycle.yaml | `skills/ll-qa-e2e-spec-gen/ll.lifecycle.yaml` | Created |
| evidence schemas | `skills/ll-qa-e2e-spec-gen/evidence/*.schema.json` | Created (2 files) |

## CLI Registration

Action: `e2e-spec-gen` in `_QA_SKILL_MAP`
