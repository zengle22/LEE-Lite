# Phase 09: 执行语义稳定 + impl-spec-test 增强 - Research

**Researched:** 2026-04-18
**Domain:** SSOT semantic stability, drift detection integration, silent override prevention
**Confidence:** HIGH

## Summary

Phase 09 integrates semantic stability checks into the existing `ll-qa-impl-spec-test` skill (adding a 9th review dimension) and adds silent override prevention to all 6 `ll-dev-*` skills via a new `silent_override.py` library. The phase reuses Phase 8's `drift_detector.py` wholesale -- no reimplementation of drift detection logic is needed.

The work splits into three concrete deliverables: (1) a new `cli/lib/silent_override.py` that compares skill output against FRZ anchor semantics and classifies changes as clarification vs semantic_change, (2) modification of `impl_spec_test_skill_guard.py` to add a `semantic_stability` dimension to the 8 existing ADR-036 dimensions, and (3) updates to all 6 dev skill `validate_output.sh` scripts to invoke `silent_override.py` as a post-output check.

**Primary recommendation:** Reuse `drift_detector.py` directly in `silent_override.py` (D-02 locked), add `semantic_stability` to the existing dimension_reviews JSON envelope in impl-spec-test, and have each dev skill's `validate_output.sh` call `python cli/lib/silent_override.py check --output <output-dir> --frz <frz-id>`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** silent_override.py compares output artifacts against **FRZ anchor semantics** (not FEAT baseline)
- **D-02:** Directly reuse Phase 8 `drift_detector.py` -- no reimplementation
- **D-03:** Need FRZ loading capability (via `frz_registry` or file path reference)
- **D-04:** **block** when: anchor missing, semantic tampered, constraint violation, new field outside derived_allowed
- **D-05:** **pass_with_revisions** when: extra fields within allowed range, expired known_unknown still open
- **D-06:** semantic_stability dimension verdict MUST include `semantic_drift` field
- **D-07:** All 6 `ll-dev-*` skills get silent_override check with **layered baselines**:
  - `feat-to-tech`, `tech-to-impl` -> full FRZ anchor comparison
  - `feat-to-ui`, `proto-to-ui` -> JRN/SM anchors only
  - `feat-to-proto`, `feat-to-surface-map` -> lightweight product_boundary check
- **D-08:** Rule-based classification (clarification vs semantic_change), no LLM or manual gate
- **D-09:** Classification criteria: output additions/modifications/deletions mapping to FRZ anchor -> anchor name matches and content is supplementary -> clarification; anchor name differs or content contradicts -> semantic_change
- **D-10:** semantic_change judgment aligns with ADR-050 §5.2: changes causing downstream test case expected behavior changes = semantic change

### Claude's Discretion
- silent_override.py specific implementation path (direct library vs standalone script)
- Error output format in validate_output.sh
- Specific structure of the 9th dimension in dimension_reviews JSON

### Deferred Ideas (OUT OF SCOPE)
None

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAB-01 | 变更 vs 补全分类器 (clarification vs semantic change) | Rule-based classifier using drift_detector drift_type + content analysis |
| STAB-02 | 执行前语义守卫检查 | semantic_stability dimension in impl-spec-test dimension_reviews |
| STAB-03 | 静默覆盖防护机制 | silent_override.py + validate_output.sh integration in all 6 dev skills |
| STAB-04 | 执行后语义一致性验证 | semantic_drift field in impl-spec-test verdict, block on drift |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `cli.lib.drift_detector` | existing (Phase 8) | Anchor-level drift detection | Already built, 27 tests passing, frozen dataclasses |
| `cli.lib.frz_schema` | existing (Phase 7) | FRZ package parsing + MSC validation | Provides FRZPackage dataclass, _parse_frz_dict |
| `cli.lib.frz_registry` | existing (Phase 7) | FRZ registry lookup | get_frz() loads FRZ record by ID |
| `cli.lib.projection_guard` | existing (Phase 8) | derived_allowed whitelist enforcement | guard_projection() for projection context |
| `cli.lib.anchor_registry` | existing (Phase 7/8) | Anchor ID resolution | resolve() maps anchors to FRZ refs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `yaml` (PyYAML) | existing | FRZ YAML parsing | Loading freeze.yaml from frz_registry package_ref |
| `json` (stdlib) | existing | dimension_reviews JSON | Reading/writing the 9th dimension JSON |
| `pathlib` (stdlib) | existing | File path handling | Resolving output dirs, FRZ file paths |

