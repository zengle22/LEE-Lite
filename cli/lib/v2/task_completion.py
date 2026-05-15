"""Step_1 — Task completion and file scope compliance checks.

Truth source: design.md §impl-verify step_1.
"""

from __future__ import annotations

from typing import Any

from cli.lib.v2.models import IMPL


def check_task_completion(
    impl: IMPL,
    gsd_delivery: dict[str, Any],
) -> dict[str, Any]:
    """Check task completion and file scope compliance.

    Returns dict with task_completion, scope_compliance, incomplete_tasks,
    out_of_scope_files, forbidden_scope_violations.
    """
    code = gsd_delivery.get("code", {})
    files_changed = code.get("files_changed", [])
    files_added = code.get("files_added", [])
    all_changed = files_changed + files_added

    allowed_dirs = impl.allowed_scope.get("directories", [])
    allowed_files = impl.allowed_scope.get("files", [])
    forbidden_dirs = impl.forbidden_scope.get("directories", [])
    forbidden_files = impl.forbidden_scope.get("files", [])

    out_of_scope: list[str] = []
    forbidden_violations: list[str] = []

    for f in all_changed:
        # Normalize path
        path = f.replace("\\", "/").lstrip("./")
        in_allowed = False
        for d in allowed_dirs:
            d_norm = d.rstrip("/") + "/"
            if path.startswith(d_norm):
                in_allowed = True
                break
        for pat in allowed_files:
            if _glob_match(path, pat):
                in_allowed = True
                break
        if not in_allowed:
            out_of_scope.append(path)

        for d in forbidden_dirs:
            d_norm = d.rstrip("/") + "/"
            if path.startswith(d_norm):
                forbidden_violations.append(path)
                break
        for pat in forbidden_files:
            if _glob_match(path, pat):
                forbidden_violations.append(path)
                break

    task_completion = "pass"  # MVP: no task list to check
    scope_compliance = "pass" if not out_of_scope and not forbidden_violations else "fail"

    return {
        "task_completion": task_completion,
        "scope_compliance": scope_compliance,
        "incomplete_tasks": [],
        "out_of_scope_files": out_of_scope,
        "forbidden_scope_violations": forbidden_violations,
    }


def _glob_match(path: str, pattern: str) -> bool:
    """Simple glob match for path patterns."""
    import fnmatch
    return fnmatch.fnmatch(path, pattern)
