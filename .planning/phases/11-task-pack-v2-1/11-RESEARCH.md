# Phase 11: Task Pack 结构（执行循环延期到 v2.1） - Research

**Researched:** 2026-04-20
**Domain:** YAML schema validation + topological dependency resolution
**Confidence:** HIGH

## Summary

Phase 11 delivers the Task Pack YAML schema definition and `depends_on` dependency resolution via topological sorting. The execution loop (PACK-03/04/05) is explicitly deferred to v2.1 per ADR-051 and REQUIREMENTS.md.

The project already has a well-established pattern for schema validation using frozen Python dataclasses, enums, and manual `_require()` checks — used consistently across `frz_schema.py`, `patch_schema.py`, and `qa_schemas.py`. No external validation library (like `pydantic` or `jsonschema`) is in use; the project's approach is lightweight and sufficient.

For dependency resolution, Python 3.13.3 (confirmed on this machine) includes `graphlib.TopologicalSorter` in the standard library, eliminating any need for external packages. This handles cycle detection and produces a deterministic execution order.

**Primary recommendation:** Follow the existing `frz_schema.py` / `qa_schemas.py` patterns for the schema validator and use `graphlib.TopologicalSorter` for `task_pack_resolver.py`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `graphlib` (stdlib) | Python 3.9+ (3.13.3 confirmed) | Topological sort for `depends_on` resolution | Built-in, no external dependency, supports cycle detection via `CycleError` |
| `pyyaml` | Used throughout project | YAML parsing | Already imported by `frz_schema.py`, `patch_schema.py`, `qa_schemas.py` |
| `pytest` | Used throughout project | Test framework | All existing tests in `cli/lib/test_*.py` use pytest |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses.dataclass(frozen=True)` | Python stdlib | Immutable schema dataclasses | Used by all existing schemas (FRZ, Patch, QA) |
| `enum.Enum` | Python stdlib | Type/status enums | Used by all existing schemas |

**No new packages to install.** Everything is stdlib or already in use.

## Architecture Patterns

### Recommended Project Structure

Following the existing project conventions:

```
ssot/schemas/qa/
  task_pack.yaml              # Human-readable YAML schema definition (new)

cli/lib/
  task_pack_schema.py         # Dataclass + validation module (new)
  test_task_pack_schema.py    # Tests for schema validation (new)
  task_pack_resolver.py       # depends_on topological sort (new)
  test_task_pack_resolver.py  # Tests for dependency resolution (new)

ssot/tasks/
  PACK-SRC-001-001-feat001.yaml  # Example Task Pack file (new, for manual testing)
```

### Pattern 1: Frozen Dataclass Schema (from `frz_schema.py`, `qa_schemas.py`)

**What:** Schema defined as a hierarchy of frozen dataclasses with enum fields, plus a `_parse_*_dict()` function to convert raw YAML dicts into typed instances.

**Example:**
```python
# Source: cli/lib/frz_schema.py (pattern to replicate)
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"
    still_failed = "still_failed"
    skipped = "skipped"
    blocked = "blocked"


class TaskType(str, Enum):
    impl = "impl"
    test_api = "test-api"
    test_e2e = "test-e2e"
    review = "review"
    doc = "doc"
    gate = "gate"


@dataclass(frozen=True)
class Task:
    task_id: str
    type: TaskType
    title: str = ""
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.pending
    verifies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TaskPack:
    artifact_type: str = "task_pack"
    pack_id: str | None = None
    feat_ref: str | None = None
    created_at: str | None = None
    tasks: list[Task] = field(default_factory=list)
