from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_feat_package(root: Path, feat_ref: str) -> Path:
    pkg = root / "feat-package"
    pkg.mkdir(parents=True, exist_ok=True)
    files = {
        "package-manifest.json": {},
        "feat-freeze-bundle.json": {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "status": "accepted",
            "source_refs": ["SRC-1"],
            "features": [
                {
                    "feat_ref": feat_ref,
                    "title": "Deferred device connection",
                    "goal": "Support complete connection journey with retry and skip.",
                    "scope": ["multi-step", "retry", "skip"],
                    "constraints": ["non-blocking", "preserve journey state"],
                    "acceptance_checks": ["user can complete happy path", "user can retry after error"],
                    "source_refs": ["SRC-1"],
                    "design_impact_required": True,
                    "candidate_design_surfaces": ["prototype", "ui", "architecture", "tech"],
                    "surface_map_required_reason": "prototype and ui shared assets must be resolved before derivation",
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
    }
    for name, payload in files.items():
        (pkg / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (pkg / "feat-freeze-bundle.md").write_text("# stub\n", encoding="utf-8")
    (pkg / "surface-map-bundle.json").write_text(
        json.dumps(
            {
                "artifact_type": "surface_map_package",
                "workflow_key": "dev.feat-to-surface-map",
                "surface_map_ref": f"SURFACE-MAP-{feat_ref}",
                "feat_ref": feat_ref,
                "related_feat_refs": [feat_ref],
                "surface_map": {
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
                    "ownership_summary": ["prototype: PROTO-COACH-MAIN (update)", "ui: UI-COACH-SHELL (update)"],
                    "create_justification_summary": [],
                    "owner_binding_status": "bound",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (pkg / "surface-map-freeze-gate.json").write_text(
        json.dumps({"freeze_ready": True}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return pkg


def _register_formal_feat(root: Path, feat_ref: str, run_id: str, package_dir: Path) -> str:
    formal_ref = f"formal.feat.{feat_ref.lower()}"
    formal_path = root / "ssot" / "feat" / f"{feat_ref}__demo.md"
    formal_path.parent.mkdir(parents=True, exist_ok=True)
    formal_path.write_text(f"---\nid: {feat_ref}\nssot_type: FEAT\nstatus: frozen\n---\n", encoding="utf-8")
    registry_path = root / "artifacts" / "registry" / f"formal-feat-{feat_ref.lower()}.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "artifact_ref": formal_ref,
                "managed_artifact_ref": f"ssot/feat/{feat_ref}__demo.md",
                "status": "materialized",
                "trace": {"run_ref": run_id, "workflow_key": "product.epic-to-feat"},
                "metadata": {
                    "layer": "formal",
                    "source_package_ref": str(package_dir.relative_to(root)).replace("\\", "/"),
                    "assigned_id": feat_ref,
                    "feat_ref": feat_ref,
                    "ssot_type": "FEAT",
                },
                "lineage": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return formal_ref


def test_feat_to_proto_requires_human_approval_before_freeze(tmp_path: Path) -> None:
    pkg = _write_feat_package(tmp_path, "FEAT-PROTO-001")
    skill_dir = Path(__file__).resolve().parents[1]
    run = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_proto.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            "FEAT-PROTO-001",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0
    result = json.loads(run.stdout)
    artifacts_dir = Path(result["artifacts_dir"])
    assert (artifacts_dir / "prototype" / "index.html").exists()
    bundle = json.loads((artifacts_dir / "prototype-bundle.json").read_text(encoding="utf-8"))
    completeness = json.loads((artifacts_dir / "prototype-completeness-report.json").read_text(encoding="utf-8"))
    assert bundle["journey_structural_spec_ref"] == "journey-ux-ascii.md"
    assert bundle["ui_shell_snapshot_ref"] == "ui-shell-spec.md"
    assert bundle["ui_shell_version"] == "1.0.0"
    assert bundle["shell_change_policy"] == "governance-only"
    assert bundle["surface_map_ref"] == "SURFACE-MAP-FEAT-PROTO-001"
    assert bundle["prototype_owner_ref"] == "PROTO-COACH-MAIN"
    assert bundle["prototype_action"] == "update"
    assert bundle["ui_owner_ref"] == "UI-COACH-SHELL"
    assert bundle["ui_action"] == "update"
    assert bundle["related_feat_refs"] == ["FEAT-PROTO-001"]
    assert len(bundle["ui_shell_snapshot_hash"]) == 64
    assert (artifacts_dir / "journey-ux-ascii.md").exists()
    assert (artifacts_dir / "ui-shell-spec.md").exists()
    assert completeness["journey_structural_spec"]["decision"] == "pass"
    assert completeness["ui_shell_snapshot"]["decision"] == "pass"

    freeze = subprocess.run(
        [sys.executable, "scripts/feat_to_proto.py", "freeze-guard", "--artifacts-dir", str(artifacts_dir)],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert freeze.returncode == 1

    review_path = artifacts_dir / "prototype-review-report.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["verdict"] = "approved"
    review["blocking_points"] = []
    review["reviewer_identity"] = "human.reviewer"
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review_cmd = subprocess.run(
        [sys.executable, "scripts/feat_to_proto.py", "supervisor-review", "--artifacts-dir", str(artifacts_dir), "--run-id", "proto-r1"],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert review_cmd.returncode == 0


def test_feat_to_proto_validate_input_accepts_formal_feat_ref(tmp_path: Path) -> None:
    run_id = "feat-proto-formal"
    pkg = _write_feat_package(tmp_path / "artifacts" / "epic-to-feat", "FEAT-PROTO-FORMAL")
    formal_ref = _register_formal_feat(tmp_path, "FEAT-PROTO-FORMAL", run_id, pkg)
    skill_dir = Path(__file__).resolve().parents[1]
    validate = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_proto.py",
            "validate-input",
            "--input",
            formal_ref,
            "--feat-ref",
            "FEAT-PROTO-FORMAL",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=skill_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate.returncode == 0, validate.stdout
