"""Bug registry with state machine and YAML persistence.

Stub for TDD RED phase — all functions raise NotImplementedError.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


BUG_STATE_TRANSITIONS: dict[str, set[str]] = {}

NOT_REPRODUCIBLE_THRESHOLDS: dict[str, int] = {}


def _timestamp() -> str:
    raise NotImplementedError


def registry_path(workspace_root: Path, feat_ref: str) -> Path:
    raise NotImplementedError


def _load_registry(path: Path) -> dict[str, Any]:
    raise NotImplementedError


def _save_registry(path: Path, registry: dict[str, Any]) -> None:
    raise NotImplementedError


def _empty_registry() -> dict[str, Any]:
    raise NotImplementedError


def load_or_create_registry(workspace_root: Path, feat_ref: str, proto_ref: str | None = None) -> dict[str, Any]:
    raise NotImplementedError


def _build_bug_record(case_id: str, run_id: str, case_result: dict[str, Any], feat_ref: str | None, proto_ref: str | None) -> dict[str, Any]:
    raise NotImplementedError


def _infer_gap_type(case_result: dict[str, Any]) -> str:
    raise NotImplementedError


def transition_bug_status(bug: dict[str, Any], new_status: str, *, reason: str | None = None, actor: str = "system", **extra_fields: Any) -> dict[str, Any]:
    raise NotImplementedError


def check_not_reproducible(bug: dict[str, Any], consecutive_nonappearances: int, test_level: str = "integration") -> bool:
    raise NotImplementedError


def sync_bugs_to_registry(workspace_root: Path, feat_ref: str | None, proto_ref: str | None, run_id: str, case_results: list[dict[str, Any]]) -> None:
    raise NotImplementedError
