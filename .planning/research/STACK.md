# Technology Stack

**Project:** LEE-Lite-skill-first — v2.0 SSOT Semantic Governance
**Researched:** 2026-04-18

## Recommended Stack

### Core Validation (FRZ MSC + Schema Enforcement)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pydantic v2** | 2.13.0 | FRZ MSC validation, Task Pack schema, Patch schema upgrade | Already uses dataclass pattern in `qa_schemas.py` and `patch_schema.py`. Pydantic v2 adds runtime validation, field constraints, and clear error messages. Frozen dataclasses map cleanly to Pydantic `BaseModel`. The project already has 29 dataclasses in `qa_schemas.py` — migration path is well-understood. |
| **PyYAML** | 6.0.2 | YAML read/write (already in use) | Used across 15+ files in `cli/lib/`. No reason to switch. |
| **jsonschema** | 4.26.0 | JSON Schema validation for external FRZ packages | Provides interoperable schema definitions that can be consumed by non-Python tools (CI gates, pre-commit hooks). Use alongside Pydantic: Pydantic for Python runtime, jsonschema for standalone `.json` schema files. |

### Semantic Diff & Drift Detection

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **DeepDiff** | 9.0.0 | Semantic comparison of FRZ/SRC/EPIC/FEAT YAML snapshots | The dominant Python library for deep structural comparison. Supports arbitrary nested dicts/lists (exactly what FRZ `freeze.yaml` produces). Can detect value changes, type changes, and structural additions/removals — directly usable for "semantic drift detection" between FRZ versions. |
| **ruamel.yaml** | 0.19.1 | Round-trip YAML parsing (comment preservation) | When updating FRZ/SRC YAML files during semantic extraction, ruamel.yaml preserves comments and formatting that PyYAML strips. Critical for maintaining human-readable SSOT artifacts. Use selectively — only for files that need comment preservation. |

### Task Pack Orchestration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Build on existing `execution_runner.py` + `loop` command** | — | Sequential Task Pack execution | The project already has ADR-018 (Execution Loop Job Runner) with `cli/lib/execution_runner.py` and `cli/commands/loop/command.py`. ADR-051 explicitly says "no complex DAG" and "sequential loop only". Adding a third-party orchestration framework violates the design intent. The existing infrastructure provides: job state machine, lease management, skill invocation, and evidence writing. Task Pack is just YAML input that feeds this existing loop. |
| **Standard library `graphlib.TopologicalSorter`** | Python 3.9+ | Linear dependency resolution for Task Pack `depends_on` | Built into Python stdlib. Handles the simple tree/linear dependency graph that ADR-051 specifies. No external dependency needed. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **rich** | 13.9+ | CLI output formatting for Task Pack status, MSC validation results | When displaying Pack execution progress, MSC validation failures, or change grading results in the CLI |
| **watchdog** | 4.0+ | File system monitoring for Patch auto-registration | When implementing the Phase 2 PreToolUse hook automation (currently MVP uses CLAUDE.md rules) |
| **hashlib** (stdlib) | — | Content hashing for FRZ fingerprinting | When computing FRZ content fingerprints for drift detection (SHA-256 of `freeze.yaml` canonical form) |
| **dataclasses** (stdlib) | — | Data models for FRZ, Task Pack, semantic extraction | Continue the existing pattern in `qa_schemas.py` and `patch_schema.py`. Upgrade to Pydantic v2 for runtime validation where needed. |

## Alternatives Considered

### FRZ Validation

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Validation engine | Pydantic v2 | Cerberus | Cerberus is unmaintained, less expressive type system, no async support |
| Validation engine | Pydantic v2 | pykwalify | pykwalify is being deprecated by major projects (Zephyr RTOS moved to jsonschema in 2025), outdated schema format |
| Validation engine | Pydantic v2 | StrictYAML | StrictYAML rejects JSON Schema compatibility — would isolate FRZ schemas from the broader ecosystem |

### Semantic Diff

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Structured diff | DeepDiff | jsondiff | jsondiff is JSON-only, DeepDiff handles any Python object (dict, list, set, custom types) |
| Structured diff | DeepDiff | yamldiff (lumicks) | yamldiff is archived/unmaintained, limited to simple key-value diffs |
| Structured diff | DeepDiff | Graphtage | Graphtage is heavier, designed for merge-style diffs; overkill for "did semantics change?" detection |

### Task Pack Orchestration

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Task orchestration | Existing `execution_runner.py` + `graphlib.TopologicalSorter` | Prefect | Requires a server component, adds infrastructure overhead. ADR-051 explicitly rejects complex orchestration |
| Task orchestration | Existing `execution_runner.py` + `graphlib.TopologicalSorter` | Luigi | Designed for batch data pipelines, not sequential task execution with human-in-the-loop |
| Task orchestration | Existing `execution_runner.py` + `graphlib.TopologicalSorter` | Airflow | Massive overkill — requires Airflow server, scheduler, web UI, database |
| Task orchestration | Existing `execution_runner.py` + `graphlib.TopologicalSorter` | Concurra | Focused on parallel/concurrent execution, but ADR-051 explicitly says "no concurrency, sequential only" |
| Task orchestration | Existing `execution_runner.py` + `graphlib.TopologicalSorter` | Daglite | Unproven, minimal community, existing `execution_runner.py` already solves the problem |

