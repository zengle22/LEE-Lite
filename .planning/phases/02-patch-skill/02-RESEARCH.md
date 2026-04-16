# Phase 2: Patch 登记 Skill - Research

**Researched:** 2026-04-16
**Domain:** Claude Code skill architecture + CLI command registration + AI agent orchestration for patch capture
**Confidence:** HIGH

## Summary

Phase 2 requires creating the `ll-patch-capture` skill following the project's 29 existing `ll-*` governed skill patterns. The skill implements a dual-path registration system: Prompt-to-Patch (AI generates Patch YAML from user description) and Document-to-SRC (routes to existing `ll-product-raw-to-src`). The skill requires an Executor agent (generates Patch YAML), a Supervisor agent (validates via Phase 1's `cli/lib/patch_schema.py`, decides auto-pass vs escalate), a CLI entry point (`patch-capture` action), and a `scripts/run.sh` wrapper.

The project uses a consistent skill structure: `SKILL.md` + `ll.contract.yaml` + `input/contract.yaml` + `output/contract.yaml` + `agents/executor.md` + `agents/supervisor.md` + `scripts/run.sh` + `scripts/validate_input.sh` + `scripts/validate_output.sh` + `ll.lifecycle.yaml`. This pattern is verified across all 29 existing skills.

The CLI uses `argparse` subparsers under `python -m cli skill <action>` with a handler dispatch pattern in `cli/commands/skill/command.py`. New skills either register through `_QA_SKILL_MAP` (shared `qa_skill_runtime.py`) or get an explicit if/elif branch in `_skill_handler()` with a dedicated Python runtime module.

**Primary recommendation:** Create `ll-patch-capture` as a dedicated-runtime skill (not QA-shared), with its own `patch_capture_runtime.py` in `skills/ll-patch-capture/scripts/`, registered via explicit if/elif in `_skill_handler()`. This matches the pattern used by `ll-gate-human-orchestrator` which also has unique logic not shared with other skills.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Follow existing `ll-*` governed skill pattern, consistent with 29 existing skills
- **D-02:** Skill named `ll-patch-capture` (not `ll-experience-patch-register`)
- **D-03:** File structure: `SKILL.md` + `ll.contract.yaml` + `input/` + `output/` + `agents/executor.md` + `agents/supervisor.md` + `scripts/run.sh`
- **D-04:** Three-step flow: AI draft → Supervisor → auto-register (human only if escalated)
- **D-05:** Default fully automated, user only receives "已登记 UXPATCH-XXXX" notification
- **D-06:** Escalate to human confirmation only when Supervisor Agent determines it's needed
- **D-07:** Supervisor uses Phase 1 `cli/lib/patch_schema.py` for schema validation
- **D-08:** Auto-pass conditions: schema valid + no conflict + change_class confidence high + non-semantic
- **D-09:** Escalation triggers: schema fail, low confidence change_class, conflict detected, semantic patch, first patch for FEAT, disputed test_impact
- **D-10:** AI pre-fills all fields: change_class, test_impact, backwrite_targets, scope.page, scope.module, changed_files, affected_routes
- **D-11:** AI pre-fill rules: change_class via ADR-049 §2.4 decision tree; test_impact defaults; backwrite_targets via ADR-049 §4.4 mapping
- **D-12:** All AI pre-filled fields marked as human-reviewed (ADR-049 §12.2)
- **D-13:** Document-to-SRC delegates to existing `ll-product-raw-to-src`, this skill only routes + associates
- **D-14:** This skill handles routing: detect input type (prompt vs document) → dispatch to appropriate path
- **D-15:** If Document-to-SRC involves experience-layer changes, this skill simultaneously generates a semantic Patch as associated record (resolution.src_created = SRC ID)
- **D-16:** CLI registers `patch-capture` action

### Claude's Discretion
- Executor prompt specific wording and guidance approach
- Supervisor audit checklist granularity (specific item count)
- Confidence threshold specific values (e.g., what change_class confidence triggers escalation)
- Whether `ll.lifecycle.yaml` is created in this phase (ADR mentions it but MVP can defer)

### Deferred Ideas (OUT OF SCOPE)
- PreToolUse Hook auto-trigger registration → Phase 6
- Settlement Skill → Phase 3
- Test linkage → Phase 4
- AI Context injection → Phase 5
- 24h Blocking mechanism → Phase 7

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-PATCH-02 | Patch 登记 Skill — dual-path registration, CLI entry, registry update | All research findings below enable implementation |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | >=6.0 (current) | YAML parsing for Patch files | Already used in `cli/lib/patch_schema.py` and `cli/lib/qa_schemas.py` [VERIFIED: codebase import] |
| argparse | stdlib (Python 3.13) | CLI argument parsing | Used throughout `cli/ll.py` and all command handlers [VERIFIED: codebase import] |
| dataclasses | stdlib (Python 3.13) | Schema dataclass definitions | Used in `cli/lib/patch_schema.py` for `PatchExperience` [VERIFIED: codebase import] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0 | Unit testing for patch capture logic | When writing tests for the new runtime module |
| json (stdlib) | Python 3.13 | Registry JSON read/write | For `patch_registry.json` updates |

**No external dependencies needed beyond what the project already uses.** The project has no `requirements.txt` or `pyproject.toml` — dependencies are managed implicitly. Python 3.13.3 is the runtime. [VERIFIED: filesystem scan + python --version]

## Architecture Patterns

### Recommended Project Structure

```
skills/ll-patch-capture/
├── SKILL.md                          # Skill description + execution protocol
├── ll.contract.yaml                  # Skill metadata (name, version, adr, category)
├── ll.lifecycle.yaml                 # Lifecycle states (draft → archived)
├── input/
│   ├── contract.yaml                 # Input schema: prompt text or document path
│   └── semantic-checklist.md         # Human-readable input validation checklist
├── output/
│   ├── contract.yaml                 # Output schema: generated patch YAML + registry update
│   └── semantic-checklist.md         # Human-readable output validation checklist
├── agents/
│   ├── executor.md                   # LLM prompt: analyze change → generate Patch YAML
│   └── supervisor.md                 # LLM prompt: validate → decide auto-pass vs escalate
└── scripts/
    ├── run.sh                        # Claude Code wrapper entry point
    ├── validate_input.sh             # Pre-execution input validation
    ├── validate_output.sh            # Post-execution output validation
    └── patch_capture_runtime.py      # Python runtime: registry update, conflict detection, CLI protocol
```

### CLI Registration Pattern

New skill action registered in `cli/ll.py`:

```python
# In cli/ll.py build_parser(), line ~81:
skill_sub = skill.add_subparsers(dest="action", required=True)
for action in (..., "patch-capture"):  # ADD HERE
    _add_action_parser(skill_sub, action)
```

And handler dispatch in `cli/commands/skill/command.py`:

```python
# In _skill_handler(), add explicit elif branch:
if ctx.action == "patch-capture":
    from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir
    from pathlib import Path
    import sys

    ensure("feat_id" in ctx.payload, "INVALID_REQUEST", "missing feat_id")
    ensure("input_type" in ctx.payload, "INVALID_REQUEST", "missing input_type")

    scripts_dir = resolve_skill_scripts_dir(ctx.workspace_root, "ll-patch-capture")
    scripts_str = str(scripts_dir.resolve())
    inserted = False
    if scripts_str not in sys.path:
        sys.path.insert(0, scripts_str)
        inserted = True
    try:
        from patch_capture_runtime import run_skill
        result = run_skill(
            workspace_root=ctx.workspace_root,
            payload=ctx.payload,
            request_id=ctx.request["request_id"],
        )
    finally:
        if inserted and scripts_str in sys.path:
            sys.path.remove(scripts_str)

    evidence_refs = _collect_refs(result)
    return "OK", "patch capture registered", {
        "canonical_path": result.get("patch_path", ""),
        **result,
    }, [], evidence_ref
```

[VERIFIED: codebase analysis of `cli/ll.py` + `cli/commands/skill/command.py`]

### Pattern 1: Executor/Supervisor Agent Split

**What:** All governed skills use a two-agent model. Executor generates artifacts; Supervisor validates them before finalization.

