#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.ui_derivation_routing import PROTOTYPE_OPTIONAL, PROTOTYPE_REQUIRED, route_ui_derivation, validate_route_decision
from feat_to_ui import (
    load_json,
    repo_root_from,
    write_json,
)

DEPRECATION_MESSAGE = (
    "ll-dev-feat-to-ui is deprecated and disabled; use ll-dev-feat-to-proto first, then ll-dev-proto-to-ui after human-reviewed prototype freeze"
)


def _write_route_artifact(artifacts_dir: Path, route: dict[str, object], bypass_rationale: str | None) -> None:
    payload = dict(route)
    payload["prototype_bypass_rationale"] = bypass_rationale or route.get("prototype_bypass_rationale")
    write_json(artifacts_dir / "ui-derivation-route.json", payload)
    manifest_path = artifacts_dir / "package-manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        manifest["ui_derivation_route_ref"] = "ui-derivation-route.json"
        write_json(manifest_path, manifest)


def _validate_route_artifact(route_path: Path) -> list[str]:
    if not route_path.exists():
        return ["ui-derivation-route.json must exist"]
    route = load_json(route_path)
    errors = validate_route_decision(route)
    if route.get("route_decision") == PROTOTYPE_REQUIRED:
        errors.append("prototype_required route must not be freeze-ready through direct feat-to-ui path")
    if route.get("route_decision") == PROTOTYPE_OPTIONAL and not str(route.get("prototype_bypass_rationale") or "").strip():
        errors.append("prototype_optional direct path requires prototype_bypass_rationale")
    return errors


def run_workflow(
    input_path: str | Path,
    feat_ref: str,
    repo_root: Path,
    run_id: str = "",
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
    prototype_bypass_rationale: str | None = None,
) -> dict[str, object]:
    return {
        "ok": False,
        "deprecated": True,
        "errors": [DEPRECATION_MESSAGE],
        "input_path": str(input_path),
        "feat_ref": feat_ref,
    }


def command_run(args: argparse.Namespace) -> int:
    result = run_workflow(
        args.input,
        args.feat_ref,
        repo_root_from(args.repo_root),
        args.run_id or "",
        args.allow_update,
        args.revision_request or None,
        args.prototype_bypass_rationale or None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {"ok": False, "deprecated": True, "errors": [DEPRECATION_MESSAGE], "input_path": args.input, "feat_ref": args.feat_ref},
            ensure_ascii=False,
        )
    )
    return 1


def command_validate_output(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {"ok": False, "deprecated": True, "errors": [DEPRECATION_MESSAGE], "artifacts_dir": args.artifacts_dir},
            ensure_ascii=False,
        )
    )
    return 1


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {"ok": False, "deprecated": True, "errors": [DEPRECATION_MESSAGE], "artifacts_dir": args.artifacts_dir},
            ensure_ascii=False,
        )
    )
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deprecated feat-to-ui compatibility workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--feat-ref", required=True)
    run.add_argument("--repo-root")
    run.add_argument("--run-id")
    run.add_argument("--allow-update", action="store_true")
    run.add_argument("--revision-request")
    run.add_argument("--prototype-bypass-rationale")
    run.set_defaults(func=command_run)
    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.add_argument("--feat-ref", required=True)
    vin.add_argument("--repo-root")
    vin.set_defaults(func=command_validate_input)
    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=command_validate_output)
    ready = sub.add_parser("validate-package-readiness")
    ready.add_argument("--artifacts-dir", required=True)
    ready.set_defaults(func=command_validate_package_readiness)
    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=command_validate_package_readiness)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
