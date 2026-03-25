"""CLI entrypoint for the governed mainline runtime."""

from __future__ import annotations

import argparse
from typing import Callable

from cli.commands.artifact.command import handle as handle_artifact
from cli.commands.audit.command import handle as handle_audit
from cli.commands.evidence.command import handle as handle_evidence
from cli.commands.gate.command import handle as handle_gate
from cli.commands.registry.command import handle as handle_registry
from cli.commands.rollout.command import handle as handle_rollout
from cli.commands.validate.command import handle as handle_validate


Handler = Callable[[argparse.Namespace], int]


def _add_action_parser(group: argparse._SubParsersAction, name: str) -> argparse.ArgumentParser:
    parser = group.add_parser(name)
    parser.add_argument("--request", required=True)
    parser.add_argument("--response-out", required=True)
    parser.add_argument("--evidence-out")
    parser.add_argument("--workspace-root")
    parser.add_argument("--strict", action="store_true")
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ll")
    groups = parser.add_subparsers(dest="group", required=True)

    artifact = groups.add_parser("artifact")
    artifact_sub = artifact.add_subparsers(dest="action", required=True)
    for action in ("read", "write", "commit", "promote", "append-run-log"):
        _add_action_parser(artifact_sub, action)
    artifact.set_defaults(handler=handle_artifact)

    registry = groups.add_parser("registry")
    registry_sub = registry.add_subparsers(dest="action", required=True)
    for action in ("resolve-formal-ref", "verify-eligibility", "validate-admission", "publish-formal", "bind-record"):
        _add_action_parser(registry_sub, action)
    registry.set_defaults(handler=handle_registry)

    audit = groups.add_parser("audit")
    audit_sub = audit.add_subparsers(dest="action", required=True)
    for action in ("scan-workspace", "emit-finding-bundle", "submit-pilot-evidence"):
        _add_action_parser(audit_sub, action)
    audit.set_defaults(handler=handle_audit)

    gate = groups.add_parser("gate")
    gate_sub = gate.add_subparsers(dest="action", required=True)
    for action in ("submit-handoff", "show-pending", "decide", "create", "verify", "evaluate", "materialize", "dispatch", "close-run"):
        _add_action_parser(gate_sub, action)
    gate.set_defaults(handler=handle_gate)

    rollout = groups.add_parser("rollout")
    rollout_sub = rollout.add_subparsers(dest="action", required=True)
    for action in ("onboard-skill", "cutover-wave", "fallback-wave", "assess-skill", "validate-pilot", "summarize-readiness"):
        _add_action_parser(rollout_sub, action)
    rollout.set_defaults(handler=handle_rollout)

    validate = groups.add_parser("validate")
    validate_sub = validate.add_subparsers(dest="action", required=True)
    for action in ("request", "response"):
        _add_action_parser(validate_sub, action)
    validate.set_defaults(handler=handle_validate)

    evidence = groups.add_parser("evidence")
    evidence_sub = evidence.add_subparsers(dest="action", required=True)
    _add_action_parser(evidence_sub, "bundle")
    evidence.set_defaults(handler=handle_evidence)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Handler = args.handler
    return handler(args)