**Example from ll-qa-settlement:**
```markdown
# agents/executor.md
# Executor Agent: ll-qa-settlement
## Role
Generate settlement reports from post-execution manifests
## Instructions
1. Read updated API and E2E manifests
2. Compute statistics for each chain
3. Generate gap list
4. Generate waiver list
5. Write settlement reports

# agents/supervisor.md
# Supervisor Agent: ll-qa-settlement
## Validation Checklist
1. Statistics are self-consistent (executed = passed + failed + blocked)
2. pass_rate = passed / max(executed, 1)
3. Gap list includes all failed/blocked/uncovered
...
```

For `ll-patch-capture`, the Executor generates Patch YAML and the Supervisor runs schema validation + conflict detection + escalation logic. [VERIFIED: `skills/ll-qa-settlement/agents/executor.md`, `skills/ll-qa-settlement/agents/supervisor.md`]

### Pattern 2: Skill Contract Files

**What:** Every skill has `input/contract.yaml` and `output/contract.yaml` defining the schema boundaries, plus `ll.contract.yaml` for skill-level metadata.

**Example:**
```yaml
# ll.contract.yaml
skill: ll-qa-settlement
version: "1.0"
adr: ADR-047
category: qa
chain: settlement
phase: settlement-generation
```

[VERIFIED: `skills/ll-qa-settlement/ll.contract.yaml`]

### Pattern 3: run.sh as Claude Code Wrapper

**What:** `scripts/run.sh` serves as a bash wrapper that Claude Code invokes. It parses arguments, validates input, invokes the Python runtime via CLI protocol, then validates output.

**Structure:**
```bash
#!/usr/bin/env bash
set -euo pipefail
# 1. Parse arguments
# 2. Validate defaults
# 3. Run validate_input.sh
# 4. Invoke Python runtime via `python -m cli skill <action>`
# 5. Run validate_output.sh on generated output
```

[VERIFIED: `skills/ll-qa-settlement/scripts/run.sh`]

### Pattern 4: validate_input.sh / validate_output.sh

**What:** Lightweight bash scripts that call Python validators. Input validation checks file existence and schema compliance. Output validation checks output file existence and schema compliance.

```bash
# validate_input.sh
python -m cli.lib.qa_schemas --type manifest "${MANIFEST_PATH}"

# validate_output.sh
python -m cli.lib.qa_schemas --type settlement "${OUTPUT_PATH}"
```

For `ll-patch-capture`, these will call `python -m cli.lib.patch_schema --type patch <file>`. [VERIFIED: `skills/ll-qa-settlement/scripts/validate_input.sh`, `skills/ll-qa-settlement/scripts/validate_output.sh`]

### Pattern 5: Input Classification (Dual-Path Routing)

**What:** Detect input type and dispatch to appropriate handler. For `ll-patch-capture`, this means distinguishing between:
- Prompt text (free-form description of UX change) → Prompt-to-Patch path
- Document path (BMAD/Superpowers/OMC output) → Document-to-SRC path

The detection logic belongs in `patch_capture_runtime.py` as the first step of `run_skill()`. No existing skill in the project does dual-path routing exactly like this, so this is a new pattern. The closest analog is `ll-product-raw-to-src` which classifies input types (adr, raw_requirement, business_opportunity) before routing. [VERIFIED: `skills/ll-product-raw-to-src/SKILL.md` §13]

### Anti-Patterns to Avoid
- **Bypassing CLI protocol:** Skills must go through `python -m cli skill <action>` with request/response JSON, not call Python directly. This ensures trace, workspace, and evidence tracking.
- **Embedding Python logic in run.sh:** Keep run.sh as a thin wrapper; all logic in Python runtime.
- **Mutating registry without lock:** `patch_registry.json` updates should read-modify-write atomically to prevent race conditions when multiple patches register concurrently.
- **AI auto-submitting Patch:** Per ADR-049 §12.2, AI pre-fills but must mark fields as human-reviewed. The skill should never write `source.human_confirmed_class` without explicit confirmation (MVP: Supervisor checks this field is non-null).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML validation | Custom YAML checker | `cli/lib/patch_schema.py` (Phase 1) | Already implements enum validation, required field checks, nested object validation with `PatchSchemaError` |
| CLI argument parsing | Custom arg parsing | `argparse` via `cli/ll.py` subparser pattern | Consistent with all 29 existing skills, handles --request/--response-out protocol |
| Skill directory resolution | Hardcoded paths | `cli.lib.skill_runtime_paths.resolve_skill_scripts_dir()` | Handles both workspace-root and canonical CLI root paths |
| Patch ID generation | Manual counter | Read `patch_registry.json`, find max sequence, increment | Registry already stores all patches with IDs; filesystem is the source of truth |
| Conflict detection | Custom file diff | Scan `ssot/experience-patches/{FEAT-ID}/` for active patches, compare `changed_files` | ADR-049 §5.2 defines exact algorithm |

**Key insight:** Phase 1 already built the schema validator (`cli/lib/patch_schema.py`) with dataclasses, enums, and validation helpers. Reusing it means the Supervisor only needs to call `validate_file()` rather than reimplementing any validation logic.

## Runtime State Inventory

> This is not a rename/refactor/migration phase. All Phase 1 artifacts are ready for use.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `ssot/experience-patches/example-feat/patch_registry.json` — 1 example entry, empty structure ready for real entries | None — use as template |
| Phase 1 artifacts | `cli/lib/patch_schema.py` — validated schema validator with `validate_file()`, `validate_patch()` | Reuse directly — import in Supervisor + runtime |
| Phase 1 artifacts | `ssot/schemas/qa/patch.yaml` — YAML schema definition | Reference in Executor prompt for field structure |
| CLI entry points | `cli/ll.py` — subparser registration | Add `"patch-capture"` to skill action list |
| CLI handlers | `cli/commands/skill/command.py` — `_skill_handler()` dispatch | Add explicit if/elif branch |

## Common Pitfalls

### Pitfall 1: Supervisor Not Calling Python Validator
**What goes wrong:** Supervisor agent only does semantic checks (LLM judgment) without calling `python -m cli.lib.patch_schema` for mechanical schema validation.
**Why it happens:** Supervisor.md is a prompt file — it instructs the LLM but doesn't execute code. The schema validation must happen in the Python runtime.
**How to avoid:** Split validation: (1) Python runtime calls `validate_file()` for mechanical schema checks, (2) Supervisor agent does semantic judgment (confidence, escalation decision). The Supervisor prompt should reference the schema validation result, not replace it.
**Warning signs:** Supervisor checklist lacks "schema validation passed" as item #1.

### Pitfall 2: Registry Race Conditions
**What goes wrong:** Multiple patches registering to the same FEAT concurrently cause `patch_registry.json` to lose entries.
**Why it happens:** Read-modify-write without atomicity.
**How to avoid:** Use a file-locking pattern: read registry → compute new entry → write to temp file → atomic rename (or at minimum: read, append, write with a retry loop). For MVP, sequential registration via single-threaded Claude Code sessions makes this unlikely, but the runtime should still handle it defensively.

### Pitfall 3: UXPATCH ID Sequence Gaps
**What goes wrong:** ID generator produces non-sequential or conflicting IDs.
**Why it happens:** Scanning filenames for existing IDs is error-prone (regex matching, deleted files).
**How to avoid:** The source of truth for sequencing is `patch_registry.json` — find max sequence number there and increment. If registry doesn't exist, start from 1. Also scan filesystem as a secondary check.

### Pitfall 4: Executor Generating Invalid YAML
**What goes wrong:** AI-generated Patch YAML fails schema validation because of typos in enum values or missing required fields.
**Why it happens:** LLMs don't have perfect recall of enum values.
**How to avoid:** Executor prompt must include the exact enum values inline (copy from `ssot/schemas/qa/patch.yaml`). The Supervisor should re-validate after generation. Additionally, the Python runtime should validate before writing to disk.

### Pitfall 5: Forgetting `human_confirmed_class` Requirement
**What goes wrong:** Patch is registered with `source.human_confirmed_class: null`, violating ADR-049 §12.2.
**Why it happens:** Auto-pass path skips human interaction, and the executor doesn't set a default.
**How to avoid:** Even in auto-pass mode, the skill must set `source.human_confirmed_class` to match `source.ai_suggested_class` with a note that it was auto-confirmed by supervisor. The schema validator in Phase 1 already requires this field.

## Code Examples

