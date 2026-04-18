# Phase 8: FRZ→SRC 语义抽取链 - Research

**Researched:** 2026-04-18
**Domain:** FRZ semantic extraction pipeline, projection invariance guards, anchor registry integration, drift detection
**Confidence:** HIGH

## Summary

Phase 8 delivers the extract mode for `ll-frz-manage` (FRZ→SRC), adds `extract` subcommands to `src_to_epic.py` (FRZ→EPIC) and `epic_to_feat.py` (FRZ→FEAT), implements a drift detector library, and integrates projection invariance guards across the full SSOT chain. All extraction uses deterministic rule-template projection (D-01), reuses existing SSOT package formats (D-02), and registers anchors at extraction time (D-09). The cascade mode chains the full FRZ→SRC→EPIC→FEAT→TECH/UI/TEST/IMPL pipeline with gate审核 between each step.

**Primary recommendation:** Build `cli/lib/drift_detector.py` first (08-01), then implement `extract_frz()` in `frz_manage_runtime.py` (08-02), then add `extract` subcommands to existing skill scripts (08-03, 08-04). Each step reuses Phase 7 infrastructure (`anchor_registry.py`, `frz_schema.py`, `frz_registry.py`) and the existing gate CLI (`cli/commands/gate/command.py`).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (argparse, dataclasses, pathlib) | 3.13 | CLI parsing, DTOs, file operations | Project standard — all Phase 7 code uses these [VERIFIED: codebase] |
| PyYAML | 6.0.3 | YAML read/write for FRZ, anchor registry, SSOT packages | Used by all Phase 7 modules [VERIFIED: codebase] |
| pytest | 9.0.2 | Unit + integration testing | Existing Phase 7 test suite uses pytest [VERIFIED: test files] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `cli.lib.errors.CommandError` | — | Structured error handling | All new CLI code [VERIFIED: errors.py] |
| `cli.lib.fs` | — | Filesystem helpers (ensure_parent, load_json, write_text) | All file I/O [VERIFIED: fs.py] |
| `cli.lib.anchor_registry.AnchorRegistry` | — | Anchor ID registration with FRZ reference + projection path | Register anchors during extract [VERIFIED: anchor_registry.py] |
| `cli.lib.frz_schema.FRZPackage, MSCValidator` | — | FRZ package loading and MSC validation | Read FRZ data for extraction [VERIFIED: frz_schema.py] |
| `cli.lib.frz_registry` | — | FRZ registry lookup (get_frz, list_frz) | Resolve FRZ ID to frozen data [VERIFIED: frz_registry.py] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rule-template projection (D-01) | LLM-based extraction | LLM is non-deterministic, excluded by ADR-050 out of scope |
| Field-level diff for drift | MSC dimension-level comparison | Too coarse; D-05 mandates anchor-level granularity |

**Installation:** No new packages needed. Phase 7 dependencies (PyYAML, pytest) are already installed.

**Version verification:** Python 3.13.3, pytest 9.0.2, PyYAML 6.0.3 — verified on target machine [VERIFIED: runtime check].

## Architecture Patterns

### Recommended Project Structure

```
cli/lib/
├── drift_detector.py          # NEW — 08-01: semantic drift detection
├── projection_guard.py        # NEW — 08-02: projection invariance guard
├── frz_extractor.py           # NEW — 08-02: FRZ→SRC extraction rules
├── test_drift_detector.py     # NEW — unit tests for drift detector
├── test_projection_guard.py   # NEW — unit tests for projection guard
└── test_frz_extractor.py      # NEW — unit tests for FRZ extractor

skills/ll-frz-manage/scripts/
├── frz_manage_runtime.py      # EXISTING — extract_frz() implementation (was stub)
└── test_frz_manage_runtime.py # EXISTING — add extract tests

skills/ll-product-src-to-epic/scripts/
├── src_to_epic.py             # EXISTING — add extract subcommand
├── src_to_epic_runtime.py     # EXISTING — add extract workflow
├── src_to_epic_extract.py     # NEW — FRZ-based EPIC extraction logic
└── test_src_to_epic_extract.py # NEW

skills/ll-product-epic-to-feat/scripts/
├── epic_to_feat.py            # EXISTING — add extract subcommand
├── epic_to_feat_runtime.py    # EXISTING — add extract workflow
├── epic_to_feat_extract.py    # NEW — FRZ-based FEAT extraction logic
└── test_epic_to_feat_extract.py # NEW
```