**No new external dependencies required.** All work uses existing project libraries and Python stdlib.

**Installation:** None needed. All dependencies already in project.

## Architecture Patterns

### Recommended Project Structure

```
cli/lib/
├── silent_override.py        # NEW: Silent override detection + classifier
└── test_silent_override.py   # NEW: Unit tests

skills/ll-qa-impl-spec-test/
├── scripts/
│   ├── impl_spec_test_skill_guard.py  # MODIFIED: +9th dimension validation
│   └── validate_output.sh             # MODIFIED: may need FRZ ref passthrough
├── output/
│   └── dimension_reviews/             # JSON structure extended

skills/ll-dev-feat-to-tech/scripts/
├── validate_output.sh        # MODIFIED: + silent_override check
└── freeze_guard.sh           # (unchanged)

skills/ll-dev-tech-to-impl/scripts/
├── validate_output.sh        # MODIFIED: + silent_override check
└── freeze_guard.sh           # (unchanged)

skills/ll-dev-feat-to-ui/scripts/
├── validate_output.sh        # MODIFIED: + silent_override check
└── freeze_guard.sh           # (unchanged)

skills/ll-dev-proto-to-ui/scripts/
├── validate_output.sh        # MODIFIED: + silent_override check
└── freeze_guard.sh           # (unchanged)

skills/ll-dev-feat-to-proto/scripts/
├── validate_output.sh        # MODIFIED: + silent_override check
└── freeze_guard.sh           # (unchanged)

skills/ll-dev-feat-to-surface-map/scripts/
└── validate_output.sh        # MODIFIED: + silent_override check (may need creation)
```

### Pattern 1: silent_override.py -- Library Module with CLI Entry

**What:** Pure library module that takes output directory + FRZ reference, loads FRZ package, runs drift detection on anchors, classifies changes, returns verdict.

**When to use:** Called by dev skill validate_output.sh scripts and potentially by impl-spec-test dimension check.

**Example:**
```python
# cli/lib/silent_override.py
"""Silent override detection — compares output against FRZ anchor semantics.

Detects when a dev skill output silently rewrites FRZ semantics without
triggering the FRZ revision workflow (D-01, D-02).

Pure library module with CLI entry point.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.lib.drift_detector import (
    check_drift,
    check_derived_allowed,
    check_constraints,
    check_known_unknowns,
)
from cli.lib.errors import CommandError, ensure
from cli.lib.frz_registry import get_frz
from cli.lib.frz_schema import FRZPackage, _parse_frz_dict

import yaml


@dataclass(frozen=True)
class OverrideResult:
    """Result of silent override check."""
    passed: bool
    classification: str  # "ok" | "clarification" | "semantic_change"
    drift_details: list[dict]
    block_reasons: list[str]
    pass_with_revisions: list[str]


def _load_frz_package(workspace_root: Path, frz_id: str) -> FRZPackage:
    """Load FRZ package from registry."""
    record = get_frz(workspace_root, frz_id)
    ensure(record is not None, "REGISTRY_MISS", f"FRZ not found: {frz_id}")
    package_ref = record.get("package_ref", "")
    ensure(package_ref, "INVALID_REQUEST", f"FRZ has no package_ref: {frz_id}")
    frz_path = Path(package_ref)
    ensure(frz_path.exists(), "INVALID_REQUEST", f"FRZ file not found: {package_ref}")
    raw = yaml.safe_load(frz_path.read_text(encoding="utf-8"))
    inner = raw.get("frz_package", raw)
    return _parse_frz_dict(inner)


def check_silent_override(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
    anchor_filter: set[str] | None = None,
) -> OverrideResult:
    """Check if output silently overrides FRZ semantics.
    
    Args:
        frz_package: FRZ package with anchor semantics.
        output_data: Output artifact data (keyed by anchor_id or flat dict).
        anchor_filter: If set, only check these anchors (for layered baselines).
    
    Returns:
        OverrideResult with classification and verdict details.
    """
    # Implementation follows D-04/D-05 block/pass thresholds
    # Uses drift_detector.check_drift for each anchor
    # Classifies as clarification vs semantic_change per D-08/D-09
    ...
```

