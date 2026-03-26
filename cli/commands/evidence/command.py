"""Evidence bundling command."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.protocol import CommandContext, run_with_protocol


def _evidence_handler(ctx: CommandContext):
    refs = ctx.payload.get("refs", [])
    ensure(isinstance(refs, list) and refs, "INVALID_REQUEST", "refs must be a non-empty list")
    bundle_ref = "artifacts/active/evidence/evidence-bundle.json"
    write_json(canonical_to_path(bundle_ref, ctx.workspace_root), {"trace": ctx.trace, "refs": refs})
    return "OK", "evidence bundled", {
        "canonical_path": bundle_ref,
        "evidence_bundle_ref": bundle_ref,
    }, [], [bundle_ref]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _evidence_handler)

