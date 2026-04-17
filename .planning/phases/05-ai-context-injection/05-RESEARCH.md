# Phase 5: AI Context 注入 - Research

**Researched:** 2026-04-17
**Domain:** AI context injection for Experience Patch Layer (ADR-049)
**Confidence:** HIGH

## Summary

Phase 5 implements change management awareness recording: when a user triggers a new SSOT chain generation (epic-to-feat, feat-to-tech, feat-to-ui, feat-to-proto), the AI agent is made aware of any existing validated or pending_backwrite Patches for that FEAT. The core principle is awareness, not enforcement — the AI sees the Patch context and records that it considered it, but is not forced to follow Patches (that is Phase 6's PreToolUse hook).

**Primary recommendation:** A dedicated `ll-patch-aware-context` utility skill that wraps `resolve_patch_context(feat_ref)` from Phase 4, generates a lightweight `patch-awareness.yaml` recording file, and is invoked as a prerequisite step by SSOT chain executor.md instructions — without restructuring any existing skill files.

## Standard Stack

### Core
No new libraries required. Phase 5 reuses existing Python 3.13 stdlib + PyYAML (already project dependency).

### Existing (Phase 4 Reuse)
| Module | Purpose | Verified Version |
|--------|---------|-----------------|
| `cli/lib/test_exec_artifacts.py` | `PatchContext` dataclass + `resolve_patch_context()` | Verified — exists, tested |
| `cli/lib/patch_schema.py` | `PatchExperience` dataclass + `validate_file()` | Verified — exists, tested |
| `ssot/experience-patches/` | Patch storage directory (per FEAT) | Verified — exists with example |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reuse `test_exec_artifacts.PatchContext` | New module in `cli/lib/` | **Not recommended** — PatchContext is already well-tested, has TOCTOU protection, and conflict resolution built in |
| Modify existing executor.md files | Add `ll-patch-aware-context` skill | **Chosen** — D-10 mandates no executor.md restructuring |

**No new packages to install.** All dependencies (PyYAML, Python 3.13 stdlib) are already in place.

## Architecture Patterns

### Recommended Project Structure

Phase 5 adds the following files:

```
skills/ll-patch-aware-context/
├── SKILL.md                          # Skill definition
├── input/
│   └── contract.yaml                 # Input contract (feat_ref)
├── output/
│   └── contract.yaml                 # Output contract (awareness record)
├── scripts/
│   ├── run.sh                        # Shell wrapper for CLI invocation
│   └── patch_aware_context.py        # Python: resolve + format awareness
└── ll.lifecycle.yaml                 # Lifecycle metadata
```

And one output artifact per SSOT chain invocation:
```
artifacts/{skill}/{run_id}/
├── patch-awareness.yaml              # Awareness recording (new)
└── ...existing outputs...
```

### Pattern: Awareness Recording (Not Enforcement)

**What:** Before the AI generates SSOT artifacts, it reads the Patch context and records its awareness. The output is a YAML file that documents: which patches exist, whether they were considered, and any divergence reasoning.

**When to use:** This pattern applies when the system needs to guarantee that AI agents acknowledge existing constraints without enforcing compliance. It is a "checklist acknowledgment" pattern, not a "gate" pattern.

**Flow:**
```
User triggers SSOT chain generation
    → ll-patch-aware-context resolves patches for feat_ref
    → Produces patch-awareness.yaml
    → AI reads awareness file before generating code
    → AI records its reasoning (compliance or divergence) in output
    → SSOT chain proceeds normally
```

### Pattern: Reuse resolve_patch_context() via Module Import

The `resolve_patch_context()` function in `cli/lib/test_exec_artifacts.py` already implements:
1. Scanning `ssot/experience-patches/{FEAT-ID}/` for `UXPATCH-*.yaml` files
2. Filtering by `status == "validated"` or `status == "pending_backwrite"` (D-08)
3. Building conflict resolution map
4. Computing TOCTOU-protected directory hash
5. Returning a frozen `PatchContext` dataclass with 7 typed fields

**Example (from source):**
```python
# Source: cli/lib/test_exec_artifacts.py:98-158
from cli.lib.test_exec_artifacts import resolve_patch_context

ctx = resolve_patch_context(workspace_root, feat_ref="FEAT-SRC-001-001")
# ctx: PatchContext(
#     has_active_patches=True,
#     validated_patches=[{...}, {...}],
#     pending_patches=[{...}],
#     conflict_resolution={".training-plan.id.detail": "use_patch"},
#     directory_hash="abc123...",
#     reviewed_at_latest="2026-04-16T10:00:00Z",
#     feat_ref="FEAT-SRC-001-001"
# )
```

### Anti-Patterns to Avoid
- **Do NOT modify existing executor.md files** — D-10 explicitly forbids restructuring. The awareness step is triggered by a new skill that runs as a prerequisite.
- **Do NOT inject Patch context into AI's system prompt** — ADR-049 §9.1 clarifies this is done via file reading, not prompt injection.
- **Do NOT enforce Patch compliance** — D-03 reserves enforcement for Phase 6. This phase only records awareness.
- **Do NOT duplicate resolve_patch_context()** — It is already implemented, tested (Phase 4), and has TOCTOU protection.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Patch directory scanning | Custom glob + YAML loading | `resolve_patch_context()` from `cli/lib/test_exec_artifacts.py` | Already implements TOCTOU protection, conflict resolution, status filtering, and returns typed dataclass |
| Patch YAML validation | Manual field checking | `validate_file()` from `cli/lib/patch_schema.py` | Already validates all required fields, enums, cross-field constraints (e.g., reviewed_at >= created_at) |
| Awareness file generation | Ad-hoc markdown | Structured `patch-awareness.yaml` with defined schema | Downstream AI agents can parse YAML reliably; free text is ambiguous |

**Key insight:** The Phase 4 implementation of `PatchContext` and `resolve_patch_context()` is production-ready and extensively tested (84 tests pass). Phase 5 should treat these as library functions, not reinvent them.

## Runtime State Inventory

> This is not a rename/refactor/migration phase. All state is file-based and newly created.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database, only YAML files on disk | None |
| Live service config | None — no external services | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | None | None |

## Common Pitfalls

### Pitfall 1: Context Budget Explosion
**What goes wrong:** Loading all Patches for a FEAT when there are 10+ active patches can consume significant context tokens, reducing AI quality on the primary task.
**Why it happens:** `resolve_patch_context()` returns the full Patch YAML data for every validated/pending patch.
**How to avoid:** The `patch_aware_context.py` utility should summarize patches beyond the first 5 (ADR-049 §12.1: 3000 token budget, max 10 full YAML). Show full YAML for most relevant patches, one-line summaries for others.
**Warning signs:** `len(ctx.validated_patches + ctx.pending_patches) > 5` — trigger summary mode.

### Pitfall 2: Import Path Confusion
**What goes wrong:** `resolve_patch_context()` is in `cli/lib/test_exec_artifacts.py`, not a dedicated `patch_context` module. The `test_exec_` prefix suggests it's test-specific, but it is a general-purpose Patch resolver.
**Why it happens:** Phase 4 implemented it as part of the test execution artifacts module (where it was first needed).
**How to avoid:** Document clearly that `resolve_patch_context()` is the canonical Patch context resolver, regardless of its module location. Consider a Phase 6 refactor to move it to `cli/lib/patch_context.py`, but do NOT do it in Phase 5 (out of scope, risks breaking Phase 4 tests).
**Warning signs:** Any new code that reimplements patch scanning logic instead of calling `resolve_patch_context()`.

### Pitfall 3: False Awareness Recording
**What goes wrong:** The AI records "I read the patches" without actually considering their impact on the generated code.
**Why it happens:** Awareness without enforcement creates a checkbox risk — the AI may acknowledge patches but ignore them.
**How to avoid:** The awareness output format includes a `divergence_rationale` field that forces the AI to explain why it did or did not follow each active Patch. This is not enforcement (Phase 6), but it creates an audit trail.
**Warning signs:** `divergence_rationale` is empty or generic ("no divergence needed").

### Pitfall 4: Empty Patch Directory
**What goes wrong:** When `resolve_patch_context()` finds no patches for a FEAT, it returns a context with `has_active_patches=False`. The awareness skill should still produce a recording file (documenting the absence).
**Why it happens:** Developers may assume "no patches = no output needed."
**How to avoid:** Always produce `patch-awareness.yaml` even when no patches exist. The `patch_scan_status` field should be `"none_found"` in this case.
**Warning signs:** Missing awareness file after SSOT chain generation.

## Code Examples

Verified patterns from existing source:

### Pattern 1: Resolve Patch Context for a FEAT
```python
# Source: cli/lib/test_exec_artifacts.py:98-158
from pathlib import Path
from cli.lib.test_exec_artifacts import resolve_patch_context

workspace_root = Path("/path/to/repo")  # or Path.cwd()
feat_ref = "FEAT-SRC-001-001"

ctx = resolve_patch_context(workspace_root, feat_ref=feat_ref)
# Returns PatchContext with validated_patches and pending_patches filtered
```

### Pattern 2: Write Awareness Recording
```python
from pathlib import Path
import yaml

def write_awareness_recording(
    patch_context,           # PatchContext from resolve_patch_context()
    output_dir: Path,        # Where to write the awareness file
    ai_reasoning: str = "",  # AI's reasoning (filled by executor agent)
) -> Path:
    """Produce a lightweight patch-awareness.yaml recording."""
    recording = {
        "patch_awareness": {
            "feat_ref": patch_context.feat_ref,
            "scan_timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "has_active_patches": patch_context.has_active_patches,
            "patch_scan_status": (
                "patches_found" if patch_context.has_active_patches else "none_found"
            ),
            "validated_patches_summary": [
                {
                    "id": p["id"],
                    "change_class": p.get("change_class"),
                    "title": p.get("title"),
                    "scope": {
                        "page": p.get("scope", {}).get("page"),
                        "module": p.get("scope", {}).get("module"),
                    },
                    "test_impact": bool(p.get("test_impact")),
                }
                for p in patch_context.validated_patches
            ],
            "pending_patches_summary": [
                {
                    "id": p["id"],
                    "change_class": p.get("change_class"),
                    "title": p.get("title"),
                }
                for p in patch_context.pending_patches
            ],
            "ai_consideration": ai_reasoning or "Patches reviewed; no divergence required.",
            "directory_hash": patch_context.directory_hash,
        }
    }

    output_path = output_dir / "patch-awareness.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(recording, f, sort_keys=False, allow_unicode=True)
    return output_path
```

### Pattern 3: Executor Agent Reads Awareness Before Generation
The AI agent's instruction (in the new skill's SKILL.md) should include:

