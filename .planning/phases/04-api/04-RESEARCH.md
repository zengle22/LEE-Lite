# Phase 04: API 链全流程试点 - Research

**Researched:** 2026-04-15
**Domain:** QA dual-chain governance (ADR-047) -- API test chain end-to-end pilot
**Confidence:** HIGH

## Summary

Phase 04 is an end-to-end pilot that chains together all skills built in Phases 1-3. No new skills are created; the goal is to verify the full pipeline `feat YAML -> api-test-plan -> api-coverage-manifest -> api-test-spec -> (test execution) -> manifest update + evidence -> settlement -> gate-evaluate -> release_gate_input.yaml` runs correctly with real artifacts.

The chain uses 5 skills: `ll-qa-feat-to-apiplan`, `ll-qa-api-manifest-init`, `ll-qa-api-spec-gen`, `ll-qa-settlement`, `ll-qa-gate-evaluate`. All skills are Prompt-first (LLM executor via `agents/executor.md`) with Python CLI wrappers (`scripts/run.sh`) that invoke `python -m cli skill <action>`. Schema validation is provided by `cli/lib/qa_schemas.py` (dataclass validators + `validate_file()` CLI).

**Primary recommendation:** Create a minimal pilot feat YAML (2-3 API objects, 3-5 capabilities, P0+P1), then invoke each skill sequentially via its `scripts/run.sh`, validating each output against the QA schema before proceeding to the next step. For test execution (the only non-skill step), manually update the manifest item states and create evidence files, then continue with settlement and gate.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Create a new minimal feat YAML as pilot input (do not select from existing api-test-plan)
- **D-02:** Minimal feat should contain 2-3 API objects, 3-5 capabilities, covering P0/P1 priorities
- **D-03:** Use single-step interactive execution -- invoke one skill, check result, proceed to next
- **D-04:** First pilot needs observation of each step's output, not full automation batch
- **D-05:** After test execution, automatically mark lifecycle_status (executed/passed/failed) and evidence_status (complete/missing) on manifest items
- **D-06:** Evidence stored as independent files in `ssot/tests/.artifacts/evidence/` directory, named by coverage_id
- **D-07:** Stop execution on any chain failure (schema mismatch, skill error)
- **D-08:** Record failure reasons to pilot-report, do not rollback completed parts
- **D-09:** Retain completed intermediate artifacts for debugging

### Claude's Discretion
- Specific content of minimal feat YAML (API objects, capabilities selection)
- Specific assertion verification method during test execution
- Detailed format of pilot-report (as long as it includes failure records and success criteria)

### Deferred Ideas (OUT OF SCOPE)
- E2E chain full pilot (v2 REQ-10)
- Python production CLI runtime (v2 REQ-20)
- CI integration with release gate (v2 REQ-21)
- Phase 2's 6 design-layer skills not yet executed, pilot may indirectly validate

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.10+ | Runtime for all CLI commands, dataclass validators | [VERIFIED: codebase] -- all skills use `python -m cli` |
| PyYAML | system | YAML parsing for schema validation and skill I/O | [VERIFIED: `cli/lib/qa_schemas.py` uses `import yaml`] |
| argparse | stdlib | CLI argument parsing | [VERIFIED: `cli/ll.py`, all `run.sh` scripts] |

### Supporting
| Library | Component | Purpose | When to Use |
|---------|-----------|---------|-------------|
| `cli/lib/qa_schemas.py` | Dataclass validators + `validate_file()` + CLI | Schema validation for plan/manifest/spec/settlement/gate | Every skill output validation |
| `cli/lib/qa_skill_runtime.py` | `run_skill()` + path resolution | Shared QA skill runtime for all 9 QA actions | All QA skill invocations |
| `cli/commands/skill/command.py` | `_QA_SKILL_MAP` + `_skill_handler()` | CLI handler dispatching 9 QA skill actions | `python -m cli skill <action>` |
| `cli/lib/protocol.py` | `CommandContext` + `run_with_protocol()` | Request/response protocol wrapper | All CLI skill invocations |
| `cli/lib/skill_runtime_paths.py` | `resolve_skill_scripts_dir()` | Skill directory resolution | Dynamic sys.path insertion for skill modules |

