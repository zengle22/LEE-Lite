#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from feat_to_surface_map_common import (  # noqa: E402
    build_freeze_gate,
    build_package_payload,
    build_review_report,
    resolve_input_dir,
    resolve_repo_root,
    stable_digest,
    utc_now,
    write_json,
    write_text,
)
from feat_to_surface_map_validation import validate_bundle_payload, validate_input_package, validate_output_package  # noqa: E402


def _artifact_rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _output_dir(repo_root: Path, run_id: str, feat_ref: str) -> Path:
    return repo_root / "artifacts" / "feat-to-surface-map" / f"{run_id}--{feat_ref}"


def _surface_summary_md(bundle: dict[str, Any]) -> str:
    selected = bundle["selected_feat"]
    surface_map = bundle["surface_map"]
    lines = [
        f"# Surface Map Bundle for {selected['title']}",
        "",
        "## Selected FEAT",
        "",
        f"- feat_ref: {selected['feat_ref']}",
        f"- title: {selected['title']}",
        f"- goal: {selected['goal']}",
        f"- scope: {', '.join(selected['scope']) if selected['scope'] else ''}",
        "",
        "## Design Impact",
        "",
        f"- design_impact_required: {str(bundle['design_impact_required']).lower()}",
        f"- owner_binding_status: {surface_map['owner_binding_status']}",
        f"- bypass_rationale: {surface_map.get('bypass_rationale') or ''}",
        "",
        "## Surface Map",
    ]
    for surface_name in ("architecture", "api", "ui", "prototype", "tech"):
        lines.append("")
        lines.append(f"### {surface_name.title()}")
        entries = surface_map["design_surfaces"].get(surface_name) or []
        if not entries:
            lines.append("[none]")
        for entry in entries:
            scope = ", ".join(entry.get("scope") or [])
            create_signals = ", ".join(entry.get("create_signals") or [])
            lines.append(f"- owner: {entry['owner']}")
            lines.append(f"  - action: {entry['action']}")
            if create_signals:
                lines.append(f"  - create_signals: {create_signals}")
            lines.append(f"  - scope: {scope}")
            lines.append(f"  - reason: {entry['reason']}")
    lines.extend(
        [
            "",
            "## Ownership Summary",
            "",
            *[f"- {line}" for line in surface_map.get("ownership_summary") or ["[none]"]],
            "",
            "## Create Justification",
            "",
            *[f"- {line}" for line in surface_map.get("create_justification_summary") or ["[none]"]],
            "",
            "## Downstream Handoff",
            "",
            f"- target_workflows: {', '.join(bundle['downstream_handoff']['target_workflows'])}",
            f"- surface_map_ref: {bundle['surface_map_ref']}",
            f"- feat_ref: {bundle['feat_ref']}",
            "",
            "## Traceability",
            "",
            *[f"- {ref}" for ref in bundle.get("source_refs") or []],
        ]
    )
    return "\n".join(lines)


def _manifest(run_id: str, feat_ref: str, bundle: dict[str, Any], artifacts_dir: Path, repo_root: Path) -> dict[str, Any]:
    return {
        "artifact_type": "surface_map_package",
        "workflow_key": "dev.feat-to-surface-map",
        "workflow_run_id": run_id,
        "status": bundle["status"],
        "feat_ref": feat_ref,
        "surface_map_ref": bundle["surface_map_ref"],
        "artifacts_dir": _artifact_rel(artifacts_dir, repo_root),
        "generated_at": utc_now(),
        "artifact_refs": {
            "surface_map_bundle": "surface-map-bundle.json",
            "surface_map_markdown": "surface-map-bundle.md",
            "surface_map_review_report": "surface-map-review-report.json",
            "surface_map_defect_list": "surface-map-defect-list.json",
            "surface_map_freeze_gate": "surface-map-freeze-gate.json",
        },
    }


