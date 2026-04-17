---
name: ll-patch-aware-context
description: "ADR-049 governed skill for patch context injection before SSOT chain generation (awareness recording, not enforcement)."
---

# LL Patch-Aware Context

This skill provides change management awareness for SSOT chain generation. When a user triggers a new SSOT chain (epic-to-feat, feat-to-tech, feat-to-ui, feat-to-proto), this skill resolves any existing validated or pending_backwrite experience patches for the target FEAT, produces a structured awareness recording, and documents the AI's consideration — without enforcing patch compliance (enforcement is Phase 6).

## Canonical Authority

- **ADR:** `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md`
  - **§12.1:** Patch-Aware Context 注入
  - **§14.2:** AI Context 注入（REQ-PATCH-05 来源）
- **Upstream handoff:** User triggers SSOT chain generation (feat-to-tech, feat-to-ui, feat-to-proto)
- **Downstream consumer:** SSOT chain executor agents

## Runtime Boundary Baseline

- Interpret this workflow using `ssot/adr/ADR-038-运行时核心抽象边界与对象分层基线.MD`.
- This capability is a governed `Skill` for `SSOT Generation Prerequisite → Patch Awareness Recording`.

## Required Read Order

1. `ll.contract.yaml`
2. `input/contract.yaml`
3. `output/contract.yaml`
4. `agents/executor.md`

## Execution Protocol

1. **Receive feat_ref** from SSOT chain trigger (e.g., `FEAT-SRC-001-001`).

2. **Run the patch context resolver:**
   ```bash
   python scripts/patch_aware_context.py resolve \
     --workspace-root $WORKSPACE_ROOT \
     --feat-ref {feat_ref} \
     --output-dir {output_dir}
   ```
   This invokes `resolve_patch_context()` from Phase 4 (`cli/lib/test_exec_artifacts.py`) to scan `ssot/experience-patches/` for validated and pending_backwrite patches.

3. **Read the generated `patch-awareness.yaml`** from the output directory. This file contains the structured awareness recording with patch summaries, scan status, and directory hash.

4. **Evaluate active patches:** If `has_active_patches` is `true`, review each entry in `validated_patches_summary` and `pending_patches_summary`. For each patch, note its `change_class` (visual, interaction, semantic) and `scope` (page, module) to determine whether the patch's scope overlaps with the SSOT artifact you are about to generate.

5. **Record consideration:** Document your reasoning in the `ai_consideration` field. If you need to re-run with explicit reasoning:
   ```bash
   python scripts/patch_aware_context.py resolve \
     --workspace-root $WORKSPACE_ROOT \
     --feat-ref {feat_ref} \
     --output-dir {output_dir} \
     --ai-reasoning "{your consideration text}"
   ```
   Be specific — if following a patch, state which patch and how it is incorporated; if diverging, state why.

6. **Proceed with SSOT artifact generation.** The `patch-awareness.yaml` file serves as an audit record that patch context was acknowledged.

## Workflow Boundary

- **Input:** `feat_ref` (e.g., `FEAT-SRC-001-001`) — the FEAT reference identifier for which patch context should be resolved.
- **Output:** `patch-awareness.yaml` in the artifacts directory — structured YAML recording of patch awareness.
- **Out of scope:**
  - Patch enforcement (Phase 6 — PreToolUse hook)
  - 24h blocking mechanism (Phase 7)
  - Modifying existing SSOT skill files (per D-02, D-10)
  - PreToolUse hook integration (Phase 6)

## Non-Negotiable Rules

- **Do NOT modify existing SSOT skill executor.md files** (D-10). This skill runs as a prerequisite, not as a restructuring of existing skills.
- **Do NOT enforce Patch compliance** (D-03). This is awareness recording only. Enforcement is handled by Phase 6 PreToolUse hook.
- **Always produce `patch-awareness.yaml`** even when no patches exist for the target FEAT. Set `patch_scan_status` to `"none_found"` in that case (RESEARCH.md Pitfall 4).
- **Use `resolve_patch_context()` from Phase 4** (`cli/lib/test_exec_artifacts.py`). Do not reimplement patch scanning logic (D-07).
- **Only inject validated + pending_backwrite patches** (D-08, per ADR-049 §10.3). Draft and active patches are not yet ready for awareness injection.
