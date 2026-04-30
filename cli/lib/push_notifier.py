"""Push notification for gate FAIL events (ADR-055 §2.4).

Creates terminal highlight, draft phase preview, and T+4h reminder.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.fs import ensure_parent, write_text


def show_terminal_notification(feat_ref: str, bug_count: int, run_id: str) -> None:
    """Show highlighted terminal notification about gate FAIL.

    Uses ANSI colors for red/yellow highlights.
    """
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    msg = f"""{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║                     GATE EVALUATION: FAIL                     ║
╠══════════════════════════════════════════════════════════════╣
║  Feature: {feat_ref:<51}║
║  Bugs Opened: {bug_count:<3}{" " * 42}║
║  Run ID: {run_id:<53}║
║                                                              ║
║  {YELLOW}Next step: Run 'll-bug-remediate --feat-ref {feat_ref}'{RED}{" " * 21}║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    print(msg, file=sys.stderr)


def create_draft_phase_preview(
    workspace_root: Path,
    feat_ref: str,
    bugs: list[dict[str, Any]],
    run_id: str,
) -> Path:
    """Create draft phase preview in .planning/drafts/.

    Returns the path to the created preview file.
    """
    drafts_dir = workspace_root / ".planning" / "drafts"
    ensure_parent(drafts_dir / ".placeholder")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    preview_path = drafts_dir / f"{timestamp}-bug-fix-preview-{feat_ref}.md"

    bug_lines = []
    for bug in bugs:
        bug_lines.append(f"- **{bug['bug_id']}**: {bug.get('title', 'N/A')}")
        bug_lines.append(f"  - Severity: {bug.get('severity', 'medium')}")
        bug_lines.append(f"  - Gap Type: {bug.get('gap_type', 'code_defect')}")
        bug_lines.append(f"  - Coverage ID: {bug.get('coverage_id', 'N/A')}")
        manifest_ref = bug.get('manifest_ref', '')
        if manifest_ref:
            bug_lines.append(f"  - Manifest: {manifest_ref}")

    bug_list = "\n".join(bug_lines) if bug_lines else "- (no bugs)"

    content = f"""\
# Draft Bug Fix Phase Preview

## Feature
{feat_ref}

## Run ID
{run_id}

## Generated At
{datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}

## Bugs to Fix
{bug_list}

## Next Steps
1. Review the bugs above
2. Run 'll-bug-remediate --feat-ref {feat_ref}' to create formal phase
3. Execute phase to fix bugs
4. Re-run gate evaluation to verify fix
"""
    write_text(preview_path, content)
    return preview_path


def schedule_reminder(
    workspace_root: Path,
    feat_ref: str,
    bugs: list[dict[str, Any]],
    trigger_at: datetime,
    reminder_type: str = "t4h",
) -> None:
    """Schedule a reminder in artifacts/bugs/{feat_ref}/reminders.yaml.

    Writes append-only to the reminders file.
    """
    bugs_dir = workspace_root / "artifacts" / "bugs" / feat_ref
    ensure_parent(bugs_dir / ".placeholder")
    reminders_path = bugs_dir / "reminders.yaml"

    reminder = {
        "trigger_at": trigger_at.isoformat().replace('+00:00', 'Z') if trigger_at.tzinfo else trigger_at.isoformat() + "Z",
        "reminder_type": reminder_type,
        "bug_count": len(bugs),
        "bug_ids": [b["bug_id"] for b in bugs],
        "acknowledged": False,
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    }

    # Read existing reminders or create empty list
    if reminders_path.exists():
        with reminders_path.open("r", encoding="utf-8") as f:
            reminders = yaml.safe_load(f) or []
    else:
        reminders = []

    reminders.append(reminder)

    with reminders_path.open("w", encoding="utf-8") as f:
        yaml.dump(reminders, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_next_phase_number(workspace_root: Path) -> int:
    """Get the next available phase number by scanning .planning/phases/.

    Returns max_phase_number + 1, or 1 if no phases exist.
    """
    phases_dir = workspace_root / ".planning" / "phases"
    if not phases_dir.exists():
        return 1

    max_num = 0
    for phase_dir in phases_dir.iterdir():
        if not phase_dir.is_dir():
            continue
        name = phase_dir.name
        # Extract number from prefix like "025-..."
        if "-" in name:
            try:
                num = int(name.split("-")[0])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue

    return max_num + 1
