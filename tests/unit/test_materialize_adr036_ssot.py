from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "materialize_adr036_ssot.py"
SPEC = importlib.util.spec_from_file_location("materialize_adr036_ssot", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_ui_scope_status_is_not_applicable_without_feat_to_ui_downstream() -> None:
    feat_bundle = {
        "downstream_workflows": [
            "workflow.dev.feat_to_tech",
            "workflow.qa.feat_to_testset",
        ]
    }
    assert MODULE.ui_scope_status(feat_bundle) == "not_applicable"


def test_release_index_omits_ui_refs_and_marks_not_applicable() -> None:
    release_index = MODULE.build_release_index(
        gate_ref="artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json",
        epic_path=ROOT / "ssot" / "epic" / "EPIC-IMPL-IMPLEMENTATION-READINESS__demo.md",
        feat_paths=["ssot/feat/FEAT-001__demo.md"],
        arch_paths=["ssot/architecture/ARCH-001__demo.md"],
        api_paths=["ssot/api/API-001__demo.md"],
        tech_paths=["ssot/tech/TECH-001__demo.md"],
        testset_paths=["ssot/testset/TESTSET-001__demo.yaml"],
        impl_paths=["ssot/impl/IMPL-001__demo.md"],
        ui_artifact_paths=["artifacts/feat-to-ui/demo/ui-spec-bundle.md"],
        ui_status="not_applicable",
    )
    gate_decision = MODULE.build_gate_decision("not_applicable")

    assert release_index["layer_applicability"]["ui"] == "not_applicable"
    assert "ui_artifact_refs" not in release_index
    assert "not_applicable" in " ".join(release_index["notes"])
    assert "feat-to-ui" not in str(gate_decision["summary"])