### Pattern 1: Subcommand Dispatch (from existing scripts)

**What:** All skill scripts use `build_parser()` → `add_subparsers()` → command dispatch pattern.

**When to use:** Adding `extract` to existing CLI scripts.

**Example:**
```python
# From src_to_epic.py L89-138 — established pattern
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the src-to-epic workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ... existing subparsers ...

    # NEW: extract subcommand
    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--frz", required=True, help="FRZ ID to extract from")
    extract_parser.add_argument("--repo-root")
    extract_parser.add_argument("--output")
    extract_parser.set_defaults(func=command_extract)
    return parser
```
[VERIFIED: src_to_epic.py L89-138, epic_to_feat.py L92-141]

### Pattern 2: CommandError + ensure() Error Handling

**What:** All CLI code uses `CommandError(status_code, message)` with predefined status codes and `ensure(condition, status_code, message)` for preconditions.

**When to use:** All new extract/drift/guard code.

**Example:**
```python
# From errors.py L52-54
def ensure(condition: bool, status_code: str, message: str, diagnostics: list[str] | None = None) -> None:
    if not condition:
        raise CommandError(status_code, message, diagnostics or [])
```
[VERIFIED: errors.py]

### Pattern 3: Frozen Dataclass DTOs

**What:** All data transfer objects use `@dataclass(frozen=True)` for immutability.

**When to use:** DriftResult, ProjectionGuardResult, ExtractResult DTOs.

**Example:**
```python
# From frz_schema.py L61-66 — CoreJourney as frozen dataclass
@dataclass(frozen=True)
class CoreJourney:
    id: str
    name: str
    steps: list[str]
```
[VERIFIED: frz_schema.py]

### Pattern 4: Workspace Root Discovery

**What:** Scripts walk up filesystem looking for `.planning` or `ssot` directory markers.

**When to use:** Extract commands need workspace root to access registry files.

**Example:**
```python
# From frz_manage_runtime.py L109-136 — _find_workspace_root()
def _find_workspace_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path.cwd()
    current = start.resolve()
    while True:
        if (current / ".planning").exists() or (current / "ssot").exists():
            return current
        parent = current.parent
        if parent == current:
            raise CommandError("INVALID_REQUEST", "Workspace root not found...")
        current = parent
```
[VERIFIED: frz_manage_runtime.py L109-136]

### Anti-Patterns to Avoid

- **Do NOT modify existing `run`/`executor-run` commands** — D-07 mandates keeping existing behavior unchanged. Add only `extract` subcommand.
- **Do NOT use field-level diff for drift** — D-05 mandates anchor-level comparison. Field diff produces noise.
- **Do NOT skip gate in cascade mode** — D-08 mandates gate审核 after each extraction step.
- **Do NOT use LLM for extraction** — ADR-050 out of scope, D-01 mandates rule-template projection.
- **Do NOT mutate FRZ data during extraction** — FRZ is frozen truth source. Extract reads, never writes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRZ YAML parsing | Custom YAML loader | `cli.lib.frz_schema._parse_frz_dict()` + `MSCValidator.validate_file()` | Handles nested dataclass conversion, ID format validation, status enum parsing [VERIFIED: frz_schema.py L174-321] |
| Anchor registration | New registry code | `cli.lib.anchor_registry.AnchorRegistry` | Already handles ID validation, duplicate detection, YAML persistence [VERIFIED: anchor_registry.py] |
| FRZ ID validation | New regex | `cli.lib.frz_schema.FRZ_ID_PATTERN` (`^FRZ-\d{3,}$`) | Already defined and tested [VERIFIED: frz_schema.py L49] |
| Gate submission | New gate client | `cli.commands.gate.command` via subprocess or `run_with_protocol` | Existing gate handles submit-handoff→evaluate→decide→materialize→dispatch [VERIFIED: gate/command.py L773-789] |
| Error handling | Custom error classes | `cli.lib.errors.CommandError` + `ensure()` | Standard status codes, exit code mapping, result_status property [VERIFIED: errors.py] |
| File I/O | Direct open/write | `cli.lib.fs` (ensure_parent, write_text, read_text) | Consistent error handling, parent dir creation, UTF-8 encoding [VERIFIED: fs.py] |

