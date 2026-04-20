"""Task Pack schema validation — dataclass definitions + YAML validators.

Truth source: ADR-051 §2.1 (Task Pack structure) + §2.2 (Task types) + §2.5 (Task states).
Task Pack YAML files must conform to the schema defined in ssot/schemas/qa/task_pack.yaml.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Lifecycle states for a task (ADR-051 §2.5)."""

    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"
    still_failed = "still_failed"
    skipped = "skipped"
    blocked = "blocked"


class TaskType(str, Enum):
    """Task type enumeration (ADR-051 §2.2)."""

    impl = "impl"
    test_api = "test-api"
    test_e2e = "test-e2e"
    review = "review"
    doc = "doc"
    gate = "gate"


# ---------------------------------------------------------------------------
# ID format patterns
# ---------------------------------------------------------------------------

PACK_ID_PATTERN = re.compile(r"^PACK-")
TASK_ID_PATTERN = re.compile(r"^TASK-\d{3,}$")


# ---------------------------------------------------------------------------
# TaskPack frozen dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Task:
    """Single task within a Task Pack."""

    task_id: str
    type: TaskType
    title: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.pending
    verifies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TaskPack:
    """Task Pack containing an ordered list of tasks."""

    artifact_type: str = "task_pack"
    pack_id: str | None = None
    feat_ref: str | None = None
    created_at: str | None = None
    tasks: list[Task] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Error class
# ---------------------------------------------------------------------------


