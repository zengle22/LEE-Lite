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
import importlib
import json
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
from cli.lib.frz_registry import (
    get_frz,
    list_frz as _list_frz_registry,
    register_frz,
    _load_registry,
    registry_path,
)

# Import extraction library
from cli.lib.frz_extractor import extract_src_from_frz, check_frz_coverage


# ---------------------------------------------------------------------------
# Cascade step module map — SSOT chain extraction steps
# ---------------------------------------------------------------------------

STEP_MODULE_MAP: list[tuple[str, str, str]] = [
    ("SRC", "cli.lib.frz_extractor", "extract_src_from_frz"),
    ("EPIC", "skills.ll_product_src_to_epic.scripts.src_to_epic_runtime", "extract_epic_from_frz"),
    ("FEAT", "skills.ll_product_epic_to_feat.scripts.epic_to_feat_runtime", "extract_feat_from_frz"),
    ("TECH", "skills.ll_product_tech_design.scripts.tech_design_runtime", "extract_tech_from_frz"),
    ("UI", "skills.ll_dev_proto_to_ui.scripts.proto_to_ui_runtime", "extract_ui_from_frz"),
    ("TEST", "skills.ll_qa_test_gen.scripts.test_gen_runtime", "extract_test_from_frz"),
    ("IMPL", "skills.ll_dev_impl.scripts.impl_runtime", "extract_impl_from_frz"),
]


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


def _check_circular_revision(
    frz_registry: dict[str, Any], new_frz_id: str, previous_frz: str
) -> list[str]:
    """Check if adding new_frz_id -> previous_frz would create a circular chain.

    Walks the revision chain from previous_frz following previous_frz_ref
    pointers. If new_frz_id is encountered, a circular chain exists.

    Args:
        frz_registry: Map of frz_id -> record dict.
        new_frz_id: The FRZ ID being created.
        previous_frz: The FRZ ID this revision claims to revise.

    Returns:
        List of FRZ IDs in the chain if circular, empty list if safe.
    """
    visited: set[str] = set()
    current = previous_frz
    while current:
        if current == new_frz_id:
            return list(visited) + [current]
        if current in visited:
            break
        visited.add(current)
        rec = frz_registry.get(current)
        if rec:
            current = rec.get("previous_frz_ref")
        else:
            current = None
    return []


