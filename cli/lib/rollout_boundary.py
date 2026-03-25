"""Scope boundary checks for governed rollout adoption."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import to_canonical_path, write_json


DISALLOWED_SCOPE_MARKERS = (
    "repository-wide",
    "global governance",
    "all file-governance cleanup",
    "full repo cleanup",
    "entire repository",
)


def check_scope_boundary(workspace_root: Path, payload: dict[str, Any], trace: dict[str, Any]) -> dict[str, str]:
    proposed = " ".join(str(item) for item in payload.get("proposed_scope_actions", []))
    proposed += " " + str(payload.get("proposal_summary", ""))
    lowered = proposed.lower()
    rejected = any(marker in lowered for marker in DISALLOWED_SCOPE_MARKERS)
    verdict_path = workspace_root / "artifacts" / "active" / "rollout" / "scope-boundary-verdict.json"
    note_path = workspace_root / "artifacts" / "active" / "rollout" / "scope-boundary-note.json"
    verdict = {
        "trace": trace,
        "scope_boundary_result": "reject" if rejected else "allow",
        "accepted_scope": "governed skill onboarding / pilot / cutover",
        "rejected_expansion": rejected,
    }
    note = {
        "trace": trace,
        "proposal_summary": str(payload.get("proposal_summary", "")),
        "rejected_expansion_note": "repository-wide governance expansion is out of scope" if rejected else "",
    }
    write_json(verdict_path, verdict)
    write_json(note_path, note)
    return {
        "scope_boundary_verdict_ref": to_canonical_path(verdict_path, workspace_root),
        "boundary_review_note_ref": to_canonical_path(note_path, workspace_root),
    }