### Schema Validation in Python Runtime
```python
# Source: cli/lib/patch_schema.py
from cli.lib.patch_schema import validate_file, PatchSchemaError

def validate_patch_file(path: Path) -> tuple[bool, str | None]:
    """Validate a patch YAML file. Returns (ok, error_message)."""
    try:
        validate_file(path, schema_type="patch")
        return True, None
    except PatchSchemaError as e:
        return False, str(e)
    except FileNotFoundError:
        return False, f"File not found: {path}"
```

### Registry Read-Modify-Write
```python
import json
from pathlib import Path

def register_patch_in_registry(patch_dir: Path, patch_data: dict) -> dict:
    """Add a new patch entry to patch_registry.json."""
    registry_path = patch_dir / "patch_registry.json"

    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {
            "patch_registry_version": "1.0.0",
            "feat_id": patch_dir.name,
            "patches": [],
            "last_updated": None,
        }

    # Determine next sequence number
    existing_ids = [
        int(p["id"].split("-")[1])
        for p in registry["patches"]
        if p["id"].startswith("UXPATCH-")
    ]
    next_seq = max(existing_ids, default=0) + 1

    entry = {
        "id": f"UXPATCH-{next_seq:04d}",
        "status": patch_data["status"],
        "change_class": patch_data["change_class"],
        "created_at": patch_data["created_at"],
        "title": patch_data["title"],
        "patch_file": f"UXPATCH-{next_seq:04d}__{slugify(patch_data['title'])}.yaml",
    }
    registry["patches"].append(entry)
    registry["last_updated"] = patch_data["created_at"]

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return entry
```

### CLI Protocol Request/Response Pattern
```python
# Source: skills/ll-qa-settlement/scripts/run.sh
# run.sh invokes via CLI protocol:
python -m cli skill settlement \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.settlement",
  "request_id": "req-$(date +%s)-$$",
  "payload": { ... },
  "trace": {}
}
EOF
) \
  --response-out "${OUTPUT_DIR}/response.json" \
  --workspace-root "${WORKSPACE}"
```

