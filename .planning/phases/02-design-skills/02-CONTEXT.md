# Phase 2: ADR-047 设计层技能补全 - Context

**Gathered:** 2026-04-15
**Status:** Complete — all 6 skills have Prompt-first runtime infrastructure
**Source:** ROADMAP.md + ADR-047 + existing skill directories

<domain>
## Phase Boundary

Phase 2 delivers 6 design-layer skills with full Prompt-first runtime infrastructure:

1. `ll-qa-feat-to-apiplan` — feat → api-test-plan + manifest draft
2. `ll-qa-prototype-to-e2eplan` — prototype → e2e-journey-plan + manifest draft
3. `ll-qa-api-manifest-init` — plan → coverage manifest initialization
4. `ll-qa-e2e-manifest-init` — plan → coverage manifest initialization
5. `ll-qa-api-spec-gen` — manifest → api-test-spec compilation
6. `ll-qa-e2e-spec-gen` — manifest → e2e-journey-spec compilation

Each skill gets:
- `scripts/run.sh` — Claude Code sub-agent invocation wrapper
- `scripts/validate_input.sh` — input file existence and schema validation
- `scripts/validate_output.sh` — output schema validation via Phase 1 qa_schemas
- `agents/executor.md` — LLM prompt template (input/output format)
- `evidence/*` — evidence schema files
- `ll.lifecycle.yaml` — lifecycle configuration

</domain>

<shared_runtime>
## Shared Runtime

- `cli/lib/qa_skill_runtime.py` — shared Python runtime for all 6 skills
- `cli/lib/qa_schemas.py` — Phase 1 schema validator (validate_plan, validate_manifest, validate_spec)

</shared_runtime>

<cli_registration>
## CLI Registration

All 6 skills registered as CLI actions via `_QA_SKILL_MAP`:
- `feat-to-apiplan`
- `prototype-to-e2eplan`
- `api-manifest-init`
- `e2e-manifest-init`
- `api-spec-gen`
- `e2e-spec-gen`

</cli_registration>

<verification>
## Verification

All 6 skills validated by Phase 4 pilot run:
- `ll-qa-feat-to-apiplan` produced valid `api-test-plan.yaml` (schema: PASS)
- `ll-qa-api-manifest-init` produced valid `api-coverage-manifest.yaml` (schema: PASS)
- `ll-qa-api-spec-gen` produced 8 valid `api-test-spec/*.yaml` files (schema: PASS)

</verification>
