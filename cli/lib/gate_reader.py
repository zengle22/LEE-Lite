"""Load gate-ready and handoff-side objects."""

from __future__ import annotations

from pathlib import Path

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, load_json


def load_gate_ready_package(workspace_root: Path, package_ref: str) -> dict[str, object]:
    package = load_json(canonical_to_path(package_ref, workspace_root))
    for field in ("candidate_ref", "acceptance_ref", "evidence_bundle_ref"):
        ensure(field in package, "PRECONDITION_FAILED", f"gate ready package missing {field}")
    return package


def load_handoff(workspace_root: Path, handoff_ref: str) -> dict[str, object]:
    handoff = load_json(canonical_to_path(handoff_ref, workspace_root))
    for field in ("producer_ref", "proposal_ref", "payload_ref"):
        ensure(field in handoff, "PRECONDITION_FAILED", f"handoff missing {field}")
    return handoff
