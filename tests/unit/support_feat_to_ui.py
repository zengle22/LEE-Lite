import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-feat-to-ui" / "scripts" / "feat_to_ui.py"


class FeatToUiWorkflowHarness(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_ui_flow(self, repo_root: Path, input_dir: Path, feat_ref: str, run_id: str) -> Path:
        result = self.run_cmd(
            "run",
            "--input",
            str(input_dir),
            "--feat-ref",
            feat_ref,
            "--repo-root",
            str(repo_root),
            "--run-id",
            run_id,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(json.loads(result.stdout)["artifacts_dir"])

    def make_bundle_json(self, feature: dict[str, object], run_id: str) -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        return {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} FEAT Freeze Bundle",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC-009-001",
            "src_root_id": "SRC-009",
            "feat_refs": [feat_ref],
            "source_refs": [
                f"product.epic-to-feat::{run_id}",
                feat_ref,
                "EPIC-SRC-009-001",
                "SRC-009",
                "ADR-021",
            ],
            "features": [feature],
        }

    def make_feat_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "epic-to-feat" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "feat-freeze-bundle.md").write_text("# FEAT Bundle\n", encoding="utf-8")
        (package_dir / "feat-freeze-bundle.json").write_text(json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "feat-review-report.json": {"decision": "pass"},
            "feat-acceptance-report.json": {"decision": "approve"},
            "feat-defect-list.json": [],
            "feat-freeze-gate.json": {"workflow_key": "product.epic-to-feat", "freeze_ready": True, "decision": "pass"},
            "handoff-to-feat-downstreams.json": {"target_workflows": [{"workflow": "workflow.dev.feat_to_proto"}], "derivable_children": ["PROTOTYPE"]},
            "execution-evidence.json": {"run_id": run_id},
            "supervision-evidence.json": {"run_id": run_id},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir
