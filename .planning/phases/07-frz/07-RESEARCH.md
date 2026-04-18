# Phase 7: FRZ 冻结层基础设施 - Research

**Researched:** 2026-04-18
**Domain:** FRZ package schema, MSC validation, anchor registry, skill creation
**Confidence:** HIGH

## Summary

Phase 7 establishes the FRZ (Freeze Package) infrastructure: a package schema definition, MSC (Minimum Semantic Completeness) validator, anchor ID registry, and a CLI skill (`ll-frz-manage`) for freeze + query operations. This is the foundational phase for the entire v2.0 semantic governance upgrade — all downstream phases (EXTR, STAB, GRADE) depend on these deliverables.

The project already has established patterns: `@dataclass(frozen=True)` schemas in `cli/lib/qa_schemas.py` and `cli/lib/patch_schema.py`, a YAML-backed registry in `cli/lib/registry_store.py`, a `CommandError` error taxonomy in `cli/lib/errors.py`, and a skill structure in `skills/*/` with `ll.contract.yaml`, `ll.lifecycle.yaml`, `SKILL.md`, `scripts/`, and `input|output/contract.yaml`.

**Primary recommendation:** Follow existing patterns for FRZ schema dataclasses + manual validation (matching `qa_schemas.py`), integrate Pydantic v2 for stricter runtime validation of FRZ packages, use the existing YAML registry pattern from `registry_store.py` for the FRZ registry, and build `ll-frz-manage` as a new skill following the `ll-patch-capture` / `ll-qa-impl-spec-test` template.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Pydantic** | 2.11.8 (installed) / 2.13.0 (latest) | FRZ package validation, MSC field constraints | Project already uses `@dataclass(frozen=True)` in `qa_schemas.py` (29 dataclasses) and `patch_schema.py`. Pydantic adds runtime validation with clear error messages. `[VERIFIED: /c/Python313/python -c "import pydantic; print(pydantic.__version__)"]` |
| **PyYAML** | 6.0.3 | YAML read/write for `freeze.yaml` and registry | Already used across 15+ files in `cli/lib/`. No reason to switch. `[VERIFIED: pip show pyyaml]` |
| **graphlib.TopologicalSorter** | Python 3.13 stdlib | Dependency resolution for future anchor chain | Built into stdlib, handles linear/tree dependencies. `[VERIFIED: stdlib import test]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **deepdiff** | 9.0.0 | FRZ version comparison, drift baseline | Phase 7 needs version diff for `freeze --type revise`. Install required (not currently present). `[VERIFIED: pypi.org/project/deepdiff/]` |
| **rich** | 13.9+ | CLI output formatting for `frz list` and MSC reports | When displaying tabular FRZ registry and validation results in CLI. `[ASSUMED]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic v2 | Manual dataclass validation (current pattern) | Current pattern works (see `qa_schemas.py`) but Pydantic gives richer error messages, JSON Schema export for CI gates. Recommended: use Pydantic for new FRZ schemas, keep existing dataclasses as-is. |
| deepdiff | Manual dict comparison | DeepDiff detects nested structural changes automatically — critical for FRZ version diffs. Manual approach would miss edge cases. |
| PyYAML | ruamel.yaml 0.19.1 | Use ruamel.yaml only when writing back to `freeze.yaml` that needs comment preservation. PyYAML is sufficient for reading. |

**Installation:**
```bash
pip install deepdiff==9.0.0
pip install rich>=13.9
# pydantic and pyyaml already installed
```

**Version verification:**
- pydantic: 2.11.8 installed (latest 2.13.0 from PyPI 2026-04-13) — acceptable
- PyYAML: 6.0.3 installed (latest 6.0.3) — current
- deepdiff: not installed (latest 9.0.0 from PyPI 2026-03-29) — needs install
- Python: 3.13.3 installed — graphlib stdlib available

## Architecture Patterns

### Recommended Project Structure

```
cli/lib/
├── frz_schema.py          # FRZPackage dataclass + MSCValidator (07-01)
├── anchor_registry.py      # AnchorRegistry class (07-02)
├── frz_registry.py         # FRZ registry read/write helpers (part of 07-03)

ssot/registry/
└── frz-registry.yaml       # FRZ registry file (07-03)

ssot/schemas/
└── frz/
    ├── frz-package.yaml    # YAML schema definition
    └── frz-package.json    # JSON Schema for external validation

skills/ll-frz-manage/       # New skill (07-04)
├── SKILL.md
├── ll.contract.yaml
├── ll.lifecycle.yaml
├── input/
│   ├── contract.yaml
│   └── semantic-checklist.md
├── output/
│   ├── contract.yaml
│   └── semantic-checklist.md
├── scripts/
│   ├── frz_manage_runtime.py  # Python CLI runtime
│   ├── validate_input.sh
│   └── validate_output.sh
└── agents/
    ├── executor.md
    └── supervisor.md
```

### Pattern 1: FRZ Package Dataclass with MSC Validation

**What:** Define `FRZPackage` as a frozen dataclass with all MSC dimensions, plus `MSCValidator` that checks completeness.

**When to use:** Always for schema definitions — follows the established pattern in `qa_schemas.py` and `patch_schema.py`.

**Example:**
```python
# Source: ADR-045 §2.3, ADR-050 §3.2, existing pattern from cli/lib/patch_schema.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class FRZStatus(str, Enum):
    draft = "draft"
    freeze_ready = "freeze_ready"
    frozen = "frozen"
    blocked = "blocked"
    revised = "revised"
    superseded = "superseded"


MSC_DIMENSIONS = [
    "product_boundary",
    "core_journeys",
    "domain_model",
    "state_machine",
    "acceptance_contract",
]


@dataclass(frozen=True)
class ProductBoundary:
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CoreJourney:
    id: str           # JRN-xxx format
    name: str
    steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DomainEntity:
    id: str           # ENT-xxx format
    name: str
    contract: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StateMachine:
    id: str           # SM-xxx format
    name: str
    states: list[str] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AcceptanceContract:
    expected_outcomes: list[str] = field(default_factory=list)
    acceptance_impact: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KnownUnknown:
    id: str           # UNK-xxx format
    topic: str
    status: str = "open"
    owner: str | None = None
    expires_in: str = "2 cycles"


@dataclass(frozen=True)
class FRZEvidence:
    source_refs: list[str] = field(default_factory=list)
    raw_path: str | None = None


@dataclass(frozen=True)
class FRZPackage:
    """FRZ Freeze Package — ADR-045 §2.1, ADR-050 §3.2."""
    artifact_type: str = "frz_package"
    frz_id: str | None = None              # FRZ-xxx
    version: str = "1.0"
    status: str = "draft"
    created_at: str | None = None          # ISO 8601
    frozen_at: str | None = None

    # MSC dimensions
    product_boundary: ProductBoundary | None = None
    core_journeys: list[CoreJourney] = field(default_factory=list)
    domain_model: list[DomainEntity] = field(default_factory=list)
    state_machine: list[StateMachine] = field(default_factory=list)
    acceptance_contract: AcceptanceContract | None = None

    # Supplementary fields
    constraints: list[str] = field(default_factory=list)
    derived_allowed: list[str] = field(default_factory=list)
    known_unknowns: list[KnownUnknown] = field(default_factory=list)
    enums: list[dict[str, Any]] = field(default_factory=list)

    # Evidence
    evidence: FRZEvidence | None = None


class FRZSchemaError(ValueError):
    """Raised when FRZ data does not conform to schema."""


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise FRZSchemaError(f"{label}: required field '{key}' is missing")


class MSCValidator:
    """Validates MSC (Minimum Semantic Completeness) of an FRZ package."""

    @staticmethod
    def validate(pkg: FRZPackage) -> dict[str, Any]:
        """Check all 5 MSC dimensions. Returns report dict."""
        missing = []
        present = []

        if not pkg.product_boundary or (
            not pkg.product_boundary.in_scope and not pkg.product_boundary.out_of_scope
        ):
            missing.append("product_boundary")
        else:
            present.append("product_boundary")

        if not pkg.core_journeys:
            missing.append("core_journeys")
        else:
            present.append("core_journeys")

        if not pkg.domain_model:
            missing.append("domain_model")
        else:
            present.append("domain_model")

        if not pkg.state_machine:
            missing.append("state_machine")
        else:
            present.append("state_machine")

        if not pkg.acceptance_contract or (
            not pkg.acceptance_contract.expected_outcomes
        ):
            missing.append("acceptance_contract")
        else:
            present.append("acceptance_contract")

        return {
            "frz_id": pkg.frz_id,
            "msc_valid": len(missing) == 0,
            "present": present,
            "missing": missing,
            "status": "frozen" if len(missing) == 0 else "blocked",
        }

    @staticmethod
    def validate_file(path: str | Path) -> dict[str, Any]:
        """Load FRZ YAML and validate MSC."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"FRZ file not found: {p}")

        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        pkg = _parse_frz_dict(data)
        return MSCValidator.validate(pkg)


def _parse_frz_dict(data: dict) -> FRZPackage:
    """Convert raw YAML dict to FRZPackage."""
    pb_raw = data.get("product_boundary")
    product_boundary = None
    if pb_raw:
        product_boundary = ProductBoundary(
            in_scope=pb_raw.get("in_scope") or [],
            out_of_scope=pb_raw.get("out_of_scope") or [],
        )

    journeys = []
    for j in data.get("core_journeys") or []:
        journeys.append(CoreJourney(
            id=j.get("id", ""),
            name=j.get("name", ""),
            steps=j.get("steps") or [],
        ))

    entities = []
    for e in data.get("domain_model") or []:
        entities.append(DomainEntity(
            id=e.get("id", ""),
            name=e.get("name", ""),
            contract=e.get("contract") or {},
        ))

    machines = []
    for s in data.get("state_machine") or []:
        machines.append(StateMachine(
            id=s.get("id", ""),
            name=s.get("name", ""),
            states=s.get("states") or [],
            transitions=s.get("transitions") or [],
        ))

    ac_raw = data.get("acceptance_contract")
    acceptance_contract = None
    if ac_raw:
        acceptance_contract = AcceptanceContract(
            expected_outcomes=ac_raw.get("expected_outcomes") or [],
            acceptance_impact=ac_raw.get("acceptance_impact") or [],
        )

    ku_list = []
    for ku in data.get("known_unknowns") or []:
        ku_list.append(KnownUnknown(
            id=ku.get("id", ""),
            topic=ku.get("topic", ""),
            status=ku.get("status", "open"),
            owner=ku.get("owner"),
            expires_in=ku.get("expires_in", "2 cycles"),
        ))

    ev_raw = data.get("evidence")
    evidence = None
    if ev_raw:
        evidence = FRZEvidence(
            source_refs=ev_raw.get("source_refs") or [],
            raw_path=ev_raw.get("raw_path"),
        )

    return FRZPackage(
        artifact_type=data.get("artifact_type", "frz_package"),
        frz_id=data.get("frz_id"),
        version=data.get("version", "1.0"),
        status=data.get("status", "draft"),
        created_at=data.get("created_at"),
        frozen_at=data.get("frozen_at"),
        product_boundary=product_boundary,
        core_journeys=journeys,
        domain_model=entities,
        state_machine=machines,
        acceptance_contract=acceptance_contract,
        constraints=data.get("constraints") or [],
        derived_allowed=data.get("derived_allowed") or [],
        known_unknowns=ku_list,
        enums=data.get("enums") or [],
        evidence=evidence,
    )
```

### Pattern 2: YAML-Backed Registry (Follow Existing Pattern)

**What:** The FRZ registry follows the same YAML-backed pattern as `cli/lib/registry_store.py` and the patch registry.

**When to use:** For the `ssot/registry/frz-registry.yaml` — a single registry file with an array of FRZ records.

**Example based on existing registry_store.py pattern:**
```python
# Source: existing cli/lib/registry_store.py pattern
from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import ensure_parent, read_text, write_text


def registry_path(workspace_root: Path) -> Path:
    return workspace_root / "ssot" / "registry" / "frz-registry.yaml"


def _load_registry(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("frz_registry", [])


def _save_registry(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    payload = {"frz_registry": records}
    write_text(path, yaml.dump(payload, default_flow_style=False, allow_unicode=True, sort_keys=False))


def register_frz(
    workspace_root: Path,
    frz_id: str,
    msc_report: dict[str, Any],
    package_ref: str,
    metadata: dict[str, Any] | None = None,
    previous_frz: str | None = None,
    revision_type: str = "new",
    reason: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Register an FRZ package in the registry."""
    from datetime import datetime, timezone

    path = registry_path(workspace_root)
    records = _load_registry(path)

    record = {
        "frz_id": frz_id,
        "status": "frozen",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_ref": package_ref,
        "msc_valid": msc_report.get("msc_valid", False),
        "version": "1.0",
        "revision_type": revision_type,
    }
    if previous_frz:
        record["previous_frz_ref"] = previous_frz
    if reason:
        record["revision_reason"] = reason
    if metadata:
        record["metadata"] = metadata

    records.append(record)
    _save_registry(path, records)
    return record, frz_id


def list_frz(workspace_root: Path, status: str | None = None) -> list[dict[str, Any]]:
    path = registry_path(workspace_root)
    records = _load_registry(path)
    if status:
        records = [r for r in records if r.get("status") == status]
    return records
```

### Pattern 3: Skill Structure

**What:** New skills follow the established template seen in `ll-patch-capture` and `ll-qa-impl-spec-test`.

**Standard skill directory:**
```
skills/ll-frz-manage/
├── SKILL.md              # Main skill description + execution protocol
├── ll.contract.yaml      # Skill metadata (skill, version, adr, category, chain, phase)
├── ll.lifecycle.yaml     # Lifecycle states
├── input/
│   ├── contract.yaml     # Input schema contract
│   └── semantic-checklist.md
├── output/
│   ├── contract.yaml     # Output schema contract
│   └── semantic-checklist.md
├── scripts/
│   ├── frz_manage_runtime.py  # Python runtime implementation
│   ├── validate_input.sh
│   └── validate_output.sh
├── agents/
│   ├── executor.md       # Executor agent instructions
│   └── supervisor.md     # Supervisor agent instructions
└── evidence/             # (optional) evidence schemas
```

### Anti-Patterns to Avoid
- **Don't create a separate registry system.** Follow `cli/lib/registry_store.py` pattern — YAML-backed, workspace-relative paths.
- **Don't use Pydantic for internal dataclasses only.** Use it where runtime validation error messages matter (FRZ validation). Keep frozen dataclasses for immutable DTOs.
- **Don't put FRZ in `ssot/` chain.** Per ADR-045 §2.1, FRZ lives in `artifacts/`, not `ssot/`. Only the registry lives in `ssot/registry/`.
- **Don't build a web UI for FRZ management.** The project is CLI-first. `ll frz-manage` commands are the interface.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRZ package validation | Custom dict-checking code | `FRZSchemaError` + dataclass pattern (follow `patch_schema.py`) | Existing pattern is proven, consistent error handling, `QaSchemaError` precedent |
| Structural comparison (FRZ version diff) | Manual nested dict comparison | `deepdiff` | DeepDiff handles arbitrary nesting, detects type changes, additions, removals — exactly what FRZ drift detection needs |
| YAML schema definition | Custom schema format | YAML file + Pydantic validation (follow `ssot/schemas/qa/patch.yaml` pattern) | Interoperable, human-readable, existing precedent |
| Dependency resolution | Custom DFS | `graphlib.TopologicalSorter` (stdlib) | Handles cycles, produces topological order, zero dependencies |
| MSC dimension checking | Ad-hoc if-statements | `MSCValidator` class with structured report | Provides machine-readable `msc_valid` boolean, `missing` list, `status` — reusable by Phase 8 extraction |
| CLI error handling | print() + sys.exit | `CommandError` with `status_code`, `exit_code` | Existing error taxonomy in `cli/lib/errors.py` maps to structured exit codes |

**Key insight:** The project has already established patterns for every domain in this phase. The biggest risk is introducing a new pattern that doesn't integrate with the existing `CommandError`/`registry_store.py`/`qa_schemas.py` ecosystem.

## Runtime State Inventory

> This is a greenfield infrastructure phase (not a rename/refactor). Runtime state inventory is N/A.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified: no existing FRZ tables/collections in any DB | N/A — greenfield |
| Live service config | None — no external services configured for FRZ | N/A |
| OS-registered state | None | N/A |
| Secrets/env vars | None — FRZ does not require secrets | N/A |
| Build artifacts | None | N/A |

## Common Pitfalls

### Pitfall 1: MSC Dimension Definition Too Loose
**What goes wrong:** MSC validator accepts empty or trivial values (e.g., `product_boundary: {in_scope: [], out_of_scope: []}` counts as "present").
**Why it happens:** The check only tests for key presence, not semantic meaningfulness.
**How to avoid:** Define minimum content rules: `product_boundary` must have at least one item in `in_scope` OR `out_of_scope`; `core_journeys` must have >= 1 journey with >= 2 steps; `domain_model` must have >= 1 entity with a non-empty contract; `acceptance_contract` must have >= 1 expected_outcome.
**Warning signs:** MSC report says "valid" but downstream extraction produces no usable anchors.

### Pitfall 2: FRZ Registry Becomes a Bottleneck
**What goes wrong:** Single YAML file with no concurrency control leads to lost writes when multiple FRZ packages are registered simultaneously.
**Why it happens:** YAML read-modify-write is not atomic.
**How to avoid:** For v2.0 (single-user CLI tool), this is acceptable. Add a file-lock mechanism (e.g., `flock` or atomic temp-file + rename) if concurrent registration becomes a real scenario. Document this as a known limitation.
**Warning signs:** Registry file shows duplicate entries or lost records after parallel operations.

### Pitfall 3: Anchor ID Format Drift
**What goes wrong:** Different modules use different anchor ID formats (`JRN-001` vs `JRN-01` vs `jrn-001`).
**Why it happens:** No centralized anchor ID format enforcement.
**How to avoid:** The `anchor_registry.py` should normalize IDs on registration: uppercase prefix, zero-padded 3-digit number. Reject IDs that don't match the pattern.
**Warning signs:** `derived_from` references in downstream artifacts can't be resolved because of format mismatches.

### Pitfall 4: Skill CLI vs Direct Python Runtime Confusion
**What goes wrong:** `ll frz-manage` invokes a skill that delegates to a Python script, but the Python script is also directly callable. Which is the "canonical" path?
**Why it happens:** Existing skills like `ll-qa-impl-spec-test` have both: `SKILL.md` (agent-facing) and `scripts/impl_spec_test_runtime.py` (Python entry point).
**How to avoid:** Follow the established convention: `ll frz-manage <mode>` is the user-facing command, which internally calls `python scripts/frz_manage_runtime.py`. The Python script is the canonical runtime; the SKILL.md wraps it with agent instructions. Document this in SKILL.md Non-Negotiable Rules section: "Do not bypass scripts/frz_manage_runtime.py."

## Code Examples

### FRZ Package YAML Example
```yaml
# Source: ADR-050 §3.2.3, ADR-045 §3.2.3
artifact_type: frz_package
frz_id: FRZ-001
version: "1.0"
status: frozen
created_at: "2026-04-18T10:00:00Z"
frozen_at: "2026-04-18T11:00:00Z"

product_boundary:
  in_scope:
    - "User can create training plans"
    - "User can view plan details"
  out_of_scope:
    - "User cannot delete plans (v2.1)"
    - "No sharing/collaboration"

core_journeys:
  - id: JRN-001
    name: "Create Training Plan"
    steps:
      - "User enters plan name"
      - "System validates name uniqueness"
      - "User selects training type"
      - "System generates plan structure"
      - "User reviews and confirms"

domain_model:
  - id: ENT-001
    name: "TrainingPlan"
    contract:
      name: "string, required, unique"
      training_type: "enum[strength, cardio, flexibility]"
      duration_weeks: "int, 1-52"

state_machine:
  - id: SM-001
    name: "Plan Lifecycle"
    states: [draft, active, paused, completed]
    transitions:
      - from: draft
        to: active
        guard: "user_confirms"
      - from: active
        to: paused
        guard: "user_requests_pause"

acceptance_contract:
  expected_outcomes:
    - "Plan is created within 30 seconds"
    - "Duplicate names are rejected"
  acceptance_impact:
    - "P0: Plan creation flow"
    - "P1: Plan validation errors"

constraints:
  - "Must support offline plan viewing"
derived_allowed:
  - "EPIC decomposition from JRN-001"
  - "FEAT breakdown from ENT-001"
known_unknowns:
  - id: UNK-001
    topic: "Mobile responsiveness requirements"
    status: open
    owner: "product-team"
    expires_in: "2 cycles"

evidence:
  source_refs: ["prd-v2.md", "architecture-v1.md", "ux-journey.md"]
  raw_path: "artifacts/frz-input/001/"
```

### FRZ Registry Entry Example
```yaml
# Source: ADR-045 §3.1, existing registry_store.py pattern
frz_registry:
  - frz_id: FRZ-001
    status: frozen
    created_at: "2026-04-18T10:00:00Z"
    package_ref: artifacts/frz-input/001/frz-package/frz-package.json
    msc_valid: true
    version: "1.0"
    revision_type: new
```

### Anchor Registry Usage
```python
# Source: follows existing cli/lib/registry_store.py pattern
from cli.lib.anchor_registry import AnchorRegistry

registry = AnchorRegistry(workspace_root=Path("."))

# Register a new anchor
registry.register(
    anchor_id="JRN-001",
    frz_ref="FRZ-001",
    projection_path="SRC",
    metadata={"journey_name": "Create Training Plan"},
)

# Resolve an anchor
entry = registry.resolve("JRN-001")
# Returns: {"anchor_id": "JRN-001", "frz_ref": "FRZ-001", "projection_path": "SRC", ...}

# List all anchors for an FRZ
anchors = registry.list_by_frz("FRZ-001")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SSOT逐层生成 (raw→SRC→EPIC→FEAT) | FRZ冻结 → 分层语义抽取 | ADR-050 (2026-04-17) | Eliminates semantic drift; FRZ is the single truth source |
| Manual FRZ validation | MSC validator with structured report | Phase 7 (this phase) | Machine-gateable validation, clear pass/fail signals |
| No anchor tracking | Anchor ID registry with FRZ references | Phase 7 (this phase) | Enables downstream projection trace and drift detection |
| Patch-only change classification | Three-tier (visual/interaction/semantic) with FRZ revise flow | ADR-049 + Phase 7 | Major semantic changes must revise FRZ, not patch in-place |

**Deprecated/outdated:**
- **FRZ generation by AI**: ADR-050 §3.1 explicitly states FRZ must come from human discussion, not AI generation.
- **SSOT逐层补义**: Downstream layers can only derive/expand FRZ semantics, never rewrite them (ADR-045 §2.2).
- **Direct SSOT modification for semantic changes**: Major changes must flow through FRZ revise (GRADE-03).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `rich` 13.9+ is available via pip install | Standard Stack | Low — alternative: plain `print()` with formatting |
| A2 | FRZ registry YAML file can be single-file without concurrency control | Pitfall 2 | Medium — if multiple users register FRZ simultaneously, need file-locking. v2.0 is single-user, so acceptable |
| A3 | Anchor ID format should be `{PREFIX}-{3-digit zero-padded number}` | Pitfall 3 | Low — can be adjusted, but needs consistency enforcement |
| A4 | `ll frz-manage` skill should follow `ll-patch-capture` directory structure | Architecture Pattern 3 | Medium — if the project introduces a new skill template, this would need adjustment |
| A5 | MSC dimensions require minimum content (not just key presence) | Pitfall 1 | Medium — if too loose, downstream phases fail silently; if too strict, FRZ becomes hard to create |

## Open Questions

1. **Where should `frz-package.json` be stored?**
   - What we know: ADR-045 §3.1 says `artifacts/raw-to-src/<run_id>/frz-package/`. ADR-050 §3.4 says `artifacts/frz-input/` for source docs, `artifacts/raw-to-src/frz-package/` for latest.
   - What's unclear: For `ll frz-manage`, the user provides input docs from any location. Should the output be placed in `artifacts/frz-input/` with auto-generated run IDs, or follow the `raw-to-src` path?
   - Recommendation: Use `artifacts/frz-input/<FRZ-ID>/` for simplicity — one directory per FRZ package containing input docs, `freeze.yaml`, `frz-package.json`, and `evidence.yaml`.

2. **Should `ll frz-manage` be a CLI command group or a skill?**
   - What we know: REQUIREMENTS.md calls it both "CLI command" (FRZ-04, FRZ-05, FRZ-06) and "skill" (FRZ-02, FRZ-03). The ROADMAP plans it as a skill in `skills/ll-frz-manage/`.
   - What's unclear: Does it need to be registered in `cli/ll.py` as a subcommand, or is it purely skill-based (invoked via the skill pipeline)?
   - Recommendation: Follow the `ll-qa-impl-spec-test` pattern — the skill has `scripts/frz_manage_runtime.py` that can be called both standalone (`python scripts/frz_manage_runtime.py validate --input <dir>`) and via `ll skill frz-manage ...`. Register it in `cli/ll.py` skill subparser if needed.

3. **What is the FRZ ID generation strategy?**
   - What we know: Examples use `FRZ-001`, `FRZ-xxx` format. Registry needs to track sequence.
   - What's unclear: Should IDs be auto-generated (next available number) or user-specified via `--id FRZ-xxx`?
   - Recommendation: User-specified via `--id` flag (as shown in REQUIREMENTS.md `--id FRZ-xxx`). Validate uniqueness against registry before accepting.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All CLI lib modules, scripts | Yes | 3.13.3 | -- |
| pydantic | FRZ schema validation | Yes | 2.11.8 | Manual dataclass validation (existing pattern) |
| PyYAML | YAML read/write for freeze.yaml and registry | Yes | 6.0.3 | -- |
| deepdiff | FRZ version diff (freeze --type revise) | No | -- | Manual nested dict comparison (limited functionality) |
| graphlib (stdlib) | Dependency resolution (anchor chain) | Yes | Python 3.9+ | -- |
| rich | CLI output formatting | Unknown | -- | Plain print() formatting |

**Missing dependencies with fallback:**
- deepdiff 9.0.0 — needed for FRZ version comparison; can fall back to manual dict comparison but loses DeepDiff's edge case handling

**Missing dependencies with no fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | None detected at project root — see Wave 0 |
| Quick run command | `pytest cli/lib/test_frz_schema.py -x` |
| Full suite command | `pytest cli/lib/test_frz_schema.py cli/lib/test_anchor_registry.py -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FRZ-01 | FRZPackage dataclass + MSC 5-dim fields | unit | `pytest cli/lib/test_frz_schema.py::test_frz_package_structure -x` | ❌ Wave 0 |
| FRZ-02 | MSCValidator rejects incomplete packages | unit | `pytest cli/lib/test_frz_schema.py::test_msc_validator_missing_dims -x` | ❌ Wave 0 |
| FRZ-03 | FRZ registry records version, status, created_at | unit | `pytest cli/lib/test_frz_registry.py::test_register_frz -x` | ❌ Wave 0 |
| FRZ-04 | `ll frz-manage validate` outputs MSC report | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_validate -x` | ❌ Wave 0 |
| FRZ-05 | `ll frz-manage freeze` writes FRZ to registry | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_freeze -x` | ❌ Wave 0 |
| FRZ-06 | `ll frz-manage list` shows registered FRZ packages | integration | `pytest skills/ll-frz-manage/scripts/test_frz_manage_runtime.py::test_list -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest <relevant_test_file> -x`
- **Per wave merge:** `pytest cli/lib/test_frz*.py cli/lib/test_anchor_registry.py skills/ll-frz-manage/scripts/test_*.py -v`
- **Phase gate:** All 6 requirement tests green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `cli/lib/test_frz_schema.py` — covers FRZ-01, FRZ-02
- [ ] `cli/lib/test_frz_registry.py` — covers FRZ-03
- [ ] `cli/lib/test_anchor_registry.py` — covers anchor registry
- [ ] `skills/ll-frz-manage/scripts/test_frz_manage_runtime.py` — covers FRZ-04, FRZ-05, FRZ-06
- [ ] `skills/ll-frz-manage/scripts/frz_manage_runtime.py` — runtime implementation