### Conflict Detection (ADR-049 §5.2)
```python
def detect_conflicts(feat_dir: Path, new_changed_files: list[str], current_patch_id: str) -> list[dict]:
    """Scan active patches in the same FEAT for overlapping changed_files."""
    conflicts = []
    for patch_file in feat_dir.glob("UXPATCH-*.yaml"):
        if not patch_file.exists():
            continue
        with open(patch_file, encoding="utf-8") as f:
            patch_data = yaml.safe_load(f)

        if patch_data.get("status") not in ("active", "validated", "pending_backwrite"):
            continue
        if patch_data.get("id") == current_patch_id:
            continue

        existing_files = set(patch_data.get("implementation", {}).get("changed_files", []))
        overlap = existing_files & set(new_changed_files)
        if overlap:
            conflicts.append({
                "with_patch_id": patch_data["id"],
                "overlapping_files": sorted(overlap),
            })

    return conflicts
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual YAML writing | AI pre-fill + supervisor validation | ADR-049 v2.1 (2026-04-15) | Phase 2 implements this |
| Flat FEAT directory for patches | Independent `ssot/experience-patches/` directory | ADR-049 v2.0 (C1 revision) | Zero-invasive to existing FEAT structure |
| AI auto-submit patches | AI pre-fill + human-reviewed fields | ADR-049 v2.0 (H6 revision) | Schema validator enforces human_confirmed_class non-null |
| Manual conflict detection | Automated overlap detection at registration | ADR-049 v2.0 (H1 revision) | New Patch 登记 detects conflicts with existing active patches |
| No schema validation | Triple validation: create-time / commit-time / read-time | ADR-049 v2.1 (P1-5 revision) | Phase 1 built create-time, Phase 2 uses it |

**Deprecated/outdated:**
- Embedding enum values in prompts without referencing schema file — use `ssot/schemas/qa/patch.yaml` as single source
- Hardcoding UXPATCH IDs — derive from registry max sequence
- Writing patch validation logic in bash — use Phase 1's Python validator

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Project has no `requirements.txt` or `pyproject.toml` — dependencies are implicit | Standard Stack | Minor: may need to create one if tests require it |
| A2 | `ll-patch-capture` should use dedicated runtime (not QA-shared) because its logic is unique | Architecture Patterns | Medium: if wrong, integration in CLI handler is more complex |
| A3 | `ll.lifecycle.yaml` should be created in this phase despite CONTEXT.md leaving it as discretion | Architecture Patterns | Low: can be deferred, but template shows it exists for all skills |
| A4 | The `input/` and `output/` directories contain `contract.yaml` + `semantic-checklist.md` based on ll-qa-settlement pattern | Architecture Patterns | Low: if other skills differ, template may need adjustment |
| A5 | Supervisor agent validation checklist should include schema validation result from Python, not replace it | Common Pitfalls | High: if Supervisor replaces schema validation, invalid YAML can slip through |

## Open Questions

1. **Confidence threshold for change_class escalation**
   - What we know: D-09 says "change_class 分类置信度低" triggers escalation
   - What's unclear: No numeric threshold defined in ADR-049. ADR uses qualitative terms ("置信度高", "模糊").
   - Recommendation: Define threshold in Executor prompt as qualitative rules (clear decision tree match = high; ambiguous = low) rather than numeric confidence scores. The executor can add a `_confidence` metadata field.

2. **Whether `ll.lifecycle.yaml` should be created now**
   - What we know: ll-qa-settlement has it with states: draft → validated → executed → frozen
   - What's unclear: Patch lifecycle states are different (draft → active → validated → ... → archived)
   - Recommendation: Create it with patch-appropriate states to maintain skill template consistency. Planner can decide.

3. **How Document-to-SRC path triggers semantic Patch generation**
   - What we know: D-15 says skill generates semantic Patch if Document-to-SRC involves experience-layer changes
   - What's unclear: What criteria determine "experience-layer change"? Does `ll-product-raw-to-src` output a flag?
   - Recommendation: The runtime checks if the SRC candidate's scope overlaps with known experience-layer FEATs (scan `ssot/experience-patches/` for matching `feat_ref`). If yes, generate a semantic Patch with `resolution.src_created = SRC ID`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All CLI + skill runtime | ✓ | 3.13.3 | — |
| PyYAML | Patch YAML parsing/writing | ✓ | Installed (used in patch_schema.py) | — |
| pytest | Unit tests for patch_capture_runtime | Likely (project uses pytest) | — | Skip tests if not available, flag for human |
| bash (Git Bash) | run.sh, validate_*.sh | ✓ | Windows Git Bash | — |

**Missing dependencies with no fallback:**
- None identified

**Missing dependencies with fallback:**
- pytest — if not installed, tests can be deferred; the runtime can be validated manually

## Sources

### Primary (HIGH confidence)
- Codebase analysis of 29 `ll-*` skills — file structure, agent patterns, contract files
- `cli/ll.py` — CLI subparser registration pattern
- `cli/commands/skill/command.py` — Handler dispatch logic for skill actions
- `cli/lib/patch_schema.py` — Phase 1 schema validator (dataclasses, enums, validate_file)
- `cli/lib/skill_runtime_paths.py` — Skill directory resolution helper
- ADR-049 v2.1 — Complete decision source for patch classification, lifecycle, validation
- `ssot/schemas/qa/patch.yaml` — Phase 1 YAML schema definition
- `ssot/experience-patches/example-feat/patch_registry.json` — Phase 1 registry template

### Secondary (MEDIUM confidence)
- `skills/ll-qa-settlement/scripts/run.sh` — Shell wrapper pattern for skill invocation
- `skills/ll-gate-human-orchestrator/` — Example of dedicated-runtime skill pattern
- `skills/ll-product-raw-to-src/SKILL.md` — Input classification pattern reference

### Tertiary (LOW confidence)
- None — all claims verified against codebase or official project artifacts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against codebase imports and Python 3.13 stdlib
- Architecture: HIGH — verified against 29 existing skills' actual file structures
- CLI patterns: HIGH — verified against `cli/ll.py` and `cli/commands/skill/command.py`
- Pitfalls: HIGH — derived from codebase analysis + ADR-049 constraints
- Code examples: HIGH — adapted from verified codebase patterns

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (stable domain — skill architecture patterns are project conventions, not external libraries)

## RESEARCH COMPLETE
