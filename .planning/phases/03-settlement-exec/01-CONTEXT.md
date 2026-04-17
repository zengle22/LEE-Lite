# Phase 3: 结算层技能 + 兼容层 - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** ROADMAP.md + ADR-047 + existing skill artifacts

<domain>
## Phase Boundary

Phase 3 delivers 3 skills with full Prompt-first runtime infrastructure (scripts/run.sh, validate_input.sh, validate_output.sh, agents/executor.md, evidence/*, ll.lifecycle.yaml) and marks 2 old testset-driven skills as deprecated:

**In scope (new/upgrade):**
1. `ll-qa-settlement` — reads executed manifests → generates api/e2e settlement reports
2. `ll-qa-gate-evaluate` — reads manifests + settlements + waivers → generates release_gate_input.yaml
3. `render-testset-view` (兼容层) — aggregates plan/manifest/spec/settlement → renders old testset compatibility view

**Out of scope (deprecate, do NOT modify):**
- `ll-test-exec-cli` — old TESTSET-driven execution, superseded by spec-driven execution
- `ll-test-exec-web-e2e` — same, old TESTSET-driven E2E execution

</domain>

<decisions>
## Implementation Decisions

### Skill Infrastructure Pattern (locked from Phase 2)
- Each skill gets 6 new files: `scripts/run.sh`, `scripts/validate_input.sh`, `scripts/validate_output.sh`, `evidence/*.schema.json`, `ll.lifecycle.yaml`
- `scripts/run.sh` calls Claude Code sub-agent via `ll skill` CLI with the skill's `agents/executor.md` prompt
- `validate_input.sh` checks input file existence and schema validity
- `validate_output.sh` calls Phase 1 `qa_schemas.py` validator for schema matching
- CLI must register new actions in `cli/commands/skill/command.py` `_QA_SKILL_MAP`

### ll-qa-settlement (locked from ADR-047 §10, existing SKILL.md)
- Input: updated API/E2E manifests after test execution (with lifecycle_status, evidence_status fields)
- Output: `api-settlement-report.yaml` and `e2e-settlement-report.yaml` in `ssot/tests/.artifacts/settlement/`
- Must compute: total/designed/executed/passed/failed/blocked/uncovered/cut/obsolete statistics
- Must generate: gap_list (failed/blocked/uncovered items), waiver_list (non-none waiver_status items)
- Statistics must be self-consistent: executed = passed + failed + blocked
- pass_rate excludes obsolete and approved waiver items from denominator

### ll-qa-gate-evaluate (locked from ADR-047 §9.4-9.5, existing SKILL.md)
- Input: api manifest + e2e manifest + api settlement + e2e settlement + waiver records
- Output: `release_gate_input.yaml` at `ssot/tests/.artifacts/settlement/release_gate_input.yaml`
- Must apply 7 anti-laziness checks: manifest freeze, cut records, pending waivers counted, evidence consistency, min exception coverage, no-evidence-not-executed, evidence hash binding
- final_decision must be one of: `pass`, `fail`, `conditional_pass`
- evidence_hash = SHA-256 of all evidence file contents
- Gate rules from ADR-047 §9.4 must be machine-executable

### render-testset-view (兼容层, locked from ADR-047 §3.7, §11.1)
- Purpose: backward compatibility — renders old testset view from new plan/manifest/spec/settlement artifacts
- Input: api-test-plan + api-coverage-manifest + api-test-spec + api-settlement-report (and E2E equivalents)
- Output: testset-compatible YAML/JSON view aggregating all coverage data
- This is a read-only aggregation, not a test execution skill

### Deprecation (locked from ROADMAP.md Phase 3)
- `ll-test-exec-cli` and `ll-test-exec-web-e2e` are ADR-035 TESTSET-old-framework skills
- Mark as deprecated in their SKILL.md and ll.lifecycle.yaml
- Do NOT add scripts/validate/evidence infrastructure to them
- New framework executes from spec directly, not from testset

### Claude's Discretion
- Whether settlement uses Python CLI or shell script wrapper (Phase 2 used shell + sub-agent)
- Exact directory structure for render-testset-view (new skill vs existing)
- Whether to add Python settlement computation module or keep prompt-first

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Architecture
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — Full dual-chain governance architecture, settlement format, gate rules
- `ssot/adr/ADR-048-SSOT-与双链测试接入-Droid-Missions-的统一治理架构.md` — SSOT integration with Droid Missions

### QA Schemas (Phase 1)
- `ssot/schemas/qa/plan.yaml` — plan schema definition
- `ssot/schemas/qa/manifest.yaml` — manifest schema definition
- `ssot/schemas/qa/spec.yaml` — spec schema definition
- `ssot/schemas/qa/settlement.yaml` — settlement schema definition
- `cli/lib/qa_schemas.py` — Python dataclass validators for QA schemas
- `cli/lib/qa_skill_runtime.py` — Shared QA skill runtime

### Existing Skill Artifacts
- `skills/ll-qa-settlement/SKILL.md` — Settlement skill definition (already exists)
- `skills/ll-qa-settlement/ll.contract.yaml` — Contract metadata
- `skills/ll-qa-settlement/agents/executor.md` — Executor prompt
- `skills/ll-qa-settlement/agents/supervisor.md` — Supervisor prompt
- `skills/ll-qa-gate-evaluate/SKILL.md` — Gate evaluate skill definition (already exists)
- `skills/ll-qa-gate-evaluate/ll.contract.yaml` — Contract metadata
- `skills/ll-qa-gate-evaluate/agents/executor.md` — Executor prompt
- `skills/ll-qa-gate-evaluate/agents/supervisor.md` — Supervisor prompt

### CLI Protocol (Phase 2 pattern)
- `cli/commands/skill/command.py` — Skill command handler with _QA_SKILL_MAP
- `cli/ll.py` — Main CLI entry point

### Phase 2 Skill Pattern (reference implementation)
- `skills/ll-qa-feat-to-apiplan/scripts/run.sh` — Reference run.sh pattern
- `skills/ll-qa-api-manifest-init/scripts/validate_input.sh` — Reference validate_input pattern
- `skills/ll-qa-api-spec-gen/scripts/validate_output.sh` — Reference validate_output pattern

</canonical_refs>

<specifics>
## Specific Ideas

- Settlement statistics computation could be a small Python module (deterministic math) called from run.sh, while the report narrative generation stays prompt-first
- Gate evaluation's 7 anti-laziness checks are all deterministic — could be computed in Python with the LLM only generating the decision rationale
- render-testset-view needs to understand the old testset format to produce compatible output — should read existing testset examples
- Consider whether `ll-test-exec-cli` and `ll-test-exec-web-e2e` should have deprecation notices in their SKILL.md headers
</specifics>

<deferred>
## Deferred Ideas

- Python production-grade CLI runtime for all 11 skills (v2 requirement REQ-20)
- CI integration with automated release gate (v2 requirement REQ-21)
- E2E chain full pipeline pilot (v2 requirement REQ-10)

</deferred>

---

*Phase: 03-settlement-exec*
*Context gathered: 2026-04-14 via ROADMAP analysis*
