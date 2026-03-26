#!/usr/bin/env python3
"""CLI entrypoint for ll-gate-human-orchestrator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gate_human_orchestrator_common import validate_input_package
from gate_human_orchestrator_interaction import capture_decision, claim_next, close_run, prepare_round, show_pending
from gate_human_orchestrator_runtime import (
    collect_evidence_report,
    projection_comment,
    regenerate_projection,
    repo_root_from,
    run_workflow,
    supervisor_review,
    validate_output_package,
    validate_package_readiness,
)


def command_run(args: argparse.Namespace) -> int:
    result = run_workflow(
        input_path=Path(args.input).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.input).resolve()),
        run_id=args.run_id or "",
        decision=args.decision or "",
        decision_reason=args.decision_reason or "",
        decision_target=args.decision_target or "",
        audit_finding_refs=args.audit_finding_ref or None,
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_executor_run(args: argparse.Namespace) -> int:
    from gate_human_orchestrator_runtime import executor_run

    result = executor_run(
        input_path=Path(args.input).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.input).resolve()),
        run_id=args.run_id or "",
        decision=args.decision or "",
        decision_reason=args.decision_reason or "",
        decision_target=args.decision_target or "",
        audit_finding_refs=args.audit_finding_ref or None,
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("freeze_ready") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(Path(args.input).resolve())
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


def command_prepare_round(args: argparse.Namespace) -> int:
    result = prepare_round(
        input_path=Path(args.input).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.input).resolve()),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_show_pending(args: argparse.Namespace) -> int:
    result = show_pending(repo_root_from(args.repo_root))
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_claim_next(args: argparse.Namespace) -> int:
    result = claim_next(
        repo_root=repo_root_from(args.repo_root),
        run_id=args.run_id or "",
        allow_update=args.allow_update,
        actor_ref=args.actor_ref,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_capture_decision(args: argparse.Namespace) -> int:
    result = capture_decision(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        reply=args.reply,
        approver=args.approver,
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_close_run(args: argparse.Namespace) -> int:
    result = close_run(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_capture_comment(args: argparse.Namespace) -> int:
    result = projection_comment(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        comment_ref=args.comment_ref,
        comment_text=args.comment_text,
        comment_author=args.comment_author,
        target_block=args.target_block or "",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_regenerate_projection(args: argparse.Namespace) -> int:
    result = regenerate_projection(
        artifacts_dir=Path(args.artifacts_dir).resolve(),
        repo_root=repo_root_from(args.repo_root, Path(args.artifacts_dir).resolve()),
        updated_ssot_ref=args.updated_ssot_ref,
        revision_request_ref=args.revision_request_ref or "",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the gate human orchestrator workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_shared_flags(target: argparse.ArgumentParser) -> None:
        target.add_argument("--repo-root")
        target.add_argument("--run-id")
        target.add_argument("--decision", choices=["approve", "revise", "retry", "handoff", "reject"])
        target.add_argument("--decision-reason")
        target.add_argument("--decision-target")
        target.add_argument("--audit-finding-ref", action="append")
        target.add_argument("--allow-update", action="store_true")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", required=True)
    add_shared_flags(run_parser)
    run_parser.set_defaults(func=command_run)

    executor_parser = subparsers.add_parser("executor-run")
    executor_parser.add_argument("--input", required=True)
    add_shared_flags(executor_parser)
    executor_parser.set_defaults(func=command_executor_run)

    prepare_parser = subparsers.add_parser("prepare-round")
    prepare_parser.add_argument("--input", required=True)
    prepare_parser.add_argument("--repo-root")
    prepare_parser.add_argument("--run-id")
    prepare_parser.add_argument("--allow-update", action="store_true")
    prepare_parser.set_defaults(func=command_prepare_round)

    show_pending_parser = subparsers.add_parser("show-pending")
    show_pending_parser.add_argument("--repo-root")
    show_pending_parser.set_defaults(func=command_show_pending)

    claim_parser = subparsers.add_parser("claim-next")
    claim_parser.add_argument("--repo-root")
    claim_parser.add_argument("--run-id")
    claim_parser.add_argument("--actor-ref", default="ll-gate-human-orchestrator")
    claim_parser.add_argument("--allow-update", action="store_true")
    claim_parser.set_defaults(func=command_claim_next)

    capture_parser = subparsers.add_parser("capture-decision")
    capture_parser.add_argument("--artifacts-dir", required=True)
    capture_parser.add_argument("--reply", required=True)
    capture_parser.add_argument("--approver", required=True)
    capture_parser.add_argument("--repo-root")
    capture_parser.add_argument("--allow-update", action="store_true")
    capture_parser.set_defaults(func=command_capture_decision)

    close_parser = subparsers.add_parser("close-run")
    close_parser.add_argument("--artifacts-dir", required=True)
    close_parser.add_argument("--repo-root")
    close_parser.add_argument("--allow-update", action="store_true")
    close_parser.set_defaults(func=command_close_run)

    supervisor_parser = subparsers.add_parser("supervisor-review")
    supervisor_parser.add_argument("--artifacts-dir", required=True)
    supervisor_parser.add_argument("--repo-root")
    supervisor_parser.add_argument("--run-id")
    supervisor_parser.add_argument("--allow-update", action="store_true")
    supervisor_parser.set_defaults(func=command_supervisor_review)

    validate_input_parser = subparsers.add_parser("validate-input")
    validate_input_parser.add_argument("--input", required=True)
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

    capture_comment_parser = subparsers.add_parser("capture-comment")
    capture_comment_parser.add_argument("--artifacts-dir", required=True)
    capture_comment_parser.add_argument("--repo-root")
    capture_comment_parser.add_argument("--comment-ref", required=True)
    capture_comment_parser.add_argument("--comment-text", required=True)
    capture_comment_parser.add_argument("--comment-author", required=True)
    capture_comment_parser.add_argument("--target-block")
    capture_comment_parser.set_defaults(func=command_capture_comment)

    regenerate_parser = subparsers.add_parser("regenerate-projection")
    regenerate_parser.add_argument("--artifacts-dir", required=True)
    regenerate_parser.add_argument("--repo-root")
    regenerate_parser.add_argument("--updated-ssot-ref", required=True)
    regenerate_parser.add_argument("--revision-request-ref")
    regenerate_parser.set_defaults(func=command_regenerate_projection)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