class TaskPackSchemaError(ValueError):
    """Raised when a Task Pack YAML does not conform to its schema."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_TASK_PACK_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise TaskPackSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise TaskPackSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


def _parse_task_dict(data: dict) -> Task:
    """Convert a raw YAML task dict to a Task instance."""
    task_id = data.get("task_id")
    if task_id is None:
        raise TaskPackSchemaError("Task: required field 'task_id' is missing")
    if not TASK_ID_PATTERN.match(task_id):
        raise TaskPackSchemaError(f"Invalid task_id format: {task_id}")

    type_raw = data.get("type", "")
    if isinstance(type_raw, str):
        try:
            task_type = TaskType(type_raw)
        except ValueError:
            raise TaskPackSchemaError(
                f"Task '{task_id}': type must be one of {[e.value for e in TaskType]}, got '{type_raw}'"
            )
    elif isinstance(type_raw, TaskType):
        task_type = type_raw
    else:
        raise TaskPackSchemaError(f"Task '{task_id}': invalid type value")

    title = data.get("title", "")
    if not title:
        raise TaskPackSchemaError(f"Task '{task_id}': required field 'title' is missing or empty")

    status_raw = data.get("status", "pending")
    if isinstance(status_raw, str):
        try:
            status = TaskStatus(status_raw)
        except ValueError:
            raise TaskPackSchemaError(
                f"Task '{task_id}': status must be one of {[e.value for e in TaskStatus]}, got '{status_raw}'"
            )
    elif isinstance(status_raw, TaskStatus):
        status = status_raw
    else:
        raise TaskPackSchemaError(f"Task '{task_id}': invalid status type")

    depends_on = data.get("depends_on") or []
    verifies = data.get("verifies") or []

    # Coerce single string to list for verifies
    if isinstance(verifies, str):
        verifies = [verifies]

    return Task(
        task_id=task_id,
        type=task_type,
        title=title,
        depends_on=depends_on,
        status=status,
        verifies=verifies,
    )


def _parse_task_pack_dict(data: dict) -> TaskPack:
    """Convert a raw YAML dict to a TaskPack instance.

    Validates ID formats for pack_id and all task_ids.
    """
    # Validate pack_id format if present
    pack_id = data.get("pack_id")
    if pack_id is not None and not PACK_ID_PATTERN.match(pack_id):
        raise TaskPackSchemaError(f"Invalid pack_id format: {pack_id}")

    # Parse tasks
    tasks: list[Task] = []
    for item in data.get("tasks") or []:
        if isinstance(item, dict):
            tasks.append(_parse_task_dict(item))
        elif isinstance(item, Task):
            tasks.append(item)

    return TaskPack(
        artifact_type=data.get("artifact_type", "task_pack"),
        pack_id=pack_id,
        feat_ref=data.get("feat_ref"),
        created_at=data.get("created_at"),
        tasks=tasks,
    )


# ---------------------------------------------------------------------------
# YAML loading helper
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# validate() — dict-level validation
# ---------------------------------------------------------------------------


def validate(data: dict) -> TaskPack:
    """Validate a raw Task Pack YAML dict and return a TaskPack instance.

    Enforces:
    - Required fields: pack_id, feat_ref, created_at, tasks
    - tasks must be a non-empty list
    - All task_ids must be unique within the pack
    - Each task has required fields: task_id, type, title, status
    - type and status must be valid enum values
    - depends_on refs must reference existing task_ids in the same pack
    - pack_id and task_id must match expected formats

    Args:
        data: Raw dict from YAML parsing (may or may not have 'task_pack' wrapper).

    Returns:
        Validated TaskPack instance.

    Raises:
        TaskPackSchemaError: If validation fails.
    """
    # Extract task_pack key if present, else use data directly
    if "task_pack" in data:
        inner = data["task_pack"]
    else:
        inner = data

    label = inner.get("pack_id", "task_pack")

    # Required top-level fields
    _require(inner, "pack_id", label)
    _require(inner, "feat_ref", label)
    _require(inner, "created_at", label)
    _require(inner, "tasks", label)

    tasks_raw = inner["tasks"]
    if not isinstance(tasks_raw, list) or len(tasks_raw) == 0:
        raise TaskPackSchemaError(f"{label}: 'tasks' must be a non-empty list")

    # Collect all task_ids for uniqueness and orphan checks
    task_ids: list[str] = []
    for i, t in enumerate(tasks_raw):
        if not isinstance(t, dict):
            raise TaskPackSchemaError(f"{label}.tasks[{i}]: must be a mapping")
        tid = t.get("task_id")
        if tid is None:
            raise TaskPackSchemaError(f"{label}.tasks[{i}]: required field 'task_id' is missing")
        task_ids.append(tid)

    # Check duplicate task_ids
    seen: set[str] = set()
    for tid in task_ids:
        if tid in seen:
            raise TaskPackSchemaError(f"{label}: duplicate task_id '{tid}'")
        seen.add(tid)

    # Validate each task has required fields and valid enum values
    task_id_set = set(task_ids)
    for i, t in enumerate(tasks_raw):
        t_label = f"{label}.tasks[{i}]"
        tid = t.get("task_id", f"tasks[{i}]")

        # Required fields
        _require(t, "task_id", t_label)
        _require(t, "type", t_label)
        _require(t, "title", t_label)

        # Enum checks
        _enum_check(t["type"], TaskType, t_label, "type")

        if "status" in t and t["status"] is not None:
            _enum_check(t["status"], TaskStatus, t_label, "status")

        # Orphan depends_on check
        deps = t.get("depends_on") or []
        for dep in deps:
            if dep not in task_id_set:
                raise TaskPackSchemaError(
                    f"{t_label}: task '{tid}' depends on unknown task '{dep}'"
                )

    return _parse_task_pack_dict(inner)


# ---------------------------------------------------------------------------
# File-level validation entry point
# ---------------------------------------------------------------------------

_VALIDATORS = {"task_pack": ("task_pack", _parse_task_pack_dict)}


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


def validate_file(path: str | Path, schema_type: str | None = None) -> TaskPack:
    """Load a YAML file and validate it as a Task Pack.

    Args:
        path: Path to the YAML file.
        schema_type: 'task_pack' or None for auto-detect.

    Returns:
        The validated TaskPack instance.

    Raises:
        TaskPackSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Task Pack file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            raise TaskPackSchemaError(
                f"Cannot detect Task Pack schema from {p}. "
                f"Expected top-level key: task_pack"
            )

    if schema_type != "task_pack":
        raise TaskPackSchemaError(
            f"Unknown schema type '{schema_type}'. Must be 'task_pack'."
        )

    top_key, parser_fn = _VALIDATORS[schema_type]

    if top_key not in data:
        raise TaskPackSchemaError(
            f"Expected top-level key '{top_key}' in {p}. "
            f"File may not be a valid Task Pack."
        )

    return validate(data)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Validate one or more Task Pack YAML files from the command line.

    Usage:
        python -m cli.lib.task_pack_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.task_pack_schema --type task_pack <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.task_pack_schema [--type <type>] <file.yaml> ...")
        sys.exit(1)

    schema_type: str | None = None
    files: list[str] = []

    i = 0
    while i < len(args):
        if args[i] == "--type":
            i += 1
            if i >= len(args):
                print("Error: --type requires a value")
                sys.exit(1)
            schema_type = args[i]
        else:
            files.append(args[i])
        i += 1

    if not files:
        print("Error: no files specified")
        sys.exit(1)

    exit_code = 0
    for f in files:
        try:
            result = validate_file(f, schema_type)
            print(f"  OK: {f} — pack_id={result.pack_id}, {len(result.tasks)} tasks")
        except (TaskPackSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