## Installation

```bash
# New dependencies for v2.0
pip install pydantic==2.13.0
pip install deepdiff==9.0.0
pip install ruamel.yaml==0.19.1
pip install rich>=13.9

# Already present (do not reinstall)
# pip install pyyaml  # already in use across 15+ files
# pip install jsonschema  # if not already present
```

## Integration Points with Existing Code

### 1. `cli/lib/qa_schemas.py` → Pydantic Migration Path

Current pattern (29 dataclasses with `@dataclass(frozen=True)`):
```python
@dataclass(frozen=True)
class SomeSchema:
    field: str
    items: list[str] = field(default_factory=list)
```

Upgrade path — wrap with Pydantic for validation:
```python
from pydantic import BaseModel, Field

class SomeSchema(BaseModel):
    field: str
    items: list[str] = Field(default_factory=list)
```

Keep the existing dataclass definitions as-is during v2.0 development. Create new Pydantic models in parallel under `cli/lib/v2_schemas.py` for FRZ, Task Pack, and semantic extraction schemas. Full migration can happen post-v2.0.

### 2. `cli/lib/patch_schema.py` → DeepDiff Integration

Current Patch schema uses dataclasses for `ChangeClass`, `PatchSource`, etc. DeepDiff integrates naturally:

```python
from deepdiff import DeepDiff
import yaml

# Compare two FRZ snapshots for semantic drift
with open("frz-v1/freeze.yaml") as f1, open("frz-v2/freeze.yaml") as f2:
    old = yaml.safe_load(f1)
    new = yaml.safe_load(f2)

diff = DeepDiff(old, new, ignore_order=True)
# diff contains: values_changed, dictionary_item_added, dictionary_item_removed
```

Use this for the "semantic drift detection" feature in ADR-050 §5.

### 3. `cli/lib/execution_runner.py` → Task Pack Loop

The existing `run_job()` function already handles: job state transitions, skill invocation, attempt tracking, and evidence writing. Task Pack orchestration is a thin layer on top:

```
Task Pack YAML
  → parse tasks array
  → graphlib.TopologicalSorter for dependency ordering
  → for each ready task: call existing run_job()
  → on test-* task: trigger ADR-047 chain validation
  → on failure: stop loop, mark FAILED, wait for human
```

New module: `cli/lib/task_pack_runner.py` — wraps the existing runner with Task Pack logic. No changes to `execution_runner.py` core.

### 4. `cli/lib/managed_gateway.py` → MSC Gate

The managed gateway system can be extended to include FRZ MSC validation as a gate check. Current gate infrastructure already supports structured validation — add an MSC validator that checks all 5 dimensions before allowing FRZ to enter `frozen` state.

### 5. `cli/lib/formalization_materialize.py` → Semantic Extraction

This module already handles YAML formalization. Extend it with semantic extraction logic: FRZ `freeze.yaml` → SRC projection, using Pydantic models to validate the output conforms to projection invariance rules (ADR-045 §2.4).

## What NOT to Add

| Technology | Why Avoid |
|------------|-----------|
| **Airflow / Prefect / Dagster** | ADR-051 explicitly rejects complex orchestration. Sequential loop + `graphlib` is sufficient |
| **SQLAlchemy / ORM** | The project uses flat YAML files. An ORM would add complexity without benefit |
| **FastAPI / web framework** | This is a CLI-first tool. No HTTP API needed for v2.0 |
| **Celery / RabbitMQ** | No async task queue needed — sequential execution is the design |
| **LangChain / LLM frameworks** | Semantic extraction is structural (YAML projection), not LLM-based |
| **Django / Flask** | No web interface in scope |
| **pytest-xdist** | ADR-051 says no concurrency. Test parallelism is not needed |

## Sources

- [Pydantic v2.13.0 — PyPI](https://pypi.org/project/pydantic/) (HIGH confidence — official PyPI, released 2026-04-13)
- [Pydantic Changelog](https://pydantic.dev/docs/validation/latest/get-started/changelog/) (HIGH confidence — official docs)
- [jsonschema 4.26.0 — PyPI](https://pypi.org/project/jsonschema/) (HIGH confidence — official PyPI, released 2026-01-07)
- [DeepDiff 9.0.0 — PyPI](https://pypi.org/project/deepdiff/) (HIGH confidence — official PyPI, released 2026-03-29)
- [ruamel.yaml 0.19.1 — PyPI](https://pypi.org/project/ruamel.yaml/) (HIGH confidence — official PyPI, released 2026-01-02)
- [Python graphlib.TopologicalSorter](https://docs.python.org/3/library/graphlib.html) (HIGH confidence — Python stdlib docs)
- [PyYAML — PyPI](https://pypi.org/project/PyYAML/) (HIGH confidence — already used in project)
