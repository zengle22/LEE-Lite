"""Patch-aware context resolver script.

Scans a workspace for patch artifacts and produces a YAML recording
of patch-awareness for AI workflow context injection.

Usage:
    python patch_aware_context.py resolve \
        --workspace-root /path/to/workspace \
        --feat-ref FEAT-001 \
        --output-dir /path/to/output \
        [--ai-reasoning "Free text reasoning"]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path so cli.lib is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from cli.lib.patch_awareness import PatchAwarenessStatus, PatchContext
from cli.lib.patch_schema import derive_grade
from cli.lib.test_exec_artifacts import resolve_patch_context


def summarize_patch(patch: dict[str, Any]) -> dict[str, Any]:
    """Extract a minimal summary from a single patch entry.

    Parameters
    ----------
    patch : dict
        A patch entry dict as produced by resolve_patch_context.

    Returns
    -------
    dict
        Minimal summary with only the fields needed for AI awareness.
    """
    change_class = patch.get("change_class", "other")
    grade_level = patch.get("grade_level", derive_grade(change_class).value)
    summary: dict[str, Any] = {
        "file_path": patch.get("file_path", ""),
        "change_class": change_class,
        "grade_level": grade_level,
        "grade_derived_from": "patch_schema.derive_grade",
        "patch_status": patch.get("patch_status", PatchAwarenessStatus.PENDING.value),
    }
    if "commit" in patch:
        summary["commit"] = patch["commit"]
    if "status" in patch:
        summary["git_status"] = patch["status"]
    return summary


def write_awareness_recording(
    patch_context: PatchContext,
    output_dir: Path,
    ai_reasoning: str = "",
) -> Path:
    """Write the patch-awareness.yaml recording file.

    Parameters
    ----------
    patch_context : PatchContext
        The resolved patch context from resolve_patch_context().
    output_dir : Path
        Directory to write the output file.
    ai_reasoning : str
        Optional AI reasoning text to embed in the recording.

    Returns
    -------
    Path
        Path to the written YAML file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    patch_scan_status = "none_found" if patch_context.none_found else "patches_found"

    summarized_patches = [
        summarize_patch(p) if not p.get("truncated") else p
        for p in patch_context.patches_found
    ]

    recording: dict[str, Any] = {
        "patch_awareness": {
            "feature_ref": patch_context.scan_ref,
            "scan_path": patch_context.scan_path,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "patch_scan_status": {
                "patches_found": summarized_patches,
                "none_found": patch_context.none_found,
            },
            "total_patches_detected": patch_context.total_count,
            "summary_budget": patch_context.summary_budget,
        }
    }

    if ai_reasoning:
        recording["patch_awareness"]["ai_reasoning"] = ai_reasoning

    output_file = output_dir / "patch-awareness.yaml"

    if yaml:
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(recording, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        # Fallback: write as plain YAML without PyYAML
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(_write_yaml_simple(recording))

    return output_file


def resolve_and_record(
    workspace_root: Path,
    feat_ref: str,
    output_dir: Path,
    ai_reasoning: str = "",
) -> Path:
    """Run the full resolve-and-record pipeline.

    Parameters
    ----------
    workspace_root : Path
        Root directory to scan for patches.
    feat_ref : str
        Feature reference string.
    output_dir : Path
        Directory for output recording.
    ai_reasoning : str
        Optional AI reasoning text.

    Returns
    -------
    Path
        Path to the written patch-awareness.yaml file.
    """
    ctx = resolve_patch_context(workspace_root, feat_ref)
    return write_awareness_recording(ctx, output_dir, ai_reasoning)


def _write_yaml_simple(data: dict[str, Any], indent: int = 0) -> str:
    """Minimal YAML serializer fallback when PyYAML is unavailable."""
    lines: list[str] = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_write_yaml_simple(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        if first:
                            lines.append(f"{prefix}  - {k}: {_yaml_scalar(v)}")
                            first = False
                        else:
                            lines.append(f"{prefix}    {k}: {_yaml_scalar(v)}")
                else:
                    lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")

    return "\n".join(lines) + "\n"


def _yaml_scalar(value: Any) -> str:
    """Format a scalar value for YAML output."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if any(c in s for c in (":", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`")):
        return f'"{s}"'
    return s


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Resolve patch context and record awareness for AI workflows",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # resolve subcommand
    resolve_parser = subparsers.add_parser("resolve", help="Scan workspace and record patch awareness")
    resolve_parser.add_argument(
        "--workspace-root",
        type=str,
        required=True,
        help="Root directory of the workspace to scan",
    )
    resolve_parser.add_argument(
        "--feat-ref",
        type=str,
        required=True,
        help="Feature reference identifier",
    )
    resolve_parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to write the patch-awareness.yaml output",
    )
    resolve_parser.add_argument(
        "--ai-reasoning",
        type=str,
        default="",
        help="Optional AI reasoning text to embed in the recording",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    workspace_root = Path(args.workspace_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not workspace_root.exists():
        print(f"Error: workspace root does not exist: {workspace_root}", file=sys.stderr)
        sys.exit(1)

    output_path = resolve_and_record(
        workspace_root=workspace_root,
        feat_ref=args.feat_ref,
        output_dir=output_dir,
        ai_reasoning=args.ai_reasoning,
    )

    print(f"Patch awareness recorded: {output_path}")


if __name__ == "__main__":
    main()
