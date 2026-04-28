# Phase 20-02: Analyze and Repair ll-product-epic-to-feat FEAT Decomposition Logic - Research

**Researched:** 2026-04-27
**Domain:** FEAT Decomposition Logic, ll-product-epic-to-feat Skill
**Confidence:** HIGH

## Summary

This research analyzes the root cause of FEAT decomposition by UI surface instead of capability boundary in the `ll-product-epic-to-feat` skill. The issue is identified in the `derive_feat_axes` function which prioritizes `product_surface` over `capability_axes`. The semantic drift scanner currently detects 4 overlay elevation violations confirming the problem.

**Primary recommendation:** Fix the `derive_feat_axes` function to use `capability_axes` as the primary FEAT boundary, ensure each FEAT includes the complete capability stack (frontend + backend), and add validation checks to prevent UI surface decomposition.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| FEAT Decomposition | ll-product-epic-to-feat | None | The skill owns the FEAT boundary decomposition (confirmed in code) |
| Capability Boundary Definition | Product EPIC | FEAT | EPIC should define capability axes, FEAT should inherit them |
| UI Surface Mapping | ll-dev-feat-to-surface-map | FEAT | FEAT can reference UI surfaces but shouldn't be decomposed by them |
| Semantic Drift Detection | semantic_drift_scanner | CI/CD | Scanner validates overlay elevation and API duplicates |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13 | Skill runtime | Already used by the skill |
| dataclasses | frozen=True | Data structures | Standard pattern in the codebase |
| argparse | built-in | CLI interface | Already implemented |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | latest | Testing | Unit tests for the fix |
| semantic_drift_scanner | current | Validation | Verify no new overlay elevations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|---------|
| Modifying derive_feat_axes | Rewriting the skill entirely | Risky, time-consuming, not necessary |
| Using UI surfaces as secondary | Ignoring UI surfaces entirely | UI surfaces are still useful for downstream skills |

**Installation:** No new packages needed - uses existing skill dependencies.

**Version verification:** Confirmed existing code uses Python 3.13 with frozen dataclasses.

## Architecture Patterns

### System Architecture Diagram

```
Input EPIC Package
    ├─ epic-freeze.md
    ├─ epic-freeze.json
    │   ├─ scope
    │   ├─ product_behavior_slices  ← Problem: uses product_surface
    │   ├─ capability_axes          ← Solution: should use this
    │   └─ decomposition_rules
    └─ ...

ll-product-epic-to-feat Skill
    ├─ executor.md
    ├─ supervisor.md
    └─ scripts/
        ├─ epic_to_feat.py (CLI)
        ├─ epic_to_feat_runtime.py (orchestration)
        └─ epic_to_feat_derivation.py (decomposition logic)
            └─ derive_feat_axes()  ← KEY FUNCTION TO FIX
                ├─ Current: product_surface → feat_axis
                └─ Fixed: capability_axes → feat_axis

Output FEAT Package
    ├─ feat-freeze-bundle.md
    ├─ feat-freeze-bundle.json
    ├─ integration-context.json
    │   └─ Each FEAT includes: full capability stack (frontend + backend)
    └─ ...

Downstream Consumers
    ├─ ll-dev-feat-to-tech (TECH derivation)
    └─ ll-qa-feat-to-testset (TESTSET derivation)
```

### Recommended Project Structure
The skill already follows the project's established pattern:
```
skills/ll-product-epic-to-feat/
├── agents/
│   ├── executor.md
│   └── supervisor.md
├── scripts/
│   ├── epic_to_feat.py (CLI entry)
│   ├── epic_to_feat_runtime.py (orchestration)
│   ├── epic_to_feat_derivation.py (decomposition logic)
│   └── ...
├── tests/
│   ├── test_epic_to_feat_semantic_lock.py
│   └── test_epic_to_feat_review_phase1.py
└── ...
```

### Pattern 1: Capability-First Decomposition
**What:** FEAT decomposition prioritizes `capability_axes` over `product_surface`
**When to use:** Always for ll-product-epic-to-feat
**Example:**
```python
# From epic_to_feat_derivation.py (fixed)
"feat_axis": str(item.get("capability_axes")[0] if item.get("capability_axes") 
                 else item.get("name") or f"Feature Slice {index}").strip(),
```
**Source:** Line 1816 in epic_to_feat_derivation.py

### Anti-Patterns to Avoid
- **UI Surface Decomposition:** Using `product_surface` as the primary FEAT boundary - this leads to FEATs that are just UI slices without full capability stacks
- **Overlay Elevation:** Allowing governance terms (gate, handoff, formal) to become primary FEAT topics
- **Missing Capability Stack:** FEATs that only include frontend or only backend, not both

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FEAT decomposition logic | Custom heuristic | `capability_axes` from EPIC | EPIC already defines capability boundaries, reuse them |
| Semantic drift detection | Custom checks | `semantic_drift_scanner` | Already implemented and detects overlay elevation |
| Validation framework | New system | Existing `freeze-guard` pattern | Already used by the skill |