**Key insight:** Phase 7 already built all the infrastructure this phase needs. The new code is primarily orchestration: read FRZ → apply projection rules → validate against derived_allowed → register anchors → run drift detector → output SSOT package → gate审核.

## Runtime State Inventory

> This is a greenfield phase (new features), not a rename/refactor/migration phase. Runtime State Inventory is N/A.

| Category | Status |
|----------|--------|
| Stored data | N/A — no existing extract data to migrate |
| Live service config | N/A — no external services |
| OS-registered state | N/A — no OS registrations |
| Secrets/env vars | N/A — no secrets needed |
| Build artifacts | N/A — no artifacts to update |

**Note:** The `extract_frz()` stub in `frz_manage_runtime.py` (L349-362) will be replaced with full implementation. The argparse extract subcommand args are already defined (L437-451). This is a code edit, not a data migration.

## Common Pitfalls

### Pitfall 1: AnchorRegistry duplicate registration during cascade

**What goes wrong:** In cascade mode, FRZ→SRC registers anchor JRN-001 with projection_path="SRC". Then FRZ→EPIC tries to register the same JRN-001 with projection_path="EPIC" and gets `CommandError("INVALID_REQUEST", "Anchor ID already registered")`.

**Why it happens:** `AnchorRegistry.register()` rejects duplicate anchor_ids (L116-120). D-10 says "same anchor_id has multiple records distinguished by projection_path" but the current implementation treats anchor_id as globally unique.

**How to avoid:** Two options: (1) Modify `AnchorRegistry` to allow same anchor_id with different projection_path (requires Phase 7 code change), or (2) Use compound key like `JRN-001@SRC` / `JRN-001@EPIC`. Option 1 is cleaner but touches Phase 7 code. Recommend Option 1 with a new `upsert` or `register_projection` method that adds a new projection_path entry for an existing anchor.

**Warning signs:** Test cascade mode and see duplicate anchor_id errors.

### Pitfall 2: VALID_PROJECTION_PATHS limited to SRC/EPIC/FEAT

**What goes wrong:** D-08 says cascade covers full SSOT chain including TECH/UI/TEST/IMPL, but `anchor_registry.py` line 23 only allows `{"SRC", "EPIC", "FEAT"}`.

**Why it happens:** Phase 7 only needed the first 3 levels. Phase 8 extends to full chain.

**How to avoid:** Extend `VALID_PROJECTION_PATHS` to include `"TECH"`, `"UI"`, `"TEST"`, `"IMPL"`. This is a small change to `anchor_registry.py` that must be made before cascade mode works.

**Warning signs:** `CommandError("INVALID_REQUEST", "Invalid projection path: TECH")` when extending cascade beyond FEAT.

### Pitfall 3: FRZ→SRC projection rules are underspecified

**What goes wrong:** The exact mapping from FRZ MSC 5 dimensions to SRC fields is left to "Claude's Discretion" in CONTEXT.md. Without a clear mapping table, the extractor produces inconsistent output.

**Why it happens:** ADR-050 defines FRZ structure but not the SRC target schema.

**How to avoid:** Define a mapping table before coding. Recommended mapping:
- `product_boundary` → SRC `in_scope` / `out_of_scope` sections
- `core_journeys` → SRC `user_journeys` (preserve JRN-xxx IDs as anchors)
- `domain_model` → SRC `entities` (preserve ENT-xxx IDs as anchors)
- `state_machine` → SRC `state_transitions` (preserve SM-xxx IDs as anchors)
- `acceptance_contract` → SRC `acceptance_criteria` (preserve FC-xxx IDs as anchors)
- `constraints` → SRC `constraints` (hard constraints, non-driftable)
- `known_unknowns` → SRC `open_questions` (with expiry tracking)

