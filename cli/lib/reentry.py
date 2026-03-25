"""Re-entry helpers for revise and retry gate outcomes."""

from __future__ import annotations

from pathlib import Path

from cli.lib.fs import to_canonical_path, write_json
from cli.lib.registry_store import slugify


def create_reentry(
    workspace_root: Path,
    handoff_ref: str,
    decision_ref: str,
    decision_type: str,
    trace: dict[str, object],
    proposal_ref: str,
    review_context_ref: str = "",
) -> dict[str, str]:
    run_ref = str(trace.get("run_ref") or "run")
    slug = slugify(f"{run_ref}-{decision_type}-{handoff_ref}")
    reentry_path = workspace_root / "artifacts" / "active" / "reentry" / f"{slug}.json"
    child_run_ref = f"{run_ref}-{decision_type}"
    write_json(
        reentry_path,
        {
            "trace": trace,
            "handoff_ref": handoff_ref,
            "decision_ref": decision_ref,
            "decision_type": decision_type,
            "proposal_ref": proposal_ref,
            "review_context_ref": review_context_ref,
            "child_run_ref": child_run_ref,
        },
    )
    return {"reentry_ref": to_canonical_path(reentry_path, workspace_root), "child_run_ref": child_run_ref}