## Security Domain

> security_enforcement is enabled (nyquist_validation: true in config.json). Security analysis follows project rules.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — CLI tool, no auth |
| V3 Session Management | No | N/A — stateless CLI ops |
| V4 Access Control | No | N/A — filesystem-only, workspace-local |
| V5 Input Validation | Yes | Pydantic schema validation + MSC validator |
| V6 Cryptography | No | N/A — no encryption at rest in v2.0 |

### Known Threat Patterns for YAML-based Schema Validation

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization attack (malicious YAML) | Tampering | Use `yaml.safe_load()` only (already project standard in `qa_schemas.py`, `patch_schema.py`) |
| Path traversal in `package_ref` or `raw_path` | Tampering | Validate paths are relative to workspace root (follow `cli/lib/fs.py` `canonical_to_path` pattern) |
| Registry file corruption | Integrity | Atomic write (temp file + rename) for registry updates |
| FRZ ID collision | Spoofing | Check uniqueness before registration, reject duplicate IDs |

## Sources

### Primary (HIGH confidence)
- ADR-045: `ssot/adr/ADR-045-引入 FRZ 冻结层与全链 Pre-SSOT 集成方案.MD` — FRZ specification, MSC dimensions, anchor ID format, projection invariance
- ADR-050: `ssot/adr/ADR-050-SSOT语义治理总纲.md` — FRZ governance, 5 MSC dimensions, change classification, execution rules
- ADR-051: `ssot/adr/ADR-051-TaskPack顺序执行循环模式.md` — Task Pack structure (Phase 11, but informs registry patterns)
- REQUIREMENTS.md: `.planning/REQUIREMENTS.md` — FRZ-01 through FRZ-06 requirements with skill/tool references
- ROADMAP.md: `.planning/ROADMAP.md` — Phase 7 plans (07-01 through 07-04) with success criteria
- `cli/lib/qa_schemas.py` — Existing dataclass + validation pattern (29 dataclasses, YAML loading, schema error classes)
- `cli/lib/patch_schema.py` — Existing Patch dataclass + validation pattern (enum validation, file loading)
- `cli/lib/registry_store.py` — Existing YAML-backed registry pattern (save/load/list/bind)
- `cli/lib/errors.py` — Existing CommandError taxonomy
- `cli/lib/fs.py` — Existing filesystem helpers (resolve_workspace_root, ensure_parent, to_canonical_path)
- `ssot/schemas/qa/patch.yaml` — Existing YAML schema definition format
- `skills/ll-patch-capture/SKILL.md` — Existing skill template (ll.contract.yaml, ll.lifecycle.yaml, execution protocol)
- `skills/ll-qa-impl-spec-test/SKILL.md` — Existing skill template with canonical runtime reference
- STACK.md: `.planning/research/STACK.md` — Pre-existing technology stack research (Pydantic, DeepDiff, ruamel.yaml)
- [Pydantic v2.13.0 — PyPI](https://pypi.org/project/pydantic/) (HIGH confidence — official PyPI)
- [DeepDiff 9.0.0 — PyPI](https://pypi.org/project/deepdiff/) (HIGH confidence — official PyPI)
- [ruamel.yaml 0.19.1 — PyPI](https://pypi.org/project/ruamel.yaml/) (HIGH confidence — official PyPI)

### Secondary (MEDIUM confidence)
- Installed package versions verified via `/c/Python313/python.exe` (Python 3.13.3)
- graphlib.TopologicalSorter verified via stdlib import test

### Tertiary (LOW confidence)
- `rich` library version — not verified on this machine, based on PyPI listing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified installed packages, confirmed patterns from existing codebase
- Architecture: HIGH — all patterns traced to existing files (`qa_schemas.py`, `registry_store.py`, `patch_schema.py`, skill templates)
- Pitfalls: MEDIUM — based on analysis of existing patterns and ADR text, not runtime-tested

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (30 days for stable infrastructure domain)
