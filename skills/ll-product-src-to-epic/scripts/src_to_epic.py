#!/usr/bin/env python3
"""
CLI entrypoint for the lite-native src-to-epic runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src_to_epic_common import validate_input_package
from src_to_epic_runtime import (
    collect_evidence_report,
    repo_root_from,
    run_workflow,
    supervisor_review,
    validate_output_package,
    validate_package_readiness,
    executor_run,
)


def command_run(args: argparse.Namespace) -> int:
    result = run_workflow(
        input_path=args.input,
        repo_root=repo_root_from(args.repo_root, args.input),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
        revision_request_path=args.revision_request or None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_executor_run(args: argparse.Namespace) -> int:
    result = executor_run(
        input_path=args.input,
        repo_root=repo_root_from(args.repo_root, args.input),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
        revision_request_path=args.revision_request or None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
        revision_request_path=args.revision_request or None,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("freeze_ready") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(args.input, repo_root_from(args.repo_root, args.input))
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_validate_output(args: argparse.Namespace) -> int:
    errors, result = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_collect_evidence(args: argparse.Namespace) -> int:
    report_path = collect_evidence_report(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": True, "report_path": str(report_path)}, ensure_ascii=False))
    return 0


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def command_freeze_guard(args: argparse.Namespace) -> int:
    return command_validate_package_readiness(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the src-to-epic workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", required=True)
    run_parser.add_argument("--repo-root")
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--allow-update", action="store_true")
    run_parser.add_argument("--revision-request")
    run_parser.set_defaults(func=command_run)

    executor_parser = subparsers.add_parser("executor-run")
    executor_parser.add_argument("--input", required=True)
    executor_parser.add_argument("--repo-root")
    executor_parser.add_argument("--run-id")
    executor_parser.add_argument("--allow-update", action="store_true")
    executor_parser.add_argument("--revision-request")
    executor_parser.set_defaults(func=command_executor_run)

    supervisor_parser = subparsers.add_parser("supervisor-review")
    supervisor_parser.add_argument("--artifacts-dir", required=True)
    supervisor_parser.add_argument("--repo-root")
    supervisor_parser.add_argument("--run-id")
    supervisor_parser.add_argument("--allow-update", action="store_true")
    supervisor_parser.add_argument("--revision-request")
    supervisor_parser.set_defaults(func=command_supervisor_review)

    validate_input_parser = subparsers.add_parser("validate-input")
    validate_input_parser.add_argument("--input", required=True)
    validate_input_parser.add_argument("--repo-root")
    validate_input_parser.set_defaults(func=command_validate_input)

    validate_output_parser = subparsers.add_parser("validate-output")
    validate_output_parser.add_argument("--artifacts-dir", required=True)
    validate_output_parser.set_defaults(func=command_validate_output)

    collect_parser = subparsers.add_parser("collect-evidence")
    collect_parser.add_argument("--artifacts-dir", required=True)
    collect_parser.set_defaults(func=command_collect_evidence)

    readiness_parser = subparsers.add_parser("validate-package-readiness")
    readiness_parser.add_argument("--artifacts-dir", required=True)
    readiness_parser.set_defaults(func=command_validate_package_readiness)

    freeze_parser = subparsers.add_parser("freeze-guard")
    freeze_parser.add_argument("--artifacts-dir", required=True)
    freeze_parser.set_defaults(func=command_freeze_guard)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