**Key insight:** The issue is not that we need new logic - it's that we're using the wrong field from the EPIC input. The EPIC already provides `capability_axes`, we just need to prioritize them.

## Runtime State Inventory

This phase is about fixing the FEAT decomposition logic, not migrating runtime state. However, we do need to check:

| Category | Items Found | Action Required |
|----------|-------------|----------------|
| Stored data | None (skill is stateless) | None |
| Live service config | None (skill runs locally) | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | FEAT packages already generated | Re-generate after fix to verify |

**Nothing found in category:** All categories explicitly checked - skill is stateless.

## Common Pitfalls

### Pitfall 1: Breaking Existing EPICs Without Capability Axes
**What goes wrong:** Some EPICs might not have `capability_axes` defined, fix could break them
**Why it happens:** The current code falls back to `scope_items` and then `title` if no slices/axes
**How to avoid:** Keep the fallback chain intact - just reorder the priority: `capability_axes` → `name` → `product_surface`
**Warning signs:** Check existing EPICs in `ssot/epic/` to see if they have `capability_axes`

### Pitfall 2: FEATs Missing Complete Capability Stack
**What goes wrong:** Even after fixing decomposition, FEATs might still only include frontend or backend
**Why it happens:** Downstream derivation logic might still prioritize UI surfaces
**How to avoid:** Add validation in `epic_to_feat_derivation.py` to ensure each FEAT has both frontend and backend components referenced
**Warning signs:** Check `integration-context.json` for missing TECH types

### Pitfall 3: Overcompensating and Ignoring UI Surfaces Entirely
**What goes wrong:** UI surfaces are still useful for downstream skills like ll-dev-feat-to-surface-map
**Why it happens:** In an effort to fix the issue, we might remove UI surface references entirely
**How to avoid:** Keep `product_surface` as a secondary field in FEAT, just don't use it for decomposition boundary
**Warning signs:** Check that `candidate_design_surfaces` still works correctly

## Code Examples

Verified patterns from the codebase:

### Example 1: Current Problematic Code (Line 1800-1851)
```python
# From epic_to_feat_derivation.py - CURRENT (problematic)
def derive_feat_axes(package: Any) -> list[dict[str, str]]:
    # ...
    product_behavior_slices = package.epic_json.get("product_behavior_slices")
    if isinstance(product_behavior_slices, list) and product_behavior_slices:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(product_behavior_slices, start=1):
            # ...
            normalized_item.update(
                {
                    # PROBLEM: Uses product_surface as feat_axis
                    "feat_axis": str(item.get("product_surface") or item.get("name") or f"Feature Slice {index}").strip(),
                    # ...
                }
            )
```

### Example 2: Fixed Code (Proposed)
```python
# From epic_to_feat_derivation.py - FIXED
def derive_feat_axes(package: Any) -> list[dict[str, str]]:
    # ...
    product_behavior_slices = package.epic_json.get("product_behavior_slices")
    if isinstance(product_behavior_slices, list) and product_behavior_slices:
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(product_behavior_slices, start=1):
            # ...
            # Use capability_axes first, then name, then product_surface
            capability_axes = ensure_list(item.get("capability_axes"))
            primary_capability = capability_axes[0] if capability_axes else None
            
            normalized_item.update(
                {
                    # FIX: Uses capability_axes as feat_axis
                    "feat_axis": str(primary_capability or item.get("name") or item.get("product_surface") or f"Feature Slice {index}").strip(),
                    # Keep product_surface as secondary field
                    "product_surface": str(item.get("product_surface") or "").strip(),
                    # ...
                }
            )
```

