"""Unit tests for Task Pack schema validation (PACK-01)."""
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
    _parse_task_dict,
)


# ---------------------------------------------------------------------------
# Dataclass construction tests
# ---------------------------------------------------------------------------


def test_task_defaults():
    """Task created without optional fields has empty defaults."""
    t = Task(task_id="TASK-001", type=TaskType.impl, title="Do it")
    assert t.depends_on == []
    assert t.verifies == []
    assert t.status == TaskStatus.pending


def test_task_pack_minimal():
    """TaskPack with minimal valid data."""
    pkg = TaskPack(
        pack_id="PACK-SRC-001-001-feat001",
        feat_ref="FEAT-SRC-001-001",
        tasks=[
            Task(task_id="TASK-001", type=TaskType.impl, title="Implement API"),
        ],
    )
    assert pkg.artifact_type == "task_pack"
    assert len(pkg.tasks) == 1
    assert pkg.tasks[0].status == TaskStatus.pending


def test_task_pack_frozen():
    """TaskPack must be immutable."""
    pkg = TaskPack()
    with pytest.raises(Exception):  # FrozenInstanceError
        pkg.pack_id = "new-id"  # type: ignore[misc]


def test_task_frozen():
    """Task must be immutable."""
    t = Task(task_id="TASK-001", type=TaskType.impl, title="Test")
    with pytest.raises(Exception):  # FrozenInstanceError
        t.task_id = "TASK-002"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


def test_task_type_enum_values():
    """TaskType enum contains all required values."""
    assert TaskType.impl.value == "impl"
    assert TaskType.test_api.value == "test-api"
    assert TaskType.test_e2e.value == "test-e2e"
    assert TaskType.review.value == "review"
    assert TaskType.doc.value == "doc"
    assert TaskType.gate.value == "gate"


def test_task_status_enum_values():
    """TaskStatus enum contains all required values."""
    assert TaskStatus.pending.value == "pending"
    assert TaskStatus.running.value == "running"
    assert TaskStatus.passed.value == "passed"
    assert TaskStatus.failed.value == "failed"
    assert TaskStatus.still_failed.value == "still_failed"
    assert TaskStatus.skipped.value == "skipped"
    assert TaskStatus.blocked.value == "blocked"


def test_task_schema_error_is_value_error():
    """TaskPackSchemaError is a subclass of ValueError."""
    assert issubclass(TaskPackSchemaError, ValueError)
    with pytest.raises(TaskPackSchemaError):
        raise TaskPackSchemaError("test error")


# ---------------------------------------------------------------------------
# validate() — accept valid packs
# ---------------------------------------------------------------------------


def test_valid_pack():
    """Valid Task Pack dict passes validation."""
    result = validate({
        "pack_id": "PACK-SRC-001-001-feat001",
        "feat_ref": "FEAT-SRC-001-001",
        "created_at": "2026-04-20T00:00:00+08:00",
        "tasks": [
            {"task_id": "TASK-001", "type": "impl", "title": "Implement API", "depends_on": [], "status": "pending", "verifies": []},
        ]
    })
    assert isinstance(result, TaskPack)
    assert result.pack_id == "PACK-SRC-001-001-feat001"
    assert len(result.tasks) == 1
    assert result.tasks[0].task_id == "TASK-001"
    assert result.tasks[0].status == TaskStatus.pending


def test_task_pack_with_top_level_key():
    """validate dict with 'task_pack': {...} wrapper works."""
    result = validate({
        "task_pack": {
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "Do it"},
            ]
        }
    })
    assert isinstance(result, TaskPack)
    assert result.pack_id == "PACK-001"


# ---------------------------------------------------------------------------
# validate() — reject invalid packs
# ---------------------------------------------------------------------------


def test_rejects_missing_task_id():
    """Task Pack with missing task_id in a task raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"type": "impl", "title": "No ID here"},
            ]
        })


def test_rejects_missing_required_fields():
    """Task Pack with missing required top-level fields raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({"tasks": [{"task_id": "TASK-001", "type": "impl", "title": "A"}]})


