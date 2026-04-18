# Phase 10: 变更分级协同 (Change Grading Collaboration) — Research

**Researched:** 2026-04-18
**Domain:** SSOT change grading (Minor/Major), Experience Patch three-classification, FRZ revision chain
**Confidence:** HIGH

## Summary

Phase 10 integrates the ADR-049 three-classification model (visual / interaction / semantic) into the Patch capture layer and maps it to the ADR-050 two-tier change handling paths: Minor (Patch-level) and Major (FRZ re-freeze). The phase touches 4 skills and 2 CLI library files.

Key discovery: The `ll-frz-manage` CLI runtime already supports `--type revise` with `--previous-frz` and `--reason` parameters (lines 678-693 of `frz_manage_runtime.py`), and `frz_registry.py` already records `revision_type`, `previous_frz_ref`, and `revision_reason` fields. This means GRADE-03 (Major path) is approximately 80% implemented at the CLI level.

The largest gap is `skills/ll-experience-patch-settle` — it has only `__pycache__` compiled `.pyc` files with **no source files at all** (no SKILL.md, no agents, no runtime script). It must be built from scratch.

`skills/ll-patch-capture` has SKILL.md, contracts, and semantic checklists but its `scripts/` directory also only contains `__pycache__` — the runtime Python script needs to be built.

The `change_class` enum in `patch_schema.py` currently uses `ui_flow, copy_text, validation, navigation, layout, interaction, ...` — it does NOT include top-level `visual` or `semantic` values. This gap must be resolved to support the three-classification → Minor/Major mapping.

**Primary recommendation:** Build `ll-patch-capture` runtime with tri-classification classifier, build `ll-experience-patch-settle` from scratch with Minor/Major settle logic, add `grade_level` field to Patch schema (Minor/Major derived from `change_class`), leverage existing `ll-frz-manage --type revise` for Major path, enhance `ll-patch-aware-context` to surface grade level during injection.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.3 | YAML serialization/deserialization for Patch/FRZ files | Already used across all project CLI libs [VERIFIED: `import yaml` in patch_schema.py, frz_registry.py] |
| Python `dataclasses` | stdlib (3.13) | Frozen dataclasses for schema types | Project standard — all existing schemas use `@dataclass(frozen=True)` [VERIFIED: patch_schema.py, frz_schema.py] |
| Python `enum.Enum` | stdlib (3.13) | Enumerated types for change_class, grade_level, PatchStatus | Project standard for state/type enums [VERIFIED: patch_schema.py] |
| pytest | 9.0.2 | Unit testing for all new runtime scripts | Project standard test framework [VERIFIED: project pyproject.toml, existing test files] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `argparse` | stdlib (3.13) | CLI subcommand parsing for runtime scripts | All existing CLI runtimes use argparse [VERIFIED: frz_manage_runtime.py, patch_auto_register.py] |
| Python `subprocess` | stdlib (3.13) | Git diff/log invocation for change detection | Used in `resolve_patch_context` and `patch_auto_register.py` |
| `pathlib.Path` | stdlib (3.13) | File system operations | Project standard for all file I/O [VERIFIED: all CLI libs] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `patch_schema.py` ChangeClass extension | Separate grading enum | Extra indirection; simpler to derive `grade_level` from existing `change_class` at capture time |
| New standalone grading module | Add to `patch_schema.py` | Schema is the right home; grade_level is a derived property of change_class |
| Full YAML schema rewrite | JSON Schema | Project already standardizes on YAML-first; migration cost unjustified |

**Installation:** No new packages needed. All dependencies are stdlib or already installed.

**Version verification:**
- PyYAML 6.0.3 confirmed via `import yaml; yaml.__version__` [VERIFIED: runtime check]
- pytest 9.0.2 confirmed via `import pytest; pytest.__version__` [VERIFIED: runtime check]
- Python 3.13.3 [VERIFIED: runtime check]

## Architecture Patterns

### Recommended Project Structure

This phase modifies existing files and creates new ones:

```
skills/
├── ll-patch-capture/
│   ├── scripts/
│   │   └── patch_capture_runtime.py        # NEW: runtime with tri-classification
│   └── SKILL.md                            # MODIFY: update execution protocol for tri-classification
├── ll-experience-patch-settle/
│   ├── SKILL.md                            # NEW: settle skill definition
│   ├── ll.contract.yaml                    # NEW
│   ├── ll.lifecycle.yaml                   # NEW
│   ├── input/contract.yaml                 # NEW
│   ├── output/contract.yaml                # NEW
│   ├── agents/
│   │   ├── executor.md                     # NEW
│   │   └── supervisor.md                   # NEW
│   └── scripts/
│       ├── settle_runtime.py               # NEW: Minor settle + backwrite logic
│       └── test_settle_runtime.py          # NEW: unit tests
├── ll-frz-manage/
│   └── scripts/
│       └── frz_manage_runtime.py           # VERIFY: --type revise already works (80% done)
└── ll-patch-aware-context/
    └── scripts/
        └── patch_aware_context.py          # MODIFY: surface grade_level in awareness output

cli/lib/
├── patch_schema.py                         # MODIFY: add grade_level field, add GradeLevel enum
└── patch_awareness.py                      # MODIFY: add grade_level to PatchContext
```

### Pattern 1: Derived Grade Level from Change Class

**What:** The `grade_level` (Minor/Major) is not an independent field but derived deterministically from `change_class` per ADR-050 §6.1.

**When to use:** Every time a patch is captured or resolved.

```python
# Source: ADR-050 §6.1 + ADR-049 §4.4
from enum import Enum

class GradeLevel(str, Enum):
    MINOR = "minor"
    MAJOR = "major"

CHANGE_CLASS_TO_GRADE: dict[str, GradeLevel] = {
    # visual sub-classes → Minor
    "ui_flow": GradeLevel.MINOR,
    "copy_text": GradeLevel.MINOR,
    "layout": GradeLevel.MINOR,
    "navigation": GradeLevel.MINOR,
    "data_display": GradeLevel.MINOR,
    "accessibility": GradeLevel.MINOR,
    # interaction → Minor
    "interaction": GradeLevel.MINOR,
    # error_handling / performance → Minor (UI-layer only)
    "error_handling": GradeLevel.MINOR,
    "performance": GradeLevel.MINOR,
    # semantic → Major
    "semantic": GradeLevel.MAJOR,
    # other → default Minor, escalate if review determines otherwise
    "other": GradeLevel.MINOR,
}

def derive_grade(change_class: str) -> GradeLevel:
    return CHANGE_CLASS_TO_GRADE.get(change_class, GradeLevel.MINOR)
```

### Pattern 2: Major Path Triggers FRZ Revise

**What:** When a semantic change is detected, the system invokes `ll frz-manage freeze --type revise` instead of creating a standard patch.

```python
# Source: frz_manage_runtime.py lines 258-346 (already implemented)
# CLI already accepts: --type revise --reason "..." --previous-frz FRZ-xxx
# register_frz() in frz_registry.py already stores:
#   - revision_type
#   - previous_frz_ref
#   - revision_reason
```

### Pattern 3: Minor Settle Backwrite Targets

**What:** Minor patches have different backwrite behavior based on their sub-class:
- visual → `retain_in_code` (no backwrite required, optional UI detail update)
- interaction → backwrite to UI Spec, Flow Spec, TESTSET

### Anti-Patterns to Avoid
- **Do NOT add `semantic` as a value to the existing `ChangeClass` enum** — it would break backward compatibility with existing Patch YAML files. Instead, use a separate `GradeLevel` enum derived from `change_class`, and add `"semantic"` as a valid `change_class` value only if the schema explicitly supports it. **Actually**, the current `ChangeClass` enum in `patch_schema.py` does NOT include `semantic`. This must be added to support the tri-classification model from ADR-049. [VERIFIED: `cli/lib/patch_schema.py` ChangeClass enum, lines 24-37]
- **Do NOT re-implement FRZ revision logic** — `frz_manage_runtime.py` freeze command already handles `--type revise` (lines 330-343). Reuse the existing code path.
- **Do NOT build settle logic in ll-patch-capture** — capture and settle are separate phases (per ADR-049 §2.1). Keep the single-responsibility boundary.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRZ revision chain tracking | New revision registry | `cli/lib/frz_registry.py` `register_frz()` with `previous_frz` and `revision_type` params | Already stores parent_frz_ref, revision_reason, revision_type [VERIFIED: frz_registry.py lines 69-130] |
| FRZ ID validation | Regex in every file | `FRZ_ID_PATTERN` from `frz_schema.py` / `frz_registry.py` | Consistent `^FRZ-\d{3,}$` pattern already defined [VERIFIED] |
| Patch YAML serialization | Manual string building | `yaml.safe_dump()` with `sort_keys=False` | Project standard across all patch/FRZ code [VERIFIED] |
| Workspace root resolution | Hardcoded paths | `_find_workspace_root()` from `frz_manage_runtime.py` or `patch_context_injector.py` | Walk-up pattern already proven [VERIFIED] |
| Patch directory discovery | Re-scan logic | `_discover_patch_dirs()` from `patch_context_injector.py` | Already handles feat_ref scoping [VERIFIED] |
| CLI argument parsing | Custom arg handling | `argparse` subparsers pattern from `frz_manage_runtime.py` | Standard pattern with `--type` choices already in place [VERIFIED] |