### Installation
No additional packages required -- all dependencies are in the existing codebase. The Python environment must have `pyyaml` installed (already present in the project).

**Version verification:** The codebase uses Python dataclass validators directly, not an external schema library like `jsonschema` or `pydantic`. All validation logic is hand-written in `qa_schemas.py`.

## Architecture Patterns

### Recommended Pilot Directory Structure
```
ssot/tests/api/FEAT-PILOT-001/
├── feat-pilot.yaml                          # Minimal feat YAML (pilot input, D-01)
├── api-test-plan.yaml                       # Output of ll-qa-feat-to-apiplan
├── api-coverage-manifest.yaml               # Output of ll-qa-api-manifest-init
├── api-test-spec/                           # Output of ll-qa-api-spec-gen (multiple files)
│   ├── spec-001.yaml
│   ├── spec-002.yaml
│   └── ...
ssot/tests/.artifacts/evidence/              # Evidence files (D-06)
├── {coverage_id}.evidence.yaml              # Per-coverage-item evidence
ssot/tests/.artifacts/settlement/
├── api-settlement-report.yaml               # Output of ll-qa-settlement
├── e2e-settlement-report.yaml               # Minimal stub (gate-evaluate needs it)
├── waiver.yaml                              # Already exists (empty waivers list)
├── release_gate_input.yaml                  # Output of ll-qa-gate-evaluate
```

### Skill Invocation Pattern
Each skill follows the same protocol:

```bash
# 1. run.sh parses arguments and validates input
bash skills/ll-qa-<skill>/scripts/run.sh --<input-arg> <path>

# 2. run.sh calls the CLI with a JSON request via process substitution
python -m cli skill <action> \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.<action>",
  "request_id": "req-$(date +%s)-$$",
  "payload": { "<input_key>": "<path>", "output_path": "<output>" },
  "trace": {}
}
EOF
) \
  --response-out <response.json> \
  --workspace-root <workspace>

# 3. validate_output.sh calls qa_schemas.py
python -m cli.lib.qa_schemas --type <schema_type> <output_file>
```

### Data Flow (verified from codebase)
```
feat YAML (input/contract.yaml requires: id, title, status, Scope, Acceptance)
  → ll-qa-feat-to-apiplan (feat_to_apiplan)
    → api-test-plan.yaml (validated by --type plan)
  → ll-qa-api-manifest-init (api_manifest_init)
    → api-coverage-manifest.yaml (validated by --type manifest)
  → ll-qa-api-spec-gen (api_spec_gen)
    → api-test-spec/*.yaml (validated by --type spec)
  → [MANUAL STEP: test execution]
    → Update manifest items: lifecycle_status=executed→passed/failed, evidence_status=complete
    → Create evidence files in ssot/tests/.artifacts/evidence/{coverage_id}.yaml
  → ll-qa-settlement (qa_settlement)
    → api-settlement-report.yaml (validated by --type settlement)
  → ll-qa-gate-evaluate (qa_gate_evaluate)
    → release_gate_input.yaml (validated by --type gate)
```

### Anti-Patterns to Avoid
- **Using existing FEAT files directly:** D-01 requires creating a NEW minimal feat YAML. Existing FEAT files (e.g., FEAT-SRC-001-001) are complex and not designed for pilot testing.
- **Skipping schema validation between steps:** Each skill's `validate_output.sh` calls `python -m cli.lib.qa_schemas --type <type>`. Skipping this defeats the pilot's goal of verifying schema correctness.
- **Hand-editing YAML without conforming to schema:** All intermediate artifacts must pass `qa_schemas.py` validation. The dataclass validators are strict (e.g., `source_feat_refs` must be non-empty, `priorities.p0` or `p1` must be non-empty).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Custom YAML validators | `cli/lib/qa_schemas.py validate_file()` | Already implements all 5 schema types with enum checks, required field validation |
| Skill invocation | Direct Python calls | `python -m cli skill <action>` via `run.sh` | Protocol wrapper handles request/response JSON, error semantics, evidence refs |
| Evidence file structure | Ad-hoc formats | `ssot/tests/templates/evidence-collection.md` template | Defines required/conditional evidence types, file naming convention |
| Gate evaluation logic | Manual pass/fail computation | `ll-qa-gate-evaluate` skill executor | 7 anti-laziness checks + SHA-256 evidence hash + deterministic computation |
| Settlement statistics | Manual counting | `ll-qa-settlement` skill executor | Self-consistency rules (executed = passed + failed + blocked), pass_rate formula |