```markdown
## Context Injection Step

Before generating any SSOT artifact:
1. Run `python scripts/patch_aware_context.py resolve --feat-ref <FEAT-ID> --output <output-dir>`
2. Read the generated `patch-awareness.yaml`
3. If `has_active_patches` is true, review each patch's scope and change_class
4. Document your consideration in the `ai_consideration` field of the awareness recording
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AI reads only SSOT (no Patch awareness) | AI reads SSOT + active Patches | This phase | Prevents AI from overwriting verified UX optimizations |
| Manual Patch lookup | Programmatic `resolve_patch_context()` | Phase 4 | Consistent, repeatable, TOCTOU-protected |
| Prompt injection for context | File-based awareness recording | This phase | Works within Claude Code's context model (no hook needed yet) |

**Deprecated/outdated:**
- `patch_registry.json` index: Phase 1 created this, but `resolve_patch_context()` scans the directory directly (more reliable, no index staleness risk)
- Manual patch scanning: Replaced by `resolve_patch_context()` which handles all edge cases

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `resolve_patch_context()` can be called with `workspace_root` as any directory containing `ssot/experience-patches/` | Code Examples | LOW confidence: function uses `workspace_root / "ssot" / "experience-patches"` path, so any valid workspace root works — but requires the SSOT directory structure |
| A2 | A new `ll-patch-aware-context` skill is the lightest integration point | Architecture Patterns | If existing executor.md files MUST be modified (contradicting D-10), this approach fails — but D-10 is explicit |
| A3 | `patch-awareness.yaml` as the awareness output format is sufficient for downstream consumption | Code Examples | If downstream agents expect a different format (e.g., JSON or embedded in existing artifact), additional mapping needed |
| A4 | No Python runtime changes needed beyond the existing `cli/lib/test_exec_artifacts.py` imports | Standard Stack | If the function needs to be refactored to separate concerns, a Phase 5 task would need to account for this |

## Open Questions

1. **Should awareness recording be a separate file or embedded in existing SSOT artifacts?**
   - What we know: D-09 says "Awareness form recorded in output artifacts." D-10 says "no executor.md restructuring."
   - What's unclear: Whether "output artifacts" means a new file (patch-awareness.yaml) or an embedded section in existing output (e.g., inside the TECH/UE/UI artifact).
   - Recommendation: Use a separate `patch-awareness.yaml` file — it is cleaner, easier to verify, and does not require modifying existing artifact formats.

2. **Should the awareness skill be auto-invoked or manually invoked?**
   - What we know: D-04 says "New SSOT chain generation is user-triggered, not auto-triggered."
   - What's unclear: Whether the awareness step should be part of the user-triggered SSOT chain (automatic prerequisite) or a separate manual step before SSOT chain generation.
   - Recommendation: Make it an automatic prerequisite of the SSOT chain. When the user triggers `feat-to-tech`, the awareness step runs first, then the chain proceeds. This is consistent with the "lightest possible" constraint — zero extra user steps.

3. **What is the exact invocation mechanism for the awareness skill from executor.md?**
   - What we know: executor.md files are AI agent instructions, not code. They tell the AI what to do.
   - What's unclear: Whether the AI agent should explicitly run a command (`python scripts/patch_aware_context.py`) or if the awareness file should already exist when the executor reads its instructions.
   - Recommendation: The executor.md for SSOT chain skills gains a new step: "Before generating artifacts, verify patch-awareness.yaml exists in the input/output directory. If not, run the awareness skill first." This is a behavioral instruction, not a structural change.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All Python scripts | Yes | 3.13.3 | -- |
| PyYAML | YAML read/write | Likely | -- | `pip install pyyaml` |
| `ssot/experience-patches/` | Patch scanning | Yes (with example) | -- | -- |
| `cli/lib/test_exec_artifacts.py` | `resolve_patch_context()` | Yes | -- | -- |
| `cli/lib/patch_schema.py` | `validate_file()` | Yes | -- | -- |

**Missing dependencies:** None detected.

## Sources

### Primary (HIGH confidence)
- `cli/lib/test_exec_artifacts.py` — PatchContext dataclass, resolve_patch_context(), mark_manifest_patch_affected() [VERIFIED: codebase]
- `cli/lib/patch_schema.py` — PatchExperience dataclass, validate_file(), resolve_patch_conflicts() [VERIFIED: codebase]
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 full text, especially §12.1 (Patch-Aware Context), §14.2 (代价与风险), §5.3 (Patch YAML Schema), §10.3 (conflict resolution) [VERIFIED: codebase]
- `skills/ll-dev-feat-to-tech/agents/executor.md` — Existing executor.md structure pattern [VERIFIED: codebase]
- `skills/ll-dev-feat-to-ui/agents/executor.md` — Existing executor.md structure pattern [VERIFIED: codebase]
- `skills/ll-dev-feat-to-proto/agents/executor.md` — Existing executor.md structure pattern [VERIFIED: codebase]
- `skills/ll-product-epic-to-feat/agents/executor.md` — Existing executor.md structure pattern [VERIFIED: codebase]
- `skills/ll-patch-capture/agents/executor.md` — Pattern for how skills use executor.md [VERIFIED: codebase]
- `skills/ll-experience-patch-settle/agents/executor.md` — Pattern for delta generation [VERIFIED: codebase]
- `tests/unit/test_test_exec_patch_context.py` — Tests confirming resolve_patch_context() behavior [VERIFIED: codebase]
- `.planning/phases/05-ai-context-injection/05-CONTEXT.md` — Phase decisions (D-01 through D-11) [VERIFIED: codebase]
- `.planning/REQUIREMENTS.md` — REQ-PATCH-05 specification [VERIFIED: codebase]
- `.planning/ROADMAP.md` — Phase 5 goal and success criteria [VERIFIED: codebase]

### Secondary (MEDIUM confidence)
- Phase 4 verification reports (`.planning/phases/04-test-integration/04-VERIFICATION.md`) — confirm resolve_patch_context() behavior in production [VERIFIED: codebase]

### Tertiary (LOW confidence)
- None — all critical claims verified against codebase source.

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — no new dependencies, all existing modules verified via codebase read
- Architecture: HIGH — patterns directly derived from existing executor.md structures and resolve_patch_context() implementation
- Pitfalls: MEDIUM — based on code analysis and ADR-049 specifications; runtime behavior not yet tested in production

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (30 days — stable codebase, no fast-moving dependencies)