**Key insight:** Phase 10 is primarily a **wiring and gap-filling** phase, not a greenfield build. ~60% of the needed plumbing exists; the missing pieces are: (1) the tri-classification runtime in ll-patch-capture, (2) the entire ll-experience-patch-settle skill, (3) the `grade_level` field addition to the Patch schema.

## Runtime State Inventory

> This phase is NOT a rename/refactor/migration phase. This section is omitted as per the instructions.

## Common Pitfalls

### Pitfall 1: Missing `semantic` in ChangeClass Enum
**What goes wrong:** The `ChangeClass` enum in `patch_schema.py` (line 24-37) does NOT include `"semantic"`. The output contract and semantic checklist both reference `visual, interaction, semantic` as valid values, but the schema validator would reject `change_class: semantic`.
**Why it happens:** The original ADR-049 implementation added fine-grained classes (ui_flow, copy_text, etc.) but omitted the top-level tri-class values.
**How to avoid:** Add `"semantic"` to `ChangeClass` enum. Also add `"visual"` if not present (it is not — visual is represented by sub-classes). The mapping layer should handle the visual→sub-class mapping.
**Warning signs:** `PatchSchemaError: change_class must be one of [...] got 'semantic'` during validation.

### Pitfall 2: ll-experience-patch-settle Has No Source Files
**What goes wrong:** The directory exists with only `__pycache__` files. Attempting to import or run anything will fail.
**Why it happens:** The skill directory was created but source files were never committed (or were lost during a worktree merge).
**How to avoid:** Build the entire skill from scratch: SKILL.md, contract files, agents, and runtime script. The `__pycache__` files contain compiled code that may hint at the original implementation but cannot be decompiled reliably.
**Warning signs:** `ModuleNotFoundError: No module named '...settle_runtime'`

### Pitfall 3: ll-patch-capture Runtime Script Missing
**What goes wrong:** Same as Pitfall 2 — only `__pycache__` exists in `scripts/`. The SKILL.md references a runtime script that does not exist as source.
**Why it happens:** Same root cause.
**How to avoid:** Build `patch_capture_runtime.py` from scratch. The SKILL.md execution protocol and the `__pycache__` filenames (`patch_capture_runtime.cpython-313.pyc`) confirm what the script should be named and its general purpose.

### Pitfall 4: Major Patch Should Not Create Standard Patch YAML
**What goes wrong:** If a semantic change creates a standard UXPATCH file AND triggers FRZ revise, you get duplicate tracking.
**Why it happens:** Unclear boundary between "record the change" and "handle the change."
**How to avoid:** Semantic (Major) changes should: (1) still record a Patch YAML for audit trail with `status: "proposed"` and `grade_level: "major"`, (2) trigger the FRZ revise flow, (3) NOT proceed to Minor settle logic. The settle runtime must branch on grade_level.

### Pitfall 5: Patch-Aware Context Does Not Distinguish Minor vs Major
**What goes wrong:** When injecting patch context, the AI does not know whether a patch is a Minor tweak or a Major semantic change waiting for FRZ re-freeze.
**Why it happens:** The current `patch_aware_context.py` and `PatchContext` dataclass do not include grade_level information.
**How to avoid:** Add `grade_level` field to `PatchContext` and update `summarize_patch()` to include it. The awareness output should flag Major patches differently.

## Code Examples

### Tri-Classification at Capture Time