def _format_frz_list(frz_records: list[dict[str, Any]]) -> str:
    """Format FRZ records as an aligned table.

    FIXED columns: FRZ_ID, STATUS, REV_TYPE, PREV_FRZ, CREATED_AT, MSC_VALID.
    '-' used for empty values to preserve column position parsing.
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

    # FIXED header — always shows all columns
    header = ["FRZ_ID", "STATUS", "REV_TYPE", "PREV_FRZ", "CREATED_AT", "MSC_VALID"]
    rows: list[list[str]] = []
    for rec in sorted_records:
        frz_id = rec.get("frz_id", "N/A")
        status = rec.get("status", "N/A")
        rev_type = rec.get("revision_type", "new")
        prev_frz = rec.get("previous_frz_ref", "-")
        created_at = rec.get("created_at", "N/A")
        msc_valid = "yes" if rec.get("msc_valid") else "no"
        rows.append([frz_id, status, rev_type, prev_frz, created_at, msc_valid])

    # Calculate widths
    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Build table
    lines: list[str] = []
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(header))
    lines.append(header_line)
    lines.append("-" * len(header_line))
    for row in rows:
        line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
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

    # Circular revision chain prevention (GRADE-03)
    if revision_type == "revise" and previous_frz:
        # Load existing registry records as a lookup map
        reg_path_file = registry_path(workspace_root)
        raw_records = _load_registry(reg_path_file)
        registry_map = {r["frz_id"]: r for r in raw_records}
        circular_chain = _check_circular_revision(registry_map, frz_id, previous_frz)
        if circular_chain:
            raise CommandError(
                "CIRCULAR_REVISION",
                f"Circular FRZ revision chain detected: {' -> '.join(circular_chain)} -> {frz_id}. "
                f"Refusing to create circular revision chain.",
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
    """Extract FRZ package contents into SRC candidate package.

    Per D-01: rule-template projection, not LLM.
    With --cascade: runs full SSOT chain with gate between steps (D-08).

    Args:
        args: Parsed CLI arguments with 'frz', 'output', 'cascade' attributes.

    Returns:
        Exit code (0 = success, 1 = failure).
    """
    if not FRZ_ID_PATTERN.match(args.frz):
        print(
            f"ERROR: Invalid FRZ ID format: {args.frz}. Must match FRZ-xxx",
            file=sys.stderr,
        )
        return 2

    workspace_root = _find_workspace_root()

    # Cascade mode
    if getattr(args, "cascade", False):
        cascade_result = run_cascade(args.frz, workspace_root)
        print(json.dumps(cascade_result, ensure_ascii=False, indent=2))
        return 0 if cascade_result.get("ok") else 1

    # Single-step extraction: FRZ→SRC
    output_dir = Path(args.output)
    try:
        result = extract_src_from_frz(args.frz, workspace_root, output_dir)
        print(json.dumps({
            "ok": result.ok,
            "output_dir": result.output_dir,
            "anchors": result.anchors_registered,
            "guard": result.guard_verdict,
            "warnings": result.warnings,
        }, ensure_ascii=False, indent=2))
        return 0 if result.ok else 1
    except CommandError as e:
        print(f"ERROR [{e.status_code}]: {e.message}", file=sys.stderr)
        return e.exit_code


def run_cascade(frz_id: str, workspace_root: Path) -> dict[str, Any]:
    """Run full SSOT chain extraction with gate between steps.

    Per D-08: each step extracts → gate审核 → continue if approved.
    Missing extract functions are gracefully skipped with warnings.

    Args:
        frz_id: FRZ identifier.
        workspace_root: Root of the workspace.

    Returns:
        Cascade result dict with ok status, summary, and per-step results.
    """
    frz_record = get_frz(workspace_root, frz_id)
    if frz_record is None:
        raise CommandError("REGISTRY_MISS", f"FRZ not found: {frz_id}")

    frz_status = frz_record.get("status", "draft")
    if frz_status != "frozen":
        raise CommandError("POLICY_DENIED", f"FRZ not frozen: {frz_id} (status={frz_status})")

    # Load FRZ package for coverage checks
    package_ref = frz_record.get("package_ref", "")
    frz_pkg = None
    if package_ref and Path(package_ref).exists():
        frz_raw = yaml.safe_load(Path(package_ref).read_text(encoding="utf-8"))
        inner = frz_raw.get("frz_package", frz_raw)
        frz_pkg = _parse_frz_dict(inner)

    total_steps = len(STEP_MODULE_MAP)
    results: list[dict[str, Any]] = []
    passed = 0
    blocked = 0
    skipped = 0

    for step_n, (layer_name, module_path, func_name) in enumerate(STEP_MODULE_MAP, 1):
        print(f"[{step_n}/{total_steps}] {layer_name}: checking extract function...", flush=True)

        # Try to dynamically import the module and function
        try:
            mod = importlib.import_module(module_path)
            extract_fn = getattr(mod, func_name, None)
        except (ImportError, ModuleNotFoundError) as e:
            print(
                f"[WARNING] Extract function for {layer_name} not yet implemented "
                f"({func_name} in {module_path}) — cascade skipping",
                flush=True,
            )
            results.append({
                "layer": layer_name,
                "status": "skipped",
                "reason": f"Module or function not available: {e}",
            })
            skipped += 1
            continue

        if extract_fn is None or not callable(extract_fn):
            print(
                f"[WARNING] Extract function for {layer_name} not callable — cascade skipping",
                flush=True,
            )
            results.append({
                "layer": layer_name,
                "status": "skipped",
                "reason": f"{func_name} is not callable",
            })
            skipped += 1
            continue

        # Check FRZ coverage for downstream layers
        warnings: list[str] = []
        if frz_pkg is not None and layer_name in ("TECH", "UI", "TEST", "IMPL"):
            warnings = check_frz_coverage(frz_pkg, layer_name)
            for w in warnings:
                print(f"[WARNING] {w}", flush=True)

        # Run extract function
        try:
            result = extract_fn(frz_id, workspace_root)
            # Handle both ExtractResult dataclass and dict return types
            extract_ok = False
            if isinstance(result, dict):
                extract_ok = result.get("ok", True)
            else:
                # ExtractResult dataclass
                extract_ok = getattr(result, "ok", True)

            if not extract_ok:
                print(f"[{step_n}/{total_steps}] {layer_name}: FAILED", flush=True)
                results.append({
                    "layer": layer_name,
                    "status": "failed",
                    "result": result,
                })
                return {
                    "ok": False,
                    "failed_at": layer_name,
                    "results": results,
                }
        except CommandError as e:
            print(
                f"[{step_n}/{total_steps}] {layer_name}: ERROR [{e.status_code}]: {e.message}",
                flush=True,
            )
            results.append({
                "layer": layer_name,
                "status": "error",
                "error": str(e.message),
                "status_code": e.status_code,
            })
            return {
                "ok": False,
                "failed_at": layer_name,
                "results": results,
            }

        # Gate review between steps
        gate_ok = True
        try:
            gate_result = _run_gate_review(layer_name, workspace_root)
            if gate_result.get("verdict") != "approve":
                gate_ok = False
        except Exception:  # noqa: BLE001
            # Gate infrastructure may not be available — log but continue
            print(
                f"[INFO] Gate review for {layer_name} not available — continuing without gate",
                flush=True,
            )

        if gate_ok:
            print(f"[{step_n}/{total_steps}] {layer_name}: PASS", flush=True)
            results.append({
                "layer": layer_name,
                "status": "passed",
                "warnings": warnings,
            })
            passed += 1
        else:
            print(f"[{step_n}/{total_steps}] {layer_name}: BLOCKED by gate", flush=True)
            results.append({
                "layer": layer_name,
                "status": "blocked_by_gate",
                "warnings": warnings,
            })
            blocked += 1
            return {
                "ok": False,
                "blocked_at_gate": layer_name,
                "results": results,
            }

    return {
        "ok": True,
        "summary": {
            "total": total_steps,
            "passed": passed,
            "blocked": blocked,
            "skipped": skipped,
        },
        "results": results,
    }


def _run_gate_review(layer_name: str, workspace_root: Path) -> dict[str, Any]:
    """Run a gate review for the extracted layer.

    Per D-13: reuse existing gate infrastructure.
    Falls back to approve if gate infrastructure is unavailable.

    Args:
        layer_name: Current layer name.
        workspace_root: Root of the workspace.

    Returns:
        Gate result dict with verdict.
    """
    # Check if gate CLI infrastructure is available
    try:
        from cli.ll import main as cli_main
    except ImportError:
        return {"verdict": "approve", "note": "gate infrastructure unavailable"}

    # Build gate request for this layer
    gate_dir = workspace_root / "artifacts" / "frz-extract" / "_gate"
    ensure_parent(gate_dir)
    request_path = gate_dir / f"{layer_name.lower()}-submit.request.json"
    response_path = gate_dir / f"{layer_name.lower()}-submit.response.json"

    request = {
        "api_version": "v1",
        "command": "gate.submit-handoff",
        "request_id": f"req-frz-extract-{layer_name}-gate-submit",
        "workspace_root": workspace_root.as_posix(),
        "actor_ref": "ll-frz-manage",
        "trace": {"workflow_key": "extract.cascade"},
        "payload": {
            "producer_ref": "ll-frz-manage",
            "proposal_ref": f"extract-{layer_name}",
            "payload_ref": f"artifacts/frz-extract/{layer_name.lower()}",
            "pending_state": "gate_pending",
            "trace_context_ref": f"frz-extract-{layer_name}",
        },
    }
    request_path.write_text(
        json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    try:
        exit_code = cli_main(["gate", "submit-handoff", "--request", str(request_path), "--response-out", str(response_path)])
        if exit_code == 0 and response_path.exists():
            response = json.loads(response_path.read_text(encoding="utf-8"))
            return {
                "verdict": response.get("data", {}).get("verdict", "approve"),
                "response": response,
            }
    except Exception:  # noqa: BLE001
        pass

    return {"verdict": "approve", "note": "gate infrastructure unavailable"}


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

    # extract subcommand (Phase 8 implementation)
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
    extract_parser.add_argument(
        "--cascade",
        action="store_true",
        help="Run full SSOT chain extraction with gate between steps",
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
