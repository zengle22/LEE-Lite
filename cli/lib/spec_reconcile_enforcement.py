"""Dispatch enforcement helpers for ADR-044 spec reconcile (Phase 0/1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, load_json, to_canonical_path


SCOPED_SOURCE_PACKAGE_PREFIXES = (
    "artifacts/epic-to-feat/",
    "artifacts/feat-to-tech/",
    "artifacts/feat-to-proto/",
    "artifacts/proto-to-ui/",
)


def _canonical_dir(workspace_root: Path, ref: str) -> str:
    path = canonical_to_path(ref, workspace_root)
    canonical = to_canonical_path(path, workspace_root).replace("\\", "/")
    return canonical.rstrip("/") + "/"


def is_scoped_source_package(workspace_root: Path, source_package_ref: str) -> bool:
    if not source_package_ref or not str(source_package_ref).strip():
        return False
    canonical = _canonical_dir(workspace_root, str(source_package_ref))
    return any(canonical.startswith(prefix) for prefix in SCOPED_SOURCE_PACKAGE_PREFIXES)


def evaluate_spec_reconcile_hold(
    workspace_root: Path,
    *,
    source_package_ref: str,
) -> dict[str, Any]:
    """Return enforcement decision for downstream dispatch from a source package."""

    if not is_scoped_source_package(workspace_root, source_package_ref):
        return {
            "in_scope": False,
            "hold": False,
            "spec_findings_ref": "",
            "spec_reconcile_report_ref": "",
            "blocking_items": [],
            "diagnostics": [],
        }

    package_dir = canonical_to_path(source_package_ref, workspace_root)
    package_dir_ref = _canonical_dir(workspace_root, source_package_ref)
    findings_path = (package_dir / "spec-findings.json").resolve()
    reconcile_path = (package_dir / "spec-reconcile-report.json").resolve()

    findings_ref = f"{package_dir_ref}spec-findings.json"
    reconcile_ref = f"{package_dir_ref}spec-reconcile-report.json"
    diagnostics: list[str] = []

    if not findings_path.exists():
        return {
            "in_scope": True,
            "hold": True,
            "spec_findings_ref": findings_ref,
            "spec_reconcile_report_ref": reconcile_ref,
            "blocking_items": ["missing spec-findings.json"],
            "diagnostics": diagnostics,
        }

    if not reconcile_path.exists():
        return {
            "in_scope": True,
            "hold": True,
            "spec_findings_ref": findings_ref,
            "spec_reconcile_report_ref": reconcile_ref,
            "blocking_items": ["missing spec-reconcile-report.json"],
            "diagnostics": diagnostics,
        }

    try:
        report = load_json(reconcile_path)
    except Exception as exc:  # pragma: no cover - defensive
        diagnostics.append(str(exc))
        return {
            "in_scope": True,
            "hold": True,
            "spec_findings_ref": findings_ref,
            "spec_reconcile_report_ref": reconcile_ref,
            "blocking_items": ["invalid spec-reconcile-report.json"],
            "diagnostics": diagnostics,
        }

    raw_blocking = report.get("blocking_items")
    blocking_items = [str(item).strip() for item in raw_blocking if str(item).strip()] if isinstance(raw_blocking, list) else []
    hold = bool(blocking_items)
    return {
        "in_scope": True,
        "hold": hold,
        "spec_findings_ref": findings_ref,
        "spec_reconcile_report_ref": reconcile_ref,
        "blocking_items": blocking_items,
        "diagnostics": diagnostics,
    }