def test_rejects_invalid_task_type():
    """Task Pack with unknown task type raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "bogus", "title": "Bad type"},
            ]
        })


def test_rejects_orphan_depends_on():
    """Task Pack with depends_on referencing nonexistent task_id raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A", "depends_on": ["TASK-999"]},
            ]
        })


def test_duplicate_task_ids_rejected():
    """Two tasks with same task_id raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A"},
                {"task_id": "TASK-001", "type": "test-api", "title": "B"},
            ]
        })


def test_rejects_empty_tasks():
    """Empty tasks list raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [],
        })


def test_rejects_invalid_task_id_format():
    """Task with non-conforming task_id raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "PACK-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "bad-id", "type": "impl", "title": "A"},
            ]
        })


def test_rejects_invalid_pack_id_format():
    """Pack with non-conforming pack_id raises TaskPackSchemaError."""
    with pytest.raises(TaskPackSchemaError):
        validate({
            "pack_id": "bad-pack-id",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "A"},
            ]
        })


# ---------------------------------------------------------------------------
# validate_file() tests
# ---------------------------------------------------------------------------


def test_validate_file_with_yaml():
    """Write a valid YAML to a temp file, call validate_file, assert returns TaskPack."""
    valid_pack = {
        "task_pack": {
            "pack_id": "PACK-TEST-001",
            "feat_ref": "FEAT-001",
            "created_at": "2026-04-20T00:00:00+08:00",
            "tasks": [
                {"task_id": "TASK-001", "type": "impl", "title": "Test task"},
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(valid_pack, f)
        f.flush()
        result = validate_file(f.name)
        assert isinstance(result, TaskPack)
        assert result.pack_id == "PACK-TEST-001"


def test_validate_file_not_found():
    """Call validate_file('nonexistent.yaml') raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_file("nonexistent.yaml")


# ---------------------------------------------------------------------------
# _parse_task_pack_dict tests
# ---------------------------------------------------------------------------


def test_parse_task_pack_dict_minimal():
    """Minimal dict → TaskPack with defaults."""
    pkg = _parse_task_pack_dict({"pack_id": "PACK-001"})
    assert pkg.pack_id == "PACK-001"
    assert pkg.artifact_type == "task_pack"
    assert pkg.tasks == []


def test_parse_task_dict_defaults():
    """Task dict with only required fields → Task with default status/depends_on/verifies."""
    t = _parse_task_dict({"task_id": "TASK-001", "type": "impl", "title": "Do it"})
    assert t.task_id == "TASK-001"
    assert t.type == TaskType.impl
    assert t.status == TaskStatus.pending
    assert t.depends_on == []
    assert t.verifies == []


def test_parse_task_dict_full():
    """Complete task dict → fully typed Task."""
    t = _parse_task_dict({
        "task_id": "TASK-001",
        "type": "test-api",
        "title": "Test API",
        "depends_on": ["TASK-000"],
        "status": "passed",
        "verifies": ["AC-001", "AC-002"],
    })
    assert t.task_id == "TASK-001"
    assert t.type == TaskType.test_api
    assert t.status == TaskStatus.passed
    assert t.depends_on == ["TASK-000"]
    assert t.verifies == ["AC-001", "AC-002"]


def test_parse_task_dict_verifies_single_string():
    """Single string verifies coerced to list."""
    t = _parse_task_dict({
        "task_id": "TASK-001",
        "type": "impl",
        "title": "Test",
        "verifies": "AC-001",
    })
    assert t.verifies == ["AC-001"]


def test_parse_task_dict_depends_on_none():
    """None depends_on coerced to empty list."""
    t = _parse_task_dict({
        "task_id": "TASK-001",
        "type": "impl",
        "title": "Test",
        "depends_on": None,
    })
    assert t.depends_on == []