### Pattern 2: 9th Dimension in dimension_reviews JSON

**What:** The existing impl-spec-test validates 8 ADR-036 dimensions in a JSON object. The 9th dimension `semantic_stability` follows the same envelope pattern.

**When to use:** impl-spec-test deep mode execution.

**Example structure for dimension_reviews.json (extended):**
```json
{
  "functional_logic": { ... },
  "data_modeling": { ... },
  "user_journey": { ... },
  "ui_usability": { ... },
  "api_contract": { ... },
  "implementation_executability": { ... },
  "testability": { ... },
  "migration_compatibility": { ... },
  "semantic_stability": {
    "checked": true,
    "frz_refs": ["FRZ-001"],
    "anchors_checked": ["JRN-001", "ENT-001", "SM-001"],
    "semantic_drift": {
      "has_drift": false,
      "drift_results": [],
      "classification": "ok"
    },
    "verdict": "pass"
  }
}
```

### Pattern 3: Layered Baseline in validate_output.sh

**What:** Each dev skill's validate_output.sh calls silent_override.py with skill-specific anchor filtering.

```bash
# ll-dev-feat-to-tech: full FRZ anchor comparison
python cli/lib/silent_override.py check \
  --output "$1" --frz "$FRZ_ID" --mode full

# ll-dev-feat-to-ui: JRN/SM anchors only
python cli/lib/silent_override.py check \
  --output "$1" --frz "$FRZ_ID" --mode journey_sm

# ll-dev-feat-to-proto: lightweight product_boundary check
python cli/lib/silent_override.py check \
  --output "$1" --frz "$FRZ_ID" --mode product_boundary
```

### Anti-Patterns to Avoid

- **Reimplementing drift detection:** drift_detector.py is complete with 27 tests. Any duplication would create maintenance debt and risk divergence.
- **LLM-based classification:** D-08 locks rule-based classification. LLM introduces nondeterminism in a guard function.
- **Checking against FEAT instead of FRZ:** D-01 locks FRZ anchor as baseline. FEAT is already one projection away from FRZ truth.
- **Blocking on all drift types:** D-05 allows pass_with_revisions for minor deviations. Over-blocking would halt legitimate clarifications.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anchor-level drift detection | New comparison logic | `drift_detector.check_drift()` | Already handles missing/tampered/new_field/constraint_violation/unknown_expired with 27 tests |
| FRZ YAML parsing | Custom YAML loader | `frz_schema._parse_frz_dict()` | Handles all MSC dimension parsing, ID validation, enum conversion |
| FRZ registry lookup | Direct file scanning | `frz_registry.get_frz()` | Atomic writes, revision chain tracking, status management |
| derived_allowed enforcement | Custom whitelist check | `drift_detector.check_derived_allowed()` | Uses INTRINSIC_KEYS constant, handles edge cases |
| Constraint validation | Custom string matching | `drift_detector.check_constraints()` | Already fixed for output_data["constraints"] list bug (Phase 8) |

**Key insight:** Phase 8 built a complete semantic integrity toolkit. Phase 9 is an integration phase, not an implementation phase. The only new code is the classifier layer (clarification vs semantic_change) and the glue that connects existing detectors to skill workflows.

## Runtime State Inventory

> This is a greenfield integration phase (not rename/refactor/migration). No runtime state changes expected.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no existing silent_override state to migrate | None |
| Live service config | None — no external services involved | None |
| OS-registered state | None — no OS registrations | None |
| Secrets/env vars | None — no secret key changes | None |
| Build artifacts | None — no compiled artifacts carry naming | None |

