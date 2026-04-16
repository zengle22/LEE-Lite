"""CLI entrypoint for the governed mainline runtime."""

from __future__ import annotations

import argparse
from typing import Callable

from cli.commands.artifact.command import handle as handle_artifact
from cli.commands.audit.command import handle as handle_audit
from cli.commands.evidence.command import handle as handle_evidence
from cli.commands.gate.command import handle as handle_gate
from cli.commands.job.command import handle as handle_job
from cli.commands.loop.command import handle as handle_loop
from cli.commands.registry.command import handle as handle_registry
from cli.commands.rollout.command import handle as handle_rollout
from cli.commands.skill.command import handle as handle_skill
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
    for action in ("submit-handoff", "show-pending", "decide", "create", "verify", "evaluate", "materialize", "dispatch", "release-hold", "close-run"):
        _add_action_parser(gate_sub, action)
    gate.set_defaults(handler=handle_gate)

    loop = groups.add_parser("loop")
    loop_sub = loop.add_subparsers(dest="action", required=True)
    for action in ("run-execution", "resume-execution", "show-status", "show-backlog", "recover-jobs"):
        _add_action_parser(loop_sub, action)
    loop.set_defaults(handler=handle_loop)

    job = groups.add_parser("job")
    job_sub = job.add_subparsers(dest="action", required=True)
    for action in ("claim", "release-hold", "run", "renew-lease", "complete", "fail"):
        _add_action_parser(job_sub, action)
    job.set_defaults(handler=handle_job)

    rollout = groups.add_parser("rollout")
    rollout_sub = rollout.add_subparsers(dest="action", required=True)
    for action in ("onboard-skill", "cutover-wave", "fallback-wave", "assess-skill", "validate-pilot", "summarize-readiness"):
        _add_action_parser(rollout_sub, action)
    rollout.set_defaults(handler=handle_rollout)

    skill = groups.add_parser("skill")
    skill_sub = skill.add_subparsers(dest="action", required=True)
    for action in ("impl-spec-test", "test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator", "failure-capture", "spec-reconcile", "tech-to-impl", "feat-to-apiplan", "prototype-to-e2eplan", "api-manifest-init", "e2e-manifest-init", "api-spec-gen", "e2e-spec-gen", "api-spec-to-tests", "e2e-spec-to-tests", "api-test-exec", "e2e-test-exec", "patch-capture", "patch-settle"):
        _add_action_parser(skill_sub, action)
    skill.set_defaults(handler=handle_skill)

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
