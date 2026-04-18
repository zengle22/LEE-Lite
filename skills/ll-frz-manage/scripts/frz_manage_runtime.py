"""FRZ Manage CLI runtime — validate, freeze, list, and extract subcommands.

Implements the user-facing CLI interface for FRZ package management.
Wraps library functions from frz_schema, frz_registry, and anchor_registry
into cohesive CLI commands per ADR-050.

Usage:
    python frz_manage_runtime.py frz-manage validate --input <doc-dir>
    python frz_manage_runtime.py frz-manage freeze --input <doc-dir> --id FRZ-001
    python frz_manage_runtime.py frz-manage list [--status frozen]
    python frz_manage_runtime.py frz-manage extract --frz FRZ-001 --output <dir>
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure the workspace root is on sys.path for cli.lib imports
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

import yaml

from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent

# Import FRZ schema components
from cli.lib.frz_schema import (
    FRZPackage,
    FRZSchemaError,
    FRZStatus,
    MSCValidator,
    _parse_frz_dict,
)

# Import FRZ registry helpers (aliased to avoid naming conflict)
from cli.lib.frz_registry import get_frz, list_frz as _list_frz_registry, register_frz


# ---------------------------------------------------------------------------
# FRZ ID validation pattern
# ---------------------------------------------------------------------------

FRZ_ID_PATTERN = re.compile(r"^FRZ-\d{3,}$")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _load_frz_from_dir(doc_dir: Path) -> dict[str, Any]:
    """Load FRZ YAML from a document directory.

    File priority:
    1. frz-package.yaml in doc_dir (explicit)
    2. First *.yaml file found (sorted by name)

    Args:
        doc_dir: Directory containing FRZ YAML files.

    Returns:
        Parsed YAML dict.

    Raises:
        CommandError: INVALID_REQUEST if no valid YAML found or file is empty.
    """
    # First check for frz-package.yaml explicitly
    explicit = doc_dir / "frz-package.yaml"
    if explicit.exists():
        text = explicit.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if data is None:
            raise CommandError(
                "INVALID_REQUEST",
                f"FRZ YAML file is empty: {explicit}",
            )
        return data

    # Glob for any YAML files and take the first one
    yaml_files = sorted(doc_dir.glob("*.yaml"))
    if not yaml_files:
        yaml_files = sorted(doc_dir.glob("*.yml"))

    if not yaml_files:
        raise CommandError(
            "INVALID_REQUEST",
            f"No FRZ YAML found in {doc_dir}",
        )

    path = yaml_files[0]
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        raise CommandError(
            "INVALID_REQUEST",
            f"FRZ YAML file is empty: {path}",
        )
    return data


def _find_workspace_root(start: Path | None = None) -> Path:
    """Walk up filesystem looking for .planning or ssot directory.

    Args:
        start: Starting directory. Defaults to Path.cwd().

    Returns:
        Workspace root Path.

    Raises:
        CommandError: INVALID_REQUEST if workspace root not found.
    """
    if start is None:
        start = Path.cwd()

    current = start.resolve()
    while True:
        if (current / ".planning").exists() or (current / "ssot").exists():
            return current
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            raise CommandError(
                "INVALID_REQUEST",
                "Workspace root not found — no .planning or ssot directory in parent chain",
            )
        current = parent


def _format_frz_list(frz_records: list[dict[str, Any]]) -> str:
    """Format FRZ records as an aligned table.

    Columns: FRZ_ID, STATUS, CREATED_AT, MSC_VALID
    Sorted by created_at descending (newest first).

    Args:
        frz_records: List of FRZ record dicts.

    Returns:
        Formatted table string.
    """
    if not frz_records:
        return "No FRZ packages registered"

    # Sort by created_at descending
    sorted_records = sorted(
        frz_records,
        key=lambda r: r.get("created_at", ""),
        reverse=True,
    )

    # Calculate column widths
    header = ["FRZ_ID", "STATUS", "CREATED_AT", "MSC_VALID"]
    rows: list[list[str]] = []
    for rec in sorted_records:
        frz_id = rec.get("frz_id", "N/A")
        status = rec.get("status", "N/A")
        created_at = rec.get("created_at", "N/A")
        msc_valid = "yes" if rec.get("msc_valid") else "no"
        rows.append([frz_id, status, created_at, msc_valid])

    # Calculate widths
    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Build table
    lines: list[str] = []
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(header))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    for row in rows:
        line = "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
        lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Command functions
# ---------------------------------------------------------------------------


def validate_frz(args: argparse.Namespace) -> int:
    """Validate an FRZ package against MSC dimensions.

    Loads FRZ YAML from doc_dir, parses to FRZPackage, runs MSC validation,
    prints structured report.

    Args:
        args: Parsed CLI arguments with 'input' attribute.

    Returns:
        Exit code (0 = PASS, 1 = FAIL).
    """
    doc_dir = Path(args.input)

    if not doc_dir.is_dir():
        print(f"ERROR: input '{doc_dir}' is not a directory", file=sys.stderr)
        return 2

    frz_data = _load_frz_from_dir(doc_dir)

    # Extract inner frz_package content if present as top-level key
    inner = frz_data.get("frz_package", frz_data)
    pkg = _parse_frz_dict(inner)

    report = MSCValidator.validate(pkg)

    # Print report
    frz_id = report.get("frz_id") or pkg.frz_id or "unknown"
    print(f"MSC Validation Report for {frz_id}")
    print("=" * 40)
    print(f"Present ({len(report['present'])}):")
    for dim in report["present"]:
        print(f"  [OK] {dim}")
    print(f"Missing ({len(report['missing'])}):")
    for dim in report["missing"]:
        print(f"  [--] {dim}")

    if report["msc_valid"]:
        print("\nSTATUS: PASS — all 5 MSC dimensions satisfied")
        return 0
    else:
        print(f"\nSTATUS: FAIL — missing dimensions: {report['missing']}")
        return 1


def freeze_frz(args: argparse.Namespace) -> int:
    """Validate and freeze an FRZ package.

    Validates MSC first, saves FRZ package as YAML to artifacts directory,
    copies source documents for evidence trail, registers to FRZ registry.

    Args:
        args: Parsed CLI arguments with 'input' and 'id' attributes.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    doc_dir = Path(args.input)
    frz_id = args.id

    # Validate FRZ ID format
    if not FRZ_ID_PATTERN.match(frz_id):
        print(
            f"ERROR: Invalid FRZ ID format: {frz_id}. Must match FRZ-xxx",
            file=sys.stderr,
        )
        return 2

    if not doc_dir.is_dir():
        print(f"ERROR: input '{doc_dir}' is not a directory", file=sys.stderr)
        return 2

    # Load and parse FRZ YAML
    frz_data = _load_frz_from_dir(doc_dir)
    inner = frz_data.get("frz_package", frz_data)
    pkg = _parse_frz_dict(inner)

    # Run MSC validation
    report = MSCValidator.validate(pkg)

    if not report["msc_valid"]:
        print(
            f"ERROR: Cannot freeze — MSC validation failed",
            file=sys.stderr,
        )
        print(f"Missing dimensions: {report['missing']}", file=sys.stderr)
        return 1

    # Find workspace root
    workspace_root = _find_workspace_root()

    # Create artifact directory
    artifact_dir = workspace_root / "artifacts" / "frz-input" / frz_id
    ensure_parent(artifact_dir / "input")

    # Copy source documents for evidence trail
    shutil.copytree(doc_dir, artifact_dir / "input", dirs_exist_ok=True)

    # Save as YAML (not JSON) for consistency
    freeze_yaml = artifact_dir / "freeze.yaml"
    with open(freeze_yaml, "w", encoding="utf-8") as f:
        yaml.dump(
            frz_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    # Check for duplicate
    existing = get_frz(workspace_root, frz_id)
    if existing is not None:
        raise CommandError(
            "INVALID_REQUEST",
            f"FRZ ID already registered: {frz_id}",
        )

    # Register the FRZ
    revision_type = getattr(args, "type", "new")
    reason = getattr(args, "reason", None)
    previous_frz = getattr(args, "previous_frz", None)

    record, _ = register_frz(
        workspace_root,
        frz_id,
        msc_report=report,
        package_ref=str(freeze_yaml),
        previous_frz=previous_frz,
        revision_type=revision_type,
        reason=reason,
    )

    print(f"{frz_id} registered, status: frozen")
    return 0


def list_frz(args: argparse.Namespace) -> int:
    """List registered FRZ packages.

    Queries FRZ registry, optionally filters by status, displays formatted table.

    Args:
        args: Parsed CLI arguments with optional 'status' attribute.

    Returns:
        Exit code (0 = success).
    """
    workspace_root = _find_workspace_root()

    status = getattr(args, "status", None)
    records = _list_frz_registry(workspace_root, status=status)

    print(_format_frz_list(records))
    return 0


def extract_frz(args: argparse.Namespace) -> int:
    """Extract FRZ package contents (stub for Phase 8).

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (1 = not implemented).
    """
    print(
        "ERROR: extract mode not implemented yet, use in Phase 8",
        file=sys.stderr,
    )
    return 1


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with frz-manage subcommands.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="frz-manage",
        description="FRZ package management: validate, freeze, list, extract",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate FRZ package MSC dimensions",
    )
    validate_parser.add_argument(
        "--input",
        required=True,
        help="Directory containing FRZ YAML source documents",
    )

    # freeze subcommand
    freeze_parser = subparsers.add_parser(
        "freeze",
        help="Validate and freeze FRZ package",
    )
    freeze_parser.add_argument(
        "--input",
        required=True,
        help="Directory containing FRZ YAML source documents",
    )
    freeze_parser.add_argument(
        "--id",
        required=True,
        help="FRZ identifier (FRZ-xxx format)",
    )
    freeze_parser.add_argument(
        "--type",
        default="new",
        choices=["new", "revise"],
        help="Revision type (default: new)",
    )
    freeze_parser.add_argument(
        "--reason",
        default=None,
        help="Reason for revision (required when --type=revise)",
    )
    freeze_parser.add_argument(
        "--previous-frz",
        default=None,
        help="Previous FRZ ID for revision chains",
    )

    # list subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List registered FRZ packages",
    )
    list_parser.add_argument(
        "--status",
        default=None,
        help="Filter by status (frozen, blocked, draft)",
    )

    # extract subcommand (stub for Phase 8)
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract FRZ package contents (Phase 8)",
    )
    extract_parser.add_argument(
        "--frz",
        required=True,
        help="FRZ ID to extract",
    )
    extract_parser.add_argument(
        "--output",
        required=True,
        help="Output directory for extracted contents",
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to appropriate command function.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    command_map = {
        "validate": validate_frz,
        "freeze": freeze_frz,
        "list": list_frz,
        "extract": extract_frz,
    }

    handler = command_map.get(args.command)
    if handler is None:
        print(f"ERROR: Unknown command: {args.command}", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except CommandError as e:
        print(f"ERROR [{e.status_code}]: {e.message}", file=sys.stderr)
        return e.exit_code
    except FRZSchemaError as e:
        print(f"ERROR [SCHEMA_ERROR]: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"ERROR [INTERNAL_ERROR]: {e}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    sys.exit(main())