```

### Pattern 2: Manual Validation with `_require()` (from `patch_schema.py`, `qa_schemas.py`)

**What:** Required-field checks via `_require()` helper, enum validation via `_enum_check()`, custom error class.

**Example:**
```python
# Source: cli/lib/patch_schema.py (pattern to replicate)
class TaskPackSchemaError(ValueError):
    """Raised when a Task Pack YAML does not conform to its schema."""


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise TaskPackSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise TaskPackSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )
```

### Pattern 3: Topological Sort with `graphlib.TopologicalSorter`

**What:** Python stdlib `graphlib.TopologicalSorter` builds a DAG from task dependencies and returns a valid execution order.

**Example:**
```python
# Verified: Python 3.13.3 stdlib
from graphlib import TopologicalSorter, CycleError


def resolve_order(pack_data: dict) -> list[str]:
    """Resolve tasks into a valid execution order via topological sort.

    Args:
        pack_data: Parsed task_pack YAML dict (the inner dict under 'task_pack' key).

    Returns:
        List of task_ids in executable order.

    Raises:
        TaskPackResolverError: If circular dependencies or missing references exist.
    """
    tasks = pack_data.get("tasks", [])
    task_ids = {t["task_id"] for t in tasks}

    # Validate all depends_on references exist
    for t in tasks:
        for dep in t.get("depends_on", []) or []:
            if dep not in task_ids:
                raise TaskPackResolverError(
                    f"Task '{t['task_id']}' depends on unknown task '{dep}'"
                )

    # Build graph: node -> set of prerequisites
    graph = {t["task_id"]: set(t.get("depends_on", []) or []) for t in tasks}

    try:
        ts = TopologicalSorter(graph)
        return list(ts.static_order())
    except CycleError as e:
        raise TaskPackResolverError(f"Circular dependency detected: {e}") from e
```

### Anti-Patterns to Avoid

- **Using `jsonschema` or `pydantic`:** The project does not use these. Adding them would introduce unnecessary dependencies and break consistency with existing schema modules.
- **Building a custom topological sort:** `graphlib.TopologicalSorter` is stdlib since Python 3.9 and handles cycle detection with clear `CycleError`.
- **Making `depends_on` required:** ADR-051 shows `depends_on: []` for root tasks. It should default to empty list.
- **Making `verifies` required:** ADR-051 shows `verifies: []` for review tasks. It should default to empty list.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topological sort | Custom DFS/Kahn's algorithm | `graphlib.TopologicalSorter` | Handles cycle detection with `CycleError`, stdlib, battle-tested |
| YAML parsing | Custom parser | `yaml.safe_load()` | Already used by all schema modules, handles all edge cases |
| Schema validation framework | New validation library | Existing `_require()` + `_enum_check()` + frozen dataclasses | Project-wide pattern, consistent error messages, no new deps |

**Key insight:** The project's schema validation pattern is deliberate and consistent across 3 modules. Introducing a different approach (pydantic, jsonschema) would create a maintenance burden and inconsistent error reporting.

## Runtime State Inventory

> This phase creates new files (schema, validator, resolver, tests, example). No existing files are renamed or refactored. No runtime state involved.

- **Stored data:** None — this is a greenfield phase creating new schema and library files.
- **Live service config:** None.
- **OS-registered state:** None.
- **Secrets/env vars:** None.
- **Build artifacts:** None.

## Common Pitfalls

### Pitfall 1: CycleError handling in topological sort
**What goes wrong:** Circular dependencies between tasks cause `CycleError` that must be caught and converted to a meaningful error message.
**Why it happens:** Users may write `TASK-A depends on TASK-B` and `TASK-B depends on TASK-A`.
**How to avoid:** Wrap `TopologicalSorter.static_order()` in a try/except `CycleError` block, raise `TaskPackResolverError` with clear message listing the cycle.
**Warning signs:** Test with a deliberate cycle: `{'A': {'B'}, 'B': {'A'}}`.

### Pitfall 2: `depends_on` is `None` vs `[]` in YAML
**What goes wrong:** YAML `depends_on:` with no value parses as `None`, not `[]`.
**Why it happens:** YAML parsing quirk — bare `depends_on:` yields `None`.
**How to avoid:** Always use `(t.get("depends_on") or [])` pattern when reading the field.
**Warning signs:** `TypeError: 'NoneType' is not iterable` when iterating over `depends_on`.

### Pitfall 3: `depends_on` references nonexistent task_id
**What goes wrong:** A task references a `depends_on` value that doesn't exist in the pack.
**Why it happens:** Typo in task_id, or task was removed but dependency wasn't updated.
**How to avoid:** Before building the graph, collect all task_ids and validate every `depends_on` reference exists. Raise `TaskPackResolverError` for unknown refs.
**Warning signs:** `TopologicalSorter` does not validate node references — it will raise a confusing error.

### Pitfall 4: `verifies` field type mismatch
**What goes wrong:** `verifies` in YAML could be a single string instead of a list.
**Why it happens:** Users might write `verifies: AC-001` instead of `verifies: [AC-001]`.
**How to avoid:** In `_parse_task_pack_dict()`, coerce single string to list: `if isinstance(v, str): v = [v]`.

### Pitfall 5: Inconsistent ID format validation
**What goes wrong:** `pack_id` and `task_id` formats are not validated, allowing arbitrary strings.
**Why it happens:** Existing schemas (FRZ, Patch) validate ID formats with regex patterns; Task Pack should too.
**How to avoid:** Add regex validation for `pack_id` (e.g., `PACK-.*`) and `task_id` (e.g., `TASK-\d{3,}`) in `_parse_task_pack_dict()`.

## Code Examples

### Schema YAML Definition (ssot/schemas/qa/task_pack.yaml)

```yaml
# Task Pack YAML Schema (ADR-051 §2.1)
# All task packs must conform to this schema.