```python
# Source: ADR-049 §4.1-4.3 + ADR-050 §6.1
# In patch_capture_runtime.py

from cli.lib.patch_schema import ChangeClass
from cli.lib.patch_schema import GradeLevel  # NEW: to be added

CLASSIFICATION_RULES = {
    # Gate 1: Affects business rules / state machine / data meaning?
    "semantic_indicators": [
        "新增用户动作", "修改状态机", "修改字段含义", "数据流变化",
        "验收标准改变", "业务规则变化", "新增正式用户动作",
    ],
    # Gate 2: Needs stakeholder alignment?
    # (determined by input complexity, document source)
    # Gate 3: Visual vs Interaction
    "visual_indicators": [
        "颜色", "尺寸", "间距", "图标", "文案优化", "样式",
        "布局调整", "默认排序",
    ],
    "interaction_indicators": [
        "页面跳转", "入口位置", "操作顺序", "页面流程",
        "确认步骤", "隐藏改为常驻",
    ],
}

def classify_change(input_text: str, input_type: str) -> tuple[ChangeClass, GradeLevel]:
    """Classify a change input into change_class and grade_level."""
    lower = input_text.lower()

    # Gate 1: semantic detection
    if any(ind in lower for ind in CLASSIFICATION_RULES["semantic_indicators"]):
        return ChangeClass.semantic, GradeLevel.MAJOR

    # Document-to-SRC path: if input is a structured document
    # with semantic-layer changes, classify as semantic
    if input_type == "document":
        # Check document content for semantic indicators
        # (implementation reads the doc and checks)
        pass

    # Gate 3: visual vs interaction
    if any(ind in lower for ind in CLASSIFICATION_RULES["interaction_indicators"]):
        return ChangeClass.interaction, GradeLevel.MINOR

    # Default to visual (sub-classified by file pattern)
    return ChangeClass.ui_flow, GradeLevel.MINOR
```

### Minor Settle Backwrite Logic

```python
# Source: ADR-049 §4.4 + ADR-050 §6.2
# In settle_runtime.py

BACKWRITE_MAP = {
    "ui_flow": {
        "must_backwrite_ssot": False,
        "backwrite_targets": ["UI 细则（可选）"],
    },
    "copy_text": {
        "must_backwrite_ssot": False,
        "backwrite_targets": [],
    },
    "layout": {
        "must_backwrite_ssot": False,
        "backwrite_targets": ["UI 细则（可选）"],
    },
    "navigation": {
        "must_backwrite_ssot": True,
        "backwrite_targets": ["UI Spec", "Flow Spec"],
    },
    "interaction": {
        "must_backwrite_ssot": True,
        "backwrite_targets": ["UI Spec", "Flow Spec", "TESTSET"],
    },
    "error_handling": {
        "must_backwrite_ssot": False,
        "backwrite_targets": [],
    },
    "performance": {
        "must_backwrite_ssot": False,
        "backwrite_targets": [],
    },
}

def settle_minor_patch(patch_yaml: dict, workspace_root: Path) -> dict:
    """Process a Minor patch: backwrite to targets, update status."""
    change_class = patch_yaml.get("change_class", "other")
    targets = BACKWRITE_MAP.get(change_class, {}).get("backwrite_targets", [])

    for target in targets:
        if target == "UI Spec":
            _backwrite_ui_spec(patch_yaml, workspace_root)
        elif target == "Flow Spec":
            _backwrite_flow_spec(patch_yaml, workspace_root)
        elif target == "TESTSET":
            _backwrite_testset(patch_yaml, workspace_root)

    # Update patch status
    patch_yaml["status"] = "applied"
    return patch_yaml
```

### FRZ Revise Trigger (Major Path)

