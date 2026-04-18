"""Unit tests for cli.lib.anchor_registry."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from cli.lib.anchor_registry import (
    ANCHOR_ID_PATTERN,
    VALID_PROJECTION_PATHS,
    AnchorEntry,
    AnchorRegistry,
)
from cli.lib.errors import CommandError


@pytest.fixture
def tmp_workspace() -> Path:
    """Create a temporary workspace directory."""
    return Path(tempfile.mkdtemp())


@pytest.fixture
def registry(tmp_workspace: Path) -> AnchorRegistry:
    return AnchorRegistry(tmp_workspace)


# --- register ---


def test_register_anchor_success(registry: AnchorRegistry) -> None:
    entry = registry.register("JRN-001", "FRZ-001", "SRC")
    assert entry.anchor_id == "JRN-001"
    assert entry.frz_ref == "FRZ-001"
    assert entry.projection_path == "SRC"
    assert entry.registered_at is not None
    assert entry.metadata == {}


def test_register_anchor_duplicate_raises(registry: AnchorRegistry) -> None:
    registry.register("ENT-001", "FRZ-001", "EPIC")
    # Same anchor_id + same projection_path should fail
    with pytest.raises(CommandError) as exc_info:
        registry.register("ENT-001", "FRZ-002", "EPIC")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "already registered" in exc_info.value.message


def test_register_same_anchor_id_different_projection_succeeds(registry: AnchorRegistry) -> None:
    """Same anchor_id with different projection_path should be allowed."""
    entry1 = registry.register("JRN-001", "FRZ-001", "SRC")
    assert entry1.anchor_id == "JRN-001"
    assert entry1.projection_path == "SRC"

    entry2 = registry.register("JRN-001", "FRZ-001", "EPIC")
    assert entry2.anchor_id == "JRN-001"
    assert entry2.projection_path == "EPIC"

    entry3 = registry.register("JRN-001", "FRZ-001", "FEAT")
    assert entry3.anchor_id == "JRN-001"
    assert entry3.projection_path == "FEAT"


def test_register_anchor_invalid_format(registry: AnchorRegistry) -> None:
    with pytest.raises(CommandError) as exc_info:
        registry.register("jrn-1", "FRZ-001", "SRC")
    assert exc_info.value.status_code == "INVALID_REQUEST"

    with pytest.raises(CommandError):
        registry.register("bad_format", "FRZ-001", "SRC")


def test_register_anchor_invalid_projection_path(registry: AnchorRegistry) -> None:
    with pytest.raises(CommandError) as exc_info:
        registry.register("JRN-002", "FRZ-001", "INVALID")
    assert exc_info.value.status_code == "INVALID_REQUEST"


def test_register_with_metadata(registry: AnchorRegistry) -> None:
    entry = registry.register(
        "SM-001", "FRZ-002", "FEAT", metadata={"journey_name": "Test"}
    )
    assert entry.metadata == {"journey_name": "Test"}


# --- resolve ---


def test_resolve_existing_anchor(registry: AnchorRegistry) -> None:
    registry.register("ENT-010", "FRZ-003", "EPIC")
    result = registry.resolve("ENT-010")
    # Without projection_path, returns a list
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].anchor_id == "ENT-010"
    assert result[0].frz_ref == "FRZ-003"


def test_resolve_nonexistent_anchor(registry: AnchorRegistry) -> None:
    result = registry.resolve("NONEXIST-001")
    assert result is None


# --- list_by_frz ---


def test_list_by_frz(registry: AnchorRegistry) -> None:
    registry.register("JRN-001", "FRZ-010", "SRC")
    registry.register("JRN-002", "FRZ-010", "EPIC")
    registry.register("JRN-003", "FRZ-010", "FEAT")
    registry.register("ENT-001", "FRZ-020", "SRC")
    registry.register("ENT-002", "FRZ-020", "EPIC")

    results = registry.list_by_frz("FRZ-010")
    assert len(results) == 3
    ids = {e.anchor_id for e in results}
    assert ids == {"JRN-001", "JRN-002", "JRN-003"}


def test_list_by_frz_same_anchor_different_paths(registry: AnchorRegistry) -> None:
    """list_by_frz may return multiple entries for same anchor_id with different paths."""
    registry.register("JRN-001", "FRZ-010", "SRC")
    registry.register("JRN-001", "FRZ-010", "EPIC")

    results = registry.list_by_frz("FRZ-010")
    assert len(results) == 2
    paths = {e.projection_path for e in results}
    assert paths == {"SRC", "EPIC"}


# --- list_all ---


def test_list_all(registry: AnchorRegistry) -> None:
    registry.register("JRN-001", "FRZ-001", "SRC")
    registry.register("ENT-001", "FRZ-001", "EPIC")
    assert len(registry.list_all()) == 2


# --- count ---


def test_count(registry: AnchorRegistry) -> None:
    assert registry.count() == 0
    registry.register("JRN-001", "FRZ-001", "SRC")
    registry.register("ENT-001", "FRZ-001", "EPIC")
    registry.register("SM-001", "FRZ-001", "FEAT")
    assert registry.count() == 3


# --- frozen dataclass ---


def test_anchor_entry_is_frozen() -> None:
    entry = AnchorEntry(
        anchor_id="JRN-001",
        frz_ref="FRZ-001",
        projection_path="SRC",
    )
    with pytest.raises(Exception):  # FrozenInstanceError (dataclasses)
        entry.anchor_id = "JRN-999"  # type: ignore[misc]


# --- persistence across instances ---


def test_persistence_across_instances(tmp_workspace: Path) -> None:
    reg1 = AnchorRegistry(tmp_workspace)
    reg1.register("JRN-050", "FRZ-005", "SRC", metadata={"key": "val"})

    reg2 = AnchorRegistry(tmp_workspace)
    result = reg2.resolve("JRN-050")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].anchor_id == "JRN-050"
    assert result[0].metadata == {"key": "val"}


# --- anchor ID edge cases ---


def test_anchor_id_edge_cases(registry: AnchorRegistry) -> None:
    """Shortest prefix (2 chars) and longest prefix (5 chars) with large numbers."""
    entry1 = registry.register("AB-100", "FRZ-001", "SRC")
    assert entry1.anchor_id == "AB-100"

    entry2 = registry.register("ABCDE-999999", "FRZ-001", "EPIC")
    assert entry2.anchor_id == "ABCDE-999999"


# --- YAML file structure ---


def test_anchor_registry_yaml_file_structure(registry: AnchorRegistry) -> None:
    """Register anchor, read YAML directly, verify top-level key."""
    registry.register("JRN-001", "FRZ-001", "SRC")
    text = registry.registry_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert "anchor_registry" in data
    assert isinstance(data["anchor_registry"], list)
    assert len(data["anchor_registry"]) == 1
    assert data["anchor_registry"][0]["anchor_id"] == "JRN-001"


# --- corrupted YAML handling ---


def test_anchor_registry_corrupted_yaml(tmp_workspace: Path) -> None:
    """Write random text to anchor registry YAML, _load should return empty list."""
    registry = AnchorRegistry(tmp_workspace)
    registry.registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry.registry_path.write_text("this is not valid yaml {{{", encoding="utf-8")
    # yaml.safe_load parses this as a plain string, not a crash
    # _load defensively returns empty list for non-dict data
    result = registry._load()
    assert result == []


# --- VALID_PROJECTION_PATHS extended ---


def test_valid_projection_paths_includes_all_layers() -> None:
    """VALID_PROJECTION_PATHS should include SRC, EPIC, FEAT, TECH, UI, TEST, IMPL."""
    assert VALID_PROJECTION_PATHS == {
        "SRC", "EPIC", "FEAT", "TECH", "UI", "TEST", "IMPL"
    }


# --- register_projection ---


def test_register_projection_new_anchor(registry: AnchorRegistry) -> None:
    """register_projection with anchor_id not yet registered creates new entry."""
    entry = registry.register_projection("JRN-001", "FRZ-001", "SRC")
    assert entry.anchor_id == "JRN-001"
    assert entry.projection_path == "SRC"
    assert entry.registered_at is not None


def test_register_projection_same_anchor_different_path(registry: AnchorRegistry) -> None:
    """register_projection with same anchor_id + different projection_path succeeds."""
    registry.register_projection("ENT-001", "FRZ-001", "SRC")
    entry = registry.register_projection("ENT-001", "FRZ-001", "EPIC")
    assert entry.anchor_id == "ENT-001"
    assert entry.projection_path == "EPIC"


def test_register_projection_same_anchor_same_path_fails(registry: AnchorRegistry) -> None:
    """register_projection with same anchor_id + same projection_path fails."""
    registry.register_projection("SM-001", "FRZ-001", "SRC")
    with pytest.raises(CommandError) as exc_info:
        registry.register_projection("SM-001", "FRZ-001", "SRC")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "already registered" in exc_info.value.message


def test_register_projection_invalid_path(registry: AnchorRegistry) -> None:
    """register_projection with invalid projection_path fails."""
    with pytest.raises(CommandError) as exc_info:
        registry.register_projection("JRN-001", "FRZ-001", "INVALID_PATH")
    assert exc_info.value.status_code == "INVALID_REQUEST"


# --- resolve with projection_path ---


def test_resolve_with_projection_path(registry: AnchorRegistry) -> None:
    """resolve(anchor_id, projection_path='SRC') returns specific entry."""
    registry.register("JRN-001", "FRZ-001", "SRC")
    registry.register("JRN-001", "FRZ-001", "EPIC")

    result = registry.resolve("JRN-001", projection_path="SRC")
    assert result is not None
    assert result.anchor_id == "JRN-001"
    assert result.projection_path == "SRC"

    result_epic = registry.resolve("JRN-001", projection_path="EPIC")
    assert result_epic is not None
    assert result_epic.projection_path == "EPIC"


def test_resolve_without_projection_path_returns_list(registry: AnchorRegistry) -> None:
    """resolve(anchor_id) without projection_path returns list of all entries."""
    registry.register("JRN-001", "FRZ-001", "SRC")
    registry.register("JRN-001", "FRZ-001", "EPIC")
    registry.register("JRN-001", "FRZ-001", "FEAT")

    result = registry.resolve("JRN-001")
    assert isinstance(result, list)
    assert len(result) == 3
    paths = {e.projection_path for e in result}
    assert paths == {"SRC", "EPIC", "FEAT"}


def test_resolve_nonexistent_returns_none(registry: AnchorRegistry) -> None:
    """resolve for nonexistent anchor_id returns None."""
    result = registry.resolve("NONEXIST-001")
    assert result is None


def test_resolve_specific_projection_not_found(registry: AnchorRegistry) -> None:
    """resolve with specific projection_path that doesn't exist returns None."""
    registry.register("JRN-001", "FRZ-001", "SRC")
    result = registry.resolve("JRN-001", projection_path="EPIC")
    assert result is None
