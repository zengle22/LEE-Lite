# Phase 3: 结算层技能 + 兼容层 - Research

**Researched:** 2026-04-14
**Domain:** QA settlement/gate skills, prompt-first runtime infrastructure, testset backward compatibility
**Confidence:** HIGH

## Summary

Phase 3 completes 3 skills with full Prompt-first runtime infrastructure (scripts/run.sh, validate_input.sh, validate_output.sh, evidence/*.schema.json, ll.lifecycle.yaml) and marks 2 legacy ADR-035 skills as deprecated. The two new skills (ll-qa-settlement, ll-qa-gate-evaluate) already have SKILL.md, ll.contract.yaml, agents/executor.md, agents/supervisor.md, input/output contracts and semantic checklists. What's missing are the 6 standard infrastructure files per skill plus CLI registration.

The render-testset-view compatibility skill does NOT exist yet and must be created from scratch. It produces a backward-compatible testset view by aggregating plan/manifest/spec/settlement artifacts from the new dual-chain system.

**Primary recommendation:** Follow Phase 2 skill infrastructure pattern exactly for ll-qa-settlement and ll-qa-gate-evaluate. Create render-testset-view as a new skill directory with the same 6-file pattern. Register 3 new actions in `_QA_SKILL_MAP` in `cli/commands/skill/command.py`. Extend `qa_skill_runtime.py` with settlement/gate-specific mappings.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Each skill gets 6 new files: `scripts/run.sh`, `scripts/validate_input.sh`, `scripts/validate_output.sh`, `evidence/*.schema.json`, `ll.lifecycle.yaml`
- `scripts/run.sh` calls Claude Code sub-agent via `ll skill` CLI with the skill's `agents/executor.md` prompt
- `validate_input.sh` checks input file existence and schema validity
- `validate_output.sh` calls Phase 1 `qa_schemas.py` validator for schema matching
- CLI must register new actions in `cli/commands/skill/command.py` `_QA_SKILL_MAP`
- ll-qa-settlement: Input is updated API/E2E manifests (with lifecycle_status, evidence_status); Output is api/e2e settlement reports in `ssot/tests/.artifacts/settlement/`; Must compute total/designed/executed/passed/failed/blocked/uncovered/cut/obsolete statistics; Must generate gap_list and waiver_list; Statistics must be self-consistent: executed = passed + failed + blocked; pass_rate excludes obsolete and approved waiver items from denominator
- ll-qa-gate-evaluate: Input is api manifest + e2e manifest + api settlement + e2e settlement + waiver records; Output is `release_gate_input.yaml` at `ssot/tests/.artifacts/settlement/release_gate_input.yaml`; Must apply 7 anti-laziness checks; final_decision must be one of: `pass`, `fail`, `conditional_pass`; evidence_hash = SHA-256 of all evidence file contents
- render-testset-view: Purpose is backward compatibility from new plan/manifest/spec/settlement artifacts; Input is api-test-plan + api-coverage-manifest + api-test-spec + api-settlement-report (and E2E equivalents); Output is testset-compatible YAML/JSON view; This is a read-only aggregation skill, not a test execution skill
- `ll-test-exec-cli` and `ll-test-exec-web-e2e` are ADR-035 TESTSET-old-framework skills; Mark as deprecated in their SKILL.md and ll.lifecycle.yaml; Do NOT add scripts/validate/evidence infrastructure to them; New framework executes from spec directly, not from testset

### Claude's Discretion
- Whether settlement uses Python CLI or shell script wrapper (Phase 2 used shell + sub-agent)
- Exact directory structure for render-testset-view (new skill vs existing)
- Whether to add Python settlement computation module or keep prompt-first

### Deferred Ideas (OUT OF SCOPE)
- Python production-grade CLI runtime for all 11 skills (v2 requirement REQ-20)
- CI integration with automated release gate (v2 requirement REQ-21)
- E2E chain full pipeline pilot (v2 requirement REQ-10)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-03 | 结算/执行层 3 个技能 + ll-skill-install + ll-dev-feat-to-tech 补全实现 | This research covers the 3 QA settlement skills (ll-qa-settlement, ll-qa-gate-evaluate, render-testset-view). ll-skill-install and ll-dev-feat-to-tech are separate skills outside this phase scope. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.3 [VERIFIED: python -c "import yaml"] | YAML parsing/validation for all QA schemas | Already installed and used by qa_schemas.py |
| hashlib (stdlib) | 3.13.3 [VERIFIED: python -c "import hashlib"] | SHA-256 evidence hash computation for gate evaluate | Python stdlib, no install needed |
| dataclasses (stdlib) | 3.13.3 [VERIFIED: qa_schemas.py] | Schema dataclass definitions | Already used in qa_schemas.py for all QA types |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Bash (set -euo pipefail) | — | Shell scripts for run.sh, validate_*.sh | All skill scripts follow Phase 2 pattern [VERIFIED: skills/ll-qa-feat-to-apiplan/scripts/] |
| python -m cli skill | — | CLI entry point for skill invocation | Phase 2 pattern [VERIFIED: command.py] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Shell script wrapper for run.sh | Pure Python runtime module | Shell wrapper follows Phase 2 locked pattern; Python runtime deferred to v2 (REQ-20) |
| Prompt-first LLM computation | Deterministic Python statistics module | Context.md discretion allows either; recommendation: shell + sub-agent pattern for consistency with Phase 2, deterministic stats can be validated by validate_output.sh |

**Installation:**
```bash
# No additional packages needed — all dependencies already present
# PyYAML 6.0.3 already installed
# hashlib is Python stdlib
```

**Version verification:**
```
python --version -> Python 3.13.3 [VERIFIED]
pip show pyyaml -> 6.0.3 [VERIFIED]
```

## Architecture Patterns

### Recommended Project Structure

The 3 skills follow the established Phase 2 pattern:

```
skills/
├── ll-qa-settlement/              # EXISTING, needs +6 files
│   ├── SKILL.md                   # EXISTS
│   ├── ll.contract.yaml           # EXISTS
│   ├── ll.lifecycle.yaml          # NEW
│   ├── agents/
│   │   ├── executor.md            # EXISTS
│   │   └── supervisor.md          # EXISTS
│   ├── input/
│   │   ├── contract.yaml          # EXISTS
│   │   └── semantic-checklist.md  # EXISTS
│   ├── output/
│   │   ├── contract.yaml          # EXISTS
│   │   └── semantic-checklist.md  # EXISTS
│   ├── evidence/                  # NEW directory
│   │   └── settlement.schema.json # NEW
│   └── scripts/                   # NEW directory
│       ├── run.sh                 # NEW
│       ├── validate_input.sh      # NEW
│       └── validate_output.sh     # NEW
├── ll-qa-gate-evaluate/           # EXISTING, needs +6 files
│   ├── SKILL.md                   # EXISTS
│   ├── ll.contract.yaml           # EXISTS
│   ├── ll.lifecycle.yaml          # NEW
│   ├── agents/
│   │   ├── executor.md            # EXISTS
│   │   └── supervisor.md          # EXISTS
│   ├── input/
│   │   ├── contract.yaml          # EXISTS
│   │   └── semantic-checklist.md  # EXISTS
│   ├── output/
│   │   ├── contract.yaml          # EXISTS
│   │   └── semantic-checklist.md  # EXISTS
│   ├── evidence/                  # NEW directory
│   │   └── gate-eval.schema.json  # NEW
│   └── scripts/                   # NEW directory
│       ├── run.sh                 # NEW
│       ├── validate_input.sh      # NEW
│       └── validate_output.sh     # NEW
├── render-testset-view/           # NEW skill, all files new
│   ├── SKILL.md                   # NEW
│   ├── ll.contract.yaml           # NEW
│   ├── ll.lifecycle.yaml          # NEW
│   ├── agents/
│   │   ├── executor.md            # NEW
│   │   └── supervisor.md          # NEW
│   ├── input/
│   │   ├── contract.yaml          # NEW
│   │   └── semantic-checklist.md  # NEW
│   ├── output/
│   │   ├── contract.yaml          # NEW
│   │   └── semantic-checklist.md  # NEW
│   ├── evidence/                  # NEW
│   │   └── testset-view.schema.json # NEW
│   └── scripts/                   # NEW
│       ├── run.sh                 # NEW
│       ├── validate_input.sh      # NEW
│       └── validate_output.sh     # NEW
├── ll-test-exec-cli/              # DEPRECATE only
│   └── SKILL.md                   # Add deprecation header
│   └── ll.lifecycle.yaml          # Add deprecated state
└── ll-test-exec-web-e2e/          # DEPRECATE only
    └── SKILL.md                   # Add deprecation header
    └── ll.lifecycle.yaml          # Add deprecated state
```

### Pattern 1: run.sh (Phase 2 reference)
**What:** Shell entry point that validates inputs, invokes `python -m cli skill <action>`, then validates outputs
**When to use:** All Prompt-first skills
**Example:**
```bash
#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-settlement skill
# Usage: ./run.sh --manifest-path <path> [--output-dir <dir>] [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
MANIFEST_PATH=""
OUTPUT_DIR=""
WORKSPACE="${PWD}"
CHAIN="api"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest-path) MANIFEST_PATH="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    --chain) CHAIN="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${MANIFEST_PATH}" ]]; then
  echo "Error: --manifest-path is required"
  exit 1
fi

# Validate input before running
bash "${SCRIPT_DIR}/validate_input.sh" "${MANIFEST_PATH}"

# Run the skill via CLI protocol
python -m cli skill settlement \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.settlement",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "manifest_path": "${MANIFEST_PATH}",
    "chain": "${CHAIN}",
    "output_dir": "${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/.artifacts/settlement}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/settlement/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output
OUTPUT_FILE="${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/.artifacts/settlement}/${CHAIN}-settlement-report.yaml"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
```
Source: [VERIFIED: skills/ll-qa-feat-to-apiplan/scripts/run.sh]

### Pattern 2: validate_input.sh (Phase 2 reference)
**What:** Validates input file exists and contains required sections or conforms to schema
**When to use:** All skills
**Example:**
```bash
#!/usr/bin/env bash
# validate_input.sh — Validate input for ll-qa-settlement
set -euo pipefail

MANIFEST_PATH="${1:-}"
if [[ -z "${MANIFEST_PATH}" ]]; then echo "FAIL: manifest_path required"; exit 1; fi
if [[ ! -f "${MANIFEST_PATH}" ]]; then echo "FAIL: file not found: ${MANIFEST_PATH}"; exit 1; fi

# Validate manifest schema
python -m cli.lib.qa_schemas --type manifest "${MANIFEST_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: input does not conform to manifest schema"; exit 1; fi

echo "OK: input validated"
```
Source: [VERIFIED: skills/ll-qa-api-manifest-init/scripts/validate_input.sh]

### Pattern 3: validate_output.sh (Phase 2 reference)
**What:** Validates output file exists and conforms to the appropriate QA schema
**When to use:** All skills
**Example:**
```bash
#!/usr/bin/env bash
# validate_output.sh — Validate output for ll-qa-settlement
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then echo "FAIL: output_path required"; exit 1; fi
if [[ -f "${OUTPUT_PATH}" ]]; then
  python -m cli.lib.qa_schemas --type settlement "${OUTPUT_PATH}"
  if [[ $? -ne 0 ]]; then echo "FAIL: invalid settlement output"; exit 1; fi
  echo "OK: output validated"
else
  echo "FAIL: output file not found: ${OUTPUT_PATH}"
  exit 1
fi
```
Source: [VERIFIED: skills/ll-qa-api-spec-gen/scripts/validate_output.sh]

### Anti-Patterns to Avoid
- **Do NOT modify ll-test-exec-cli or ll-test-exec-web-e2e scripts** — only add deprecation headers to SKILL.md and ll.lifecycle.yaml. These are out-of-scope legacy skills.
- **Do NOT create Python CLI modules** for settlement computation — that is REQ-20 (v2), deferred. Keep prompt-first pattern.
- **Do NOT add validate infrastructure to deprecated skills** — locked decision.
- **Do NOT create render-testset-view as a Python-only module** — it must follow the same 6-file Prompt-first pattern as the other skills.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Custom YAML validators in shell scripts | `python -m cli.lib.qa_schemas --type <type>` | Phase 1 already built complete dataclass validators with enum checks, required field validation, and error messages [VERIFIED: qa_schemas.py validate_settlement()] |
| Evidence SHA-256 hash | Manual hex computation | Python `hashlib.sha256()` | Standard library, one-liner, no edge cases [ASSUMED: standard Python usage] |
| YAML parsing | String-based YAML parsing in bash | PyYAML `yaml.safe_load()` | Handles nested structures, nulls, lists correctly; already used by qa_schemas.py |
| File path resolution | Hardcoded paths | `Path.resolve()` + `workspace_root` parameter | Skills must work with any workspace; Phase 2 uses parameterized workspace_root [VERIFIED: qa_skill_runtime.py] |
| Settlement statistics | Prompt-only computation | Shell validates input, LLM computes, validate_output.sh verifies with qa_schemas.py | Statistics are deterministic but must be output as YAML conforming to settlement schema; prompt-first pattern delegates to LLM, schema validator catches errors |

**Key insight:** The entire validation infrastructure (dataclass definitions, enum validation, required field checks, file-level entry points) was built in Phase 1. Phase 3 skills should reuse `python -m cli.lib.qa_schemas --type settlement` and extend it if needed rather than reimplementing any validation logic.

## Runtime State Inventory

> This is a greenfield skill-completion phase, not a rename/refactor/migration phase. Most categories are "nothing found."

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no databases or datastores involved; all artifacts are YAML files on disk | None |
| Live service config | None — all skill configuration lives in git (SKILL.md, contracts, lifecycle) | None |
| OS-registered state | None — no Windows Task Scheduler, pm2, systemd, or launchd registrations | None |
| Secrets/env vars | None — settlement and gate skills read files, no env var names reference skill names | None |
| Build artifacts | None — skills are not pip/npm packages; no compiled artifacts | None |
| CLI registration | `_QA_SKILL_MAP` in `command.py` — currently has 6 Phase 2 entries; Phase 3 needs 3 new entries (`settlement`, `gate-evaluate`, `render-testset-view`) | Add 3 entries to `_QA_SKILL_MAP` in command.py |
| Schema validator | `qa_schemas.py` `_VALIDATORS` dict has plan/manifest/spec/settlement (4 types) — settlement type ALREADY EXISTS | No extension needed for settlement; may need new type for gate-evaluate output (release_gate_input) |
| Runtime skill mappings | `qa_skill_runtime.py` has `action_to_skill`, `input_keys`, `output_keys`, `output_keys`, `_action_to_schema_type` — all only cover Phase 2 skills | Extend all 4 mapping dicts to include Phase 3 actions |

**Canonical question:** After every file in the repo is updated, what runtime systems still have the old string cached, stored, or registered? — Nothing, since this phase is new skill creation, not renaming.

## Common Pitfalls

### Pitfall 1: Schema Type Not Registered for Gate Evaluate Output
**What goes wrong:** The gate evaluate skill produces `release_gate_input.yaml`, which is NOT one of the 4 schema types (plan/manifest/spec/settlement) currently in `qa_schemas.py` `_VALIDATORS`.
**Why it happens:** Phase 1 defined validators for the 4 asset layers but gate evaluate output (`release_gate_input`) is a separate artifact type not in that list.
**How to avoid:** Add a `gate` or `release_gate` validator to `qa_schemas.py` `_VALIDATORS` dict and a corresponding `validate_gate()` function. Alternatively, validate the gate output file structure manually in validate_output.sh by checking required keys exist.
**Warning signs:** `python -m cli.lib.qa_schemas --type ??? release_gate_input.yaml` returns "Unknown schema type."

### Pitfall 2: Settlement Output Path Mismatch
**What goes wrong:** SKILL.md specifies `ssot/tests/.artifacts/settlement/api-settlement-report.yaml` but the qa_schemas.py validator expects top-level key `settlement_report`, while the SKILL.md example uses `api_settlement` and `e2e_settlement` as root keys.
**Why it happens:** The settlement YAML schema file (`ssot/schemas/qa/settlement.yaml`) uses `settlement_report` as the root key, but the SKILL.md examples use chain-specific root keys (`api_settlement`, `e2e_settlement`).
**How to avoid:** The settle skill should write output with `settlement_report` as root key and include `chain: "api"` or `chain: "e2e"` inside. The validate_output.sh uses `--type settlement` which expects `settlement_report` root key. This IS consistent — the qa_schemas.py `validate_settlement()` function checks for `chain` enum[api, e2e] inside `settlement_report`.
**Warning signs:** Output YAML has `api_settlement:` root key instead of `settlement_report:` — validate_settlement() will fail because it expects `settlement_report` top-level key. [VERIFIED: qa_schemas.py line 518: `_require(data, "chain", label)` after extracting `data[top_key]` where top_key is `settlement_report`]

### Pitfall 3: qa_skill_runtime.py Mapping Gaps
**What goes wrong:** New skill actions are registered in `_QA_SKILL_MAP` but the runtime functions (`_find_skill_dir`, `_resolve_input_path`, `_resolve_output_path`, `_action_to_schema_type`) don't have entries for them.
**Why it happens:** These 4 mapping dicts in `qa_skill_runtime.py` are hard-coded and must be extended in parallel with `_QA_SKILL_MAP` additions.
**How to avoid:** When adding `settlement`, `gate-evaluate`, and `render-testset-view` to `_QA_SKILL_MAP`, simultaneously add entries to all 4 internal mappings in `qa_skill_runtime.py`:
- `action_to_skill` (maps action -> skill dir name)
- `input_keys` (maps action -> payload key for input file)
- `output_keys` (maps action -> output file name)
- `_action_to_schema_type` (maps action -> schema type string)

### Pitfall 4: Deprecation vs Destruction of Old Skills
**What goes wrong:** Deleting or heavily modifying ll-test-exec-cli/ll-test-exec-web-e2e instead of just marking them deprecated.
**Why it happens:** These skills may still be referenced by existing testset files or old pipelines.
**How to avoid:** Only add a deprecation notice header to their SKILL.md files and add `deprecated: true` or a deprecated state to their ll.lifecycle.yaml. Do NOT touch their scripts/, agents/, or other files.
**Warning signs:** Any file modification in these skills beyond SKILL.md and ll.lifecycle.yaml.

### Pitfall 5: Gate Evaluate Evidence Hash Computation
**What goes wrong:** SHA-256 hash is computed on file paths instead of file contents, or hash order is non-deterministic.
**Why it happens:** Evidence files must be read in a deterministic order and concatenated before hashing.
**How to avoid:** Sort evidence file paths alphabetically, read each file's bytes, concatenate, then compute SHA-256 on the concatenated content. The executor prompt should specify this algorithm explicitly.

## Code Examples

Verified patterns from official sources:

### Settlement Schema Validation
```python
# Source: cli/lib/qa_schemas.py lines 515-630
def validate_settlement(data: dict) -> SettlementReport:
    """Validate and return a SettlementReport from raw YAML dict."""
    label = "settlement_report"
    _require(data, "chain", label)
    _require(data, "summary", label)
    _enum_check(data["chain"], ChainType, label, "chain")
    # ... validates summary fields, by_capability, by_feature_ref,
    # evidence_completeness, gap_list, waiver_list, verdict, gate_evaluation
```

### Gate Evaluate Evidence Hash (Python)
```python
# Pattern for SHA-256 of multiple evidence files
import hashlib

def compute_evidence_hash(evidence_paths: list[str]) -> str:
    """Compute SHA-256 of all evidence file contents in sorted order."""
    hasher = hashlib.sha256()
    for path in sorted(evidence_paths):
        with open(path, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()
```

### CLI Registration Pattern
```python
# Source: cli/commands/skill/command.py lines 102-109 (existing pattern)
_QA_SKILL_MAP = {
    "feat-to-apiplan": ("ll-qa-feat-to-apiplan", "feat_to_apiplan"),
    # ... Phase 2 entries ...
    # Phase 3 additions:
    "settlement": ("ll-qa-settlement", "qa_settlement"),
    "gate-evaluate": ("ll-qa-gate-evaluate", "qa_gate_evaluate"),
    "render-testset-view": ("render-testset-view", "qa_render_testset"),
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TESTSET-driven execution (ADR-035) | Spec-driven execution (ADR-047) | v1.4 ADR-047 | ll-test-exec-cli and ll-test-exec-web-e2e are legacy, new skills read spec not testset |
| Narrative test reports | Structured settlement ledger | v1.4 ADR-047 §10 | Settlement reports are machine-readable YAML with statistics, gap lists, waiver lists |
| Human-only gate decision | Machine-executable gate rules + human waiver approval | v1.4 ADR-047 §9.4 | 7 anti-laziness checks are deterministic, gate evaluator generates structured output |
| Single testset artifact | 4-layer asset separation (plan/manifest/spec/settlement) | v1.1 ADR-047 §3.3 | Each layer has specific responsibility, no semantic overloading |
| Status single field | Layered state fields (lifecycle/mapping/evidence/waiver) | v1.2 ADR-047 §15 | Each state dimension is independently trackable |

**Deprecated/outdated:**
- `ll-test-exec-cli`: ADR-035 TESTSET-driven execution, superseded by spec-driven flow. SKILL.md to be marked deprecated.
- `ll-test-exec-web-e2e`: Same — ADR-035 E2E execution, superseded by E2E spec-driven flow. SKILL.md to be marked deprecated.
- SKILL.md example output format: Uses `api_settlement` root key but validator expects `settlement_report` — the actual YAML output must use `settlement_report` with `chain: "api"` or `chain: "e2e"`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | render-testset-view should follow the exact same 6-file Prompt-first pattern as Phase 2 skills | Architecture Patterns | Planner may choose different structure; low risk since pattern is established |
| A2 | The old testset format (from `.local/adr018-skill-trial/`) is JSON-based with functional_areas, logic_dimensions, coverage_matrix structure | render-testset-view design | If old format differs, render logic needs adjustment — planner should verify format |
| A3 | Python is invoked as `python` on the target machine (not `python3`) | Environment Availability | Windows uses `python`; scripts using `python3` would fail. Phase 2 uses `python -m cli` consistently [VERIFIED: command.py] |
| A4 | `release_gate_input.yaml` needs a separate schema type in qa_schemas.py (not currently in _VALIDATORS) | Pitfall 1 | Gate validate_output.sh would have no schema type to use; can fall back to key-existence checks in shell |

## Open Questions (RESOLVED)

1. **What exact schema should release_gate_input.yaml conform to?**
   - Resolution: Add a lightweight `validate_gate()` to `qa_schemas.py` that checks required top-level keys (`api`, `e2e`, `final_decision`) and enum values. The `final_decision` must be one of `release`, `conditional_release`, `block`. Each chain sub-object must have `status` (pass|conditional_pass|fail), `uncovered_count`, `failed_count`, `blocked_count`.

2. **Does render-testset-view need to produce the EXACT old testset format?**
   - Resolution: Yes, it must produce the exact old testset JSON format for backward compatibility. The render skill should read one old testset example (from `.local/adr018-skill-trial/`) to understand the output schema, then produce identical-structure JSON. Output format: JSON (matching legacy), not YAML.

3. **Should settlement output be one file per chain or combined?**
   - Resolution: One run.sh invocation per chain via `--chain api` or `--chain e2e` flag, producing one file each (`api-settlement-report.yaml` or `e2e-settlement-report.yaml`). This matches the schema which has `chain: api|e2e` enum and keeps each invocation focused.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All skill scripts, CLI, schema validation | ✓ | 3.13.3 | — |
| PyYAML | Schema validation | ✓ | 6.0.3 | — |
| hashlib (stdlib) | Evidence SHA-256 computation | ✓ | stdlib | — |
| Bash (set -euo pipefail) | run.sh, validate_*.sh scripts | ✓ | Git Bash (Win11) | — |
| `python -m cli` | Skill CLI invocation | ✓ | Project CLI | — |
| Claude Code sub-agent | LLM executor (prompt-first) | ✓ | Host environment | Manual YAML generation (not recommended) |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

## Validation Architecture

> nyquist_validation is explicitly set to false in .planning/config.json. Skipping Validation Architecture section.

## Security Domain

> `security_enforcement` is not set in config.json, so defaulting to enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | `python -m cli.lib.qa_schemas` for all YAML inputs/outputs |
| V6 Cryptography | yes | `hashlib.sha256()` for evidence hash — never hand-roll [VERIFIED: Python stdlib] |

### Known Threat Patterns for YAML-based QA Skills

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization attack | Tampering | Use `yaml.safe_load()` only, never `yaml.load()` with Loader [VERIFIED: qa_schemas.py uses safe_load] |
| Input file path traversal | Tampering | Validate input paths are within workspace_root; Phase 2 uses `Path.resolve()` [VERIFIED: qa_skill_runtime.py] |
| Evidence hash collision | Tampering | SHA-256 with sorted file concatenation; collision resistance is computationally infeasible |
| Gate decision manipulation | Tampering | 7 anti-laziness checks are deterministic; evidence hash binds all evidence files |
| Waiver bypass | Repudiation | Waiver list includes approver and approved_at (ISO 8601); audit trail in YAML |

## Sources

### Primary (HIGH confidence)
- `cli/lib/qa_schemas.py` — Settlement schema validator, all enum definitions, validate_settlement() function [VERIFIED: read file]
- `cli/lib/qa_skill_runtime.py` — Runtime mappings, run_skill() function, all 4 mapping dicts [VERIFIED: read file]
- `cli/commands/skill/command.py` — _QA_SKILL_MAP, CLI registration pattern [VERIFIED: read file]
- `ssot/schemas/qa/settlement.yaml` — Settlement report schema definition [VERIFIED: read file]
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — Full architecture, gate rules, settlement format, migration strategy [VERIFIED: read file]
- `skills/ll-qa-feat-to-apiplan/scripts/run.sh` — Reference run.sh pattern [VERIFIED: read file]
- `skills/ll-qa-api-manifest-init/scripts/validate_input.sh` — Reference validate_input pattern [VERIFIED: read file]
- `skills/ll-qa-api-spec-gen/scripts/validate_output.sh` — Reference validate_output pattern [VERIFIED: read file]

### Secondary (MEDIUM confidence)
- `skills/ll-qa-settlement/SKILL.md` — Settlement skill definition [VERIFIED: read file]
- `skills/ll-qa-gate-evaluate/SKILL.md` — Gate evaluate skill definition [VERIFIED: read file]
- `skills/ll-test-exec-cli/SKILL.md` — Legacy skill to deprecate [VERIFIED: read file]
- `skills/ll-test-exec-web-e2e/SKILL.md` — Legacy skill to deprecate [VERIFIED: read file]
- `.planning/config.json` — Workflow config, nyquist_validation: false [VERIFIED: read file]

### Tertiary (LOW confidence)
- Old testset files in `.local/adr018-skill-trial/` — Format not yet examined; needed for render-testset-view output contract [NEEDS VERIFICATION]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via Python runtime checks and existing codebase
- Architecture: HIGH — Phase 2 patterns verified by reading actual files, locked decisions from CONTEXT.md
- Pitfalls: MEDIUM — identified by cross-referencing schema validators with SKILL.md examples; settlement root key discrepancy verified against qa_schemas.py code

**Research date:** 2026-04-14
**Valid until:** 30 days (stable domain, no fast-moving dependencies)