## Common Pitfalls

### Pitfall 1: FRZ Not Found at Runtime
**What goes wrong:** silent_override.py tries to load an FRZ package that hasn't been frozen yet or doesn't exist in the registry.
**Why it happens:** Dev skills may be invoked before the FRZ extraction chain completes, or with a stale FRZ ID.
**How to avoid:** Check FRZ exists and status == "frozen" before running drift checks. Return informative error (not crash) when FRZ unavailable.
**Warning signs:** `REGISTRY_MISS` or `POLICY_DENIED` errors from drift_detector.

### Pitfall 2: validate_output.sh Not Receiving FRZ Reference
**What goes wrong:** Current validate_output.sh scripts only receive artifacts-dir. They have no way to know which FRZ to compare against.
**Why it happens:** The FRZ reference lives in upstream artifacts (FEAT package contains frz_ref), not in the validate_output.sh invocation.
**How to avoid:** silent_override.py must extract frz_ref from the output artifacts themselves (e.g., read the FEAT/TECH/UI output JSON/YAML to find the frz_ref field). This mirrors how drift_detector receives frz_package as a parameter.
**Warning signs:** silent_override.py failing with "no FRZ reference" before checking anything.

### Pitfall 3: Over-Blocking on New Fields
**What goes wrong:** Every new field in output gets flagged as drift, blocking legitimate clarifications.
**Why it happens:** drift_detector.check_drift returns "new_field" for any extra key in target_data not present in FRZ anchor content. But dev skills legitimately add implementation details.
**How to avoid:** Use check_derived_allowed (whitelist-based) for field-level checks, not check_drift (which is designed for extraction integrity). The classifier should distinguish: new fields within derived_allowed = clarification; new fields outside derived_allowed = semantic_change.
**Warning signs:** All dev skill outputs blocked because they add tech implementation fields.

### Pitfall 4: surface-map Skill Missing validate_output.sh
**What goes wrong:** `ll-dev-feat-to-surface-map` has no `validate_output.sh` file (verified: glob returned no results). The CONTEXT.md lists it as needing update.
**Why it happens:** This skill may have been created without a validation script, or uses a different validation pattern.
**How to avoid:** Create validate_output.sh for this skill following the same pattern as other dev skills. Verify it exists before running silent_override check.
**Warning signs:** Phase plan lists 6 skills but only 5 validate_output.sh files exist.

### Pitfall 5: Case Sensitivity in Drift Comparison
**What goes wrong:** The existing `_semantics_match()` in drift_detector does case-insensitive comparison. This may miss subtle semantic tampering.
**Why it happens:** `_semantics_match` normalizes to lowercase for comparison. "Login" == "login" passes.
**How to avoid:** For silent_override, this behavior is acceptable -- it's about semantic meaning, not exact text matching. Document this as expected behavior.
**Warning signs:** Tests expecting exact-match failures that actually pass due to case normalization.

## Code Examples

### Loading FRZ + Running Drift Check (adapted from frz_extractor.py)
```python
# Source: cli/lib/frz_extractor.py lines 233-311
from cli.lib.frz_registry import get_frz
from cli.lib.frz_schema import _parse_frz_dict
from cli.lib.drift_detector import check_drift
import yaml

# Load FRZ from registry
record = get_frz(workspace_root, frz_id)
frz_path = Path(record["package_ref"])
raw = yaml.safe_load(frz_path.read_text(encoding="utf-8"))
frz_pkg = _parse_frz_dict(raw.get("frz_package", raw))

# Build target_data keyed by anchor_id
target_data = {
    journey.id: {"name": journey.name, "id": journey.id, "steps": journey.steps}
    for journey in frz_pkg.core_journeys
}

# Check each anchor
for aid in target_data:
    result = check_drift(aid, frz_pkg, target_data)
    # result.has_drift, result.drift_type, result.detail
```