### Pitfall 4: Gate integration in cascade is a subprocess dependency

**What goes wrong:** The cascade mode calls `ll gate` between extraction steps. If gate CLI is not on PATH or requires specific protocol setup, cascade fails silently.

**Why it happens:** Gate uses `run_with_protocol()` which expects a specific `CommandContext` setup (L787-789 in gate/command.py). Direct import is complex.

**How to avoid:** Use subprocess invocation of the gate CLI rather than direct import. The gate CLI is invoked via `ll gate <action>` — use `subprocess.run()` with appropriate JSON payloads. Alternatively, extract the gate logic into a callable function that accepts minimal parameters (workspace_root, candidate_ref, decision_target).

### Pitfall 5: Missing FRZ content for downstream layers

**What goes wrong:** FRZ may not contain TECH/UI/TEST/IMPL specific content. Cascade should warn but not block.

**Why it happens:** FRZ focuses on product-level semantics (PRD/UX/Arch). TECH/UI details may be intentionally deferred.

**How to avoid:** D-08 mandates warning-level notifications when FRZ content for a layer is missing. Implement a `check_frz_coverage()` function that checks each SSOT layer against FRZ MSC dimensions and emits warnings for gaps.

## Code Examples

### Drift Detector Pattern

```python
"""cli/lib/drift_detector.py — Semantic drift detection at anchor level."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.lib.anchor_registry import AnchorRegistry
from cli.lib.errors import CommandError
from cli.lib.frz_schema import FRZPackage, MSCValidator, _parse_frz_dict


@dataclass(frozen=True)
class DriftResult:
    anchor_id: str
    frz_ref: str
    has_drift: bool
    drift_type: str  # "missing", "tampered", "new_field", "constraint_violation", "unknown_expired"
    detail: str


def check_anchor_drift(
    anchor_id: str,
    frz_package: FRZPackage,
    target_data: dict[str, Any],
) -> DriftResult:
    """Check if an anchor's semantic content has drifted from FRZ baseline."""
    # Extract original FRZ content for this anchor
    frz_content = _extract_anchor_content(frz_package, anchor_id)
    if frz_content is None:
        return DriftResult(
            anchor_id=anchor_id, frz_ref=frz_package.frz_id or "",
            has_drift=True, drift_type="missing",
            detail=f"Anchor {anchor_id} not found in FRZ package",
        )

    # Compare semantic content (not exact string match — structural comparison)
    if not _semantics_match(frz_content, target_data.get(anchor_id, {})):
        return DriftResult(
            anchor_id=anchor_id, frz_ref=frz_package.frz_id or "",
            has_drift=True, drift_type="tampered",
            detail=f"Anchor {anchor_id} semantics differ from FRZ baseline",
        )

    return DriftResult(
        anchor_id=anchor_id, frz_ref=frz_package.frz_id or "",
        has_drift=False, drift_type="none", detail="OK",
    )


def check_derived_allowed(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[str]:
    """Return list of non-allowed fields in output (violates derived_allowed whitelist)."""
    allowed = set(frz_package.derived_allowed)
    violations = [
        key for key in output_data
        if key not in allowed
        and key not in _core_frz_keys()  # intrinsic FRZ keys always allowed
    ]
    return violations


def check_constraints(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[str]:
    """Return list of constraint violations."""
    violations = []
    for constraint in frz_package.constraints:
        if not _constraint_satisfied(constraint, output_data):
            violations.append(constraint)
    return violations


def check_known_unknowns(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[dict[str, str]]:
    """Return list of known_unknowns that are still open but have expired."""
    expired = []
    for ku in frz_package.known_unknowns:
        if ku.status == "open" and _is_expired(ku.expires_in):
            expired.append({
                "id": ku.id,
                "topic": ku.topic,
                "status": "expired",
            })
    return expired
```

