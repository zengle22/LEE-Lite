from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _approve_prototype(proto_dir: Path) -> None:
    review_path = proto_dir / "prototype-review-report.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["verdict"] = "approved"
    review["blocking_points"] = []
    review["reviewer_identity"] = "human.reviewer"
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gate_path = proto_dir / "prototype-freeze-gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate["freeze_ready"] = True
    gate["checks"]["human_review_approved"] = True
    gate["checks"]["no_blocking_points"] = True
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_proto_to_ui_emits_semantic_ledger(tmp_path: Path) -> None:
    feat_pkg = tmp_path / "feat-package"
    feat_pkg.mkdir()
    for name, payload in {
        "package-manifest.json": {},
        "feat-freeze-bundle.json": {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "status": "accepted",
            "source_refs": ["SRC-1"],
            "features": [
                {
                    "feat_ref": "FEAT-PROTO-TO-UI-001",
                    "title": "Deferred device connection",
                    "goal": "Support complete connection journey with retry and skip.",
                    "scope": ["multi-step", "retry", "skip"],
                    "constraints": ["non-blocking", "preserve journey state"],
                    "acceptance_checks": ["user can complete happy path", "user can retry after error"],
                    "source_refs": ["SRC-1"],
                    "design_impact_required": True,
                    "candidate_design_surfaces": ["prototype", "ui", "architecture", "tech"],
                    "surface_map_required_reason": "prototype and ui updates require owner routing",
                    "ui_units": [{"page_name": "Entry"}, {"page_name": "Result"}],
                }
            ],
        },
        "feat-freeze-gate.json": {"freeze_ready": True},
        "feat-review-report.json": {},
        "feat-acceptance-report.json": {},
        "feat-defect-list.json": {},
        "handoff-to-feat-downstreams.json": {},
        "execution-evidence.json": {},
        "supervision-evidence.json": {},
    }.items():
        (feat_pkg / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (feat_pkg / "feat-freeze-bundle.md").write_text("# stub\n", encoding="utf-8")
    (feat_pkg / "surface-map-bundle.json").write_text(
        json.dumps(
            {
                "artifact_type": "surface_map_package",
                "workflow_key": "dev.feat-to-surface-map",
                "feat_ref": "FEAT-PROTO-TO-UI-001",
                "related_feat_refs": ["FEAT-PROTO-TO-UI-001"],
                "design_surfaces": {
                    "prototype": [
                        {
                            "owner": "PROTO-COACH-MAIN",
                            "action": "update",
                            "scope": ["connection_flow"],
                            "reason": "extends existing prototype shell",
                        }
                    ],
                    "ui": [
                        {
                            "owner": "UI-COACH-SHELL",
                            "action": "update",
                            "scope": ["connection_card"],
                            "reason": "extends existing ui shell",
                        }
                    ],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (feat_pkg / "surface-map-freeze-gate.json").write_text(
        json.dumps({"freeze_ready": True}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    proto_skill = Path(__file__).resolve().parents[2] / "ll-dev-feat-to-proto"
    run_proto = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_proto.py",
            "run",
            "--input",
            str(feat_pkg),
            "--feat-ref",
            "FEAT-PROTO-TO-UI-001",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=proto_skill,
        capture_output=True,
        text=True,
        check=False,
    )
    proto_dir = Path(json.loads(run_proto.stdout)["artifacts_dir"])
    _approve_prototype(proto_dir)

    skill_dir = Path(__file__).resolve().parents[1]
    run_ui = subprocess.run(
        [
            sys.executable,
            "scripts/proto_to_ui.py",
            "run",
            "--input",
            str(proto_dir),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_ui.returncode == 0
    ui_dir = Path(json.loads(run_ui.stdout)["artifacts_dir"])
    ledger = json.loads((ui_dir / "ui-semantic-source-ledger.json").read_text(encoding="utf-8"))
    bundle = json.loads((ui_dir / "ui-spec-bundle.json").read_text(encoding="utf-8"))
    assert "ui_spec_semantic_sources" in ledger
    assert (ui_dir / "ui-spec-bundle.json").exists()
    assert bundle["journey_structural_spec_ref"] == "journey-ux-ascii.md"
    assert bundle["ui_shell_snapshot_ref"] == "ui-shell-spec.md"
    assert bundle["surface_map_ref"] == "surface-map-bundle.json"
    assert bundle["ui_owner_ref"] == "UI-COACH-SHELL"
    assert bundle["ui_action"] == "update"
    assert bundle["ui_ref"] == "UI-COACH-SHELL"
    assert bundle["prototype_owner_ref"] == "PROTO-COACH-MAIN"
    assert bundle["prototype_action"] == "update"
    assert any(entry["semantic_area"] == "journey_structure" for entry in ledger["ui_spec_semantic_sources"]["from_other_authority"])
    assert any(entry["semantic_area"] == "shell_frame" for entry in ledger["ui_spec_semantic_sources"]["from_other_authority"])


def test_proto_to_ui_rejects_pending_human_reviewer(tmp_path: Path) -> None:
    proto_dir = tmp_path / "prototype-package"
    proto_dir.mkdir()
    (proto_dir / "prototype-bundle.json").write_text(
        json.dumps(
            {
                "artifact_type": "prototype_package",
                "workflow_key": "dev.feat-to-proto",
                "feat_ref": "FEAT-BAD-REVIEW",
                "prototype_entry_ref": "prototype/index.html",
                "journey_structural_spec_ref": "journey-ux-ascii.md",
                "ui_shell_snapshot_ref": "ui-shell-spec.md",
                "ui_shell_source_ref": "skills/ll-dev-feat-to-proto/resources/ui-shell/default-ui-shell-spec.md",
                "ui_shell_version": "1.0.0",
                "ui_shell_snapshot_hash": "abc",
                "shell_change_policy": "governance-only",
                "surface_map_ref": "surface-map-bundle.json",
                "prototype_owner_ref": "PROTO-BAD-REVIEW",
                "prototype_action": "update",
                "ui_owner_ref": "UI-BAD-REVIEW",
                "ui_action": "update",
                "related_feat_refs": ["FEAT-BAD-REVIEW"],
                "pages": [{"page_id": "entry", "title": "Entry", "page_goal": "Goal", "main_path": ["A", "B"], "branch_paths": [], "states": [{"name": "initial", "ui_behavior": "ready"}], "buttons": [{"label": "Continue", "action": "next"}]}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (proto_dir / "journey-ux-ascii.md").write_text(
        "# Journey Structural Spec\n\n## 1. Journey Main Chain\n- A\n\n## 2. Page Map\n- entry\n\n## 3. Decision Points\n- none\n\n## 4. CTA Hierarchy\n- Continue\n\n## 5. Container Hints\n- page\n\n## 6. Error / Degraded / Retry Paths\n- none\n\n## 7. Open Questions / Frozen Assumptions\n- none\n",
        encoding="utf-8",
    )
    (proto_dir / "ui-shell-spec.md").write_text(
        "# UI Shell Source\n\n- ui_shell_source_id: UI-SHELL-DEFAULT-001\n- ui_shell_family: default-app-shell\n- ui_shell_version: 1.0.0\n- shell_change_policy: governance-only\n\n## App Shell\n- ok\n\n## Container Rules\n- ok\n\n## CTA Placement\n- ok\n\n## State Expression\n- ok\n\n## Common Structural Components\n- ok\n\n## Governance\n- ok\n",
        encoding="utf-8",
    )
    (proto_dir / "prototype-review-report.json").write_text(
        json.dumps(
            {
                "verdict": "approved",
                "review_contract_ref": "contract",
                "coverage_declaration": {"required_checks": [], "completed_checks": [], "not_checked": []},
                "journey_check": {"passed": True, "issues": []},
                "cta_hierarchy_check": {"passed": True, "issues": []},
                "flow_consistency_check": {"passed": True, "issues": []},
                "state_experience_check": {"passed": True, "issues": []},
                "feat_alignment_check": {"passed": True, "issues": []},
                "blocking_points": [],
                "human_adjustments": [],
                "reviewer_identity": "pending_human_review",
                "reviewed_at": "2026-04-03T10:00:00Z",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (proto_dir / "prototype-freeze-gate.json").write_text(
        json.dumps({"freeze_ready": True, "checks": {"human_review_approved": True}}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    skill_dir = Path(__file__).resolve().parents[1]
    validate = subprocess.run(
        [sys.executable, "scripts/proto_to_ui.py", "validate-input", "--input", str(proto_dir)],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 1
    assert "real human reviewer identity" in validate.stdout