def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    feat_ref = str(context["selected_feat_ref"]).strip()
    output_dir = _output_dir(repo_root, run_id, feat_ref)
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"], "artifacts_dir": str(output_dir)}
    output_dir.mkdir(parents=True, exist_ok=True)

    bundle = build_package_payload(context, run_id)
    validation_errors: list[str] = []
    validate_bundle_payload(validation_errors, bundle)
    review_report = build_review_report(run_id, feat_ref, validation_errors)
    gate = build_freeze_gate(review_report, validation_errors)
    defects = [{"severity": "P1", "title": error, "type": "validation"} for error in validation_errors]

    write_json(output_dir / "package-manifest.json", _manifest(run_id, feat_ref, bundle, output_dir, repo_root))
    write_json(output_dir / "surface-map-bundle.json", bundle)
    write_text(output_dir / "surface-map-bundle.md", _surface_summary_md(bundle))
    write_json(output_dir / "surface-map-review-report.json", review_report)
    write_json(output_dir / "surface-map-defect-list.json", defects)
    write_json(output_dir / "surface-map-freeze-gate.json", gate)
    write_json(
        output_dir / "execution-evidence.json",
        {
            "workflow_key": "dev.feat-to-surface-map",
            "run_id": run_id,
            "generated_at": utc_now(),
            "commands": [
                f"validate-input --feat-ref {feat_ref}",
                f"run --feat-ref {feat_ref}",
                "freeze-guard",
            ],
            "artifacts": [
                "package-manifest.json",
                "surface-map-bundle.json",
                "surface-map-bundle.md",
                "surface-map-review-report.json",
                "surface-map-defect-list.json",
                "surface-map-freeze-gate.json",
            ],
            "surface_map_digest": stable_digest(bundle["surface_map"]),
        },
    )
    write_json(
        output_dir / "supervision-evidence.json",
        {
            "workflow_key": "dev.feat-to-surface-map",
            "run_id": run_id,
            "reviewed_at": utc_now(),
            "reviewer": "system.surface-map-supervisor",
            "decision": review_report["verdict"],
            "notes": ["surface-map owner bindings validated", "freeze gate derived from structural output consistency"],
        },
    )
    output_errors, _ = validate_output_package(output_dir)
    if output_errors:
        review_report = build_review_report(run_id, feat_ref, output_errors)
        gate = build_freeze_gate(review_report, output_errors)
        defects = [{"severity": "P1", "title": error, "type": "validation"} for error in output_errors]
        write_json(output_dir / "surface-map-review-report.json", review_report)
        write_json(output_dir / "surface-map-defect-list.json", defects)
        write_json(output_dir / "surface-map-freeze-gate.json", gate)
        write_json(
            output_dir / "supervision-evidence.json",
            {
                "workflow_key": "dev.feat-to-surface-map",
                "run_id": run_id,
                "reviewed_at": utc_now(),
                "reviewer": "system.surface-map-supervisor",
                "decision": review_report["verdict"],
                "notes": ["surface-map owner bindings validated", "freeze gate derived from structural output consistency"],
            },
        )
        return {"ok": False, "errors": output_errors, "artifacts_dir": str(output_dir), "freeze_ready": False, "review_report": review_report, "gate": gate}
    return {
        "ok": True,
        "artifacts_dir": str(output_dir),
        "freeze_ready": gate["freeze_ready"],
        "review_report": review_report,
        "gate": gate,
        # NOTE: The dev.feat-to-surface-map skill should only materialize artifacts.
        # Formal SSOT materialization happens later under epic-to-feat gate control.
        "formal_surface_map_md_ref": None,
        "formal_surface_map_json_ref": None,
    }


def run_command(input_value: str, feat_ref: str, repo_root: str | None, allow_update: bool) -> int:
    repo_root_path = resolve_repo_root(repo_root)
    input_dir = resolve_input_dir(input_value, repo_root_path)
    errors, context = validate_input_package(input_dir, feat_ref)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    result = build_package(context, repo_root_path, str(context["bundle"].get("workflow_run_id") or feat_ref), allow_update)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def validate_input_command(input_value: str, feat_ref: str, repo_root: str | None) -> int:
    repo_root_path = resolve_repo_root(repo_root)
    input_dir = resolve_input_dir(input_value, repo_root_path)
    errors, context = validate_input_package(input_dir, feat_ref)
    print(json.dumps({"ok": not errors, "errors": errors, "context": {k: v for k, v in context.items() if k != "bundle" and k != "feature"}}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def validate_output_command(artifacts_dir: str) -> int:
    errors, result = validate_output_package(artifacts_dir)
    print(json.dumps({"ok": not errors, "errors": errors, "result": result}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def freeze_guard_command(artifacts_dir: str) -> int:
    errors, result = validate_output_package(artifacts_dir)
    ok = not errors and bool(result.get("freeze_ready"))
    print(json.dumps({"ok": ok, "errors": errors, "result": result}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Governed FEAT to surface-map workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.add_argument("--feat-ref", required=True)
    vin.add_argument("--repo-root", default=None)
    vin.set_defaults(func=lambda args: validate_input_command(args.input, args.feat_ref, args.repo_root))

    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--feat-ref", required=True)
    run.add_argument("--repo-root", default=None)
    run.add_argument("--allow-update", action="store_true")
    run.set_defaults(func=lambda args: run_command(args.input, args.feat_ref, args.repo_root, args.allow_update))

    alias = sub.add_parser("executor-run")
    alias.add_argument("--input", required=True)
    alias.add_argument("--feat-ref", required=True)
    alias.add_argument("--repo-root", default=None)
    alias.add_argument("--allow-update", action="store_true")
    alias.set_defaults(func=lambda args: run_command(args.input, args.feat_ref, args.repo_root, args.allow_update))

    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=lambda args: validate_output_command(args.artifacts_dir))

    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=lambda args: freeze_guard_command(args.artifacts_dir))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
