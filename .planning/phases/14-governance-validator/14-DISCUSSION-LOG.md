# Phase 14: 治理对象验证器 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 14-governance-validator
**Areas discussed:** Architecture, Validation mode, Dataclass design, CLI structure, Integration approach

---

## Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Single file (Recommended) | One governance_validator.py with 11 object definitions + validate() for each | ✓ |
| Separate per object | skill_validator.py, module_validator.py, etc. — more modular, but scattered | |
| Hybrid: Grouped by axis | governance_validator_core.py + governance_validator_objects.py | |

**User's choice:** Single file (Recommended)

---

## Validation Mode

| Option | Description | Selected |
|--------|-------------|----------|
| Collect-all (Recommended) | Return list of all violations — developer sees all problems at once (enum_guard.py uses this) | ✓ |
| Fail-fast | Raise on first error — simpler code, but developer must fix one at a time | |

**User's choice:** Collect-all (Recommended)

---

## Dataclass Design

| Option | Description | Selected |
|--------|-------------|----------|
| Frozen dataclass (Recommended) | SkillValidator, ModuleValidator, etc. dataclasses — type-safe, immutable | ✓ |
| Dict-based specs | Field definition dicts + generic validator — more flexible but loses type safety | |

**User's choice:** Frozen dataclass (Recommended)

---

## CLI Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Unified (Recommended) | python -m cli.lib.governance_validator --object Skill file.yaml | ✓ |
| Schema-per-file | python -m cli.lib.skill_validator file.yaml | |

**User's choice:** Unified (Recommended)

---

## Integration Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Tight coupling now | Call enum_guard.validate_enums() internally — Phase 15 just wires into write path | ✓ |
| Standalone for now | Validate fields only, let Phase 15 add enum_guard integration | |

**User's choice:** Tight coupling now

---

## Claude's Discretion

All implementation details delegated to planning:
- Specific dataclass field names and types
- Helper function naming conventions
- Test file organization

