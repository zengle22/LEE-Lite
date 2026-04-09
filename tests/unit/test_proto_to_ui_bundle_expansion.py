from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-proto-to-ui" / "scripts" / "proto_to_ui.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _journey_doc() -> str:
    sections = [
        "## 1. Journey Main Chain",
        "## 2. Page Map",
        "## 3. Decision Points",
        "## 4. CTA Hierarchy",
        "## 5. Container Hints",
        "## 6. Error / Degraded / Retry Paths",
        "## 7. Open Questions / Frozen Assumptions",
    ]
    lines = ["# Journey Structural Spec", ""]
    for section in sections:
        lines.extend([section, "content", ""])
    return "\n".join(lines).rstrip() + "\n"


def _shell_doc() -> str:
    sections = [
        "## App Shell",
        "## Container Rules",
        "## CTA Placement",
        "## State Expression",
        "## Common Structural Components",
        "## Governance",
    ]
    lines = ["# UI Shell Snapshot", ""]
    for section in sections:
        lines.extend([section, "content", ""])
    return "\n".join(lines).rstrip() + "\n"


def test_proto_to_ui_expands_ui_spec_bundle_from_ui_spec_refs(tmp_path: Path) -> None:
    repo_root = tmp_path
    input_dir = repo_root / "artifacts" / "feat-to-proto" / "proto-demo"

    ui_spec_source = repo_root / "ssot" / "ui" / "SRC-TEST" / "UI-FEAT-SRC-TEST-001__example-ui-spec.md"
    _write_text(ui_spec_source, "# Example UI Spec\n\nSome UI standard.\n")

    _write_text(input_dir / "journey-ux-ascii.md", _journey_doc())
    _write_text(input_dir / "ui-shell-spec.md", _shell_doc())

    _write_json(
        input_dir / "prototype-review-report.json",
        {
            "verdict": "approved",
            "review_contract_ref": "ADR-040",
            "coverage_declaration": {"required_checks": [], "completed_checks": [], "not_checked": []},
            "blocking_points": [],
            "human_adjustments": [],
            "reviewer_identity": "tester.human",
            "reviewed_at": "2026-04-08T00:00:00Z",
            "journey_check": {"passed": True, "issues": []},
            "cta_hierarchy_check": {"passed": True, "issues": []},
            "flow_consistency_check": {"passed": True, "issues": []},
            "state_experience_check": {"passed": True, "issues": []},
            "feat_alignment_check": {"passed": True, "issues": []},
        },
    )
    _write_json(input_dir / "prototype-freeze-gate.json", {"workflow_key": "dev.feat-to-proto", "freeze_ready": True})

    _write_json(
        input_dir / "prototype-bundle.json",
        {
            "artifact_type": "prototype_package",
            "workflow_key": "dev.feat-to-proto",
            "workflow_run_id": "proto-demo",
            "schema_version": "1.0.0",
            "status": "accepted",
            "title": "Prototype Bundle",
            "feat_ref": "FEAT-SRC-TEST-001",
            "feat_title": "Test Feature",
            "source_refs": ["SRC-TEST"],
            "journey_structural_spec_ref": "journey-ux-ascii.md",
            "ui_shell_snapshot_ref": "ui-shell-spec.md",
            "ui_shell_source_ref": "shell-source",
            "ui_shell_version": "v1",
            "ui_shell_snapshot_hash": "hash",
            "shell_change_policy": "frozen",
            "surface_map_ref": "SURFACE-MAP-SRC-TEST-001",
            "prototype_owner_ref": "PROTO-TEST-001",
            "prototype_action": "create",
            "ui_owner_ref": "UI-TEST-001",
            "ui_action": "create",
            "pages": [],
            "ui_spec_refs": [ui_spec_source.relative_to(repo_root).as_posix()],
        },
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--input", str(input_dir), "--repo-root", str(repo_root), "--run-id", "proto2ui-demo"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    artifacts_dir = Path(payload["artifacts_dir"])
    markdown = (artifacts_dir / "ui-spec-bundle.md").read_text(encoding="utf-8")

    assert "## UI Spec Refs" in markdown
    assert "## UI Specs (Embedded)" in markdown
    assert "Some UI standard." in markdown

    completeness = json.loads((artifacts_dir / "ui-spec-completeness-report.json").read_text(encoding="utf-8"))
    assert completeness["decision"] == "pass"
    freeze_gate = json.loads((artifacts_dir / "ui-spec-freeze-gate.json").read_text(encoding="utf-8"))
    assert freeze_gate["freeze_ready"] is True

