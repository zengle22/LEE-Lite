"""Task Pack schema validation module (PACK-01). Stub for Wave 0."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


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
    title: str
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


class TaskPackSchemaError(ValueError):
    pass


def validate(data: dict) -> TaskPack:
    raise NotImplementedError


def validate_file(path: str | Path) -> TaskPack:
    raise NotImplementedError