**Key insight:** The entire chain is designed to be driven by the CLI protocol (`python -m cli skill <action>`). Each skill's business logic is delegated to the LLM via `agents/executor.md` (Prompt-first pattern). The Python runtime only handles I/O routing and schema validation.

## Runtime State Inventory

N/A -- This is a greenfield pilot, not a rename/refactor/migration phase. No existing runtime state needs updating.

**Note on existing artifacts:** The directory `ssot/tests/.artifacts/settlement/` already contains placeholder files:
- `api-settlement-report.yaml` -- Contains placeholder data for FEAT-SRC-005-001 with `executed: 0, uncovered: 19`
- `e2e-settlement-report.yaml` -- Exists (content not read)
- `waiver.yaml` -- Contains `waivers: []` (empty)

These are **NOT** pilot artifacts and should not be overwritten. The pilot should produce its own settlement files (either in the same directory with different naming, or in a pilot-specific subdirectory).

## Common Pitfalls

### Pitfall 1: Gate-Evaluate Requires 5 Inputs Including E2E Artifacts
**What goes wrong:** `ll-qa-gate-evaluate` requires 5 inputs: `api_manifest`, `e2e_manifest`, `api_settlement`, `e2e_settlement`, `waivers` (verified from `skills/ll-qa-gate-evaluate/scripts/run.sh` lines 33-37). The pilot only runs the API chain.
**Why it happens:** The gate evaluator was designed for the full dual-chain (API + E2E) evaluation.
**How to avoid:** Create minimal E2E stub artifacts (empty manifest, minimal settlement report) to satisfy the 5-input requirement. The existing `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml` may serve as a stub, but it must conform to the settlement schema.
**Warning signs:** `run.sh` exits with "Error: missing required arguments: --e2e-manifest --e2e-settlement"

### Pitfall 2: Schema Top-Level Key Mismatch
**What goes wrong:** `validate_file()` in `qa_schemas.py` looks for specific top-level keys: `api_test_plan`, `api_coverage_manifest`, `api_test_spec`, `settlement_report`, `gate_evaluation` (line 718-724). If the LLM generates YAML with different top-level keys, validation fails.
**Why it happens:** The executor prompts (`agents/executor.md`) do not explicitly state the required top-level YAML key.
**How to avoid:** Ensure `agents/executor.md` or the `run.sh` wrapper explicitly tells the LLM the required top-level key. Alternatively, the `_detect_schema_type()` function (line 773) auto-detects from top-level keys.
**Warning signs:** `QaSchemaError: Expected top-level key 'api_test_plan' in <path>. File may not be a valid plan asset.`

### Pitfall 3: Existing Manifest Uses `.md` Extension, Schema Expects `.yaml`
**What goes wrong:** The existing `api-test-plan.md` (line 1 of FEAT-SRC-001-001) is a Markdown file, but the schema validator expects YAML. The output contract says `api-test-plan.md` but `validate_output.sh` calls `--type plan` which expects YAML.
**Why it happens:** There is a format mismatch between the output contract (`.md`) and the schema validator (`.yaml`). The `run.sh` default output path is `api-test-plan.yaml`.
**How to avoid:** Use `.yaml` extension for all intermediate artifacts. The `.md` format is legacy.

### Pitfall 4: Manifest `scenario_type` Field Not Enum-Validated
**What goes wrong:** The existing manifest (FEAT-SRC-001-001) uses `scenario_type: happy_path`, `state_constraint`, `parameter_validation`, `exception`, `data_side_effect`, `boundary_value`. The `validate_manifest()` function in `qa_schemas.py` does NOT validate `scenario_type` against the `ScenarioType` enum (lines 399-463). It only validates `priority`, `lifecycle_status`, `mapping_status`, `evidence_status`, `waiver_status`.
**Why it happens:** `scenario_type` is listed as a required field but not enum-checked in the validator.
**How to avoid:** This is NOT a blocking issue for the pilot -- the validator accepts any string for `scenario_type`. However, consistency with the enum values (`happy_path`, `validation`, `boundary`, `permission`, `error`, `idempotent`, `state_constraint`, `data_sideeffect`) is recommended.
**Note:** The existing manifest uses `boundary_value` while the enum defines `BOUNDARY = "boundary"`. Similarly `data_side_effect` vs `DATA_SIDEEFFECT = "data_sideeffect"`.

