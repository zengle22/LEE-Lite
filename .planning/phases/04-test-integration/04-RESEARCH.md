# Phase 4: 测试联动规则 - Research

**Researched:** 2026-04-17
**Domain:** Patch-test integration, schema evolution, conflict detection unification, harness adaptation
**Confidence:** HIGH

## Summary

Phase 4 implements the test integration layer between Experience Patches and the ADR-047 dual-chain test governance system. The key changes are: (1) enforcing `test_impact` boolean flags on interaction/semantic Patches, (2) adding `patch_affected` + `patch_refs` to manifest items, (3) injecting Patch context into the test execution harness via `resolve_patch_context()`, (4) unifying three duplicate `detect_conflicts()` implementations into `patch_schema.py`, and (5) wiring conflict resolution into the execution loop so that `TEST_BLOCKED` maps to `lifecycle_status: blocked` per item.

Under ADR-047, TESTSET is a compatibility view. The truth source is `api-coverage-manifest` / `e2e-coverage-manifest` + `api-test-spec` / `e2e-journey-spec`. All "mark TESTSET" language from ROADMAP/REQUIREMENTS must be reinterpreted as "mark manifest items."

**Primary recommendation:** Modify 3 existing files (`patch_schema.py`, `test_exec_artifacts.py`, `test_exec_runtime.py`) and update 2 schema definitions (`ssot/schemas/qa/manifest.yaml`, `ssot/schemas/qa/patch.yaml`). Zero new files.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Keep ADR-049 boolean flags design (impacts_user_path, impacts_acceptance, impacts_existing_testcases, affected_routes, test_targets); no enum
- **D-02:** REQ-PATCH-04 test_impact enum is outdated
- **D-03:** interaction/semantic Patch AI auto-fills test_impact, marks human-reviewed
- **D-04:** Settlement blocks if test_impact null AND change_class interaction/semantic
- **D-05:** visual Patch test_impact remains optional (default no test impact)
- **D-06:** No lifecycle_status state machine changes (ADR-047 forward-only)
- **D-07:** New patch_affected: boolean + patch_refs: [string] on manifest item schema
- **D-08:** test_impact != none sets patch_affected: true + adds patch_id to patch_refs
- **D-09:** New test case scenarios get manifest item with lifecycle_status: drafted
- **D-10:** resolve_patch_context() added to test_exec_artifacts.py alongside resolve_ssot_context()
- **D-11:** test_exec_runtime.py injects patch context + pre-sync check hook
- **D-12:** No new standalone files; reuse existing test_exec_* module boundaries
- **D-13:** Unify to patch_schema.py resolve_patch_conflicts()
- **D-14:** Eliminate 3 duplicates: patch_capture_runtime.py, settle_runtime.py, new logic
- **D-15:** SSOT baseline, validated/pending Patch overrides in scope
- **D-16:** Multi-Patch conflict: latest validated wins (tie-break: larger patch_id)
- **D-17:** Irreconcilable conflict: TEST_BLOCKED = lifecycle_status: blocked, skip item
- **D-18:** visual -> WARN continue; interaction/semantic -> block; no manifest -> WARN + audit
- **D-19:** Patch-covered manifest items must retain acceptance refs
- **D-20:** resolve_patch_context() returns strict typed struct, no free strings to subprocess env
- **D-21:** reviewed_at timestamp, validate reviewed_at >= created_at
- **D-22:** TOCTOU protection via hash check on Patch directory

### Claude's Discretion
- patch_affected and patch_refs field schema definition format
- resolve_patch_context() specific struct design
- Conflict detection unified old function migration strategy (compat vs direct replace)
- reviewed_at format (ISO8601 vs Unix timestamp)

### Deferred Ideas (OUT OF SCOPE)
- Phase 5: AI Context injection (executor.md integration)
- Phase 6: PreToolUse hook auto-trigger Patch registration
- Phase 7: 24h Blocking mechanism
- Patch conflict auto-detection -> consumed by settle skill after unification
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-PATCH-04 | Patch schema test_impact field required; auto-mark manifest needs_review; Patch-aware Harness | Schema changes to patch.yaml + manifest.yaml; resolve_patch_context() in test_exec_artifacts.py; enforcement in test_exec_runtime.py; conflict unification in patch_schema.py |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13.3 | Runtime | Project standard [VERIFIED: python --version] |
| PyYAML | 6.x (system) | YAML parsing | Already imported in all existing modules [VERIFIED: codebase] |
| pytest | 8.x (system) | Unit testing | Project test framework [VERIFIED: project conventions] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib | stdlib | TOCTOU hash verification | D-22 Patch directory hash [VERIFIED: already imported in test_exec_artifacts.py] |
| json | stdlib | Registry reads | Already used in patch_capture_runtime.py [VERIFIED: codebase] |

