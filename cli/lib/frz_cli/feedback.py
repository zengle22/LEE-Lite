"""Issue classification and FRZ Revise routing.

Truth source: design.md §Error Handling & Recovery, §FRZ Revise.
"""

from __future__ import annotations

from typing import Any

from frz_cli.models import FEAT, UI


def classify_issue(
    issue_type: str,
    description: str,
    feat: FEAT | None = None,
    ui: UI | None = None,
) -> dict[str, Any]:
    """Classify an issue into bug_fix / experience_patch / frz_revise.

    Routing rules:
    - Code doesn't match AC -> bug_fix
    - UI detail mismatch, no core impact -> experience_patch
    - Scope violation, semantic change -> frz_revise
    """
    if issue_type in ("unauthorized_feature", "scope_violation", "semantic_change"):
        return {
            "type": "frz_revise",
            "linked_src": "",
            "revise_scope": description,
            "requires_frz_thaw": True,
            "impact_assessment": "Major: scope or semantics changed",
        }

    if issue_type in ("ui_mismatch", "copy_mismatch", "visual_detail"):
        return {
            "type": "experience_patch",
            "linked_ui": ui.ui_id if ui else "",
            "patch_scope": description,
            "can_settle_locally": True,
        }

    # Default: bug fix
    return {
        "type": "bug_fix",
        "linked_feat": feat.feat_id if feat else "",
        "linked_ac": feat.acceptance_criteria[0] if feat and feat.acceptance_criteria else "",
        "fix_scope": description,
        "retry_flow": "re-implement -> re-verify",
    }


def route_issues(
    findings: list[dict[str, Any]],
    feats: list[FEAT],
    uis: list[UI],
) -> list[dict[str, Any]]:
    """Route all findings to appropriate channels."""
    routed: list[dict[str, Any]] = []
    for finding in findings:
        issue_type = finding.get("type", "bug_fix")
        description = finding.get("description", "")
        feat = feats[0] if feats else None
        ui = uis[0] if uis else None
        classification = classify_issue(issue_type, description, feat, ui)
        routed.append({**finding, **classification})
    return routed
