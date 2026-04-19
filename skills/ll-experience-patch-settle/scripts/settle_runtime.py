"""Settle runtime for Minor Experience Patches (ADR-049).

Creates backwrite RECORDS in backwrites/ subdirectory for human review.
Does NOT modify actual SSOT files.

Usage:
    python settle_runtime.py process --patch <patch-yaml-path> --workspace-root <root>
    python settle_runtime.py settle --patch <patch-yaml-path> [--workspace-root <root>] [--apply]
"""

import argparse
import sys
import textwrap
import warnings
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Import grade derivation from the canonical schema — do NOT re-implement.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cli.lib.patch_schema import GradeLevel, derive_grade


class CommandError(Exception):
    """Structured error for settle operations."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# BACKWRITE_MAP — determines what backwrite RECORDS to create per change_class
# ---------------------------------------------------------------------------

BACKWRITE_MAP = {
    "ui_flow":       {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "copy_text":     {"must_backwrite_ssot": False, "backwrite_targets": []},
    "layout":        {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "navigation":    {"must_backwrite_ssot": True,  "backwrite_targets": ["ui_spec", "flow_spec"]},
    "interaction":   {"must_backwrite_ssot": True,  "backwrite_targets": ["ui_spec", "flow_spec", "testset"]},
    "error_handling":{"must_backwrite_ssot": False, "backwrite_targets": []},
    "performance":   {"must_backwrite_ssot": False, "backwrite_targets": []},
    "accessibility": {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "data_display":  {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "visual":        {"must_backwrite_ssot": False, "backwrite_targets": ["ui_spec_optional"]},
    "semantic":      {"must_backwrite_ssot": True,  "backwrite_targets": ["frz_revise"]},  # NOT handled by settle
    "other":         {"must_backwrite_ssot": False, "backwrite_targets": []},
}


# ---------------------------------------------------------------------------
# Workspace root resolution
# ---------------------------------------------------------------------------

def _find_workspace_root(start: Path | None = None) -> Path:
    """Walk up from start looking for a directory containing 'ssot/'."""
    if start is None:
        start = Path.cwd()
    current = start.resolve()
    while current != current.parent:
        if (current / "ssot").exists():
            return current
        current = current.parent
    return start


# ---------------------------------------------------------------------------
# Backwrite record creation
# ---------------------------------------------------------------------------

def _write_backwrite_record(
    patch_yaml: dict,
    target: str,
    workspace_root: Path,
) -> Path:
    """Write a structured backwrite RECORD for human review.

    Records are written to ssot/experience-patches/{feat_ref}/backwrites/{target}_updates.yaml.
    These are RECORDS, NOT actual SSOT file modifications.
    """
    feat_ref = patch_yaml.get("scope", {}).get("feat_ref", "unknown")
    backwrite_dir = workspace_root / "ssot" / "experience-patches" / feat_ref / "backwrites"
    backwrite_dir.mkdir(parents=True, exist_ok=True)

    record_path = backwrite_dir / f"{target}_updates.yaml"

    record = {
        "patch_id": patch_yaml.get("id"),
        "change_class": patch_yaml.get("change_class"),
        "grade_level": patch_yaml.get("grade_level"),
        "backwrite_target": target,
        "changed_files": patch_yaml.get("changed_files", []),
        "test_impact": patch_yaml.get("test_impact", {}),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "note": "Record for human review — NOT applied to actual SSOT files",
    }

    with open(record_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(record, f, default_flow_style=False, sort_keys=False)

    return record_path


# ---------------------------------------------------------------------------
# Core settle logic
# ---------------------------------------------------------------------------

def settle_minor_patch(patch_yaml: dict, workspace_root: Path) -> dict:
    """Process a Minor patch: create backwrite RECORDS, update status.

    Args:
        patch_yaml: Patch YAML dict (mutated in-place for status/settled_at).
        workspace_root: Root of the workspace containing ssot/ directory.

    Returns:
        dict with status, backwrite_targets, files_written.

    Raises:
        CommandError: If grade is major or input is invalid.
    """
    # --- Idempotency check ---
    if patch_yaml.get("status") == "applied":
        return {
            "status": "already_applied",
            "message": "Patch already settled — no-op (idempotent)",
            "backwrite_targets": [],
            "files_written": [],
        }

    # --- Derive grade if not present ---
    grade_level = patch_yaml.get("grade_level")
    if grade_level is None:
        change_class = patch_yaml.get("change_class", "other")
        grade_level = derive_grade(change_class).value
        patch_yaml["grade_level"] = grade_level

    # --- Reject Major patches ---
    if grade_level == GradeLevel.MAJOR.value:
        raise CommandError(
            "INVALID_REQUEST",
            "Major patches must use ll-frz-manage --type revise, not settle"
        )

    # --- Look up backwrite targets ---
    change_class = patch_yaml.get("change_class", "other")
    backwrite_config = BACKWRITE_MAP.get(change_class, BACKWRITE_MAP["other"])
    backwrite_targets = backwrite_config.get("backwrite_targets", [])

    # --- Write backwrite RECORDS ---
    files_written = []
    for target in backwrite_targets:
        record_path = _write_backwrite_record(patch_yaml, target, workspace_root)
        files_written.append(str(record_path))

    # --- Update patch status ---
    patch_yaml["status"] = "applied"
    patch_yaml["settled_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "status": "applied",
        "backwrite_targets": backwrite_targets,
        "files_written": files_written,
    }


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for settle_runtime CLI."""
    parser = argparse.ArgumentParser(
        description="Settle Minor Experience Patches with backwrite RECORDS",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # process subcommand
    process_parser = subparsers.add_parser(
        "process",
        help="Process a Minor patch YAML file",
    )
    process_parser.add_argument("--patch", required=True, help="Path to Patch YAML file")
    process_parser.add_argument("--workspace-root", required=True, help="Workspace root directory")

    # settle subcommand (same as process, but with optional --apply flag)
    settle_parser = subparsers.add_parser(
        "settle",
        help="Settle a Minor patch (alias for process with optional --apply)",
    )
    settle_parser.add_argument("--patch", required=True, help="Path to Patch YAML file")
    settle_parser.add_argument("--workspace-root", help="Workspace root directory (auto-detected if omitted)")
    settle_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply backwrite to actual SSOT files (NOT YET IMPLEMENTED — creates RECORDS only)",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the settle_runtime CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    patch_path = Path(args.patch)
    if not patch_path.exists():
        print(f"ERROR: Patch file not found: {patch_path}", file=sys.stderr)
        sys.exit(1)

    # Load patch YAML
    with open(patch_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Support both top-level and nested experience_patch
    if "experience_patch" in data:
        patch_yaml = data["experience_patch"]
    else:
        patch_yaml = data

    # Resolve workspace root
    if hasattr(args, "workspace_root") and args.workspace_root:
        workspace_root = Path(args.workspace_root)
    else:
        workspace_root = _find_workspace_root(patch_path.parent)

    # Handle --apply flag (stub)
    if getattr(args, "apply", False):
        print("WARNING: --apply flag is reserved for future use. "
              "Currently, settle only creates backwrite RECORDS for human review. "
              "Actual SSOT file modification is not yet implemented.")
        # Future: _apply_backwrite_to_ssot() would modify actual spec files
        # gated behind human confirmation

    # Execute settle
    try:
        result = settle_minor_patch(patch_yaml, workspace_root)
    except CommandError as e:
        print(f"ERROR [{e.code}]: {e.message}", file=sys.stderr)
        sys.exit(1)

    # Write updated patch YAML back to its original location
    with open(patch_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    # Report results
    patch_id = patch_yaml.get("id", "unknown")
    print(f"Patch settled: {patch_id}")
    print(f"  Status: {result['status']}")
    print(f"  Backwrite targets: {result['backwrite_targets']}")
    print(f"  Records written: {len(result['files_written'])}")
    for fp in result["files_written"]:
        print(f"    - {fp}")


if __name__ == "__main__":
    main()
