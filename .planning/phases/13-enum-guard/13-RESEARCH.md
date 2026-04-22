# Phase 13: Enum Guard - Research

**Researched:** 2026-04-22
**Domain:** Python enum validation, YAML schema enforcement, SSOT governance
**Confidence:** HIGH

## Summary

The codebase has a well-established pattern for enum validation across 7 schema modules, each defining their own `str, Enum` classes and using a shared `_enum_check()` helper. There is no centralized `enum_guard.py` module yet. The 6 enum fields (skill_id, module_id, assertion_layer, failure_class, gate_verdict, phase) and their allowed/forbidden values are authoritatively defined in SRC-009 and ADR-052. The enum_guard must centralize these frozen values and provide a single validation entry point that can be called by all schema validators and the SSOT write path.

**Primary recommendation:** Create `cli/lib/enum_guard.py` as a centralized module with enum definitions, allowed_values/forbidden_semantics maps, and a `validate_enums(data: dict) -> list[str]` function that returns error messages for all violations.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `enum.Enum` | 3.13 (built-in) | Enum definitions | Already used across 7 schema modules in codebase |
| Python stdlib `dataclasses` | 3.13 (built-in) | Immutable validation result | Matches codebase pattern (frozen=True dataclasses) |

### No new dependencies needed
All validation uses Python stdlib. The codebase already has `pyyaml` for YAML loading.

## User Constraints (from upstream requirements)

### Requirements
- **ENUM-01**: Implement `cli/lib/enum_guard.py` with allowed_values validation for 6 enum fields (skill_id, module_id, assertion_layer, failure_class, gate_verdict, phase)
- **ENUM-02**: enum_guard rejects forbidden_semantics values for all 6 enum fields
- **ENUM-03**: enum_guard provides clear error messages with field name, value, and allowed values

### Locked Enum Values (from SRC-009, frozen)

| Field | Allowed Values | Forbidden Semantics |
|-------|---------------|---------------------|
| skill_id | `["qa.test-plan", "qa.test-run"]` | Internal modules registered as Skill |
| module_id | `["feat-to-testset", "api-plan-compile", "api-manifest-compile", "api-spec-compile", "e2e-plan-compile", "e2e-manifest-compile", "e2e-spec-compile", "environment-provision", "run-manifest-gen", "scenario-spec-compile", "state-machine-executor", "bypass-detector", "independent-verifier", "accident-package", "failure-classifier", "test-data-provision", "l0-smoke-check", "test-exec-web-e2e", "test-exec-cli", "settlement", "gate-evaluation"]` | Direct user invocation |
| assertion_layer | `["A", "B", "C"]` | Skip A or B layer, go directly to C |
| failure_class | `["ENV", "DATA", "SCRIPT", "ORACLE", "BYPASS", "PRODUCT", "FLAKY", "TIMEOUT"]` | New undefined categories, ad-hoc classification |
| gate_verdict | `["pass", "conditional_pass", "fail", "provisional_pass"]` | Custom verdict types |
| phase | `["1a", "1b", "2", "3", "4"]` | Skip phases, go directly to production |

Source: [VERIFIED: `ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md` lines 190-224]

## Architecture Patterns

### Current Pattern: Distributed `_enum_check()` Across 7 Modules

Every schema module defines its own `_enum_check()` function with identical logic:

```python
def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise <SpecificSchemaError>(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )
```

Source: [VERIFIED: codebase grep, found in all 7 files below]

| Module | `_enum_check` Location | Enum Classes Defined |
|--------|----------------------|---------------------|
| `cli/lib/qa_schemas.py` | line 327 | LifecycleStatus, MappingStatus, EvidenceStatus, WaiverStatus, Priority, ScenarioType, ChainType, VerdictConclusion, ReleaseRecommendation, CapStatus, GateResult |
| `cli/lib/task_pack_schema.py` | line 103 | TaskStatus, TaskType |
| `cli/lib/testset_schema.py` | line 38 | (imports Enum, no enum classes defined yet) |
| `cli/lib/gate_schema.py` | line 52 | GateVerdict |
| `cli/lib/environment_schema.py` | line 40 | Browser |
| `cli/lib/frz_schema.py` | (no _enum_check, manual enum parsing) | FRZStatus |
| `cli/lib/patch_schema.py` | (no _enum_check, manual validation) | PatchStatus, ChangeClass, GradeLevel, PatchProblem, PatchDecision |

