from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.feat_to_surface_map import freeze_guard_command
from scripts.feat_to_surface_map_validation import validate_input_package, validate_output_package


def _write_feat_package(root: Path, feat_ref: str, *, design_impact_required: bool, include_surfaces: bool = True) -> Path:
    pkg = root / "feat-package"
    pkg.mkdir(parents=True, exist_ok=True)
    feature = {
        "feat_ref": feat_ref,
        "title": "Coach daily adjustment",
        "goal": "Adjust the plan after readiness and feedback signals.",
        "scope": ["daily-plan", "feedback", "adjustment"],
        "constraints": ["preserve existing plan ownership"],
        "acceptance_checks": [{"check": "adjustment is available"}],
        "source_refs": ["FEAT-SRC-1"],
        "design_impact_required": design_impact_required,
    }
    if include_surfaces:
        feature["design_surfaces"] = {
            "architecture": {
                "owner": "ARCH-COACH-CORE",
                "action": "update",
                "scope": ["daily_adjustment_flow"],
                "reason": "existing architecture already owns the plan adjustment flow",
            },
            "ui": {
                "owner": "UI-COACH-SHELL",
                "action": "create",
                "scope": ["adjustment_card"],
                "reason": "new visible surface needed for adjustment entry and diff rendering",
                "create_signals": [
                    "new long-lived owner",
                    "future multi-feat reuse",
                ],
            },
        }
    else:
        feature["surface_map_bypass_rationale"] = "backend-only routing placeholder with no new design surfaces"
    files = {
        "package-manifest.json": {},
        "feat-freeze-bundle.json": {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": "RUN-1",
            "status": "accepted",
            "epic_freeze_ref": "EPIC-1",
            "src_root_id": "SRC-1",
            "feat_refs": [feat_ref],
            "features": [feature],
            "source_refs": ["product.epic-to-feat::RUN-1", "FEAT-SRC-1", "EPIC-1", "SRC-1"],
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
    return pkg


def test_surface_map_cli_run_generates_freezable_package(tmp_path: Path) -> None:
    feat_ref = "FEAT-SM-001"
    pkg = _write_feat_package(tmp_path, feat_ref, design_impact_required=True, include_surfaces=True)
    run = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_surface_map.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            feat_ref,
            "--repo-root",
            str(tmp_path),
            "--allow-update",
        ],
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    result = json.loads(run.stdout)
    artifacts_dir = Path(result["artifacts_dir"])
    assert (artifacts_dir / "surface-map-bundle.json").exists()
    bundle = json.loads((artifacts_dir / "surface-map-bundle.json").read_text(encoding="utf-8"))
    assert bundle["artifact_type"] == "surface_map_package"
    assert bundle["surface_map_ref"] == f"SURFACE-MAP-{feat_ref}"
    assert bundle["design_impact_required"] is True
    assert bundle["surface_map"]["owner_binding_status"] == "bound"
    assert bundle["surface_map"]["design_surfaces"]["ui"][0]["action"] == "create"
    assert bundle["surface_map"]["design_surfaces"]["ui"][0]["create_signals"] == [
        "new long-lived owner",
        "future multi-feat reuse",
    ]
    assert result.get("formal_surface_map_md_ref") in (None, "")
    assert result.get("formal_surface_map_json_ref") in (None, "")
    errors, output_result = validate_output_package(artifacts_dir)
    assert not errors, errors
    assert output_result["freeze_ready"] is True
    assert freeze_guard_command(str(artifacts_dir)) == 0


def test_surface_map_create_requires_two_signals(tmp_path: Path) -> None:
    feat_ref = "FEAT-SM-003"
    pkg = _write_feat_package(tmp_path, feat_ref, design_impact_required=True, include_surfaces=True)
    bundle_path = pkg / "feat-freeze-bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["features"][0]["design_surfaces"]["ui"]["create_signals"] = ["new long-lived owner"]
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_surface_map.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            feat_ref,
            "--repo-root",
            str(tmp_path),
            "--allow-update",
        ],
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 1
    payload = json.loads(run.stdout)
    assert any("create requires at least two create_signals" in err for err in payload["errors"])


def test_surface_map_bypass_requires_explicit_rationale(tmp_path: Path) -> None:
    feat_ref = "FEAT-SM-002"
    pkg = _write_feat_package(tmp_path, feat_ref, design_impact_required=False, include_surfaces=False)
    errors, context = validate_input_package(pkg, feat_ref)
    assert not errors, errors
    run = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_surface_map.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            feat_ref,
            "--repo-root",
            str(tmp_path),
            "--allow-update",
        ],
        cwd=SKILL_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    result = json.loads(run.stdout)
    artifacts_dir = Path(result["artifacts_dir"])
    bundle = json.loads((artifacts_dir / "surface-map-bundle.json").read_text(encoding="utf-8"))
    assert bundle["design_impact_required"] is False
    assert bundle["surface_map_ref"] == f"SURFACE-MAP-{feat_ref}"
    assert bundle["surface_map"]["owner_binding_status"] == "bypassed"
    assert bundle["surface_map"]["bypass_rationale"]
    errors, output_result = validate_output_package(artifacts_dir)
    assert not errors, errors
    assert output_result["freeze_ready"] is True