task_pack:
  pack_id: string               # PACK-{SRC}-{FEAT}-{slug} format
  feat_ref: string              # References the FEAT this pack belongs to
  created_at: datetime          # ISO 8601
  tasks:
    - task_id: string           # TASK-NNN format (3+ digit zero-padded)
      type: enum[impl, test-api, test-e2e, review, doc, gate]
      title: string
      depends_on:               # Optional — list of prerequisite task_ids
        - string
      status: enum[pending, running, passed, failed, still_failed, skipped, blocked]  # default: pending
      verifies:                 # Optional — list of acceptance criteria IDs
        - string                # e.g., "AC-001"
```

### Example Task Pack File (ssot/tasks/PACK-SRC-001-001-feat001.yaml)

```yaml
task_pack:
  pack_id: PACK-SRC-001-001-feat001
  feat_ref: FEAT-SRC-001-001
  created_at: "2026-04-20T00:00:00+08:00"
  tasks:
    - task_id: TASK-001
      type: impl
      title: Implement User API endpoint
      depends_on: []
      status: pending
      verifies: []

    - task_id: TASK-002
      type: test-api
      title: API test for User endpoint
      depends_on: [TASK-001]
      status: pending
      verifies: [AC-001, AC-002]

    - task_id: TASK-003
      type: test-e2e
      title: E2E journey for User feature
      depends_on: [TASK-001]
      status: pending
      verifies: [AC-003]

    - task_id: TASK-004
      type: review
      title: Code review
      depends_on: [TASK-002, TASK-003]
      status: pending
      verifies: []
```

### Test Pattern (from `test_frz_schema.py` and `test_drift_detector.py`)

```python
"""Unit tests for Task Pack schema validation."""

import tempfile

import pytest
import yaml

from cli.lib.task_pack_schema import (
    Task,
    TaskPack,
    TaskPackSchemaError,
    TaskStatus,
    TaskType,
    validate,
    validate_file,
    _parse_task_pack_dict,
)


def test_task_pack_minimal_structure():
    """TaskPack with minimal valid data."""
    pkg = TaskPack(
        pack_id="PACK-SRC-001-001-feat001",
        feat_ref="FEAT-SRC-001-001",
        tasks=[
            Task(task_id="TASK-001", type=TaskType.impl, title="Do something"),
        ],
    )
    assert pkg.artifact_type == "task_pack"
    assert pkg.tasks[0].status == TaskStatus.pending
    assert pkg.tasks[0].depends_on == []
    assert pkg.tasks[0].verifies == []