### Extending dimension_reviews Validation (from impl_spec_test_skill_guard.py)
```python
# Source: cli/lib/impl_spec_test_skill_guard.py lines 278-289
# Current pattern:
expected_dimensions = {
    "functional_logic", "data_modeling", "user_journey", "ui_usability",
    "api_contract", "implementation_executability", "testability",
    "migration_compatibility",
}
if set(dimension_reviews.keys()) != expected_dimensions:
    raise ValueError("dimension reviews must contain all 8 ADR-036 dimensions")

# Modified pattern for Phase 9:
expected_dimensions = {
    "functional_logic", "data_modeling", "user_journey", "ui_usability",
    "api_contract", "implementation_executability", "testability",
    "migration_compatibility", "semantic_stability",  # <-- 9th dimension
}
```

### validate_output.sh Pattern (from existing dev skills)
```bash
# Source: skills/ll-dev-feat-to-tech/scripts/validate_output.sh
#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_output.sh <artifacts-dir>"
  exit 1
fi

python scripts/feat_to_tech.py validate-output --artifacts-dir "$1"
# NEW: Add silent_override check after the skill-specific validation
python cli/lib/silent_override.py check --artifacts-dir "$1"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dev skills validate output format only | Dev skills validate output + semantic stability | Phase 9 (now) | Prevents silent semantic tampering during implementation |
| impl-spec-test has 8 dimensions | impl-spec-test has 9 dimensions (semantic_stability) | Phase 9 (now) | Pre-implementation semantic guard |
| Semantic drift checked only during extraction | Drift checked during extraction + execution | Phase 8 → Phase 9 | Full-chain semantic integrity |

**Deprecated/outdated:**
- Pre-Phase 8: No semantic drift detection existed at all
- Pre-Phase 9: Dev skills had no silent override prevention -- implementers could rewrite semantics undetected

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ll-dev-feat-to-surface-map` needs a new `validate_output.sh` created | Architecture Patterns | Phase 03 plan would miss this skill, leaving a gap in silent override coverage |
| A2 | FRZ reference can be extracted from dev skill output artifacts (e.g., FEAT file contains `frz_ref`) | Pitfall 2 | silent_override.py cannot find FRZ baseline without an explicit --frz parameter or embedded reference |
| A3 | The dimension_reviews JSON file is generated by the CLI runtime (`cli/lib/impl_spec_test_runtime.py`) and not by the skill prompt alone | Code Examples | Modifying the wrong file would not affect actual output |

## Open Questions

1. **How does validate_output.sh get the FRZ reference?**
   - What we know: Current validate_output.sh scripts only receive artifacts-dir. FRZ references exist in upstream artifacts.
   - What's unclear: Whether the artifacts-dir contains a file with frz_ref, or if it needs to be passed as a separate parameter.
   - Recommendation: silent_override.py should first try to extract frz_ref from output artifacts (e.g., feat-package.json), falling back to --frz CLI parameter. This makes the skill scripts minimally invasive.

2. **What is the exact JSON structure of dimension_reviews?**
   - What we know: impl_spec_test_skill_guard.py loads it from a _ref path and checks that keys match expected_dimensions.
   - What's unclear: Whether each dimension value has a standardized sub-structure (verdict, findings, etc.) that semantic_stability must follow.
   - Recommendation: Follow the pattern of existing dimensions -- at minimum include `verdict` ("pass"/"block") and a `semantic_drift` field as required by D-06.

3. **Does ll-dev-feat-to-surface-map need validate_output.sh created or does it validate differently?**
   - What we know: Glob found no validate_output.sh in that skill directory.
   - What's unclear: Whether this is intentional (skill doesn't produce artifacts needing validation) or an oversight.
   - Recommendation: Create validate_output.sh following the standard pattern during 09-03 plan execution.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3 | All scripts | Need to verify | — | — |
| PyYAML | FRZ loading | Need to verify | — | — |
| pytest | Unit tests | Need to verify | — | — |
| `ll-dev-feat-to-surface-map` skill exists | 09-03 validate_output.sh | Need to verify | — | Create skill dir if missing |

