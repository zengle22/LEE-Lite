"""Unit tests for cli.lib.frz_registry."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from cli.lib.frz_registry import (
    FRZ_ID_PATTERN,
    get_frz,
    list_frz,
    register_frz,
    registry_path,
    update_frz_status,
)
from cli.lib.errors import CommandError


@pytest.fixture
def tmp_workspace() -> Path:
    """Create a temporary workspace directory."""
    return Path(tempfile.mkdtemp())


# --- register_frz ---


def test_register_frz_success(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True, "present": ["product_boundary"]}
    record, frz_id = register_frz(
        tmp_workspace,
        frz_id="FRZ-001",
        msc_report=msc_report,
        package_ref="ssot/frz/FRZ-001.yaml",
    )
    assert record["frz_id"] == "FRZ-001"
    assert record["status"] == "frozen"
    assert record["created_at"] is not None
    assert record["msc_valid"] is True
    assert record["package_ref"] == "ssot/frz/FRZ-001.yaml"
    assert record["version"] == "1.0"


def test_register_frz_duplicate_raises(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg1")
    with pytest.raises(CommandError) as exc_info:
        register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg2")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "already registered" in exc_info.value.message


def test_register_frz_with_previous_ref(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    record, _ = register_frz(
        tmp_workspace,
        frz_id="FRZ-002",
        msc_report=msc_report,
        package_ref="pkg",
        previous_frz="FRZ-001",
    )
    assert record["previous_frz_ref"] == "FRZ-001"


def test_register_frz_with_reason(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    record, _ = register_frz(
        tmp_workspace,
        frz_id="FRZ-003",
        msc_report=msc_report,
        package_ref="pkg",
        reason="scope change",
    )
    assert record["revision_reason"] == "scope change"


def test_register_frz_with_all_revision_fields(tmp_workspace: Path) -> None:
    """Register with previous_frz, revision_type, and reason."""
    msc_report = {"msc_valid": True}
    record, _ = register_frz(
        tmp_workspace,
        frz_id="FRZ-010",
        msc_report=msc_report,
        package_ref="pkg",
        previous_frz="FRZ-001",
        revision_type="revise",
        reason="scope change",
    )
    assert record["previous_frz_ref"] == "FRZ-001"
    assert record["revision_type"] == "revise"
    assert record["revision_reason"] == "scope change"


def test_register_frz_msc_valid_false(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": False, "missing": ["domain_model"]}
    record, _ = register_frz(
        tmp_workspace,
        frz_id="FRZ-004",
        msc_report=msc_report,
        package_ref="pkg",
    )
    assert record["msc_valid"] is False


def test_register_frz_invalid_id_format(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    with pytest.raises(CommandError):
        register_frz(tmp_workspace, "invalid", msc_report, "pkg")

    with pytest.raises(CommandError):
        register_frz(tmp_workspace, "frz-001", msc_report, "pkg")


# --- list_frz ---


def test_list_frz_all(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg1")
    register_frz(tmp_workspace, "FRZ-002", msc_report, "pkg2")
    assert len(list_frz(tmp_workspace)) == 2


def test_list_frz_filter_by_status(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg1")
    register_frz(tmp_workspace, "FRZ-002", msc_report, "pkg2")
    update_frz_status(tmp_workspace, "FRZ-002", "superseded")

    frozen = list_frz(tmp_workspace, status="frozen")
    assert len(frozen) == 1
    assert frozen[0]["frz_id"] == "FRZ-001"


# --- get_frz ---


def test_get_frz_existing(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg1")
    result = get_frz(tmp_workspace, "FRZ-001")
    assert result is not None
    assert result["frz_id"] == "FRZ-001"


def test_get_frz_nonexistent(tmp_workspace: Path) -> None:
    result = get_frz(tmp_workspace, "FRZ-999")
    assert result is None


# --- update_frz_status ---


def test_update_frz_status(tmp_workspace: Path) -> None:
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg1")
    updated = update_frz_status(tmp_workspace, "FRZ-001", "superseded")
    assert updated["status"] == "superseded"

    # Verify persistence
    result = get_frz(tmp_workspace, "FRZ-001")
    assert result is not None
    assert result["status"] == "superseded"


def test_update_frz_status_not_found_raises(tmp_workspace: Path) -> None:
    with pytest.raises(CommandError) as exc_info:
        update_frz_status(tmp_workspace, "FRZ-999", "superseded")
    assert exc_info.value.status_code == "REGISTRY_MISS"


# --- registry file creation ---


def test_registry_file_created_on_first_register(tmp_workspace: Path) -> None:
    """Ensure registry YAML is created after first register."""
    rp = registry_path(tmp_workspace)
    assert not rp.exists()
    msc_report = {"msc_valid": True}
    register_frz(tmp_workspace, "FRZ-001", msc_report, "pkg")
    assert rp.exists()
    text = rp.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert "frz_registry" in data