**No new external dependencies needed.** This phase modifies existing Python modules only.

## Architecture Patterns

### Recommended Project Structure

No new directories or files. All changes are within existing modules:

```
cli/lib/
  patch_schema.py          # MODIFIED: add resolve_patch_conflicts(), reviewed_at validation, test_impact enforcement
  test_exec_artifacts.py   # MODIFIED: add resolve_patch_context(), PatchContext dataclass
  test_exec_runtime.py     # MODIFIED: inject patch context + pre-sync check
  qa_schemas.py            # MODIFIED: ManifestItem + patch_affected + patch_refs fields

ssot/schemas/qa/
  manifest.yaml            # MODIFIED: add patch_affected + patch_refs to item schema
  patch.yaml               # MODIFIED: add reviewed_at field
```

### Pattern 1: Context Resolution (resolve_ssot_context mirror)

**What:** `resolve_patch_context()` mirrors the existing `resolve_ssot_context()` pattern in `test_exec_artifacts.py` — it reads Patch files, validates them, and returns a typed dict suitable for injection into the execution context.

**When to use:** Every test execution run, to merge active/resolved Patch information into the test context.

**Existing pattern (from test_exec_artifacts.py:37-78):**
```python
def resolve_ssot_context(test_set, environment, ui_source_spec) -> dict[str, Any]:
    functional_areas = normalize_functional_areas(test_set)
    # ... returns typed dict with environment_contract, coverage_matrix, etc.
```

**New function mirrors this:**
```python
@dataclass(frozen=True)
class PatchContext:
    has_active_patches: bool
    validated_patches: list[dict]       # List of validated patch dicts
    pending_patches: list[dict]         # List of pending_backwrite patch dicts
    conflict_resolution: dict           # {coverage_id: resolution_action}
    directory_hash: str                 # TOCTOU protection (D-22)
    reviewed_at_latest: str | None      # Latest reviewed_at timestamp
```

### Pattern 2: Manifest Item Augmentation

**What:** Manifest items gain two new optional fields: `patch_affected` (boolean) and `patch_refs` (list of patch IDs).

**Why:** Per D-07, this is the mechanism to track which manifest items are influenced by active Patches, without touching the `lifecycle_status` state machine.

### Anti-Patterns to Avoid
- **Embedding test_impact in subprocess environment variables:** D-20 mandates strict typed struct. Do NOT stringify Patch data into `os.environ`.
- **Mutating lifecycle_status for test blocking:** D-06 forbids changing the state machine. Use a separate mechanism (per-case skip flag) instead.
- **Duplicating detect_conflicts() logic:** D-13/D-14 require unification. The old functions must delegate to the new central one.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conflict detection | New detect_conflicts() in test_exec_* | patch_schema.py resolve_patch_conflicts() | 3 existing implementations prove this is deceptively complex (file overlap, status filtering, path normalization) |
| YAML validation | Ad-hoc dict checks | patch_schema.py validate_patch() + qa_schemas.py validate_manifest() | Existing validators handle enum checking, required fields, type coercion |
| Directory hash | Custom file iteration | hashlib.sha1 of sorted file contents (test_exec_artifacts.py already uses sha1 checksums) | TOCTOU protection needs deterministic ordering |
| Manifest item writes | Direct YAML manipulation | qa_schemas.py ManifestItem dataclass + yaml.dump | Dataclass provides type safety, prevents field drift |

