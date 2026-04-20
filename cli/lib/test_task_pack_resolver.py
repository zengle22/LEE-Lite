"""Unit tests for Task Pack dependency resolution (PACK-02)."""
import pytest
import yaml
import tempfile
from pathlib import Path

from cli.lib.task_pack_resolver import (
    resolve_order,
    resolve_file,
    TaskPackResolverError,
)


# ---------------------------------------------------------------------------
# Core resolution tests
# ---------------------------------------------------------------------------


def test_linear_chain():
    """A -> B -> C: sequential dependency chain."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A"},
            {"task_id": "TASK-002", "type": "test-api", "title": "B", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "type": "review", "title": "C", "depends_on": ["TASK-002"]},
        ]
    }
    order = resolve_order(pack)
    assert order.index("TASK-001") < order.index("TASK-002") < order.index("TASK-003")


def test_cycle_detection():
    """A -> B -> A: circular dependency raises error."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-002"]},
            {"task_id": "TASK-002", "type": "impl", "title": "B", "depends_on": ["TASK-001"]},
        ]
    }
    with pytest.raises(TaskPackResolverError, match="[Cc]ircular"):
        resolve_order(pack)


def test_diamond_dependency():
    """A -> B, A -> C, B -> D, C -> D: diamond resolves correctly."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A"},
            {"task_id": "TASK-002", "type": "impl", "title": "B", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "type": "impl", "title": "C", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-004", "type": "review", "title": "D", "depends_on": ["TASK-002", "TASK-003"]},
        ]
    }
    order = resolve_order(pack)
    assert order.index("TASK-001") < order.index("TASK-002")
    assert order.index("TASK-001") < order.index("TASK-003")
    assert order.index("TASK-002") < order.index("TASK-004")
    assert order.index("TASK-003") < order.index("TASK-004")
    assert len(order) == 4


def test_orphan_depends_on_raises():
    """Task depends on nonexistent task_id raises TaskPackResolverError."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-999"]},
        ]
    }
    with pytest.raises(TaskPackResolverError, match="unknown task"):
        resolve_order(pack)


def test_no_deps_returns_as_is():
    """Tasks with no depends_on return in some valid order (all tasks present)."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A"},
            {"task_id": "TASK-002", "type": "impl", "title": "B"},
            {"task_id": "TASK-003", "type": "impl", "title": "C"},
        ]
    }
    order = resolve_order(pack)
    assert set(order) == {"TASK-001", "TASK-002", "TASK-003"}
    assert len(order) == 3


def test_resolve_file():
    """Write YAML to temp file, call resolve_file, returns list of task_ids."""
    pack = {
        "task_pack": {
            "pack_id": "PACK-TEST-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A"},
                {"task_id": "TASK-002", "type": "test-api", "title": "B", "depends_on": ["TASK-001"]},
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(pack, f)
        f.flush()
        order = resolve_file(f.name)
        assert isinstance(order, list)
        assert order.index("TASK-001") < order.index("TASK-002")


def test_single_task():
    """Pack with one task returns [task_id]."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "Solo"},
        ]
    }
    order = resolve_order(pack)
    assert order == ["TASK-001"]


def test_resolve_file_not_found():
    """resolve_file on nonexistent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        resolve_file("nonexistent_pack.yaml")


def test_wrapped_format():
    """YAML with 'task_pack' wrapper resolves correctly."""
    pack = {
        "task_pack": {
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A"},
                {"task_id": "TASK-002", "type": "test-api", "title": "B", "depends_on": ["TASK-001"]},
            ]
        }
    }
    order = resolve_order(pack)
    assert order.index("TASK-001") < order.index("TASK-002")


def test_depends_on_none_handled():
    """Task with depends_on: None (YAML quirk) handled gracefully."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": None},
            {"task_id": "TASK-002", "type": "test-api", "title": "B", "depends_on": ["TASK-001"]},
        ]
    }
    order = resolve_order(pack)
    assert order.index("TASK-001") < order.index("TASK-002")


def test_three_way_cycle():
    """A -> B -> C -> A: three-way cycle detected."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-003"]},
            {"task_id": "TASK-002", "type": "impl", "title": "B", "depends_on": ["TASK-001"]},
            {"task_id": "TASK-003", "type": "impl", "title": "C", "depends_on": ["TASK-002"]},
        ]
    }
    with pytest.raises(TaskPackResolverError, match="[Cc]ircular"):
        resolve_order(pack)


def test_self_dependency():
    """Task depending on itself raises error."""
    pack = {
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-001"]},
        ]
    }
    with pytest.raises(TaskPackResolverError, match="[Cc]ircular"):
        resolve_order(pack)


# ---------------------------------------------------------------------------
# Sample pack E2E test
# ---------------------------------------------------------------------------


def test_sample_pack_e2e():
    """Load the sample Task Pack file, validate schema, resolve order."""
    from cli.lib.task_pack_schema import validate_file as schema_validate

    sample_path = Path(__file__).parent.parent.parent / "ssot" / "tasks" / "PACK-SRC-001-001-feat001.yaml"
    assert sample_path.exists(), f"Sample pack not found at {sample_path}"

    # Schema validation
    pack = schema_validate(sample_path)
    assert pack.pack_id == "PACK-SRC-001-001-feat001"
    assert len(pack.tasks) == 4

    # Dependency resolution
    order = resolve_file(sample_path)
    assert len(order) == 4
    assert order.index("TASK-001") == 0  # impl first
    assert order.index("TASK-002") > order.index("TASK-001")  # test-api after impl
    assert order.index("TASK-003") > order.index("TASK-001")  # test-e2e after impl
    assert order.index("TASK-004") > order.index("TASK-002")  # review after test-api
    assert order.index("TASK-004") > order.index("TASK-003")  # review after test-e2e
