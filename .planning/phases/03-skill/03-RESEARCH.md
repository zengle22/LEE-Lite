# Phase 3: 结算 Skill + 回写工具 - Research

**Researched:** 2026-04-16
**Domain:** Experience Patch Settlement + Backwrite Draft Generation
**Confidence:** HIGH

## Summary

Phase 3 creates a new independent skill `ll-experience-patch-settle` that reads `pending_backwrite` patches, groups them by `change_class`, generates delta drafts and SRC candidates, updates patch statuses, and produces a settlement report. The skill follows the established `ll-*` file structure pattern (SKILL.md + executor.md + supervisor.md + contracts + scripts + lifecycle). Python runtime handles batch operations; LLM agents handle delta content generation and escalation decisions.

**Primary recommendation:** Follow the exact skill skeleton from `ll-qa-settlement` and `ll-patch-capture`, add a `settle_runtime.py` for batch scanning/registry updates, use executor for delta/SRC content generation, and keep zero new dependencies beyond the existing `pyyaml`/`pytest`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** 新建独立技能 `ll-experience-patch-settle`，不扩展 `ll-qa-settlement`（两者输入输出域完全不同）
- **D-02:** visual → `retain_in_code`，不回写主 SSOT（仅保留代码）
- **D-03:** interaction → `pending_backwrite`，生成 `ui-spec-delta.yaml` + `flow-spec-delta.yaml` + `test-impact-draft.yaml`
- **D-04:** semantic → `upgraded_to_src`，生成 `SRC-XXXX__{slug}.yaml` 候选文档
- **D-05:** 本阶段只生成新文件（delta 草案 + SRC 候选），不修改任何 frozen SSOT
- **D-06:** 回写 delta 文件必须带原文引用（类似 diff 格式，便于后续合并定位）
- **D-07:** "执行" = 更新 Patch 状态 + 写 delta 文件 + 出结算报告，无其他动作
- **D-08:** 默认 Agent 全自动处理（无需人工审核），仅在判定需要时升级人工确认
- **D-09:** Agent 按 `change_class` 自动分组批量处理，不确定/有冲突时才升级人工
- **D-10:** 升级人工确认条件：`change_class` 歧义、`test_impact` 不确定、同文件多 Patch 冲突

### Claude's Discretion

- Executor prompt 的具体措辞和引导方式
- delta 文件的具体格式（JSON vs YAML）
- 批量操作的分组策略粒度
- `ll.lifecycle.yaml` 是否本阶段创建

### Deferred Ideas (OUT OF SCOPE)

- 审核后实际合并 delta 到 frozen SSOT → 后续 Milestone
- Patch 冲突检测 + 索引/查询 → Phase 6 或独立
- Test-aware 联动（TESTSET 标记 needs_review）→ Phase 4
- PreToolUse hook 自动触发 → Phase 6
- 24h blocking 机制 → Phase 7

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-PATCH-03 | 结算 Skill + 回写工具 | Skill skeleton pattern identified, patch registry format known, patch_schema.py reusable, runtime batch scanning pattern from patch_capture_runtime.py, delta generation via executor agent |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.3 | Runtime for all skill scripts | [VERIFIED: python --version] Project standard per ADR-049 |
| PyYAML | 6.0.3 | Patch YAML read/write | [VERIFIED: yaml.__version__] Already used in patch_schema.py and patch_capture_runtime.py |
| pytest | 9.0.2 | Unit testing for runtime | [VERIFIED: pytest.__version__] Project standard per common/testing.md |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cli/lib/patch_schema.py | Existing | Patch validation during settlement | [VERIFIED: filesystem] Reuse for validating patches before settlement and delta outputs |
| cli/lib/errors.py | Existing | Error handling (ensure function) | [VERIFIED: filesystem] Used by patch_capture_runtime.py, reuse for consistent error handling |
| json (stdlib) | stdlib | patch_registry.json read/write | [VERIFIED: filesystem] Standard pattern from existing registry operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML (pyyaml) | ruamel.yaml (round-trip) | ruamel.yaml preserves formatting but adds dependency; pyyaml sufficient for read-then-write pattern |
| dataclass validation | pydantic v2 | pydantic provides runtime validation but is external dependency; project uses dataclass+enum pattern consistently |

**Installation:**
No new packages needed. All dependencies already available:
```bash
# Verify existing deps
python -c "import yaml; import pytest; print('OK')"
```

