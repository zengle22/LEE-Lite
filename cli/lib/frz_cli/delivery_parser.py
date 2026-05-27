"""GSD delivery package parser.

Truth source: design.md §Appendix B.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_gsd_delivery(gsd_dir: str | Path) -> dict[str, Any]:
    """Parse a GSD delivery directory.

    Expected structure:
        gsd_delivery_package/
          code/
            git.diff
            files_changed.list
            files_added.list
          engineering_docs/
            change_description.md
            key_decisions.md
            dependency_changes.md
            known_issues.md
            rollback_strategy.md
          execution_report.yaml
    """
    root = Path(gsd_dir)
    if not root.is_dir():
        raise ValueError(f"GSD delivery path is not a directory: {root}")

    code_dir = root / "code"
    docs_dir = root / "engineering_docs"

    def _read(path: Path) -> str:
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _read_lines(path: Path) -> list[str]:
        text = _read(path)
        return [line.strip() for line in text.splitlines() if line.strip()]

    return {
        "feat_ref": "",
        "code": {
            "git_diff": _read(code_dir / "git.diff"),
            "files_changed": _read_lines(code_dir / "files_changed.list"),
            "files_added": _read_lines(code_dir / "files_added.list"),
        },
        "engineering_artifacts": {
            "change_description": _read(docs_dir / "change_description.md"),
            "key_decisions": _read(docs_dir / "key_decisions.md"),
            "dependency_changes": _read(docs_dir / "dependency_changes.md"),
            "known_issues": _read(docs_dir / "known_issues.md"),
            "rollback_plan": _read(docs_dir / "rollback_strategy.md"),
        },
        "execution_report": {},
    }
