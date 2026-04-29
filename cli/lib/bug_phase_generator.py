"""Phase directory generator for bug fix workflows (ADR-055 §2.5)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.fs import write_text


# 6-task template per ADR-055 §2.5 (locked D-14)
PLAN_6TASK_TEMPLATE = """\
<task type="auto">
  <name>Task 1: Root Cause Analysis</name>
  <action>Analyze bug evidence from CONTEXT.md, identify root cause, output fix_hypothesis</action>
</task>

<task type="auto">
  <name>Task 2: Implement Fix</name>
  <action>Minimal-scope code change based on root cause analysis</action>
</task>

<task type="auto">
  <name>Task 3: Update Bug Status</name>
  <action>Transition bug status: fixing -> fixed</action>
</task>

<task type="auto">
  <name>Task 4: Verify Fix</name>
  <action>Run targeted test, transition fixed -> re_verify_passed or back to open</action>
</task>

<task type="auto">
  <name>Task 5: Review & Close</name>
  <action>If re_verify_passed and no new failures, auto-close bug</action>
</task>

<task type="auto">
  <name>Task 6: Update Failure Case</name>
  <action>Update failure case file with root cause and fix summary</action>
</task>
"""


def _build_context_md(bug: dict[str, Any]) -> str:
    """Render CONTEXT.md from bug record fields."""
    diagnostics = bug.get("diagnostics", [])
    diag_lines = "\n".join(f"- {d}" for d in diagnostics) if diagnostics else "- (none)"

    return f"""\
# Bug Context: {bug['bug_id']}

## Bug Record

- **Bug ID:** {bug['bug_id']}
- **Case ID:** {bug.get('case_id', 'N/A')}
- **Title:** {bug.get('title', 'N/A')}
- **Status:** {bug.get('status', 'open')}
- **Severity:** {bug.get('severity', 'medium')}
- **Gap Type:** {bug.get('gap_type', 'code_defect')}
- **Run ID:** {bug.get('run_id', 'N/A')}
- **Discovered At:** {bug.get('discovered_at', 'N/A')}

## Evidence

- **Actual:** {bug.get('actual', 'N/A')}
- **Expected:** {bug.get('expected', 'N/A')}
- **Evidence Ref:** {bug.get('evidence_ref', 'N/A')}

## Diagnostics

{diag_lines}
"""


def _build_plan_md(bugs: list[dict[str, Any]], is_batch: bool) -> str:
    """Render PLAN.md with frontmatter and 6-task template."""
    if is_batch:
        bug_ids = ", ".join(b["bug_id"] for b in bugs)
        title = f"Bug Fix Batch: {bug_ids}"
        task_sections = []
        for bug in bugs:
            bid = bug["bug_id"]
            section = PLAN_6TASK_TEMPLATE.replace(
                "<name>Task 1:", f"<name>[{bid}] Task 1:"
            ).replace(
                "<name>Task 2:", f"<name>[{bid}] Task 2:"
            ).replace(
                "<name>Task 3:", f"<name>[{bid}] Task 3:"
            ).replace(
                "<name>Task 4:", f"<name>[{bid}] Task 4:"
            ).replace(
                "<name>Task 5:", f"<name>[{bid}] Task 5:"
            ).replace(
                "<name>Task 6:", f"<name>[{bid}] Task 6:"
            )
            task_sections.append(f"### {bid}\n\n{section}")
        body = "\n\n".join(task_sections)
    else:
        title = f"Bug Fix: {bugs[0]['bug_id']}"
        body = PLAN_6TASK_TEMPLATE

    return f"""\
---
autonomous: false
phase: {title}
---

{body}
"""


def _build_discussion_log_md() -> str:
    """Return empty discussion log placeholder."""
    return "# Discussion Log\n\n"


def _build_summary_md() -> str:
    """Return empty summary placeholder."""
    return "# Summary\n\n"


def generate_bug_phase(
    workspace_root: Path,
    bug: dict[str, Any],
    phase_number: int,
) -> Path:
    """Generate a single-bug fix phase directory.

    Creates .planning/phases/{N}-bug-fix-{bug_id}/ with 4 files:
    CONTEXT.md, PLAN.md, DISCUSSION-LOG.md, SUMMARY.md
    """
    phase_dir = (
        workspace_root
        / ".planning"
        / "phases"
        / f"{phase_number:03d}-bug-fix-{bug['bug_id']}"
    )
    phase_dir.mkdir(parents=True, exist_ok=True)

    write_text(phase_dir / "CONTEXT.md", _build_context_md(bug))
    write_text(phase_dir / "PLAN.md", _build_plan_md([bug], is_batch=False))
    write_text(phase_dir / "DISCUSSION-LOG.md", _build_discussion_log_md())
    write_text(phase_dir / "SUMMARY.md", _build_summary_md())

    return phase_dir


def generate_batch_phase(
    workspace_root: Path,
    bugs: list[dict[str, Any]],
    phase_number: int,
) -> Path:
    """Generate a batch fix phase directory (max 3 same-feat same-module bugs).

    Creates .planning/phases/{N}-bug-fix-batch-{hash}/ with 4 files.
    Raises CommandError if more than 3 bugs provided.
    """
    if len(bugs) > 3:
        raise CommandError(
            "INVALID_REQUEST",
            f"batch size {len(bugs)} exceeds maximum of 3 bugs per phase",
        )

    batch_key = "-".join(b["bug_id"] for b in bugs)
    batch_hash = hashlib.md5(batch_key.encode()).hexdigest()[:8]
    phase_dir = (
        workspace_root
        / ".planning"
        / "phases"
        / f"{phase_number:03d}-bug-fix-batch-{batch_hash}"
    )
    phase_dir.mkdir(parents=True, exist_ok=True)

    write_text(phase_dir / "CONTEXT.md", _build_batch_context_md(bugs))
    write_text(phase_dir / "PLAN.md", _build_plan_md(bugs, is_batch=True))
    write_text(phase_dir / "DISCUSSION-LOG.md", _build_discussion_log_md())
    write_text(phase_dir / "SUMMARY.md", _build_summary_md())

    return phase_dir


def _build_batch_context_md(bugs: list[dict[str, Any]]) -> str:
    """Render batch CONTEXT.md with all bug records."""
    sections = []
    for bug in bugs:
        sections.append(_build_context_md(bug))
    return "\n---\n\n".join(sections)