**Version verification:**
- Python 3.13.3 [VERIFIED: python --version]
- PyYAML 6.0.3 [VERIFIED: yaml.__version__]
- pytest 9.0.2 [VERIFIED: pytest.__version__]

## Architecture Patterns

### Recommended Project Structure
```
skills/ll-experience-patch-settle/
├── SKILL.md                    # Skill overview + execution protocol
├── ll.contract.yaml            # Skill metadata (skill, version, adr, category, chain, phase)
├── ll.lifecycle.yaml           # Lifecycle state definitions
├── input/
│   ├── contract.yaml           # Input requirements (feat_id, workspace)
│   └── semantic-checklist.md   # Pre-settlement validation checklist
├── output/
│   ├── contract.yaml           # Output requirements (resolved_patches.yaml, delta files)
│   └── semantic-checklist.md   # Post-settlement validation checklist
├── agents/
│   ├── executor.md             # LLM prompt for delta/SRC generation
│   └── supervisor.md           # LLM validation checklist
└── scripts/
    ├── run.sh                  # CLI entry wrapper
    ├── validate_input.sh       # Pre-settlement validation
    ├── validate_output.sh      # Post-settlement validation
    └── settle_runtime.py       # Python batch scanning + registry update
```

This structure is directly copied from the established pattern:
- `ll-qa-settlement/SKILL.md` [VERIFIED: filesystem] — 12 files across same directories
- `ll-patch-capture/SKILL.md` [VERIFIED: filesystem] — same pattern with runtime.py

### Pattern 1: Skill File Organization
**What:** Every `ll-*` skill uses the same skeleton: SKILL.md + ll.contract.yaml + ll.lifecycle.yaml + input/output contracts + agents/ + scripts/
**When to use:** Always — this is the project convention
**Example from ll-patch-capture:** [CITED: skills/ll-patch-capture/SKILL.md]
```markdown
---
name: ll-patch-capture
description: ADR-049 governed skill for dual-path experience patch registration.
---
## Required Read Order
1. ll.contract.yaml
2. input/contract.yaml
3. output/contract.yaml
4. agents/executor.md
5. agents/supervisor.md
```

