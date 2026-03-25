"""Evidence bundle command."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.fs import write_json
from cli.lib.protocol import CommandContext, run_with_protocol


def _evidence_handler(ctx: CommandContext):
    payload = ctx.payload
    evidence_refs = payload.get("evidence_refs", [])
    ensure(isinstance(evidence_refs, list), "INVALID_REQUEST", "evidence_refs must be a list")
    bundle_ref = "artifacts/active/evidence/evidence-bundle.json"
    write_json(ctx.workspace_root / bundle_ref, {"trace": ctx.trace, "evidence_refs": evidence_refs})
    return "OK", "evidence bundled", {
        "canonical_path": bundle_ref,
        "evidence_bundle_ref": bundle_ref,
        "evidence_count": len(evidence_refs),
    }, [], [bundle_ref]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _evidence_handler)
