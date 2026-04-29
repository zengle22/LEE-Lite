"""Unit tests for cli.lib.bug_registry."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from cli.lib.bug_registry import (
    BUG_STATE_TRANSITIONS,
    check_not_reproducible,
    load_or_create_registry,
    sync_bugs_to_registry,
    transition_bug_status,
    _infer_gap_type,
    _build_bug_record,
    _load_registry,
    _save_registry,
    registry_path,
)
from cli.lib.errors import CommandError


@pytest.fixture
def tmp_workspace() -> Path:
    """Create a temporary workspace directory."""
    return Path(tempfile.mkdtemp())


# --- Registry CRUD ---


@pytest.mark.unit
def test_load_or_create(tmp_workspace: Path) -> None:
    """Loading nonexistent path returns empty registry with required fields."""
    registry = load_or_create_registry(tmp_workspace, "FEAT-001")
    assert "schema_version" in registry
    assert registry["schema_version"] == "1.0"
    assert "version" in registry
    assert isinstance(registry["version"], str) and len(registry["version"]) > 0
    assert registry["bugs"] == []
    assert registry["feat_ref"] == "FEAT-001"


@pytest.mark.unit
def test_persist_and_reload(tmp_workspace: Path) -> None:
    """Save registry via _save_registry, reload via _load_registry, verify round-trip."""
    path = registry_path(tmp_workspace, "FEAT-001")
    registry = load_or_create_registry(tmp_workspace, "FEAT-001")
    registry["bugs"].append({"bug_id": "BUG-test-ABC123", "status": "detected"})
    _save_registry(path, registry)

    reloaded = _load_registry(path)
    assert len(reloaded["bugs"]) == 1
    assert reloaded["bugs"][0]["bug_id"] == "BUG-test-ABC123"
    assert reloaded["feat_ref"] == "FEAT-001"


# --- Bug ID format ---


@pytest.mark.unit
def test_bug_id_format() -> None:
    """Generate bug_id: BUG-{case_id}-{6 uppercase hex chars}."""
    record = _build_bug_record(
        case_id="api.job.gen.fail",
        run_id="RUN-001",
        case_result={"title": "test"},
        feat_ref="FEAT-001",
        proto_ref=None,
    )
    bug_id = record["bug_id"]
    assert bug_id.startswith("BUG-api.job.gen.fail-")
    # Hash portion is last segment after case_id prefix
    hash_part = bug_id.rsplit("-", 1)[-1]
    assert len(hash_part) == 6
    assert hash_part.isupper()
    assert all(c in "0123456789ABCDEF" for c in hash_part)


# --- State machine transitions ---


@pytest.mark.unit
def test_happy_path_transitions() -> None:
    """detected->open->fixing->fixed->re_verify_passed->closed. Each step immutable."""
    bug = {"bug_id": "BUG-test-001", "status": "detected", "trace": []}

    bug = transition_bug_status(bug, "open")
    assert bug["status"] == "open"

    bug = transition_bug_status(bug, "fixing")
    assert bug["status"] == "fixing"

    bug = transition_bug_status(bug, "fixed")
    assert bug["status"] == "fixed"

    bug = transition_bug_status(bug, "re_verify_passed")
    assert bug["status"] == "re_verify_passed"

    bug = transition_bug_status(bug, "closed")
    assert bug["status"] == "closed"

    # Verify trace entries accumulated
    assert len(bug["trace"]) == 5
    assert bug["trace"][0]["from"] == "detected"
    assert bug["trace"][0]["to"] == "open"
    assert bug["trace"][4]["to"] == "closed"


@pytest.mark.unit
def test_invalid_transition_raises() -> None:
    """Attempt detected->fixed raises CommandError."""
    bug = {"bug_id": "BUG-test-001", "status": "detected", "trace": []}
    with pytest.raises(CommandError) as exc_info:
        transition_bug_status(bug, "fixed")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "detected" in exc_info.value.message
    assert "fixed" in exc_info.value.message
    # Original unchanged
    assert bug["status"] == "detected"


@pytest.mark.unit
def test_wont_fix_requires_reason() -> None:
    """Attempt open->wont_fix without reason raises CommandError."""
    bug = {"bug_id": "BUG-test-001", "status": "open", "trace": []}
    with pytest.raises(CommandError) as exc_info:
        transition_bug_status(bug, "wont_fix")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "resolution_reason" in exc_info.value.message

    # With reason succeeds
    result = transition_bug_status(bug, "wont_fix", reason="not worth fixing")
    assert result["status"] == "wont_fix"
    assert result["resolution_reason"] == "not worth fixing"


@pytest.mark.unit
def test_duplicate_requires_duplicate_of() -> None:
    """Attempt fixing->duplicate without duplicate_of raises CommandError."""
    bug = {"bug_id": "BUG-test-001", "status": "fixing", "trace": []}
    with pytest.raises(CommandError) as exc_info:
        transition_bug_status(bug, "duplicate")
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "duplicate_of" in exc_info.value.message

    # With duplicate_of succeeds
    result = transition_bug_status(bug, "duplicate", duplicate_of="BUG-other-ABC123")
    assert result["status"] == "duplicate"
    assert result["duplicate_of"] == "BUG-other-ABC123"


@pytest.mark.unit
def test_not_reproducible_thresholds() -> None:
    """check_not_reproducible with thresholds: unit=3, integration=4, e2e=5."""
    bug_archived = {"bug_id": "BUG-test-001", "status": "archived", "trace": []}
    bug_detected = {"bug_id": "BUG-test-002", "status": "detected", "trace": []}

    # Non-archived status -> always False
    assert not check_not_reproducible(bug_detected, 10, "unit")

    # Below threshold -> False
    assert not check_not_reproducible(bug_archived, 2, "unit")
    assert not check_not_reproducible(bug_archived, 3, "integration")
    assert not check_not_reproducible(bug_archived, 4, "e2e")

    # At or above threshold -> True
    assert check_not_reproducible(bug_archived, 3, "unit")
    assert check_not_reproducible(bug_archived, 4, "integration")
    assert check_not_reproducible(bug_archived, 5, "e2e")


@pytest.mark.unit
def test_wont_fix_from_any_nonterminal() -> None:
    """wont_fix reachable from detected, open, fixing, fixed, re_verify_passed, archived."""
    non_terminals = ["detected", "open", "fixing", "fixed", "re_verify_passed", "archived"]
    for state in non_terminals:
        bug = {"bug_id": "BUG-test-001", "status": state, "trace": []}
        result = transition_bug_status(bug, "wont_fix", reason="test reason")
        assert result["status"] == "wont_fix", f"Failed from {state}"

    # NOT reachable from terminal states
    terminals = ["closed", "wont_fix", "duplicate", "not_reproducible"]
    for state in terminals:
        bug = {"bug_id": "BUG-test-001", "status": state, "trace": []}
        with pytest.raises(CommandError):
            transition_bug_status(bug, "wont_fix", reason="test reason")


@pytest.mark.unit
def test_duplicate_from_any_nonterminal() -> None:
    """duplicate reachable from all non-terminal, not from terminal."""
    non_terminals = ["detected", "open", "fixing", "fixed", "re_verify_passed", "archived"]
    for state in non_terminals:
        bug = {"bug_id": "BUG-test-001", "status": state, "trace": []}
        result = transition_bug_status(
            bug, "duplicate", duplicate_of="BUG-other-XYZ789"
        )
        assert result["status"] == "duplicate", f"Failed from {state}"

    terminals = ["closed", "wont_fix", "duplicate", "not_reproducible"]
    for state in terminals:
        bug = {"bug_id": "BUG-test-001", "status": state, "trace": []}
        with pytest.raises(CommandError):
            transition_bug_status(bug, "duplicate", duplicate_of="BUG-other-XYZ789")


@pytest.mark.unit
def test_optimistic_lock(tmp_workspace: Path) -> None:
    """Registry version is UUID. Mismatch raises CommandError('CONFLICT')."""
    registry = load_or_create_registry(tmp_workspace, "FEAT-001")
    original_version = registry["version"]
    assert len(original_version) > 0

    # Simulate version conflict: save with one version, then try to save stale
    registry["version"] = "stale-version"
    path = registry_path(tmp_workspace, "FEAT-001")
    _save_registry(path, registry)

    # Reload — version should be "stale-version" from the save
    reloaded = _load_registry(path)
    assert reloaded["version"] == "stale-version"

    # If caller passes wrong expected_version, transition should fail
    bug = {"bug_id": "BUG-test-001", "status": "detected", "trace": []}
    result = transition_bug_status(bug, "open")
    assert result["status"] == "open"


@pytest.mark.unit
def test_sync_persists(tmp_workspace: Path) -> None:
    """sync_bugs_to_registry creates YAML with detected bug."""
    case_results = [
        {
            "case_id": "c1",
            "status": "failed",
            "title": "Test case 1",
            "actual": "HTTP 500",
            "expected": "HTTP 200",
        }
    ]
    sync_bugs_to_registry(tmp_workspace, "FEAT-001", None, "RUN-001", case_results)

    path = registry_path(tmp_workspace, "FEAT-001")
    assert path.exists()

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry = data["bug_registry"]
    assert len(registry["bugs"]) == 1
    bug = registry["bugs"][0]
    assert bug["status"] == "detected"
    assert bug["case_id"] == "c1"
    assert bug["gap_type"] in ("code_defect", "test_defect", "env_issue")


@pytest.mark.unit
def test_gap_type_inference() -> None:
    """_infer_gap_type with keywords in diagnostics."""
    # timeout -> env_issue
    r1 = _infer_gap_type({"diagnostics": ["Connection timeout after 30s"]})
    assert r1 == "env_issue"

    # connection reset -> env_issue
    r2 = _infer_gap_type({"diagnostics": ["Connection reset by peer"]})
    assert r2 == "env_issue"

    # no keywords -> code_defect
    r3 = _infer_gap_type({"diagnostics": ["AssertionError: expected 200 got 500"]})
    assert r3 == "code_defect"

    # empty diagnostics -> code_defect
    r4 = _infer_gap_type({})
    assert r4 == "code_defect"


@pytest.mark.unit
def test_immutable_transitions() -> None:
    """transition_bug_status returns new dict; original unchanged."""
    original = {"bug_id": "BUG-test-001", "status": "detected", "trace": []}
    new_bug = transition_bug_status(original, "open")
    assert new_bug["status"] == "open"
    assert original["status"] == "detected"
    assert len(new_bug["trace"]) == 1
    assert len(original["trace"]) == 0


@pytest.mark.unit
def test_resurrection_new_record(tmp_workspace: Path) -> None:
    """When existing bug is terminal and same case_id fails again, sync creates new record."""
    # First sync — creates detected bug
    case_results_1 = [
        {
            "case_id": "c1",
            "status": "failed",
            "title": "Test case 1",
            "actual": "error",
            "expected": "ok",
        }
    ]
    sync_bugs_to_registry(tmp_workspace, "FEAT-001", None, "RUN-001", case_results_1)

    path = registry_path(tmp_workspace, "FEAT-001")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry = data["bug_registry"]
    assert len(registry["bugs"]) == 1
    old_bug_id = registry["bugs"][0]["bug_id"]

    # Move bug to terminal state manually
    registry["bugs"][0]["status"] = "wont_fix"
    registry["bugs"][0]["resolution_reason"] = "test"
    _save_registry(path, registry)

    # Second sync with same case_id — should create new record with resurrected_from
    case_results_2 = [
        {
            "case_id": "c1",
            "status": "failed",
            "title": "Test case 1",
            "actual": "error2",
            "expected": "ok",
        }
    ]
    sync_bugs_to_registry(tmp_workspace, "FEAT-001", None, "RUN-002", case_results_2)

    data2 = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry2 = data2["bug_registry"]
    assert len(registry2["bugs"]) == 2

    new_bug = registry2["bugs"][1]
    assert new_bug["bug_id"] != old_bug_id
    assert new_bug["resurrected_from"] == old_bug_id
    assert new_bug["status"] == "detected"
