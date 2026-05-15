"""Step_4 — Code change traceability verification.

Truth source: design.md §impl-verify step_4.
"""

from __future__ import annotations

import re
from typing import Any

from cli.lib.v2.models import FEAT


EXEMPT_PATTERNS = [
    "README.md",
    ".github/workflows/*.yml",
    "poetry.lock",
    "package-lock.json",
    ".env.example",
    ".gitignore",
    "pyproject.toml",
    "package.json",
    "docs/**/*.md",
    "scripts/*.sh",
]


def _is_exempt(path: str) -> bool:
    import fnmatch
    for pat in EXEMPT_PATTERNS:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, f"**/{pat}"):
            return True
    return False


def verify_traceability(
    gsd_delivery: dict[str, Any],
    feats: list[FEAT],
) -> dict[str, Any]:
    """Verify code changes trace back to SSOT requirements.

    Returns dict with traceability, full_traces, partial_traces, no_trace_items, exempt_items.
    """
    code = gsd_delivery.get("code", {})
    git_diff = code.get("git_diff", "")

    full_traces: list[dict[str, Any]] = []
    partial_traces: list[dict[str, Any]] = []
    no_trace_items: list[dict[str, Any]] = []
    exempt_items: list[dict[str, Any]] = []

    # Parse diff for changed files
    changed_files: list[str] = []
    for line in git_diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:].strip()
            changed_files.append(path)

    for path in changed_files:
        normalized = path.replace("\\", "/")
        if _is_exempt(normalized):
            exempt_items.append({"file": normalized, "reason": "infrastructure/tooling exempt"})
            continue

        # Simple heuristic: check if path contains feat-related keywords
        matched = False
        for feat in feats:
            feat_keywords = [feat.feat_id.lower(), feat.title.lower().split()[0]]
            if any(kw in normalized.lower() for kw in feat_keywords if len(kw) > 2):
                full_traces.append({"file": normalized, "feat_ref": feat.feat_id})
                matched = True
                break

        if not matched:
            # Check if path matches allowed scope patterns
            if "src/" in normalized or "test" in normalized:
                partial_traces.append({"file": normalized, "linked_requirement": "general implementation"})
            else:
                no_trace_items.append({"file": normalized})

    if no_trace_items:
        traceability = "fail"
    elif partial_traces:
        traceability = "conditional_pass"
    else:
        traceability = "pass"

    return {
        "traceability": traceability,
        "full_traces": full_traces,
        "partial_traces": partial_traces,
        "no_trace_items": no_trace_items,
        "exempt_items": exempt_items,
    }