### Pattern 2: CLI Wrapper (run.sh)
**What:** Bash script parses args, validates input, constructs JSON payload, calls `python -m cli skill <name>`, validates output
**When to use:** Every skill that needs CLI invocation
**Example from ll-qa-settlement:** [VERIFIED: skills/ll-qa-settlement/scripts/run.sh]
```bash
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

### Pattern 3: Python Runtime + LLM Agent Separation
**What:** Python handles filesystem operations (scan, read, write, update registry); LLM agent handles content generation (delta drafts, SRC candidates)
**When to use:** Skills with both mechanical and creative operations
**Example from patch_capture_runtime.py:** [CITED: skills/ll-patch-capture/scripts/patch_capture_runtime.py]
- Python: `get_next_patch_id()`, `detect_conflicts()`, `register_patch_in_registry()`, `run_skill()`
- LLM (executor.md): Analyzes change description, generates Patch YAML content

### Anti-Patterns to Avoid
- **Single-file skill without runtime separation:** The project consistently separates mechanical operations (Python runtime) from content generation (LLM agent). Mixing them breaks the executor/supervisor pattern.
- **Direct registry manipulation from agent:** The Python runtime is the sole registry writer [CITED: skills/ll-patch-capture/agents/executor.md line 111].
- **Skipping validate_input.sh / validate_output.sh:** Both existing skills include these for pre/post checks [VERIFIED: filesystem].

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Patch YAML validation | Custom YAML checker | `cli/lib/patch_schema.py validate_file()` | [VERIFIED: filesystem] Already handles all enum checks, required fields, nested objects |
| FEAT directory resolution | Manual path string concat | `Path(workspace_root) / "ssot" / "experience-patches" / feat_id` with path containment check | [VERIFIED: patch_capture_runtime.py lines 151-158] Security: prevents path traversal |
| Sequential Patch ID generation | Hardcoded counters | `get_next_patch_id()` from filesystem scan | [VERIFIED: patch_capture_runtime.py lines 25-52] Reads registry for max sequence, handles missing registry |
| Patch conflict detection | Simple string matching | `detect_conflicts()` with set intersection on `changed_files` | [VERIFIED: patch_capture_runtime.py lines 55-83] Scans active/validated/pending_backwrite patches |
| Error handling | print + sys.exit | `cli/lib/errors.py ensure()` | [VERIFIED: filesystem] Consistent error format with error codes |
| YAML safe loading | `yaml.load()` without Loader | `yaml.safe_load()` | [VERIFIED: patch_capture_runtime.py] Security: prevents arbitrary code execution |

**Key insight:** The `cli/lib/patch_schema.py` module already has all the dataclass definitions, enum validators, and file-level validation entry points. Settlement only needs to read patches through `validate_file()` to confirm they are valid before processing.

## Runtime State Inventory

> This is a greenfield skill creation phase. No runtime state exists yet for `ll-experience-patch-settle`.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — skill does not exist yet | N/A |
| Live service config | None — no external services involved | N/A |
| OS-registered state | None | N/A |
| Secrets/env vars | None required | N/A |
| Build artifacts | None | N/A |

**Note:** The skill will operate on existing `ssot/experience-patches/` data created by Phase 2, but no new runtime state is introduced by this phase's creation.

## Common Pitfalls

### Pitfall 1: Settlement Fatigue (Too Many Patches)
**What goes wrong:** Scanning 20+ patches per FEAT and processing each individually causes the executor to timeout or produce low-quality delta drafts.
**Why it happens:** LLM context budget gets consumed by reading multiple patch YAMLs + generating multiple delta files.
**How to avoid:** Python runtime pre-groups patches by `change_class` and passes grouped batches to executor. For interaction patches in the same FEAT, merge related patches before delta generation (ADR-049 §8.3 `merge-patches`).
**Warning signs:** Executor output has "unknown" or "N/A" fields in delta files; supervisor flags incomplete output.

### Pitfall 2: Delta Format Ambiguity
**What goes wrong:** Delta files generated without clear "before/after" text references make later merge operations error-prone.
**Why it happens:** Executor not instructed to include original text (ADR-049 §12.3, D-06).
**How to avoid:** Delta files MUST follow a structured format with `original_text`, `proposed_change`, and `rationale` fields. Use YAML (not JSON) to match the project's existing artifact format.
**Warning signs:** Delta files contain only "change X to Y" without quoting the original.

### Pitfall 3: Registry Update Atomicity
**What goes wrong:** If settlement partially fails (e.g., 3 of 5 patches updated), the registry becomes inconsistent — some patches marked `resolved` but their delta files not written.
**Why it happens:** No transaction-like guarantee in JSON file operations.
**How to avoid:** Python runtime writes all delta files first, THEN updates patch statuses in-memory, THEN writes registry in a single `json.dump()` call. If any step fails, the registry remains unchanged. [ASSUMED: Standard write-first-then-commit pattern; needs verification in implementation]
**Warning signs:** `patch_registry.json` last_updated is recent but some patches still show `pending_backwrite`.

### Pitfall 4: YAML Unwrapping Inconsistency
**What goes wrong:** Patch files have `experience_patch:` as the root key, but settlement code treats them as flat dicts.
**Why it happens:** `patch_capture_runtime.py` explicitly unwraps with `patch_data.get("experience_patch", patch_data)` [CITED: skills/ll-patch-capture/scripts/patch_capture_runtime.py lines 69, 200, 212]. Settlement runtime must use the same pattern.
**How to avoid:** Create a shared `unwrap_patch()` helper or consistently use `patch_data.get("experience_patch", patch_data)` pattern.
**Warning signs:** KeyError when accessing `patch["change_class"]` on a nested YAML structure.

### Pitfall 5: Same-File Multi-Patch Conflicts During Settlement
**What goes wrong:** Multiple patches modify the same file but propose different changes. Executor may generate conflicting delta drafts.
**Why it happens:** ADR-049 §5.2 conflict detection runs at registration time, not at settlement time. Patches registered at different times may accumulate conflicts.
**How to avoid:** Python runtime checks for overlapping `changed_files` among patches in the same settlement batch. If conflicts found, escalate to human (D-10).
**Warning signs:** Two patches in the same `change_class` group have intersecting `implementation.changed_files`.

## Code Examples

### Scanning Pending Backwrite Patches
```python
# Source: adapted from patch_capture_runtime.py detect_conflicts() pattern
from pathlib import Path
import yaml

