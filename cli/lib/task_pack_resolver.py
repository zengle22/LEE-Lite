"""Task Pack dependency resolution via topological sort.

Truth source: ADR-051 §2.3 (sequential execution loop) + §2.4 (execution rules).
Uses Python stdlib graphlib.TopologicalSorter for DAG resolution.
"""

from __future__ import annotations

import sys
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from typing import Any

import yaml

from cli.lib.task_pack_schema import TaskPackSchemaError, validate


class TaskPackResolverError(ValueError):
    """Raised when dependency resolution fails (circular deps, missing refs)."""


def resolve_order(pack_yaml: dict[str, Any]) -> list[str]:
    """Resolve tasks into a valid execution order via topological sort.

    Args:
        pack_yaml: Parsed task_pack YAML dict (with or without 'task_pack' wrapper).

    Returns:
        List of task_ids in executable order.

    Raises:
        TaskPackResolverError: If circular dependencies or missing references exist.
    """
    # Extract tasks list: handle both wrapped and unwrapped formats
    if "task_pack" in pack_yaml:
        tasks = pack_yaml["task_pack"].get("tasks", [])
    else:
        tasks = pack_yaml.get("tasks", [])

    # Collect all task_ids
    task_ids: set[str] = {t["task_id"] for t in tasks}

    # Validate all depends_on references exist BEFORE building the graph
    for t in tasks:
        for dep in (t.get("depends_on") or []):
            if dep not in task_ids:
                raise TaskPackResolverError(
                    f"Task '{t['task_id']}' depends on unknown task '{dep}'"
                )

    # Build graph: node -> set of prerequisites
    graph = {t["task_id"]: set(t.get("depends_on") or []) for t in tasks}

    try:
        ts = TopologicalSorter(graph)
        return list(ts.static_order())
    except CycleError as e:
        raise TaskPackResolverError(f"Circular dependency detected: {e}") from e


def resolve_file(path: str | Path) -> list[str]:
    """Load a YAML file and resolve its task execution order.

    Args:
        path: Path to the Task Pack YAML file.

    Returns:
        List of task_ids in executable order.

    Raises:
        TaskPackResolverError: If dependency resolution fails.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Task Pack file not found: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return resolve_order(data)


def main() -> None:
    """Resolve dependency order for one or more Task Pack YAML files.

    Usage: python -m cli.lib.task_pack_resolver <file.yaml> [...]
    """
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.task_pack_resolver <file.yaml> ...")
        sys.exit(1)

    exit_code = 0
    for f in args:
        try:
            order = resolve_file(f)
            print(f"OK: {f}")
            for i, tid in enumerate(order, 1):
                print(f"  {i}. {tid}")
        except (TaskPackResolverError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
