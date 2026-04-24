"""Generate unique run-manifest.yaml per execution with environment binding.

Stores manifests in ssot/tests/.artifacts/runs/{run_id}/ per ADR-054 D-01/D-02.
Append-only semantics — do NOT delete or overwrite existing manifests.
"""

from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.job_state import utc_now

# Canonical storage directory relative to workspace root
RUN_ARTIFACTS_DIR = "ssot/tests/.artifacts/runs"


def _validate_run_id(run_id: str) -> None:
    """Reject path traversal patterns and absolute paths.

    Per T-18-01 mitigation.
    """
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise ValueError(f"run_id contains invalid path characters: {run_id!r}")
    if run_id.startswith("/") or (len(run_id) > 1 and run_id[1] == ":"):
        raise ValueError(f"run_id must not be an absolute path: {run_id!r}")


def _get_build_version(workspace_root: Path, subdir: Path) -> str:
    """Return build version from subdir or 'unknown' if unavailable.

    Checks for a VERSION file, then falls back to git describe.
    """
    version_file = workspace_root / subdir / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    try:
        result = subprocess.run(
            ["git", "describe", "--always", "--dirty"],
            cwd=str(workspace_root / subdir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return "unknown"


def _git_sha(workspace_root: Path) -> str:
    """Return git SHA of workspace root or 'unknown' if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return "unknown"


def generate_run_manifest(
    workspace_root: Path,
    run_id: str,
    *,
    app_url: str,
    api_url: str | None = None,
    browser: str = "chromium",
    accounts: list[str] | None = None,
) -> Path:
    """Generate a run-manifest.yaml for this execution.

    Creates ssot/tests/.artifacts/runs/{run_id}/run-manifest.yaml with:
    - run_id, run_id_format, created_at
    - git_sha (from workspace root)
    - frontend_build, backend_build (from respective subdirs or 'unknown')
    - base_url (app + api)
    - browser, accounts
    - artifact_version

    Per ADR-054 D-01 (dedicated directory), D-02 (append-only).

    Args:
        workspace_root: Root of the workspace.
        run_id: Unique identifier for this run. Must not contain path separators.
        app_url: Frontend application URL.
        api_url: Backend API URL (optional).
        browser: Browser name (default: 'chromium').
        accounts: List of account identifiers (default: empty list).

    Returns:
        Path to the generated run-manifest.yaml file.

    Raises:
        ValueError: If run_id contains path traversal characters.
        FileExistsError: If manifest directory already exists (append-only).
    """
    _validate_run_id(run_id)

    git_sha_value = _git_sha(workspace_root)
    frontend_build = _get_build_version(workspace_root, Path("frontend"))
    backend_build = _get_build_version(workspace_root, Path("backend"))

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "run_id_format": "e2e.run-{timestamp}-{random}",
        "created_at": utc_now(),
        "git_sha": git_sha_value,
        "frontend_build": frontend_build,
        "backend_build": backend_build,
        "base_url": {
            "app": app_url,
            "api": api_url,
        },
        "browser": browser,
        "accounts": accounts if accounts is not None else [],
        "artifact_version": "1.0",
    }

    run_dir = workspace_root / RUN_ARTIFACTS_DIR / run_id
    manifest_file = run_dir / "run-manifest.yaml"

    if manifest_file.exists():
        raise FileExistsError(f"run-manifest already exists for {run_id!r}; append-only semantics")

    run_dir.mkdir(parents=True, exist_ok=True)

    with manifest_file.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(manifest, fh, allow_unicode=True, sort_keys=False)

    return manifest_file


def load_run_manifest(workspace_root: Path, run_id: str) -> dict[str, Any]:
    """Load a run-manifest by run_id.

    Per T-18-02 mitigation: wraps YAML load in try/except and validates structure.

    Args:
        workspace_root: Root of the workspace.
        run_id: Unique identifier for the run.

    Returns:
        Manifest dict loaded from ssot/tests/.artifacts/runs/{run_id}/run-manifest.yaml.

    Raises:
        FileNotFoundError: If manifest does not exist.
        ValueError: If manifest is not a valid dict or is corrupted.
    """
    _validate_run_id(run_id)

    manifest_file = workspace_root / RUN_ARTIFACTS_DIR / run_id / "run-manifest.yaml"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"run-manifest not found for {run_id!r}")

    try:
        raw = manifest_file.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"Corrupted run-manifest for {run_id!r}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"run-manifest for {run_id!r} is not a valid YAML object")

    return data


def get_run_id_from_manifest_path(manifest_path: Path) -> str | None:
    """Extract run_id from a run-manifest path.

    E.g. /path/to/ssot/tests/.artifacts/runs/e2e.run-20260424-ABC12345/run-manifest.yaml
    → "e2e.run-20260424-ABC12345"

    Returns None if path is invalid or does not contain a run_id.
    """
    try:
        parts = manifest_path.parts
        runs_idx = None
        for i, part in enumerate(parts):
            if part == "runs":
                runs_idx = i
                break
        if runs_idx is None or runs_idx + 1 >= len(parts):
            return None
        run_id = parts[runs_idx + 1]
        # Validate extracted run_id
        if not run_id or ".." in run_id or "/" in run_id or "\\" in run_id:
            return None
        return run_id
    except (IndexError, TypeError):
        return None


def list_run_manifests(workspace_root: Path) -> list[str]:
    """List all run_ids stored under the runs directory.

    Returns:
        Sorted list of run_id strings.
    """
    runs_dir = workspace_root / RUN_ARTIFACTS_DIR
    if not runs_dir.is_dir():
        return []

    run_ids: list[str] = []
    for entry in runs_dir.iterdir():
        if entry.is_dir() and (entry / "run-manifest.yaml").is_file():
            run_ids.append(entry.name)

    return sorted(run_ids)