def test_task_pack_frozen():
    """TaskPack must be immutable."""
    pkg = TaskPack()
    with pytest.raises(Exception):  # FrozenInstanceError
        pkg.pack_id = "new-id"


def test_validate_rejects_missing_task_id():
    """Task without task_id raises error."""
    with pytest.raises(TaskPackSchemaError):
        validate({"tasks": [{"type": "impl", "title": "No ID"}]})


def test_validate_rejects_orphan_depends_on():
    """depends_on referencing nonexistent task_id raises error."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-999"]},
            ]
        })


def test_validate_rejects_invalid_task_type():
    """Unknown task type raises error."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "tasks": [
                {"task_id": "TASK-001", "type": "unknown-type", "title": "A"},
            ]
        })


def test_validate_rejects_circular_dependency():
    """Circular depends_on raises error (delegated to resolver)."""
    # Note: Schema validates structure; resolver checks cycles
    # This test belongs in test_task_pack_resolver.py
    pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual task execution order | `graphlib.TopologicalSorter` (Python 3.9+) | Python 3.9 | No external dependency, clear cycle errors |
| `pydantic` / `jsonschema` for YAML validation | Frozen dataclasses + `_require()` | Project convention | Consistent error messages, zero new dependencies |
| Ad-hoc YAML parsing | `yaml.safe_load()` + typed parsing functions | Project convention | Safe parsing (no arbitrary code execution) |

**Deprecated/outdated:**
- External topological sort libraries (`networkx`, `toposort`): Unnecessary since `graphlib` in stdlib.
- `pyyaml` `yaml.load()`: Use `yaml.safe_load()` exclusively to prevent arbitrary code execution.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pack_id` format is `PACK-{src}-{feat}-{slug}` | Code Examples | ID validation regex may need adjustment if actual format differs |
| A2 | `task_id` format is `TASK-\d{3,}` (3+ digits) | Code Examples | Same as A1 — format may differ in practice |
| A3 | No external validation libraries are in use | Standard Stack | Would change approach, but verified by inspecting all 3 existing schema modules |

## Open Questions

1. **Should `verifies` field format be validated?**
   - What we know: ADR-051 shows `verifies: [AC-001, AC-002]` — references acceptance criteria.
   - What's unclear: Whether the AC-ID format should be validated (like FRZ validates `JRN-001` format).
   - Recommendation: Validate `verifies` items are non-empty strings, but don't enforce a specific AC-ID format yet (too restrictive). Let the QA layer validate AC references.

2. **Should `title` be required?**
   - What we know: ADR-051 example includes `title` for all tasks.
   - What's unclear: Whether tasks without titles should be rejected.
   - Recommendation: Make `title` required (non-empty string) for human readability in manual execution mode.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9+ | All code | Yes | 3.13.3 | -- |
| pyyaml | YAML parsing | Yes | Installed | -- |
| pytest | Tests | Yes | Installed | -- |
| graphlib (stdlib) | Topological sort | Yes | 3.13.3 stdlib | -- |

**No missing dependencies.** All required libraries are either stdlib or already installed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | None — see `.pytest_cache/` in `cli/lib/` |
| Quick run command | `python -m pytest cli/lib/test_task_pack_schema.py cli/lib/test_task_pack_resolver.py -x` |
| Full suite command | `python -m pytest cli/lib/test_task_pack*.py -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PACK-01 | Schema validates valid Task Pack | unit | `python -m pytest cli/lib/test_task_pack_schema.py -x` | Wave 0 |
| PACK-01 | Schema rejects missing task_id | unit | `python -m pytest cli/lib/test_task_pack_schema.py::test_validate_rejects_missing_task_id -x` | Wave 0 |
| PACK-01 | Schema rejects invalid task type | unit | `python -m pytest cli/lib/test_task_pack_schema.py::test_validate_rejects_invalid_task_type -x` | Wave 0 |
| PACK-01 | Schema rejects orphan depends_on | unit | `python -m pytest cli/lib/test_task_pack_schema.py::test_validate_rejects_orphan_depends_on -x` | Wave 0 |
| PACK-01 | `validate_file()` works with YAML file | unit | `python -m pytest cli/lib/test_task_pack_schema.py -x` | Wave 0 |
| PACK-02 | `resolve_order()` returns correct order (chain) | unit | `python -m pytest cli/lib/test_task_pack_resolver.py -x` | Wave 0 |
| PACK-02 | `resolve_order()` returns correct order (diamond) | unit | `python -m pytest cli/lib/test_task_pack_resolver.py -x` | Wave 0 |
| PACK-02 | `resolve_order()` detects cycles | unit | `python -m pytest cli/lib/test_task_pack_resolver.py -x` | Wave 0 |
| PACK-02 | `resolve_order()` detects missing refs | unit | `python -m pytest cli/lib/test_task_pack_resolver.py -x` | Wave 0 |