### Projection Guard Pattern

```python
"""cli/lib/projection_guard.py — Projection invariance guard."""
from __future__ import annotations
from dataclasses import dataclass

from cli.lib.frz_schema import FRZPackage
from cli.lib.errors import CommandError, ensure


@dataclass(frozen=True)
class GuardResult:
    passed: bool
    violations: list[str]
    verdict: str  # "pass" | "block"


def guard_projection(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> GuardResult:
    """Verify output does not exceed derived_allowed whitelist."""
    violations: list[str] = []

    # Check derived_allowed fields
    allowed = set(frz_package.derived_allowed)
    for key in output_data:
        if key not in allowed and key not in _intrinsic_keys():
            violations.append(f"Non-derived field '{key}' not in derived_allowed whitelist")

    # Check constraints
    for constraint in frz_package.constraints:
        if not _constraint_satisfied(constraint, output_data):
            violations.append(f"Constraint violation: {constraint}")

    passed = len(violations) == 0
    return GuardResult(
        passed=passed,
        violations=violations,
        verdict="pass" if passed else "block",
    )
```

### Extract Subcommand Pattern (for src_to_epic.py)

```python
# Add to build_parser():
extract_parser = subparsers.add_parser("extract")
extract_parser.add_argument("--frz", required=True, help="FRZ ID to extract from")
extract_parser.add_argument("--repo-root")
extract_parser.add_argument("--output")
extract_parser.set_defaults(func=command_extract)

def command_extract(args: argparse.Namespace) -> int:
    result = extract_epic_from_frz(
        frz_id=args.frz,
        repo_root=repo_root_from(args.repo_root, args.output),
        output_dir=Path(args.output) if args.output else None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1
```
[VERIFIED: src_to_epic.py subcommand pattern L89-138]

### Cascade Mode Pattern