**Key insight:** The codebase already has robust schema validation (`patch_schema.py` + `qa_schemas.py`) and context resolution patterns (`resolve_ssot_context`). The phase extends these, not replaces them.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — `ssot/experience-patches/` has only `.gitkeep`, `README.md`, and one example UXPATCH-0001 file. No production patches exist yet. | None |
| Live service config | None — no external services registered. All test execution is file-based (YAML manifests/specs in `.artifacts/active/`). | None |
| OS-registered state | None — no cron jobs, scheduled tasks, or system services reference Patch IDs. | None |
| Secrets/env vars | None — Patch system uses no secrets. All files are plain YAML. | None |
| Build artifacts | None — no compiled artifacts, egg-info directories, or cached builds carry Patch-related strings. | None |

## Common Pitfalls

### Pitfall 1: TESTSET vs Manifest Confusion
**What goes wrong:** Planning tasks that "mark TESTSET as needs_review" because ROADMAP/REQUIREMENTS use outdated TESTSET terminology.
**Why it happens:** ADR-047 downgraded TESTSET to a compatibility view. The truth source is manifest + spec layer.
**How to avoid:** All tasks must target `api_coverage_manifest.items[]` (in `qa_schemas.py` ManifestItem), not any hypothetical TESTSET file. Use `patch_affected` + `patch_refs` fields.
**Warning signs:** Task descriptions containing "TESTSET", "test_set", or "TESTSET-SRC-*".

### Pitfall 2: test_impact Enforcement Level Mismatch
**What goes wrong:** Blocking at schema validation time vs. blocking at execution time. D-18 says visual -> WARN continue, interaction/semantic -> block. The enforcement point matters.
**Why it happens:** Two natural enforcement points exist: (a) `validate_patch()` in `patch_schema.py` when reading Patches, and (b) `run_narrow_execution()` in `test_exec_runtime.py` before execution.
**How to avoid:** Schema validation checks presence; harness execution checks enforcement. Schema raises `PatchSchemaError` for missing test_impact on interaction/semantic; harness blocks execution for unresolved conflicts.
**Warning signs:** Interaction/semantic Patches with `test_impact: null` passing validation.

### Pitfall 3: Conflict Resolution TOCTOU Race
**What goes wrong:** Patches are read and resolved at context-build time, but a new Patch is written before execution completes, invalidating the resolution.
**Why it happens:** File-based Patch storage has no locking. Multiple agents can write Patches concurrently.
**How to avoid:** D-22 mandates computing a hash of the Patch directory at context-build time and re-verifying before execution. Use `hashlib.sha1` over sorted file contents (existing pattern in `test_exec_artifacts.py:_checksum`).
**Warning signs:** `resolve_patch_context()` returns `directory_hash` but nothing checks it before `run_narrow_execution()`.

### Pitfall 4: Breaking Existing validate_file() API
**What goes wrong:** `patch_schema.py`'s `validate_file()` is called by both `patch_capture_runtime.py` and `settle_runtime.py`. Adding test_impact enforcement as a hard error could break Phase 2/3 workflows that legitimately create visual Patches without test_impact.
**Why it happens:** Visual Patches have optional test_impact per D-05. If enforcement is unconditional, visual Patches fail.
**How to avoid:** Enforcement is conditional: only block when `change_class` is `interaction` or `semantic` AND `test_impact` is null/empty. Visual Patches pass regardless.
**Warning signs:** Test failures in Phase 2/3 tests after adding validation.

### Pitfall 5: Old detect_conflicts() Functions Breaking
**What goes wrong:** `patch_capture_runtime.py:detect_conflicts()` (line 55-83) and `settle_runtime.py:detect_settlement_conflicts()` (line 266-284) are called by their respective `run_skill()` functions. Removing them without updating callers breaks Phase 2/3.
**Why it happens:** D-14 says "eliminate 3 duplicates" but these functions are actively imported and called.
**How to avoid:** Migration strategy: (1) Create `resolve_patch_conflicts()` in `patch_schema.py`, (2) Update old functions to delegate to it, (3) Keep old function signatures for backward compatibility, (4) Phase out after Phase 5.
**Warning signs:** `run_skill()` in capture/settle returning errors after refactoring.