```python
# Source: frz_manage_runtime.py lines 330-346 [VERIFIED: already implemented]
# This code ALREADY EXISTS — no need to rewrite, just invoke

# From freeze_frz() in frz_manage_runtime.py:
revision_type = getattr(args, "type", "new")  # Line 331
reason = getattr(args, "reason", None)         # Line 332
previous_frz = getattr(args, "previous_frz", None)  # Line 333

record, _ = register_frz(
    workspace_root, frz_id,
    msc_report=report,
    package_ref=str(freeze_yaml),
    previous_frz=previous_frz,
    revision_type=revision_type,
    reason=reason,
)
# Registry record now contains:
#   - revision_type: "revise"
#   - previous_frz_ref: <previous FRZ ID>
#   - revision_reason: <reason string>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary change classification (big/small) | Tri-classification (visual/interaction/semantic) mapped to Minor/Major | ADR-050 (2026-04-17) | More precise routing: interaction patches now get backwrite to TESTSET |
| Patch capture without grading | Auto-grading at capture time | This phase (new) | Eliminates manual classification step |
| Manual FRZ revision creation | CLI `--type revise` with automatic revision chain tracking | Already in frz_manage_runtime.py (Phase 7) | Revision chain is automatic, not manual |
| Patch awareness without grade context | Awareness output includes Minor/Major flag | This phase (new) | AI can distinguish "this is a small tweak" from "this needs FRZ re-freeze" |

**Deprecated/outdated:**
- The `ChangeClass` enum's current values (`ui_flow, copy_text, ...`) are sub-classes of `visual`. The top-level `visual` and `semantic` values are missing and must be added for the tri-classification model to work end-to-end.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ll-patch-capture/scripts/patch_capture_runtime.py` does not exist as source (only `__pycache__`) | Architecture Patterns, Pitfall 3 | If a source file exists elsewhere, work may be duplicated. Verified: glob returned no `.py` files in that directory. |
| A2 | `ll-experience-patch-settle/` has no source files at all (only `__pycache__`) | Architecture Patterns, Pitfall 2 | Verified: glob returned no `.py`, `.md`, or `.yaml` files except `__pycache__`. |
| A3 | The `__pycache__` compiled files in both directories are from a previous worktree session and cannot be reliably decompiled | Pitfalls | Correct — `.pyc` decompilation is unreliable and not worth the effort compared to building from spec. |
| A4 | `ChangeClass.semantic` is NOT in the current enum, but the output contract references it as a valid value | Pitfall 1, Code Examples | Verified: `patch_schema.py` line 24-37 does not include `semantic`. |
| A5 | The `--type revise` CLI path in `frz_manage_runtime.py` is fully functional for Major changes | Pattern 2, Code Examples | Verified: code at lines 330-346 reads `--type`, `--reason`, `--previous-frz` args and passes them to `register_frz()`. However, MSC validation still runs before freeze, which may be too strict for a "revise" operation that only needs to record a revision chain without full MSC re-validation. [MEDIUM confidence — needs validation during planning] |

## Open Questions

1. **Should `semantic` be added as a `ChangeClass` enum value, or should a separate `SemanticChangeClass` be used?**
   - What we know: The output contract references `change_class: one of visual, interaction, semantic`. The current enum has `ui_flow, copy_text, ...` but not `visual`, `interaction`, or `semantic` as top-level values.
   - What's unclear: Whether the fine-grained sub-classes should coexist with top-level tri-class values, or if the schema should migrate to tri-class as the primary dimension with sub-class as optional.
   - Recommendation: Add `"visual"`, `"interaction"`, `"semantic"` to `ChangeClass`. Keep existing sub-class values for backward compatibility. Add `grade_level` as a derived field.

2. **Does the `--type revise` flow need to skip MSC validation?**
   - What we know: `freeze_frz()` runs MSC validation before registration (line 291). For a revise operation triggered during execution, the input may not be a full FRZ package.
   - What's unclear: Whether the Major revise flow should accept partial input (just the changed semantic) or require a full FRZ package.
   - Recommendation: For Phase 10, `--type revise` should still require valid FRZ input but may need a relaxed MSC mode. The planner should consider adding a `--minimal` flag for revise operations.

3. **What triggers the `ll-patch-capture` runtime in the actual workflow?**
   - What we know: The SKILL.md describes "user prompt text described UX change OR document path" as input.
   - What's unclear: Is it triggered manually by the user, by the PreToolUse hook, or by the dev skill's validate_output.sh?
   - Recommendation: For Phase 10, keep the existing trigger model (manual invocation via skill) and document the workflow position clearly.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All runtime scripts | Yes | 3.13.3 | -- |
| PyYAML | YAML serialization | Yes | 6.0.3 | Manual YAML writer (already exists in patch_aware_context.py) |
| pytest | Unit tests | Yes | 9.0.2 | -- |
| git | Change detection via git diff | Yes | Available | File system comparison (fallback in resolve_patch_context) |
| `cli/lib/frz_schema.py` | FRZ package parsing | Yes | -- | -- |
| `cli/lib/frz_registry.py` | FRZ revision chain recording | Yes | -- | -- |
| `cli/lib/patch_schema.py` | Patch validation | Yes | -- | -- |
| `cli/lib/test_exec_artifacts.py` | resolve_patch_context | Yes | -- | -- |