```python
# Pseudocode for cascade in frz_manage_runtime.py
def run_cascade(frz_id: str, workspace_root: Path) -> dict:
    steps = [
        ("SRC", extract_src_from_frz),
        ("EPIC", extract_epic_from_frz),
        ("FEAT", extract_feat_from_frz),
        # ... TECH, UI, TEST, IMPL
    ]
    results = []
    for layer_name, extract_fn in steps:
        result = extract_fn(frz_id, workspace_root)
        results.append(result)
        if not result["ok"]:
            return {"ok": False, "failed_at": layer_name, "results": results}

        # Gate review after each step
        gate_result = run_gate_review(result["artifacts_dir"], workspace_root)
        if gate_result["verdict"] != "approve":
            return {"ok": False, "blocked_at_gate": layer_name, "gate": gate_result, "results": results}

    return {"ok": True, "results": results}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SSOT逐层生成 (SRC→EPIC→FEAT) | FRZ统一语义 + 分层抽取 | ADR-050 (2026-04-17) | 消除逐层语义漂移，FRZ为唯一真相源 |
| LLM辅助抽取 | 规则模板投影 (D-01) | Phase 8 decision | 确定性输出，可复现，非LLM |
| 全局漂移检测 | 锚点级漂移检测 (D-05) | Phase 8 decision | 精确到每个锚点，噪声低 |
| 自动修正漂移 | 拦截 + 报告 (D-06) | Phase 8 decision | 人类判断漂移根因 |
| Gate仅审核生成产物 | Gate审核抽取产物 (D-13) | Phase 8 decision | 复用现有gate流程，仅加锚点存在性检查 |

**Deprecated/outdated:**
- `ll-product-raw-to-src` generation mode — replaced by `ll-frz-manage extract` (EXTR-01)
- EPIC/FEAT generation from direct parent — replaced by FRZ-based extraction (EXTR-02)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `AnchorRegistry` needs modification to support multiple projection_paths per anchor_id (TECH/UI/TEST/IMPL) | Pitfall 1, Pitfall 2 | Cascade mode fails beyond FEAT layer |
| A2 | Gate integration via subprocess is preferred over direct import | Pitfall 4 | Subprocess overhead vs. direct import complexity — needs validation |
| A3 | TECH/UI/TEST/IMPL extraction follows same pattern as SRC/EPIC/FEAT (FRZ→rule-template→output) | Extract Subcommand Pattern | If downstream layers need different extraction logic, more modules needed |
| A4 | FRZ content for TECH/UI/TEST/IMPL layers exists in `constraints` and `derived_allowed` fields, not MSC dimensions | Pitfall 5 | If FRZ lacks downstream content entirely, warnings are correct but extract produces empty output |

## Open Questions

1. **What is the exact FRZ→SRC field mapping?**
   - What we know: FRZ has 5 MSC dimensions + constraints + derived_allowed + known_unknowns. SRC format is determined by existing `raw-to-src` output format.
   - What's unclear: The precise mapping from each FRZ field to SRC sections is not defined in ADR-050 or CONTEXT.md. Marked as Claude's Discretion.
   - Recommendation: Define mapping table in PLAN.md and get user confirmation before coding.

2. **How does cascade mode invoke gate for each step?**
   - What we know: Gate uses `run_with_protocol()` with `CommandContext`. Existing skills create gate-ready packages and submit via `submit_gate_pending()`.
   - What's unclear: Whether cascade should use the same `submit_gate_pending()` flow or a simplified gate check.
   - Recommendation: Reuse the existing gate package + submit pattern from `src_to_epic_runtime.py` and `epic_to_feat_runtime.py` supervisor_review functions.

3. **What happens when FRZ content for TECH/UI/TEST/IMPL is completely absent?**
   - What we know: D-08 mandates warning but not blocking.
   - What's unclear: Should the cascade skip these layers entirely, or produce empty/minimal packages?
   - Recommendation: Skip layers where FRZ has zero relevant content. Emit warning with specific missing dimensions.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All scripts | YES | 3.13.3 | — |
| pytest | Testing | YES | 9.0.2 | — |
| PyYAML | FRZ/SSOT YAML I/O | YES | 6.0.3 | — |
| `cli.lib.anchor_registry` | Anchor registration | YES | Phase 7 | — |
| `cli.lib.frz_schema` | FRZ loading/validation | YES | Phase 7 | — |
| `cli.lib.frz_registry` | FRZ registry lookup | YES | Phase 7 | — |
| `cli.lib.errors` | Error handling | YES | Phase 7 | — |
| `cli.lib.fs` | File I/O | YES | Phase 7 | — |
| `cli.commands.gate` | Gate review in cascade | YES | Existing | — |
| `skills/ll-frz-manage/scripts/frz_manage_runtime.py` | Extract CLI | YES (stub) | Phase 7 | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None at project root — use `pytest` direct invocation (same as Phase 7) |
| Quick run command | `python -m pytest cli/lib/test_drift_detector.py -x` |
| Full suite command | `python -m pytest cli/lib/test_drift_detector.py cli/lib/test_projection_guard.py cli/lib/test_frz_extractor.py skills/ll-frz-manage/scripts/test_frz_manage_runtime.py skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py skills/ll-product-epic-to-feat/scripts/test_epic_to_feat_extract.py -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXTR-01 | FRZ→SRC projection | unit + integration | `pytest cli/lib/test_frz_extractor.py -x` | ❌ W0 |
| EXTR-02 | SRC→EPIC→FEAT cascade extract | unit + integration | `pytest skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py -x` | ❌ W0 |
| EXTR-03 | Anchor registration during extract | unit | `pytest cli/lib/test_anchor_registry.py::test_register_with_projection -x` | ❌ (extend existing) |
| EXTR-04 | Drift detection 5 scenarios | unit | `pytest cli/lib/test_drift_detector.py -x` | ❌ W0 |
| EXTR-05 | Projection guard blocks non-allowed | unit | `pytest cli/lib/test_projection_guard.py -x` | ❌ W0 |