### Pitfall 5: `_run_llm_executor` Does Not Actually Invoke Claude
**What goes wrong:** `qa_skill_runtime.py` line 168-190: `_run_llm_executor()` writes the prompt to a temp file but does NOT actually invoke the Claude Code subprocess. It logs the prompt location and returns.
**Why it happens:** The comment says "The outer LLM will read this file and execute the skill." This is by design in Prompt-first mode -- the current LLM session is expected to read the prompt file and perform the skill's work.
**How to avoid:** The pilot must explicitly read the generated prompt file (`.artifacts/qa/_executor_prompt.md`) and execute the skill's business logic, then write the output file. Alternatively, invoke the skill logic directly rather than relying on the subprocess mechanism.

### Pitfall 6: Pilot Has No Backend to Test Against
**What goes wrong:** The pilot generates test specs (api-test-spec) but there is no actual API server to execute tests against.
**Why it happens:** This project is a governance/orchestration layer, not an API product. The specs define contracts but have no running service.
**How to avoid:** For the pilot, "test execution" should be simulated: update manifest items to `lifecycle_status: executed` and `evidence_status: complete`, create evidence files that document the simulated execution. The pilot's goal is to verify the chain, not to test a real API. The evidence files should clearly note this is simulated execution.

## Code Examples

### CLI Skill Invocation (verified from run.sh)
```bash
# Step 1: feat-to-apiplan
python -m cli skill feat-to-apiplan \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.feat-to-apiplan",
  "request_id": "req-$(date +%s)",
  "payload": {
    "feat_path": "ssot/tests/api/FEAT-PILOT-001/feat-pilot.yaml",
    "output_path": "ssot/tests/api/FEAT-PILOT-001/api-test-plan.yaml"
  },
  "trace": {}
}
EOF
) \
  --response-out ".artifacts/qa/feat-to-apiplan/response.json" \
  --workspace-root "$PWD"

# Step 2: validate output
python -m cli.lib.qa_schemas --type plan ssot/tests/api/FEAT-PILOT-001/api-test-plan.yaml
```

### Schema Validation (verified from qa_schemas.py)
```bash
# Validate any QA asset
python -m cli.lib.qa_schemas --type plan <file.yaml>
python -m cli.lib.qa_schemas --type manifest <file.yaml>
python -m cli.lib.qa_schemas --type spec <file.yaml>
python -m cli.lib.qa_schemas --type settlement <file.yaml>
python -m cli.lib.qa_schemas --type gate <file.yaml>

# Auto-detect schema type from file content
python -m cli.lib.qa_schemas <file.yaml>
```

### Evidence File Format (verified from evidence-collection.md template)
```yaml
evidence_record:
  case_id: api_case.pilot.create.happy
  coverage_id: api.pilot.create.happy
  executed_at: "2026-04-15T10:00:00Z"
  run_id: "run-pilot-001"
  evidence:
    request_snapshot:
      method: POST
      url: /api/v1/pilot/test
      body: { "key": "value" }
    response_snapshot:
      status_code: 201
      body: { "status": "success" }
    assertion_results:
      - assertion: status_code == 201
        result: pass
  side_effects: []
  execution_status: success
```