### Wave 0 Gaps
- [ ] `cli/lib/test_task_pack_schema.py` — covers PACK-01
- [ ] `cli/lib/test_task_pack_resolver.py` — covers PACK-02
- [ ] `ssot/tasks/PACK-SRC-001-001-feat001.yaml` — manual example for SUCCESS criterion #4

## Security Domain

> This phase creates schema validation and dependency resolution for YAML files. No authentication, no external API calls, no user input handling at runtime. Security risk is minimal.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `yaml.safe_load()` (not `yaml.load()`), schema validation rejects malformed input |

### Known Threat Patterns for YAML Processing

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization attack | Tampering | Use `yaml.safe_load()` exclusively — never `yaml.load()` without `Loader=yaml.SafeLoader` |
| Path traversal via file paths | Information Disclosure | Validate file paths are within expected directories (`ssot/schemas/`, `ssot/tasks/`) |

## Sources

### Primary (HIGH confidence)
- `cli/lib/frz_schema.py` — Read directly: frozen dataclass schema pattern, MSCValidator, _parse_frz_dict
- `cli/lib/patch_schema.py` — Read directly: PatchSchemaError, _require(), _enum_check(), validate_patch()
- `cli/lib/qa_schemas.py` — Read directly: QaSchemaError, validate_file(), _detect_schema_type()
- `cli/lib/test_frz_schema.py` — Read directly: test patterns, frozen dataclass tests, file validation tests
- `ssot/adr/ADR-051-TaskPack顺序执行循环模式.md` — Read directly: Task Pack YAML structure, TaskType enum, TaskStatus state machine, execution rules
- `ssot/adr/ADR-050-SSOT语义治理总纲.md` — Read directly: Task Pack structure definition (section 8.3)
- Python 3.13.3 `graphlib.TopologicalSorter` — Verified via live execution: chain, diamond, and cycle detection all work correctly
- `ssot/schemas/qa/patch.yaml` — Read directly: YAML schema definition pattern
- `ssot/schemas/qa/manifest.yaml` — Read directly: YAML schema definition pattern

### Secondary (MEDIUM confidence)
- `cli/lib/test_drift_detector.py` — Read directly: test pattern with helper functions
- `cli/lib/errors.py` — Read directly: CommandError pattern (used by feat_input_resolver, not by schema modules)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against 3 existing schema modules and Python 3.13.3 stdlib
- Architecture: HIGH — patterns directly extracted from project codebase
- Pitfalls: HIGH — verified via live TopologicalSorter testing, YAML parsing edge cases known

**Research date:** 2026-04-20
**Valid until:** 2026-05-20 (stable — schema patterns are unlikely to change)