### Sampling Rate
- **Per task commit:** `python -m pytest <relevant_test_file> -x`
- **Per wave merge:** Full suite command above
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `cli/lib/test_drift_detector.py` — covers EXTR-04 (5 drift scenarios)
- [ ] `cli/lib/test_projection_guard.py` — covers EXTR-05
- [ ] `cli/lib/test_frz_extractor.py` — covers EXTR-01
- [ ] `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py` — extend with extract tests
- [ ] `skills/ll-product-src-to-epic/scripts/test_src_to_epic_extract.py` — covers EXTR-02 EPIC extract
- [ ] `skills/ll-product-epic-to-feat/scripts/test_epic_to_feat_extract.py` — covers EXTR-02 FEAT extract
- [ ] `cli/lib/test_anchor_registry.py` — extend with multi-projection tests for EXTR-03
- [ ] Integration test for full cascade FRZ→SRC→EPIC→FEAT

## Security Domain

> `security_enforcement` is not set in config — default enabled. However, this phase has no user input handling, no database queries, no file system operations beyond controlled YAML I/O, no external API calls, no cryptographic operations. Security surface is minimal.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Yes | FRZ ID format validation (`FRZ_ID_PATTERN`), anchor ID format validation (`ANCHOR_ID_PATTERN`), projection path whitelist |
| V6 Cryptography | No | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in output dir | Tampering | Use `cli.lib.fs.canonical_to_path()` for all path resolution |
| Malformed FRZ YAML | Tampering | `MSCValidator.validate_file()` with schema error handling |
| Anchor ID injection | Tampering | `ANCHOR_ID_PATTERN` validation in `AnchorRegistry.register()` |
| Cascading failure without gate | Integrity | D-08 mandates gate review after each step |

## Sources

### Primary (HIGH confidence)
- `cli/lib/frz_schema.py` — FRZPackage dataclass, MSCValidator, ID patterns [VERIFIED: read]
- `cli/lib/frz_registry.py` — register_frz, list_frz, get_frz, update_frz_status [VERIFIED: read]
- `cli/lib/anchor_registry.py` — AnchorRegistry class, ANCHOR_ID_PATTERN, VALID_PROJECTION_PATHS [VERIFIED: read]
- `cli/lib/errors.py` — CommandError, ensure(), STATUS_SEMANTICS, EXIT_CODE_MAP [VERIFIED: read]
- `cli/lib/fs.py` — ensure_parent, load_json, write_text, canonical_to_path [VERIFIED: read]
- `skills/ll-frz-manage/scripts/frz_manage_runtime.py` — CLI architecture, extract stub [VERIFIED: read]
- `skills/ll-product-src-to-epic/scripts/src_to_epic.py` — Subcommand pattern [VERIFIED: read]
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat.py` — Subcommand pattern [VERIFIED: read]
- `cli/commands/gate/command.py` — Gate flow: submit-handoff→evaluate→decide→materialize→dispatch [VERIFIED: read]
- `ssot/adr/ADR-050-SSOT语义治理总纲.md` — SSOT governance principles [VERIFIED: read]
- `ssot/adr/ADR-051-TaskPack顺序执行循环模式.md` — Task Pack structure [VERIFIED: read]
- `.planning/REQUIREMENTS.md` — EXTR-01~05 requirements [VERIFIED: read]
- `.planning/ROADMAP.md` — Phase 8 plans and success criteria [VERIFIED: read]

### Secondary (MEDIUM confidence)
- Phase 7 test files (`test_frz_schema.py`, `test_anchor_registry.py`, `test_frz_registry.py`, `test_frz_manage_runtime.py`) — test patterns and fixture structure [VERIFIED: read partial]
- `src_to_epic_runtime.py` and `epic_to_feat_runtime.py` — workflow patterns, gate integration [VERIFIED: read]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified from existing codebase and runtime checks
- Architecture: HIGH — patterns verified from Phase 7 and existing skill scripts
- Pitfalls: MEDIUM — Pitfall 1 (AnchorRegistry duplicate) and Pitfall 2 (VALID_PROJECTION_PATHS) are inferred from code analysis, not confirmed by running tests
- Drift detector design: MEDIUM — design is proposed, not yet validated against actual FRZ data

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (30 days — stable domain, no fast-moving dependencies)
