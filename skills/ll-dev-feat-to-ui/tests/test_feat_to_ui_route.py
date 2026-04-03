from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from feat_to_ui_route import _validate_route_artifact


def _write_feat_package(root: Path, feat_ref: str, feature: dict) -> Path:
    pkg = root / "feat-package"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "package-manifest.json").write_text("{}", encoding="utf-8")
    (pkg / "feat-freeze-gate.json").write_text(json.dumps({"freeze_ready": True}), encoding="utf-8")
    (pkg / "feat-freeze-bundle.json").write_text(
        json.dumps(
            {
                "artifact_type": "feat_freeze_package",
                "workflow_key": "product.epic-to-feat",
                "status": "accepted",
                "source_refs": ["FEAT-SOURCE"],
                "features": [{**feature, "feat_ref": feat_ref}],
            }
        ),
        encoding="utf-8",
    )
    for name in [
        "feat-freeze-bundle.md",
        "feat-review-report.json",
        "feat-acceptance-report.json",
        "feat-defect-list.json",
        "handoff-to-feat-downstreams.json",
        "execution-evidence.json",
        "supervision-evidence.json",
    ]:
        (pkg / name).write_text("{}" if name.endswith(".json") else "# stub\n", encoding="utf-8")
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


def test_route_script_blocks_high_complexity_direct_path(tmp_path: Path) -> None:
    pkg = _write_feat_package(
        tmp_path,
        "FEAT-UI-HIGH",
        {
            "title": "Device connection flow",
            "goal": "Multi-step connection with retry",
            "scope": ["multi-step", "retry", "skip", "state sync"],
            "constraints": ["non-blocking", "error recovery"],
            "acceptance_checks": ["retry path works"],
            "source_refs": ["SRC-1"],
            "ui_units": [{"page_name": "entry"}, {"page_name": "result"}],
        },
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_ui_route.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            "FEAT-UI-HIGH",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["deprecated"] is True
    assert "deprecated and disabled" in payload["errors"][0]


def test_route_artifact_rejects_optional_path_without_bypass_rationale(tmp_path: Path) -> None:
    route_path = tmp_path / "ui-derivation-route.json"
    route_path.write_text(
        json.dumps(
            {
                "ui_complexity_level": "medium",
                "route_decision": "prototype_optional",
                "routing_rationale": "workflow_branching",
                "evaluated_dimensions": {
                    "multi_step_flow": False,
                    "workflow_branching": True,
                    "async_or_stateful_behavior": False,
                    "user_decision_sensitivity": False,
                    "cta_or_information_hierarchy_risk": False,
                },
                "prototype_bypass_rationale": "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    errors = _validate_route_artifact(route_path)
    assert any("prototype_optional direct path requires prototype_bypass_rationale" in error for error in errors)


def test_route_script_allows_low_complexity_direct_path(tmp_path: Path) -> None:
    pkg = _write_feat_package(
        tmp_path,
        "FEAT-UI-LOW",
        {
            "title": "Edit nickname",
            "goal": "Update a single visible profile field.",
            "scope": ["single field edit"],
            "constraints": ["no new journey"],
            "acceptance_checks": ["user can save nickname"],
            "source_refs": ["SRC-1"],
            "ui_input_fields": [{"field": "nickname", "type": "string", "required": True, "source": "user_input"}],
            "ui_display_fields": [{"field": "current_nickname", "type": "string", "source": "display"}],
            "ui_api_touchpoints": ["PATCH /profile"],
            "ui_units": [
                {
                    "page_name": "Edit Nickname",
                    "page_type": "single-page form",
                    "page_goal": "Let the user update the nickname and save.",
                    "entry_condition": "User opens profile edit.",
                    "exit_condition": "User sees save success feedback.",
                    "main_user_path": ["Open page", "Edit nickname", "Click save", "See success"],
                }
            ],
        },
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_ui_route.py",
            "run",
            "--input",
            str(pkg),
            "--feat-ref",
            "FEAT-UI-LOW",
            "--repo-root",
            str(tmp_path),
            "--prototype-bypass-rationale",
            "single-screen edit with bounded save action",
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["deprecated"] is True
    assert "deprecated and disabled" in payload["errors"][0]


def test_route_validate_input_accepts_formal_feat_ref(tmp_path: Path) -> None:
    run_id = "feat-ui-formal"
    pkg = _write_feat_package(
        tmp_path / "artifacts" / "epic-to-feat",
        "FEAT-UI-FORMAL",
        {
            "title": "Edit nickname",
            "goal": "Update nickname.",
            "scope": ["single field edit"],
            "constraints": ["no new journey"],
            "acceptance_checks": ["user can save nickname"],
            "source_refs": ["SRC-1", "EPIC-1"],
            "ui_units": [
                {
                    "page_name": "Edit Nickname",
                    "page_type": "single-page form",
                    "page_goal": "Let the user update the nickname and save.",
                    "entry_condition": "User opens profile edit.",
                    "exit_condition": "User sees save success feedback.",
                    "main_user_path": ["Open page", "Edit nickname", "Click save", "See success"],
                }
            ],
        },
    )
    formal_ref = _register_formal_feat(tmp_path, "FEAT-UI-FORMAL", run_id, pkg)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/feat_to_ui_route.py",
            "validate-input",
            "--input",
            formal_ref,
            "--feat-ref",
            "FEAT-UI-FORMAL",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout
    payload = json.loads(result.stdout)
    assert payload["deprecated"] is True
    assert "deprecated and disabled" in payload["errors"][0]