### Recommended Pattern: Centralized `enum_guard.py`

```
cli/lib/enum_guard.py
├── Enum classes (6 governance enums from SRC-009)
├── ENUM_REGISTRY: dict[field_name, EnumClass]
├── FORBIDDEN_SEMANTICS: dict[field_name, list[str]]
├── EnumGuardError(dataclass): field, value, allowed, forbidden_reason
├── validate_field(field_name, value, label) -> list[EnumGuardError]
├── validate_enums(data: dict, label: str) -> list[EnumGuardError]
└── check_all(data: dict, label: str) -> None  # raises on first error
```

### Existing `projection_guard.py` Pattern (Related, Not Enum)

`cli/lib/projection_guard.py` provides a `GuardResult` dataclass with `passed`, `verdict`, `violations` fields for FRZ-derived field whitelisting. This is a different concern (field projection from FRZ) but shares the pattern of returning structured validation results.

Source: [VERIFIED: `cli/lib/test_projection_guard.py`]

### Existing `forbidden field` Pattern

Each schema module already implements forbidden field checks:
- `gate_schema.py`: `hidden_verifier_failure` forbidden (line 151)
- `environment_schema.py`: `embedded_in_testset` forbidden (line 153)
- `testset_schema.py`: `test_case_pack`, `script_pack` forbidden (line 121)
- `patch_schema.py`: change_class/ status validated against enum values (lines 196-207)

The enum_guard should extend this pattern to cover the 6 governance enum fields.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Enum value validation | Custom string matching | `str, Enum` + `_enum_check()` | Already the established pattern across 7 modules |
| Forbidden value detection | Regex or partial matching | `forbidden_semantics` lookup table | SRC-009 defines exact forbidden semantics per field |
| Error message formatting | Ad-hoc string concatenation | `EnumGuardError` dataclass | Ensures ENUM-03 compliance (field, value, allowed values) |

**Key insight:** The codebase already has 13 `str, Enum` classes across schema modules. The enum_guard should define the 6 governance enums as `str, Enum` classes to maintain consistency, not use a different mechanism.

## Common Pitfalls

### Pitfall 1: GateVerdict Enum Duplication
**What goes wrong:** `gate_schema.py` already defines `GateVerdict` enum with the exact 4 values that enum_guard needs. If enum_guard redefines it, there will be two sources of truth.
**Why it happens:** `gate_schema.py` was created in Phase 12, before enum_guard (Phase 13).
**How to avoid:** enum_guard should either (a) import `GateVerdict` from `gate_schema.py`, or (b) be the single source of truth and have `gate_schema.py` import from enum_guard. Recommendation: (a) -- import existing enums from their source modules, only define enums that don't already have a module.

### Pitfall 2: Forbidden Semantics vs Allowed Values
**What goes wrong:** Confusing "value not in allowed_values" (ENUM-01) with "value matches forbidden_semantics" (ENUM-02). These are separate checks.
**Why it happens:** The forbidden_semantics are behavioral descriptions ("internal modules registered as Skill"), not literal string values to reject.
**How to avoid:** The enum_guard should check allowed_values first (concrete string comparison). For forbidden_semantics, document them as metadata in error messages but focus validation on the allowed_values whitelist. The forbidden_semantics in SRC-009 are governance rules, not runtime-checkable string patterns.

### Pitfall 3: skill_id vs skill_ref Confusion
**What goes wrong:** The codebase uses `skill_id` (dot notation: `qa.test-plan`) for user-facing calls and `skill_ref` (underscore: `skill.qa.test_plan`) for internal registration. enum_guard must validate `skill_id` only.
**Why it happens:** ADR-052 explicitly distinguishes these two naming conventions (lines 186-188).
**How to avoid:** enum_guard's `skill_id` enum values use dot notation only: `["qa.test-plan", "qa.test-run"]`.

### Pitfall 4: module_id Has 21 Values -- Easy to Miss One
**What goes wrong:** Manually typing all 21 module_id values risks typos or omissions.
**Why it happens:** The list is long and was manually compiled.
**How to avoid:** Copy-paste directly from SRC-009 line 198. The enum_guard module should include a comment citing the source line for auditability.