**Note:** Environment probing is limited on Windows without direct access to the project's Python environment. The planner should verify `python --version`, `python -c "import yaml"`, and `python -m pytest --version` before writing test code.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | None detected at project root (tests run standalone) |
| Quick run command | `python -m pytest cli/lib/test_silent_override.py -x` |
| Full suite command | `python -m pytest cli/lib/test_silent_override.py skills/ll-qa-impl-spec-test/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAB-01 | Clarification vs semantic_change classification | unit | `pytest cli/lib/test_silent_override.py -k classification -x` | ❌ needs creation |
| STAB-02 | semantic_stability dimension in impl-spec-test | unit | `pytest skills/ll-qa-impl-spec-test/ -x` | ❌ needs creation |
| STAB-03 | silent_override blocks tampered output | unit | `pytest cli/lib/test_silent_override.py -k block -x` | ❌ needs creation |
| STAB-04 | semantic_drift field in verdict | unit | `pytest cli/lib/test_silent_override.py -k drift -x` | ❌ needs creation |

### Sampling Rate
- **Per task commit:** `python -m pytest cli/lib/test_silent_override.py -x`
- **Per wave merge:** `python -m pytest cli/lib/test_silent_override.py skills/ll-qa-impl-spec-test/tests/ -x`
- **Phase gate:** All tests green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `cli/lib/test_silent_override.py` — covers STAB-01, STAB-03, STAB-04
- [ ] `skills/ll-qa-impl-spec-test/tests/test_semantic_stability_dimension.py` — covers STAB-02
- [ ] Test data fixtures: FRZ packages with known anchors for drift comparison scenarios

## Security Domain

> Security enforcement is enabled per config.json (nyquist_validation: true).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | FRZPackage schema validation via frz_schema._parse_frz_dict |
| V6 Cryptography | no | — |

### Known Threat Patterns for drift_detector + silent_override

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| FRZ package tampering | Tampering | MSC validation + registry integrity (Phase 7) |
| Malicious anchor IDs | Tampering | ANCHOR_ID_PATTERN regex validation (drift_detector line 148) |
| Output injection (fake clean drift results) | Tampering | silent_override computes drift independently, does not trust upstream results |
| FRZ reference manipulation | Spoofing | Registry lookup validates package_ref path existence |

## Sources

### Primary (HIGH confidence)
- `cli/lib/drift_detector.py` — Full source read: check_drift, check_derived_allowed, check_constraints, check_known_unknowns APIs
- `cli/lib/frz_schema.py` — Full source read: FRZPackage dataclass, _parse_frz_dict, MSCValidator
- `cli/lib/frz_registry.py` — Full source read: get_frz, register_frz, list_frz
- `cli/lib/projection_guard.py` — Full source read: guard_projection, GUARD_INTRINSIC_KEYS
- `cli/lib/anchor_registry.py` — Full source read: AnchorRegistry, ANCHOR_ID_PATTERN
- `cli/lib/test_drift_detector.py` — Full source read: 27 passing tests
- `skills/ll-qa-impl-spec-test/scripts/impl_spec_test_skill_guard.py` — Full source read: validate_output, 8-dimension validation
- `skills/ll-qa-impl-spec-test/SKILL.md` — Full source read: 8 ADR-036 dimensions, deep mode triggers
- `ssot/adr/ADR-050-SSOT语义治理总纲.md` — Full source read: §5 execution semantic stability, §6 change classification
- `.planning/phases/09-impl-spec-test/09-CONTEXT.md` — Full source read: 10 locked decisions (D-01 through D-10)

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — STAB-01 through STAB-04 requirement definitions
- `.planning/ROADMAP.md` — Phase 9 goals and success criteria
- `.planning/phases/08-frz-src/08-01-SUMMARY.md` — Phase 8 drift detector implementation summary

### Tertiary (LOW confidence)
- `ll-dev-feat-to-surface-map` skill directory structure — glob returned no files; existence unverified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via direct source reads
- Architecture: HIGH — existing patterns from impl_spec_test_skill_guard.py and validate_output.sh files provide clear templates
- Pitfalls: MEDIUM — based on analysis of existing code patterns; some edge cases (FRZ reference extraction) need runtime verification

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (stable domain, no fast-moving dependencies)