### Pitfall 6: Manifest Write Path Unknown
**What goes wrong:** Need to mark manifest items as `patch_affected: true` but manifest files are generated by `ll-qa-api-manifest-init` and `ll-qa-api-spec-gen` skills, not directly writable by Patch code.
**Why it happens:** Manifests live in `.artifacts/active/` or skill output directories, not a stable path. The harness reads them via `load_yaml_document()` in `test_exec_runtime.py`.
**How to avoid:** The marking happens in-memory during `resolve_patch_context()` — the resolved context carries `patch_affected` and `patch_refs` flags that the harness uses for per-item decisions. Persistent manifest file updates happen via a separate manifest-update step (not in this phase's scope).
**Warning signs:** Tasks that try to "write to manifest.yaml" directly.

## Code Examples

### Conflict Detection Unified (patch_schema.py)

```python
# Source: Existing pattern from patch_capture_runtime.py:detect_conflicts() (lines 55-83)
# and settle_runtime.py:detect_settlement_conflicts() (lines 266-284)

from pathlib import Path
from typing import Any

def resolve_patch_conflicts(
    feat_dir: Path,
    patch_ids: list[str] | None = None,
    *,
    include_active: bool = True,
    include_validated: bool = True,
    include_pending: bool = False,
) -> list[dict[str, Any]]:
    """Unified conflict detection for experience patches.

    Scans patches in feat_dir, groups by changed_files overlap,
    returns conflict records. Replaces detect_conflicts() in
    patch_capture_runtime.py and detect_settlement_conflicts()
    in settle_runtime.py.

    Args:
        feat_dir: ssot/experience-patches/{FEAT-ID}/ directory
        patch_ids: If provided, only check these IDs against others
        include_active: Include 'active' status patches
        include_validated: Include 'validated' status patches
        include_pending: Include 'pending_backwrite' status patches
    """
    valid_statuses: set[str] = set()
    if include_active:
        valid_statuses.add("active")
    if include_validated:
        valid_statuses.add("validated")
    if include_pending:
        valid_statuses.add("pending_backwrite")

    patches: list[dict[str, Any]] = []
    for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
        try:
            import yaml
            with open(patch_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            patch = data.get("experience_patch", data)
        except Exception:
            continue
        if patch.get("status") not in valid_statuses:
            continue
        if patch_ids and patch.get("id") not in patch_ids:
            continue
        patches.append(patch)

    conflicts: list[dict[str, Any]] = []
    for i in range(len(patches)):
        for j in range(i + 1, len(patches)):
            files_a = set(patches[i].get("implementation", {}).get("changed_files", []))
            files_b = set(patches[j].get("implementation", {}).get("changed_files", []))
            overlap = files_a & files_b
            if overlap:
                # D-16: latest validated wins; tie-break: larger patch_id
                winner = _resolve_conflict_winner(patches[i], patches[j])
                conflicts.append({
                    "patch_a": patches[i]["id"],
                    "patch_b": patches[j]["id"],
                    "overlapping_files": sorted(overlap),
                    "winner": winner,
                    "resolution": "superseded" if winner != patches[i]["id"] else None,
                })
    return conflicts
```

### resolve_patch_context() (test_exec_artifacts.py)

```python
# Source: Mirrors resolve_ssot_context() pattern (test_exec_artifacts.py:37-78)
# D-20: returns strict typed struct, not free strings

@dataclass(frozen=True)
class PatchContext:
    """Strict typed struct for Patch context injection (D-20)."""
    has_active_patches: bool
    validated_patches: list[dict[str, Any]]
    pending_patches: list[dict[str, Any]]
    conflict_resolution: dict[str, str]  # {coverage_id: "skip" | "warn" | "use_patch"}
    directory_hash: str                   # TOCTOU protection (D-22)
    reviewed_at_latest: str | None        # Latest reviewed_at (D-21)
    feat_ref: str | None                  # Associated FEAT reference


def resolve_patch_context(
    workspace_root: Path,
    feat_ref: str | None = None,
) -> PatchContext:
    """Scan experience-patches for active/resolved Patches.

    Mirrors resolve_ssot_context() pattern. Returns typed PatchContext
    suitable for injection into test execution runtime.

    TOCTOU protection: computes sha1 hash of Patch directory contents.
    """
    patches_dir = workspace_root / "ssot" / "experience-patches"
    if not patches_dir.exists():
        return PatchContext(
            has_active_patches=False,
            validated_patches=[],
            pending_patches=[],
            conflict_resolution={},
            directory_hash="",
            reviewed_at_latest=None,
            feat_ref=feat_ref,
        )

    # Collect patches by status
    validated: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    all_patches: list[dict[str, Any]] = []

    for feat_dir in sorted(patches_dir.iterdir()):
        if not feat_dir.is_dir():
            continue
        if feat_ref and feat_dir.name != feat_ref:
            continue
        for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
            try:
                patch = _load_and_validate_patch(patch_file)
            except Exception:
                continue
            all_patches.append(patch)
            if patch.get("status") == "validated":
                validated.append(patch)
            elif patch.get("status") == "pending_backwrite":
                pending.append(patch)

    # D-22: TOCTOU hash
    dir_hash = _compute_patch_dir_hash(patches_dir)

    # D-15/D-16: Conflict resolution
    conflict_resolution = _build_conflict_resolution_map(all_patches)

    # D-21: Latest reviewed_at
    reviewed_at_latest = _latest_reviewed_at(all_patches)

    return PatchContext(
        has_active_patches=bool(all_patches),
        validated_patches=validated,
        pending_patches=pending,
        conflict_resolution=conflict_resolution,
        directory_hash=dir_hash,
        reviewed_at_latest=reviewed_at_latest,
        feat_ref=feat_ref,
    )
```

### test_impact Enforcement in Harness (test_exec_runtime.py)

```python
# Source: Inject into execute_test_exec_skill() before run_narrow_execution()
# D-18: visual -> WARN continue; interaction/semantic -> block

def _check_patch_test_impact(
    patch_context: PatchContext,
    workspace_root: Path,
) -> list[str]:
    """Verify test_impact declarations before execution.

    Returns list of warnings/errors. Empty list = proceed.
    """
    warnings: list[str] = []
    for patch in patch_context.validated_patches + patch_context.pending_patches:
        change_class = patch.get("change_class", "visual")
        test_impact = patch.get("test_impact")

        if change_class == "visual":
            # D-05: optional, WARN only if present but incomplete
            if test_impact and not test_impact.get("affected_routes"):
                warnings.append(
                    f"WARN: Patch {patch['id']} (visual) has test_impact "
                    f"but no affected_routes listed"
                )
            continue

        # D-04: interaction/semantic must have test_impact
        if not test_impact:
            return [f"ERROR: Patch {patch['id']} ({change_class}) missing test_impact"]

        if not test_impact.get("affected_routes"):
            return [f"ERROR: Patch {patch['id']} ({change_class}) has empty affected_routes"]

    return warnings
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TESTSET as truth source | Manifest + Spec as truth source, TESTSET compatibility view | ADR-047 v1.4 | Phase 4 tasks must target manifest items, not TESTSET files |
| test_impact as enum (none, path_change, assertion_change, new_case_needed) | Boolean flags (impacts_user_path, impacts_acceptance, impacts_existing_testcases, affected_routes, test_targets) | D-01/D-02 | Schema and validation use boolean dataclass, not enum matching |
| 3 duplicate detect_conflicts() functions | Single resolve_patch_conflicts() in patch_schema.py | This phase | Eliminates drift between capture, settle, and harness conflict logic |
| SSOT-only test context | SSOT + validated/pending Patch context | ADR-049 v2.1 | Harness must merge Patch rules with SSOT baseline |

**Deprecated/outdated:**
- REQ-PATCH-04 test_impact enum definition: superseded by D-02. Use boolean flags.
- ROADMAP "mark TESTSET as needs_review": superseded by ADR-047. Use `patch_affected` + `patch_refs` on manifest items.
- `.artifacts/{FEAT-ID}/experience-patches/` directory structure from original ADR: superseded by `ssot/experience-patches/{FEAT-ID}/` (ADR-049 v2.1, C1 revision).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `qa_schemas.py`'s `ManifestItem` is the only place manifest items are defined | Schema evolution | If other manifest item definitions exist, updates would be incomplete |
| A2 | Manifest files are read-only during test execution (no in-phase write-back) | Pitfall 6 | If manifests need persistent updates, a separate manifest-modification step is needed |
| A3 | `ssot/experience-patches/` is the only Patch directory (not `.artifacts/...`) | Code examples | If legacy patches exist in old path, they would be missed |

## Open Questions

1. **Manifest persistence: how should `patch_affected` and `patch_refs` be persisted?**
   - What we know: D-07/D-08 define the fields. `resolve_patch_context()` can set them in-memory.
   - What's unclear: Whether a separate step writes these back to the manifest YAML file, or if they exist only in the resolved context during execution.
   - Recommendation: In-phase, keep in-memory only. Persistent manifest updates are a separate concern (potentially Phase 5 or a manifest-refresh skill).

2. **How does `patch_affected: true` interact with existing manifest `lifecycle_status` values?**
   - What we know: D-06 says don't touch lifecycle_status state machine. D-17 says TEST_BLOCKED items get `lifecycle_status: blocked`.
   - What's unclear: Whether `blocked` is set on the manifest item or on the individual test case. The existing `lifecycle_status` enum already includes `blocked`.
   - Recommendation: Set `lifecycle_status: blocked` on the specific manifest item that conflicts, skip it during execution, but don't block the entire suite.

3. **What is the scope for `patch_affected` matching?**
   - What we know: D-08 says "set related manifest item's patch_affected: true". Patches have `feat_ref`, `page`, `module`. Manifest items have `feature_id`, `capability`, `endpoint`, `source_feat_ref`.
   - What's unclear: The join key between Patch scope and manifest items. `feat_ref` -> `source_feat_ref` is the most obvious, but not confirmed.
   - Recommendation: Match on `scope.feat_ref == item.source_feat_ref`. This is the only common identifier between the two schemas.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All phase code | Yes | 3.13.3 | -- |
| PyYAML | YAML parsing/loading | Yes | Installed (verified via imports) | -- |
| pytest | Unit testing | ASSUMED yes | -- | Install via pip if missing |
| ssot/experience-patches/ | Patch scanning | Yes (empty, has example) | -- | Handle empty directory gracefully |

**Missing dependencies with fallback:**
- None identified. All dependencies are stdlib or already installed.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — no auth in this phase |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A — file-based, no access control |
| V5 Input Validation | Yes | patch_schema.py validate_patch(), qa_schemas.py validate_manifest() |
| V6 Cryptography | No | hashlib.sha1 for TOCTOU hash (not security crypto) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via feat_id | Tampering | Existing: `str(feat_dir).startswith(str(base_dir.resolve()))` check in patch_capture_runtime.py [VERIFIED: codebase] |
| Malformed Patch YAML injection | Tampering | Existing: yaml.safe_load() + validate_patch() [VERIFIED: codebase] |
| TOCTOU race on Patch directory | Tampering | D-22: directory hash before/after execution [DECISION] |
| AI-generated test_impact spoofing | Spoofing | D-03/D-06: human-reviewed field, validated reviewed_at >= created_at [DECISION] |

## Sources

### Primary (HIGH confidence)
- `cli/lib/patch_schema.py` — Full code read: PatchTestImpact dataclass, PatchExperience, validate_patch, validate_file
- `cli/lib/test_exec_artifacts.py` — Full code read: resolve_ssot_context pattern, build_test_case_pack
- `cli/lib/test_exec_runtime.py` — Full code read: execute_test_exec_skill, run_narrow_execution entry point
- `cli/lib/test_exec_execution.py` — Full code read: _execute_round, execute_cases, run_narrow_execution loop
- `cli/lib/qa_schemas.py` — Full code read: ManifestItem dataclass, validate_manifest
- `ssot/schemas/qa/manifest.yaml` — Full code read: API coverage manifest schema
- `ssot/schemas/qa/patch.yaml` — Full code read: Experience Patch schema
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — Full ADR text
- `.planning/phases/04-test-integration/04-CONTEXT.md` — Phase decisions D-01 through D-22

### Secondary (MEDIUM confidence)
- `skills/ll-patch-capture/scripts/patch_capture_runtime.py` — detect_conflicts() implementation
- `skills/ll-experience-patch-settle/scripts/settle_runtime.py` — detect_settlement_conflicts(), test-impact-draft.yaml generation
- `.planning/ADR047-IMPLEMENTATION-PROPOSAL.md` — Dual-chain architecture, CLI protocol

### Tertiary (LOW confidence)
- None — all critical claims verified against source code.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against existing imports, no new dependencies
- Architecture: HIGH — based on direct code analysis of all target modules
- Pitfalls: HIGH — 6 of 6 identified from concrete code patterns; 1 assumption flagged

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (30 days — stable codebase, no fast-moving dependencies)