### Pitfall 5: phase Values Are Strings, Not Integers
**What goes wrong:** Treating `"1a"` and `"1b"` as numeric phase identifiers.
**Why it happens:** `"1a"` looks like it should be `1.1` or similar.
**How to avoid:** Phase values must be strings: `["1a", "1b", "2", "3", "4"]`. ADR-052 defines them as implementation stages, not version numbers.

## Code Examples

### Enum Definition Pattern (from existing gate_schema.py)
```python
# Source: cli/lib/gate_schema.py:33-37
class GateVerdict(str, Enum):
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"
    PROVISIONAL_PASS = "provisional_pass"
```

### Enum Validation Pattern (from existing qa_schemas.py)
```python
# Source: cli/lib/qa_schemas.py:327-332
def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise QaSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )
```

### Forbidden Field Pattern (from existing gate_schema.py)
```python
# Source: cli/lib/gate_schema.py:151-154
if "hidden_verifier_failure" in inner:
    raise GateSchemaError(
        f"{label}: forbidden field 'hidden_verifier_failure' is not allowed in Gate"
    )
```

### Recommended enum_guard Error Dataclass
```python
@dataclass(frozen=True)
class EnumGuardError:
    field: str           # e.g., "skill_id"
    value: str           # the invalid value
    allowed: list[str]   # allowed_values for this field
    label: str           # context (e.g., "module XYZ")

    def __str__(self) -> str:
        return (
            f"{self.label}: {self.field} must be one of {self.allowed}, "
            f"got '{self.value}'"
        )
```

## How Enum Values Appear in Practice (YAML Artifacts)

### skill_id -- NOT YET present in any YAML
The `skill_id` field is defined in governance object contracts (SRC-009 line 104) but no existing YAML files use it yet. It will appear in future Skill definition files.

### module_id -- NOT YET present in any YAML
Appears in ADR-052 module tables (lines 129-138, 143-159, 165-507) as table cell values. Not yet serialized to YAML.

### assertion_layer -- Appears as `assertion_requirements` in TESTSET
```yaml
# Source: ssot/testset/TESTSET-009__test-governance-dual-axis-testset.yaml:52-55
assertion_requirements:
- A层（交互断言）: 所有 golden paths 必须覆盖
- B层（页面结果断言）: 所有 golden paths 必须覆盖
- C层（业务状态断言）: 按阶段要求执行
```

### failure_class -- Appears in TESTSET as test descriptions
```yaml
# Source: ssot/testset/TESTSET-009__test-governance-dual-axis-testset.yaml:56-64
failure_classification_test:
- ENV: 环境不可用/版本不匹配
- DATA: 测试数据缺失/脏状态
- SCRIPT: 测试脚本缺陷
- ORACLE: 断言预期行为定义不清
- BYPASS: AI 执行跳步/违规
- PRODUCT: 产品真实 bug
- FLAKY: 偶发性失败
- TIMEOUT: 超时失败
```

### gate_verdict -- Appears in Gate JSON
```json
// Source: ssot/gates/GATE-FRZ-SRC-009.json:6
"verdict": "pass"
```

### phase -- NOT YET present in any YAML
Phase values are defined in ADR-052 implementation plan (lines 983-1035) as section headers. They appear in `gate_schema.py` Gate dataclass as optional `phase` field but no YAML file currently uses it.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No enum validation | Per-module `_enum_check()` | Phase 12 (gate_schema, environment_schema) | Each module manages its own enums |
| No forbidden field guards | Per-module forbidden field checks | Phase 12 | Manual per-module enforcement |
| No centralized enum registry | enum_guard (Phase 13) | NOW | Single source of truth for 6 governance enums |

**Outdated approaches to avoid:**
- Defining enums as plain string constants (dict or list) -- all existing modules use `str, Enum` classes
- Using `IntEnum` -- the codebase exclusively uses `str, Enum` for YAML serialization compatibility

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | forbidden_semantics are governance rules not runtime-checkable strings | Pitfall 2 | enum_guard may need different validation logic if forbidden_semantics are literal values |
| A2 | GateVerdict should be imported from gate_schema.py, not redefined | Pitfall 1 | Duplicate enum definitions could drift out of sync |
| A3 | enum_guard.validate_enums() should return a list of errors (not raise on first) | Code Examples | Caller may expect exception-based API instead |