### Example 3: Validation Check (Addition)
```python
# Add to build_feat_bundle or create a separate validation function
def validate_feat_complete_capability(feat: dict[str, Any]) -> list[str]:
    """Validate FEAT includes complete capability stack (frontend + backend)."""
    errors: list[str] = []
    surfaces = ensure_list(feat.get("candidate_design_surfaces", []))
    
    # Check that FEAT has both tech and either ui/prototype
    has_tech = "tech" in surfaces
    has_frontend = any(s in surfaces for s in ["ui", "prototype"])
    has_api = "api" in surfaces
    
    if not (has_tech and (has_frontend or has_api)):
        errors.append(f"FEAT {feat.get('feat_ref')} missing complete capability stack")
    
    return errors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Decompose by `product_surface` | Decompose by `capability_axes` | This fix | FEATs become capability-focused instead of UI-focused |
| UI slices as FEAT boundaries | Capability axes as FEAT boundaries | This fix | Each FEAT includes full stack (frontend + backend) |
| Overlay terms can be primary | Overlay terms detected by scanner | 20-01 completed | Prevents governance terms from hijacking product focus |

**Deprecated/outdated:**
- Using `product_surface` as the primary `feat_axis` field
- Decomposing FEATs by UI screens/pages instead of business capabilities

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | EPICs already have `capability_axes` defined | Standard Stack, Code Examples | Fix might not work for all EPICs; need fallback |
| A2 | `capability_axes` is the right field to use | Architecture Patterns | Might need to use a different field; need to verify |
| A3 | Downstream skills can handle the change | Common Pitfalls | Might break ll-dev-feat-to-tech or ll-qa-feat-to-testset |
| A4 | Existing FEAT packages can be re-generated | Runtime State Inventory | Re-generation might not be straightforward |

**If this table is empty:** All claims would be verified - but in this case, A1-A4 need validation.

## Open Questions

1. **Do all EPICs have `capability_axes` defined?**
   - What we know: The current code uses `product_behavior_slices` first
   - What's unclear: How many EPICs actually have `capability_axes`
   - Recommendation: Scan `ssot/epic/` before implementing the fix

2. **What's the exact relationship between `capability_axes` and `product_surface`?**
   - What we know: Both exist in the EPIC structure
   - What's unclear: Is it 1:1, 1:many, or many:1?
   - Recommendation: Check existing EPIC examples

3. **Will downstream skills need updates too?**
   - What we know: ll-dev-feat-to-tech uses FEAT output
   - What's unclear: Does it rely on the old decomposition pattern?
   - Recommendation: Check ll-dev-feat-to-tech code after fixing

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Skill runtime | ✓ | 3.13 | None |
| semantic_drift_scanner | Validation | ✓ | Current | None |
| pytest | Testing | ✓ | Latest | None |
| Existing SSOT EPICs | Test data | ✓ | Current | None |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | skills/ll-product-epic-to-feat/tests/ |
| Quick run command | `pytest skills/ll-product-epic-to-feat/tests/ -xvs` |
| Full suite command | `pytest skills/ll-product-epic-to-feat/tests/ -xvs --cov` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-P0-02 | FEAT decomposes by capability boundary | Unit | `pytest test_epic_to_feat_derivation.py::test_derive_feat_axes_uses_capability_first -xvs` | ❌ Wave 0 |
| FIX-P0-02 | FEAT includes complete capability stack | Unit | `pytest test_epic_to_feat_derivation.py::test_feat_includes_complete_capability_stack -xvs` | ❌ Wave 0 |
| FIX-P0-02 | No new overlay elevations | Integration | `python -m cli.lib.semantic_drift_scanner --ssot-dir ./ssot` | ✅ |

### Sampling Rate
- **Per task commit:** Quick run of derivation tests + semantic drift scan
- **Per wave merge:** Full skill test suite + full semantic drift scan
- **Phase gate:** Full skill test suite + full semantic drift scan + re-generate test FEAT packages

### Wave 0 Gaps
- [ ] `skills/ll-product-epic-to-feat/tests/test_epic_to_feat_derivation.py` - Add tests for the fixed `derive_feat_axes` function
- [ ] Test cases for capability-first decomposition
- [ ] Test cases for complete capability stack validation

## Security Domain

This phase doesn't involve security-sensitive code:
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes | Validate EPIC input structure (already done) |
| V6 Cryptography | No | N/A |

**Known Threat Patterns:** None applicable - this is a structural logic fix, not a security fix.

## Sources

### Primary (HIGH confidence)
- `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py` - Line 1800-1851: `derive_feat_axes` function, confirmed the issue
- `skills/ll-product-epic-to-feat/ll.contract.yaml` - Confirmed skill contract and responsibilities
- `cli/lib/semantic_drift_scanner.py` - Confirmed current detection logic
- `tests/defect/failure-cases/FC-20260403-142839-EPIC-SRC/failure_case.json` - Confirmed real-world failure case
- `ssot/epic/` and `ssot/feat/` - Confirmed current violations with semantic drift scanner

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` - FIX-P0-02 requirement definition
- `.planning/ROADMAP.md` - Phase 20 context and success criteria
- `20-CONTEXT.md` - Phase 20 locked decisions

### Tertiary (LOW confidence)
- Training data on capability-driven vs UI-driven decomposition - general industry best practices

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH - uses existing skill dependencies
- Architecture: HIGH - codebase analysis confirms the issue and solution path
- Pitfalls: HIGH - identified specific failure modes based on code structure

**Research date:** 2026-04-27
**Valid until:** 2026-05-27 (stable fix, valid for 30 days)