### Manifest Item Update (post-execution)
```yaml
# Before execution:
lifecycle_status: designed
mapping_status: unmapped
evidence_status: missing
waiver_status: none

# After simulated execution (passed):
lifecycle_status: passed
mapping_status: mapped
evidence_status: complete
waiver_status: none
evidence_refs:
  - ssot/tests/.artifacts/evidence/api.pilot.create.happy.evidence.yaml
rerun_count: 0
last_run_id: run-pilot-001

# After simulated execution (failed):
lifecycle_status: failed
mapping_status: mapped
evidence_status: complete
waiver_status: pending
evidence_refs:
  - ssot/tests/.artifacts/evidence/api.pilot.create.happy.evidence.yaml
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single testset as truth source | Four-layer asset separation (plan/manifest/spec/settlement) | ADR-047 v1.4 (2026-04-10) | Pilot must produce all 4 layers |
| Narrative test reports | Settlement ledger with machine-executable statistics | ADR-047 §10 | `release_gate_input.yaml` is the sole gate input |
| `status` single field | Layered status: `lifecycle_status`/`mapping_status`/`evidence_status`/`waiver_status` | ADR-047 v1.2 | All 4 fields required on manifest items |
| Free-form test execution | Spec-driven execution with evidence requirements | ADR-047 §6 | Each spec defines `evidence_required` list |
| Human-only gate decision | 7 anti-laziness checks + SHA-256 evidence hash + deterministic rules | ADR-047 §9.4 | Gate evaluation is machine-verifiable |

**Deprecated/outdated:**
- `ll-test-exec-cli` and `ll-test-exec-web-e2e` -- marked DEPRECATED in Phase 3. Pilot does NOT use these.
- `feat-to-api-test-plan` (old skill name) -- replaced by `ll-qa-feat-to-apiplan` (Phase 2).
- Narrative test reports -- replaced by settlement ledgers.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_run_llm_executor()` does not invoke Claude subprocess, only writes prompt to temp file | Common Pitfalls #5 | HIGH -- If it does invoke Claude, the pilot execution approach changes significantly |
| A2 | No actual API backend exists to test against | Common Pitfalls #6 | HIGH -- If a backend exists, test execution should be real, not simulated |
| A3 | E2E stub artifacts are needed for gate-evaluate (not already present in a usable form) | Common Pitfalls #1 | MEDIUM -- Existing `e2e-settlement-report.yaml` may not conform to current schema |
| A4 | The existing `api-settlement-report.yaml` in `.artifacts/settlement/` is a placeholder and must NOT be overwritten by pilot | Runtime State Inventory | MEDIUM -- Overwriting would lose existing artifact |
| A5 | `pyyaml` is installed in the project's Python environment | Standard Stack | LOW -- `qa_schemas.py` imports it and was presumably tested in Phase 1 |

## Open Questions

1. **Which FEAT should the pilot use as template?**
   - What we know: D-01 says "create a new minimal feat YAML". Existing FEAT files have varied complexity (5-8 capabilities each).
   - What's unclear: The exact structure of the minimal feat YAML -- should it follow the existing FEAT markdown format with frontmatter, or a simpler YAML format?
   - Recommendation: Follow the existing FEAT markdown format (frontmatter + Goal + Scope + Constraints + Acceptance Checks) since `validate_input.sh` checks for these sections. Create a simplified version with 2-3 API objects.

2. **How should test execution be simulated?**
   - What we know: No backend exists. D-03 says "single-step interactive execution".
   - What's unclear: Should evidence files document the simulation explicitly, or treat it as if real execution occurred?
   - Recommendation: Evidence files should note `execution_status: "simulated"` with a field indicating no real backend was called. This maintains honesty while still exercising the full chain.

3. **Does the existing `e2e-settlement-report.yaml` conform to the current schema?**
   - What we know: It exists at `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`.
   - What's unclear: Whether it has the `settlement_report` top-level key with all required fields (`chain`, `summary`, etc.).
   - Recommendation: Run `python -m cli.lib.qa_schemas --type settlement ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml` before the pilot to check. If it fails, create a minimal E2E settlement stub.

4. **What should the pilot-report format be?**
   - What we know: D-09 says "record failure reasons to pilot-report". CONTEXT.md says "pilot-report detailed format is at Claude's discretion".
   - What's unclear: Where should pilot-report be written? ROADMAP says `.planning/pilot-report.md`.
   - Recommendation: Write to `.planning/pilot-report.md` with sections: chain execution log (step-by-step), schema validation results, failure records, improvement suggestions.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All CLI commands, schema validation | To be verified at execution | -- | None -- blocking |
| PyYAML | `qa_schemas.py` YAML parsing | To be verified at execution | -- | None -- blocking |
| Bash (WSL/Git Bash) | `run.sh` scripts | Available (current shell) | -- | -- |
| Claude Code subprocess | Prompt-first skill execution | Available (current session) | -- | Manual execution of skill logic |
| API backend | Test execution | Not available | -- | Simulated execution (document in evidence) |

