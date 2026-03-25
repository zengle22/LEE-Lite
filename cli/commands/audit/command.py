"""Audit operations for bypass detection and findings."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.protocol import CommandContext, run_with_protocol


def _build_findings(ctx: CommandContext) -> tuple[list[dict[str, object]], list[str]]:
    payload = ctx.payload
    diagnostics: list[str] = []
    findings: list[dict[str, object]] = []

    for path in payload.get("attempted_unmanaged_reads", []):
        findings.append(
            {
                "violation_type": "attempted_unmanaged_consumption",
                "severity": "blocker",
                "object_ref": path,
                "minimal_patch_scope": "route read through gateway+registry",
            }
        )
    for path in payload.get("bypass_write_paths", []):
        findings.append(
            {
                "violation_type": "bypass_write",
                "severity": "blocker",
                "object_ref": path,
                "minimal_patch_scope": "route write through artifact gateway",
            }
        )
    if not payload.get("gateway_receipt_refs"):
        diagnostics.append("gateway_receipt_refs missing; audit assumes potential bypass")
    if not payload.get("registry_refs"):
        diagnostics.append("registry_refs missing; audit cannot confirm formal lineage")
    if not findings and diagnostics:
        findings.append(
            {
                "violation_type": "evidence_gap",
                "severity": "warn",
                "object_ref": "audit-input",
                "minimal_patch_scope": "supply missing receipt and registry evidence",
            }
        )
    return findings, diagnostics


def _audit_handler(ctx: CommandContext):
    payload = ctx.payload
    for field in ("workspace_diff_ref", "gateway_receipt_refs", "registry_refs", "policy_verdict_refs"):
        ensure(field in payload, "INVALID_REQUEST", f"missing audit field: {field}")
    findings, diagnostics = _build_findings(ctx)
    status_code = "OK"
    message = "audit completed"
    bundle_ref = "artifacts/active/audit/finding-bundle.json"
    if ctx.action == "emit-finding-bundle":
        bundle_path = ctx.workspace_root / bundle_ref
        write_json(
            bundle_path,
            {"trace": ctx.trace, "findings": findings, "diagnostics": diagnostics, "severity_summary": _severity(findings)},
        )
    return status_code, message, {
        "canonical_path": bundle_ref,
        "finding_bundle_ref": bundle_ref,
        "severity_summary": _severity(findings),
        "minimal_patch_scope": [item["minimal_patch_scope"] for item in findings],
        "findings": findings,
    }, diagnostics, [bundle_ref]


def _severity(findings: list[dict[str, object]]) -> dict[str, int]:
    summary = {"blocker": 0, "warn": 0, "info": 0}
    for finding in findings:
        key = str(finding.get("severity", "info"))
        summary[key] = summary.get(key, 0) + 1
    return summary


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _audit_handler)

