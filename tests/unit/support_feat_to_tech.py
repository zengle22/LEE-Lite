import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ll-dev-feat-to-tech" / "scripts" / "feat_to_tech.py"


class FeatToTechWorkflowHarness(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def run_tech_flow(self, repo_root: Path, input_dir: Path, feat_ref: str, run_id: str) -> Path:
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

    def make_feat_package(self, root: Path, run_id: str, bundle_json: dict[str, object]) -> Path:
        package_dir = root / "artifacts" / "epic-to-feat" / run_id
        package_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "status": bundle_json["status"],
            "schema_version": bundle_json["schema_version"],
            "epic_freeze_ref": bundle_json["epic_freeze_ref"],
            "src_root_id": bundle_json["src_root_id"],
            "feat_refs": bundle_json["feat_refs"],
        }
        markdown = [
            "---",
            *[f"{key}: {value}" for key, value in frontmatter.items() if key != "feat_refs"],
            "feat_refs:",
            *[f"  - {item}" for item in bundle_json["feat_refs"]],
            "source_refs:",
            *[f"  - {item}" for item in bundle_json["source_refs"]],
            "---",
            "",
            f"# {bundle_json['title']}",
            "",
            "## FEAT Bundle Intent",
            "",
            str(bundle_json["bundle_intent"]),
            "",
            "## EPIC Context",
            "",
            f"- epic_freeze_ref: {bundle_json['epic_freeze_ref']}",
            f"- src_root_id: {bundle_json['src_root_id']}",
            "",
            "## Boundary Matrix",
            "",
            *[f"- {item['feat_ref']}: {item['title']}" for item in bundle_json["boundary_matrix"]],
            "",
            "## FEAT Inventory",
            "",
            *[f"### {feature['feat_ref']} {feature['title']}" for feature in bundle_json["features"]],
            "",
            "## Acceptance and Review",
            "",
            "- upstream acceptance: approve",
            "",
            "## Downstream Handoff",
            "",
            "- workflow.dev.feat_to_tech",
            "",
            "## Traceability",
            "",
            *[f"- {item}" for item in bundle_json["source_refs"]],
        ]
        (package_dir / "feat-freeze-bundle.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (package_dir / "feat-freeze-bundle.json").write_text(
            json.dumps(bundle_json, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payloads = {
            "package-manifest.json": {"status": bundle_json["status"], "run_id": run_id},
            "feat-review-report.json": {"decision": "pass", "summary": "review ok"},
            "feat-acceptance-report.json": {"decision": "approve", "summary": "acceptance ok"},
            "feat-defect-list.json": [],
            "feat-freeze-gate.json": {"workflow_key": "product.epic-to-feat", "freeze_ready": True, "decision": "pass"},
            "handoff-to-feat-downstreams.json": {
                "target_workflows": [
                    {"workflow": "workflow.dev.feat_to_tech"},
                    {"workflow": "workflow.qa.feat_to_testset"},
                ],
                "derivable_children": ["TECH", "TESTSET"],
            },
            "execution-evidence.json": {"run_id": run_id, "decision": "pass"},
            "supervision-evidence.json": {"run_id": run_id, "decision": "pass"},
        }
        for name, payload in payloads.items():
            (package_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return package_dir

    def make_bundle_json(self, feature: dict[str, object], run_id: str = "feat-src001") -> dict[str, object]:
        feat_ref = str(feature["feat_ref"])
        return {
            "artifact_type": "feat_freeze_package",
            "workflow_key": "product.epic-to-feat",
            "workflow_run_id": run_id,
            "title": f"{feature['title']} FEAT Bundle",
            "status": "accepted",
            "schema_version": "1.0.0",
            "epic_freeze_ref": "EPIC-SRC001",
            "src_root_id": "SRC-001",
            "feat_refs": [feat_ref],
            "downstream_workflows": [
                "workflow.dev.feat_to_tech",
                "workflow.qa.feat_to_testset",
            ],
            "source_refs": [
                f"product.epic-to-feat::{run_id}",
                feat_ref,
                "EPIC-SRC001",
                "SRC-001",
                "ADR-009",
            ],
            "bundle_intent": "Derive a governed FEAT bundle for downstream design work.",
            "boundary_matrix": [
                {
                    "feat_ref": feat_ref,
                    "title": feature["title"],
                    "responsible_for": list(feature["scope"])[:2],
                    "not_responsible_for": list(feature.get("non_goals") or [])[:2],
                    "boundary_dependencies": list(feature.get("dependencies") or []),
                }
            ],
            "features": [feature],
        }
