"""Path and mode policy enforcement."""

from __future__ import annotations

from pathlib import Path

from cli.lib.errors import CommandError
from cli.lib.fs import to_canonical_path


MANAGED_ROOTS = ("artifacts", "contracts", "docs", "evidence", "ssot")
BLOCKED_ROOTS = ("cli", "skills", "tests", "deploy", "legacy", ".git")
STAGING_ROOTS = (".workflow", ".artifacts", ".local")


def classify_path(path: Path, workspace_root: Path) -> str:
    canonical = to_canonical_path(path, workspace_root)
    head = canonical.split("/", 1)[0]
    if head in MANAGED_ROOTS:
        return "managed_target"
    if head in STAGING_ROOTS:
        return "staging"
    if head in BLOCKED_ROOTS:
        return "illegal_root"
    return "unmanaged_workspace"


def policy_verdict(path: Path, requested_mode: str, workspace_root: Path) -> dict[str, str]:
    path_class = classify_path(path, workspace_root)
    if path_class == "illegal_root":
        raise CommandError("POLICY_DENIED", "writes into code or control roots are denied", [path_class])
    if requested_mode == "promote":
        if path_class != "managed_target":
            raise CommandError("POLICY_DENIED", "promote target must be a managed target", [path_class])
    elif requested_mode in {"write", "commit", "append-run-log", "create", "replace", "patch", "append"}:
        if path_class != "managed_target":
            raise CommandError("POLICY_DENIED", "managed writes must target managed roots", [path_class])
    elif requested_mode == "read":
        if path_class not in {"managed_target", "staging"}:
            raise CommandError("POLICY_DENIED", "managed reads cannot target arbitrary workspace paths", [path_class])
    return {
        "allow": "true",
        "path_class": path_class,
        "requested_mode": requested_mode,
        "canonical_path": to_canonical_path(path, workspace_root),
    }