**Missing dependencies with fallback:**
- API backend -- not available, but pilot can use simulated execution with evidence files noting simulation status.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `cli.lib.qa_schemas` (custom dataclass validators) |
| Config file | None -- schema validation is CLI-driven |
| Quick run command | `python -m cli.lib.qa_schemas --type <type> <file.yaml>` |
| Full suite command | `python -m cli.lib.qa_schemas --type plan <plan.yaml> && python -m cli.lib.qa_schemas --type manifest <manifest.yaml> && python -m cli.lib.qa_schemas --type spec <spec.yaml> && python -m cli.lib.qa_schemas --type settlement <settlement.yaml> && python -m cli.lib.qa_schemas --type gate <gate.yaml>` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-04 | Full API chain runs end-to-end | integration | Sequential `run.sh` invocations per skill | N/A -- pilot execution |
| REQ-05 | All intermediate artifacts pass schema validation | unit | `python -m cli.lib.qa_schemas --type <type> <file>` | Validator: `cli/lib/qa_schemas.py` |
| REQ-06 | Pilot report with results and improvements | manual | N/A -- document review | `.planning/pilot-report.md` |

### Sampling Rate
- **Per skill step:** `python -m cli.lib.qa_schemas --type <type> <output.yaml>`
- **Phase-gate:** All 5 schema validations pass + `release_gate_input.yaml` generated + pilot report written

### Wave 0 Gaps
- None -- existing test infrastructure (`qa_schemas.py`) covers all phase requirements. The pilot IS the integration test.

## Security Domain

`security_enforcement` is not explicitly set in `.planning/config.json`, so Validation Architecture is included above (nyquist_validation is `false` in config, so validation section was included).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Pilot has no auth layer |
| V3 Session Management | No | No session handling in pilot |
| V4 Access Control | No | No access control in pilot |
| V5 Input Validation | Yes | `qa_schemas.py` dataclass validators + `validate_input.sh` scripts |
| V6 Cryptography | Partial | `gate-evaluate` computes SHA-256 evidence hash (use `hashlib`, never hand-roll) |

### Known Threat Patterns for QA Chain

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Schema bypass (invalid YAML accepted) | Tampering | `validate_output.sh` calls `qa_schemas.py` after every skill |
| Evidence fabrication (fake evidence refs) | Repudiation | Anti-laziness check `evidence_hash_binding` + `no_evidence_not_executed` |
| Manifest state manipulation | Tampering | Layered status fields + settlement statistics self-consistency check |

## Sources

### Primary (HIGH confidence)
- Codebase files read directly: `cli/lib/qa_schemas.py`, `cli/lib/qa_skill_runtime.py`, `cli/commands/skill/command.py`, `cli/ll.py`, all `skills/ll-qa-*/scripts/run.sh`, all `skills/ll-qa-*/agents/executor.md`, all `skills/ll-qa-*/input/contract.yaml`, all `skills/ll-qa-*/output/contract.yaml`, `ssot/schemas/qa/*.yaml`, `ssot/adr/ADR-047`
- Existing artifacts: `ssot/tests/api/FEAT-SRC-001-001/api-test-plan.md`, `ssot/tests/api/FEAT-SRC-001-001/api-coverage-manifest.yaml`, `ssot/tests/.artifacts/settlement/`

### Secondary (MEDIUM confidence)
- ADR-047 section references for gate rules (§9.4), settlement format (§10), manifest state machine (§15)

### Tertiary (LOW confidence)
- Assumption that `_run_llm_executor()` does not invoke Claude subprocess (code comment suggests this, but no runtime test performed)
- Assumption that no API backend exists (project is governance layer, but unverified)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all components verified from codebase
- Architecture: HIGH -- skill directories, CLI protocol, and data flow verified from source
- Pitfalls: MEDIUM -- identified from code analysis but not runtime-tested
- Schema validation: HIGH -- `qa_schemas.py` fully read and understood

**Research date:** 2026-04-15
**Valid until:** 2026-05-15 (stable domain, no fast-moving dependencies)
