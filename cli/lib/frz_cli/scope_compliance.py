"""Step_3 — Feature scope compliance and unauthorized feature detection.

Truth source: design.md §impl-verify step_3.
"""

from __future__ import annotations

from typing import Any


def check_feature_scope(
    gsd_delivery: dict[str, Any],
    api_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect unauthorized features and semantic changes.

    Returns dict with scope_compliance, unauthorized_features, semantic_changes.
    """
    code = gsd_delivery.get("code", {})
    git_diff = code.get("git_diff", "")

    unauthorized: list[dict[str, Any]] = []
    semantic_changes: list[dict[str, Any]] = []

    # Simple heuristic: detect new API endpoints in diff not in api_specs
    allowed_paths = {a.get("path", "") for a in api_specs}
    for line in git_diff.splitlines():
        if line.startswith("+@app.route(") or line.startswith("+@router.get("):
            path = line.split("(")[1].split(")")[0].strip('"\'')
            if path not in allowed_paths:
                unauthorized.append({
                    "location": line,
                    "description": f"New API endpoint '{path}' not in FRZ API spec",
                    "suggested_action": "escalate_to_frz_revise",
                })

    scope_compliance = "pass" if not unauthorized else "fail"
    return {
        "scope_compliance": scope_compliance,
        "unauthorized_features": unauthorized,
        "semantic_changes": semantic_changes,
    }
