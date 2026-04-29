"""Bug registry with state machine and YAML persistence.

Truth source: ADR-055 §2.2 state machine, §2.3 YAML schema.
Provides CRUD operations, immutable state transitions, and atomic YAML persistence.
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent, read_text


# --- State machine ---

BUG_STATE_TRANSITIONS: dict[str, set[str]] = {
    "detected":         {"open", "wont_fix", "duplicate"},
    "open":             {"fixing", "wont_fix", "duplicate"},
    "fixing":           {"fixed", "wont_fix", "duplicate"},
    "fixed":            {"re_verify_passed", "open", "wont_fix", "duplicate"},
    "re_verify_passed": {"closed", "wont_fix", "duplicate"},
    "archived":         {"wont_fix", "duplicate", "not_reproducible"},
    "closed":           set(),
    "wont_fix":         set(),
    "duplicate":        set(),
    "not_reproducible": set(),
}

NOT_REPRODUCIBLE_THRESHOLDS: dict[str, int] = {
    "unit": 3,
    "integration": 4,
    "e2e": 5,
}

TERMINAL_STATES: set[str] = {"closed", "wont_fix", "duplicate", "not_reproducible"}


# --- Helpers ---


def _timestamp() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def registry_path(workspace_root: Path, feat_ref: str) -> Path:
    """Return path to bug-registry.yaml for the given feat_ref."""
    return workspace_root / "artifacts" / "bugs" / feat_ref / "bug-registry.yaml"


def _empty_registry() -> dict[str, Any]:
    """Return an empty registry dict with all required fields."""
    return {
        "schema_version": "1.0",
        "registry_id": "",
        "feat_ref": "",
        "proto_ref": None,
        "version": str(uuid.uuid4()),
        "generated_at": _timestamp(),
        "last_synced_at": _timestamp(),
        "last_sync_run_id": "",
        "bugs": [],
    }


def _load_registry(path: Path) -> dict[str, Any]:
    """Read YAML file and return registry dict. Returns empty registry if missing."""
    if not path.exists():
        return _empty_registry()
    text = read_text(path)
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return _empty_registry()
    return data.get("bug_registry", _empty_registry())


def _save_registry(path: Path, registry: dict[str, Any]) -> None:
    """Write registry to YAML using atomic write (temp file + os.replace)."""
    ensure_parent(path)
    content = yaml.dump(
        {"bug_registry": registry},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    dir_name = path.parent
    fd, temp_path = tempfile.mkstemp(dir=str(dir_name), suffix=".yaml.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, str(path))
    except BaseException:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def load_or_create_registry(
    workspace_root: Path,
    feat_ref: str,
    proto_ref: str | None = None,
) -> dict[str, Any]:
    """Load existing registry or create a new one for the given feat_ref."""
    path = registry_path(workspace_root, feat_ref)
    registry = _load_registry(path)
    if not registry.get("registry_id"):
        registry["registry_id"] = f"BUG-REG-{feat_ref}"
    if not registry.get("feat_ref"):
        registry["feat_ref"] = feat_ref
    if proto_ref is not None:
        registry["proto_ref"] = proto_ref
    return registry


# --- Gap type inference ---


def _infer_gap_type(case_result: dict[str, Any]) -> str:
    """MVP gap_type inference. Developer can override via CLI."""
    diagnostics = case_result.get("diagnostics", [])
    for d in diagnostics:
        dl = str(d).lower()
        if any(kw in dl for kw in ("timeout", "connection reset", "flaky", "intermittent")):
            return "env_issue"
    return "code_defect"


# --- Bug record construction ---


def _build_bug_record(
    case_id: str,
    run_id: str,
    case_result: dict[str, Any],
    feat_ref: str | None,
    proto_ref: str | None,
) -> dict[str, Any]:
    """Build a new bug record from a failed case result."""
    now = datetime.now(timezone.utc).isoformat()
    hash_input = f"{case_id}{run_id}{now}"
    hash_6 = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
    bug_id = f"BUG-{case_id}-{hash_6}"

    ref = feat_ref or proto_ref or "unknown"
    manifest_ref = f"ssot/tests/api/{ref}/api-coverage-manifest.yaml" if ref != "unknown" else ""

    return {
        "bug_id": bug_id,
        "case_id": case_id,
        "coverage_id": case_result.get("coverage_id", case_id),
        "title": case_result.get("title", case_id),
        "status": "detected",
        "severity": case_result.get("severity", "medium"),
        "gap_type": _infer_gap_type(case_result),
        "actual": case_result.get("actual", ""),
        "expected": case_result.get("expected", ""),
        "evidence_ref": case_result.get("evidence_ref", ""),
        "stdout_ref": case_result.get("stdout_ref", ""),
        "stderr_ref": case_result.get("stderr_ref", ""),
        "diagnostics": case_result.get("diagnostics", [])[:5],
        "run_id": run_id,
        "discovered_at": now,
        "fixed_at": None,
        "verified_at": None,
        "closed_at": None,
        "resolution": None,
        "fix_commit": None,
        "duplicate_of": None,
        "resolution_reason": None,
        "re_verify_result": None,
        "resurrected_from": None,
        "strike_count": 0,
        "fix_hypothesis": None,
        "trace": [{"event": "discovered", "at": now, "run_id": run_id}],
        "manifest_ref": manifest_ref,
    }


# --- State transitions ---


def transition_bug_status(
    bug: dict[str, Any],
    new_status: str,
    *,
    reason: str | None = None,
    actor: str = "system",
    **extra_fields: Any,
) -> dict[str, Any]:
    """Transition a bug to a new status. Returns new bug dict (immutable).

    Raises CommandError on invalid transitions or missing required fields.
    """
    current = bug["status"]
    valid = BUG_STATE_TRANSITIONS.get(current, set())

    # Terminal state exceptions: wont_fix and duplicate reachable from any non-terminal
    if new_status in {"wont_fix", "duplicate"} and current not in TERMINAL_STATES:
        pass  # allowed
    elif new_status not in valid:
        raise CommandError(
            "INVALID_REQUEST",
            f"Cannot transition bug {bug['bug_id']} from '{current}' to '{new_status}'",
        )

    # Terminal state field requirements
    if new_status == "wont_fix" and not reason:
        raise CommandError(
            "INVALID_REQUEST",
            "wont_fix requires resolution_reason",
        )
    if new_status == "duplicate" and not extra_fields.get("duplicate_of"):
        raise CommandError(
            "INVALID_REQUEST",
            "duplicate requires duplicate_of",
        )

    # Build new bug dict (immutable — return new copy)
    new_bug = {**bug, "status": new_status}
    new_bug["trace"] = [*bug.get("trace", []), {
        "event": "status_changed",
        "at": _timestamp(),
        "from": current,
        "to": new_status,
        "actor": actor,
    }]
    if reason:
        new_bug["resolution_reason"] = reason
    for k, v in extra_fields.items():
        new_bug[k] = v

    return new_bug


# --- not_reproducible check ---


def check_not_reproducible(
    bug: dict[str, Any],
    consecutive_nonappearances: int,
    test_level: str = "integration",
) -> bool:
    """Should this bug be auto-marked as not_reproducible?"""
    threshold = NOT_REPRODUCIBLE_THRESHOLDS.get(test_level, 4)
    return (
        bug["status"] == "archived"
        and consecutive_nonappearances >= threshold
    )


# --- Sync ---


def sync_bugs_to_registry(
    workspace_root: Path,
    feat_ref: str | None,
    proto_ref: str | None,
    run_id: str,
    case_results: list[dict[str, Any]],
) -> None:
    """Sync failed cases to bug-registry.yaml. Called as on_complete callback."""
    failed = [cr for cr in case_results if cr.get("status") == "failed"]
    if not failed:
        return

    ref = feat_ref or proto_ref or "unknown"
    registry = load_or_create_registry(workspace_root, ref, proto_ref)

    for case_result in failed:
        case_id = case_result["case_id"]

        # Check if this case_id has an existing non-terminal bug
        existing_terminal = None
        for existing_bug in registry["bugs"]:
            if existing_bug["case_id"] == case_id:
                if existing_bug["status"] in TERMINAL_STATES:
                    existing_terminal = existing_bug
                else:
                    # Already tracked in non-terminal state — skip
                    break
        else:
            # No non-terminal match found — create new record
            bug_record = _build_bug_record(
                case_id, run_id, case_result, feat_ref, proto_ref
            )
            if existing_terminal:
                bug_record["resurrected_from"] = existing_terminal["bug_id"]
            registry["bugs"].append(bug_record)
            continue

    registry["last_synced_at"] = _timestamp()
    registry["last_sync_run_id"] = run_id
    registry["version"] = str(uuid.uuid4())

    path = registry_path(workspace_root, ref)
    _save_registry(path, registry)