## Open Questions

1. **Should enum_guard import existing enums from their source modules or redefine them?**
   - What we know: `GateVerdict`, `Browser`, `FRZStatus`, `PatchStatus`, `ChangeClass`, `TaskStatus`, `TaskType`, and 10+ enums in qa_schemas already exist
   - What's unclear: Whether enum_guard should be the single source of truth for ALL enums, or only the 6 governance enums from SRC-009
   - Recommendation: enum_guard defines only the 6 governance enums from SRC-009. For `GateVerdict`, import from `gate_schema.py`. Other enums remain in their modules. This minimizes refactoring.

2. **Should forbidden_semantics be checked at runtime or documented only?**
   - What we know: SRC-009 defines forbidden_semantics as behavioral descriptions ("内部模块注册为Skill", "直接用户调用")
   - What's unclear: These are not string literals that can be matched against a YAML value
   - Recommendation: Include forbidden_semantics as metadata in the module (for documentation and error messages) but only validate allowed_values at runtime. Flag for discuss-phase confirmation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | enum_guard.py implementation | Yes | 3.13.3 | -- |
| pytest | Test suite | Yes | 9.0.2 | -- |
| pyyaml | YAML loading (existing) | Yes | installed | -- |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None detected (using pytest defaults) |
| Quick run command | `python -m pytest cli/lib/test_enum_guard.py -x` |
| Full suite command | `python -m pytest cli/lib/test_enum_guard.py -v` |

### Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENUM-01 | allowed_values validation for 6 fields | unit | `pytest cli/lib/test_enum_guard.py::test_allowed_values -x` | Will create |
| ENUM-02 | forbidden_semantics rejection | unit | `pytest cli/lib/test_enum_guard.py::test_forbidden_semantics -x` | Will create |
| ENUM-03 | Clear error messages with field/value/allowed | unit | `pytest cli/lib/test_enum_guard.py::test_error_messages -x` | Will create |

### Wave 0 Gaps
- [ ] `cli/lib/test_enum_guard.py` -- covers ENUM-01, ENUM-02, ENUM-03
- [ ] Framework install: `pip install pytest` -- already installed

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | enum_guard whitelist validation |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid enum value injection | Tampering | Whitelist validation (allowed_values) |
| Unauthorized module invocation | Elevation of Privilege | module_id whitelist prevents user-called internal modules |

## Sources

### Primary (HIGH confidence)
- `ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md` -- authoritative enum definitions (lines 190-224), governance object contracts (lines 104-182), frozen contracts (lines 93-99)
- `ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md` -- comprehensive architecture reference, module tables, enum freeze section
- `cli/lib/gate_schema.py` -- GateVerdict enum, _enum_check pattern, forbidden field pattern
- `cli/lib/environment_schema.py` -- Browser enum, _enum_check pattern
- `cli/lib/task_pack_schema.py` -- TaskStatus/TaskType enums, _enum_check pattern
- `cli/lib/qa_schemas.py` -- 11 enum classes, _enum_check pattern, extensive validation examples
- `cli/lib/patch_schema.py` -- PatchStatus/ChangeClass enums, manual enum validation
- `cli/lib/frz_schema.py` -- FRZStatus enum, manual enum parsing
- `.planning/REQUIREMENTS.md` -- ENUM-01, ENUM-02, ENUM-03 requirements with exact allowed values

### Secondary (MEDIUM confidence)
- `ssot/testset/TESTSET-009__test-governance-dual-axis-testset.yaml` -- example of how failure_class/assertion_layer appear in YAML
- `ssot/gates/GATE-FRZ-SRC-009.json` -- gate_verdict in practice
- `ssot/feat/FEAT-009-D__test-governance-declarative-asset-layering.md` -- FEAT scope confirmation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Python stdlib, no new dependencies needed
- Architecture: HIGH -- 7 existing modules with identical patterns to follow
- Pitfalls: HIGH -- identified from codebase analysis (GateVerdict duplication, skill_id/skill_ref distinction)
- Enum values: HIGH -- directly copied from frozen SRC-009

**Research date:** 2026-04-22
**Valid until:** 2026-05-22 (stable governance enums, unlikely to change before Phase 13 implementation)