def scan_pending_patches(feat_dir: Path) -> list[dict]:
    """Scan for patches with pending_backwrite status."""
    pending = []
    for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
        with open(patch_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Unwrap nested structure
        patch = data.get("experience_patch", data)
        if patch.get("status") == "pending_backwrite":
            patch["_file"] = str(patch_file)
            pending.append(patch)
    return pending
```

### Grouping by change_class
```python
from collections import defaultdict

def group_by_class(patches: list[dict]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for p in patches:
        groups[p["change_class"]].append(p)
    return dict(groups)
```

### Updating Patch Status and Registry
```python
import json
from datetime import datetime, timezone

def settle_patch(feat_dir: Path, patch: dict, new_status: str) -> None:
    """Update a single patch file status."""
    patch_file = Path(patch["_file"])
    with open(patch_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    root_key = "experience_patch" if "experience_patch" in data else None
    target = data[root_key] if root_key else data
    target["status"] = new_status
    target["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if root_key:
        data[root_key] = target
    else:
        data = target

    with open(patch_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
```

### Registry Batch Update
```python
def update_registry_statuses(feat_dir: Path, updated_patches: list[dict]) -> None:
    """Update registry entries after settlement."""
    registry_path = feat_dir / "patch_registry.json"
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    status_map = {p["id"]: p["status"] for p in updated_patches}
    for entry in registry["patches"]:
        if entry["id"] in status_map:
            entry["status"] = status_map[entry["id"]]

    registry["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct SSOT modification | Patch layer buffer with settlement | ADR-049 v2.1 (2026-04-15) | Small changes no longer pollute SSOT |
| All-or-nothing settlement | Batch settlement by change_class | ADR-049 §8.3 (C3 revision) | Reduces settlement fatigue |
| Manual delta generation | Agent-assisted delta with original text reference | This phase | Consistent, mergeable delta format |

**Deprecated/outdated:**
- **Settlement to ll-qa-settlement:** ADR-049 §12.4 originally assigned settlement to ll-qa-settlement skill. The discuss phase decision (D-01) overrides this — new independent skill is correct because input/output domains are fundamentally different (test results vs patch batch).
- **Manual registry updates:** Phase 2 established `patch_capture_runtime.py` as the sole registry writer. Settlement must use the same runtime, not duplicate logic.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Delta files should use YAML format (not JSON) | Architecture Patterns | Medium — planner may design JSON delta files, inconsistent with rest of project |
| A2 | Settlement runtime should be a separate `settle_runtime.py` (not extending patch_capture_runtime.py) | Architecture Patterns | Low — both are valid, separate file keeps concerns clean |
| A3 | `ll.lifecycle.yaml` should be created in this phase | Claude's Discretion | Low — other skills all have it, consistency matters |
| A4 | Executor agent generates delta file content (not Python) | Code Examples | Medium — if Python generates deltas, executor prompt is simpler but deltas lack semantic understanding of SSOT artifacts |

## Open Questions (RESOLVED)

1. **Delta file location within FEAT directory** — RESOLVED: Same level as patches within the FEAT's artifact subdirectory (e.g., `.artifacts/{FEAT-ID}/`), using naming convention to differentiate (`ui-spec-delta.yaml`, `flow-spec-delta.yaml`, `test-impact-draft.yaml` vs `UXPATCH-*.yaml`). No separate `deltas/` subdirectory needed for Phase 3.

2. **Batch settlement scope: per-FEAT or cross-FEAT?** — RESOLVED: Per-FEAT scope for Phase 3. The skill accepts a single `feat_id` parameter. Cross-FEAT settlement can be added later via `--all-feats` flag when needed.

3. **SRC candidate format for semantic patches** — RESOLVED: Follow existing SRC file naming convention (`SRC-XXXX__{slug}.yaml`) placed in the FEAT's artifact directory. The candidate should include minimal required fields: id, type, title, description, source_artifact reference (linking back to the semantic Patch ID), and status=candidate. Scan existing SRC files under `ssot/` for exact schema during implementation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime (settle_runtime.py) | ✓ | 3.13.3 | — |
| PyYAML | YAML read/write | ✓ | 6.0.3 | — |
| pytest | Unit tests | ✓ | 9.0.2 | — |
| bash | Shell wrappers (run.sh) | ✓ | (Git Bash on Windows) | — |
| cli/lib/patch_schema.py | Patch validation | ✓ | Existing | — |
| cli/lib/errors.py | Error handling | ✓ | Existing | — |

All dependencies are available. No missing items.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None detected at project root (Phase 2 tests ran without config) |
| Quick run command | `pytest skills/ll-experience-patch-settle/scripts/test_settle_runtime.py -x` |
| Full suite command | `pytest skills/ll-experience-patch-settle/scripts/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-PATCH-03 | Scan pending_backwrite patches | unit | `pytest ... -k test_scan_pending` | ❌ Wave 0 |
| REQ-PATCH-03 | Group by change_class | unit | `pytest ... -k test_group_by_class` | ❌ Wave 0 |
| REQ-PATCH-03 | Visual → retain_in_code | unit | `pytest ... -k test_settle_visual` | ❌ Wave 0 |
| REQ-PATCH-03 | Interaction → delta files | unit | `pytest ... -k test_settle_interaction` | ❌ Wave 0 |
| REQ-PATCH-03 | Semantic → SRC candidate | unit | `pytest ... -k test_settle_semantic` | ❌ Wave 0 |
| REQ-PATCH-03 | Update patch status | unit | `pytest ... -k test_update_status` | ❌ Wave 0 |
| REQ-PATCH-03 | Update registry | unit | `pytest ... -k test_update_registry` | ❌ Wave 0 |
| REQ-PATCH-03 | Generate settlement report | unit | `pytest ... -k test_settlement_report` | ❌ Wave 0 |
| REQ-PATCH-03 | Escalation on conflict | unit | `pytest ... -k test_escalation` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `skills/ll-experience-patch-settle/scripts/test_settle_runtime.py` — covers all REQ-PATCH-03 behaviors
- [ ] Framework install: already available (pytest 9.0.2)
- [ ] Fixture for example FEAT directory with sample patches

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | feat_id format validation (alphanumeric + hyphens + dots), path containment check |
| V4 Access Control | yes | Path traversal prevention in FEAT directory resolution |
| V6 Cryptography | no | No cryptographic operations |

### Known Threat Patterns for this Skill

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via crafted feat_id | Tampering | Regex validation + `resolve().startswith()` check [VERIFIED: patch_capture_runtime.py lines 143-158] |
| Malformed Patch YAML injection | Tampering | `yaml.safe_load()` + `patch_schema.py validate_file()` before processing |
| Registry race condition | Tampering | Read-modify-write with in-memory state, single write at end [ASSUMED: Pattern from patch_capture_runtime.py] |
| Overflow from massive patch batches | Availability | Batch size limit or warning if >50 patches per FEAT [ASSUMED] |

## Sources

### Primary (HIGH confidence)
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 full text, verified sections 4.4, 5.3, 7, 8, 12.3, 12.4
- `skills/ll-qa-settlement/SKILL.md` — Settlement skill structure template [VERIFIED: filesystem]
- `skills/ll-patch-capture/SKILL.md` — Patch capture skill structure [VERIFIED: filesystem]
- `skills/ll-patch-capture/scripts/patch_capture_runtime.py` — Runtime patterns for registry, conflict detection, ID generation [VERIFIED: filesystem]
- `cli/lib/patch_schema.py` — Patch schema validation [VERIFIED: filesystem]
- `ssot/schemas/qa/patch.yaml` — Patch YAML schema [VERIFIED: filesystem]
- `ssot/experience-patches/example-feat/patch_registry.json` — Registry format [VERIFIED: filesystem]
- `.planning/phases/03-skill/03-CONTEXT.md` — Phase 3 locked decisions [VERIFIED: filesystem]

### Secondary (MEDIUM confidence)
- `skills/ll-patch-capture/scripts/run.sh` — CLI wrapper pattern [VERIFIED: filesystem]
- `skills/ll-patch-capture/agents/executor.md` — Agent prompt structure with dual-path routing [VERIFIED: filesystem]
- `skills/ll-qa-settlement/scripts/run.sh` — Alternative CLI wrapper pattern [VERIFIED: filesystem]

### Tertiary (LOW confidence)
- A1 (delta format as YAML) — [ASSUMED] Based on project convention, not explicitly specified in ADR
- A2 (separate runtime file) — [ASSUMED] Follows convention but not mandated by any source
- A4 (executor generates deltas, not Python) — [ASSUMED] Inferred from agent responsibility split

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified via python --version, import checks
- Architecture: HIGH — verified via filesystem inspection of 2 existing skills
- Pitfalls: MEDIUM — derived from code analysis + ADR review; runtime behavior not yet observed
- Delta format specifics: LOW — ADR-049 §12.3 says "AI 自动生成回写清单 + 草案" but doesn't specify exact file format

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (30 days — stable domain, ADR-049 is frozen)