**Missing dependencies:** None. All required libraries and tools are available.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None detected at project root (tests run directly) |
| Quick run command | `pytest skills/ll-patch-capture/scripts/ -x` |
| Full suite command | `pytest skills/ -x --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRADE-01 | Tri-classification at capture time | unit | `pytest skills/ll-patch-capture/scripts/test_patch_capture_runtime.py -x` | Need to create source + test |
| GRADE-02 | Minor settle backwrite to UI/TESTSET | unit | `pytest skills/ll-experience-patch-settle/scripts/test_settle_runtime.py -x` | Need to create source + test |
| GRADE-03 | Major FRZ revise with revision chain | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py -x -k revise` | Test file exists, may need new test cases |
| GRADE-04 | Patch-aware context includes grade_level | unit | `pytest skills/ll-patch-aware-context/ -x` | Need to add test for grade_level |

### Wave 0 Gaps
- [ ] `skills/ll-patch-capture/scripts/patch_capture_runtime.py` — main runtime with tri-classification
- [ ] `skills/ll-patch-capture/scripts/test_patch_capture_runtime.py` — covers GRADE-01
- [ ] `skills/ll-experience-patch-settle/` — entire skill (SKILL.md, agents, runtime, tests)
- [ ] `cli/lib/patch_schema.py` — add `GradeLevel` enum, `grade_level` field
- [ ] `cli/lib/patch_awareness.py` — add `grade_level` to `PatchContext`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | YAML schema validation via `patch_schema.py` + `validate_patch()` |
| V6 Cryptography | No | No cryptographic operations in this phase |
| V8 File Operations | Yes | Path traversal prevention in patch discovery (workspace root validation) |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization of untrusted input | Tampering | `yaml.safe_load()` only — never `yaml.load()` [VERIFIED: frz_manage_runtime.py line 55 rule] |
| Path traversal in file discovery | Information Disclosure | Workspace root validation in `_find_workspace_root()` [VERIFIED] |
| FRZ ID injection | Tampering | Regex validation `^FRZ-\d{3,}$` [VERIFIED: frz_registry.py] |
| Unconfirmed auto-classification | Integrity | Human confirmation required for `change_class` and `grade_level` per ADR-049 §4.5 |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] `cli/lib/patch_schema.py` — ChangeClass enum, validate_patch(), validate_file()
- [VERIFIED: codebase] `cli/lib/patch_awareness.py` — PatchContext dataclass, PatchAwarenessStatus enum
- [VERIFIED: codebase] `cli/lib/patch_auto_register.py` — detect_changes(), draft_patch_yaml(), _suggest_change_class()
- [VERIFIED: codebase] `cli/lib/patch_context_injector.py` — find_related_patches(), inject_context(), _discover_patch_dirs()
- [VERIFIED: codebase] `cli/lib/frz_registry.py` — register_frz() with revision chain support
- [VERIFIED: codebase] `skills/ll-frz-manage/scripts/frz_manage_runtime.py` — freeze command with --type revise support
- [VERIFIED: codebase] `cli/lib/test_exec_artifacts.py` — resolve_patch_context(), _classify_change()
- [VERIFIED: codebase] `ssot/schemas/qa/patch.yaml` — Patch YAML schema definition
- [VERIFIED: codebase] `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — three-classification model, decision tree
- [VERIFIED: codebase] `ssot/adr/ADR-050-SSOT语义治理总纲.md` — §6 change grading mechanism, Minor/Major mapping
- [VERIFIED: codebase] `.planning/REQUIREMENTS.md` — GRADE-01 through GRADE-04 requirements
- [VERIFIED: codebase] `.planning/ROADMAP.md` — Phase 10 structure and plans

### Secondary (MEDIUM confidence)
- [ASSUMED] The `__pycache__` files in `ll-patch-capture/scripts/` and `ll-experience-patch-settle/scripts/` are from a previous worktree merge and do not have corresponding `.py` source files in the current branch. This was verified by glob returning zero `.py` files in both directories.

### Tertiary (LOW confidence)
- None. All critical claims were verified against source code or official ADR documents.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via import/runtime check
- Architecture: HIGH — verified against existing codebase files and ADR documents
- Pitfalls: HIGH — verified by reading patch_schema.py, glob-ing directories, cross-referencing ADR-049 and ADR-050
- FRZ revise implementation status: HIGH — verified frz_manage_runtime.py lines 330-346 and frz_registry.py register_frz()
- MSC validation behavior during revise: MEDIUM — code shows MSC validation runs, but whether it should be skipped for revise is unclear

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (30 days — stable domain, ADR-governed)
